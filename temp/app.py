from pathlib import Path
from datetime import date, datetime
import io
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="기온으로 떠나는 시간여행",
    page_icon="🌡️",
    layout="wide",
)

# 같은 폴더에서 우선적으로 찾을 기본 파일명
PREFERRED_FILES = [
    "전국기온데이터(1973-2026)(1).csv",
    "전국기온데이터(1973-2026).csv",
    "전국기온데이터.csv",
]

# 역사 속 날씨 메뉴에 표시할 예시 사건
HISTORICAL_EVENTS = {
    "대한민국 제10대 대통령 취임": "1979-12-06",
    "서울 올림픽 개막": "1988-09-17",
    "대전 엑스포 개막": "1993-08-07",
    "2002 한일 월드컵 개막": "2002-05-31",
    "대한민국 월드컵 4강전": "2002-06-25",
    "서울 G20 정상회의 개막": "2010-11-11",
    "평창 동계올림픽 개막": "2018-02-09",
    "누리호 3차 발사 성공": "2023-05-25",
}

# =========================================================
# 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #fff9f0 0%, #f2f8ff 48%, #ffffff 100%);
    }
    .hero {
        padding: 2rem 2.2rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #ff7a59 0%, #ffb347 48%, #4facfe 100%);
        color: white;
        box-shadow: 0 12px 30px rgba(45, 92, 150, 0.18);
        margin-bottom: 1.2rem;
    }
    .hero h1 { margin: 0; font-size: 2.5rem; }
    .hero p { margin: .7rem 0 0; font-size: 1.08rem; }
    .info-card {
        padding: 1.15rem 1.25rem;
        border-radius: 18px;
        background: rgba(255,255,255,.92);
        border: 1px solid rgba(65,105,225,.12);
        box-shadow: 0 7px 20px rgba(30, 70, 120, .08);
        min-height: 135px;
    }
    .big-number {
        font-size: 2rem;
        font-weight: 800;
        margin-top: .3rem;
    }
    .warm { color: #ef553b; }
    .cool { color: #2f80ed; }
    .small-note { color: #5c677d; font-size: .9rem; }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.9);
        border: 1px solid rgba(70,100,160,.12);
        padding: 14px;
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🌡️ 기온으로 떠나는 시간여행</h1>
        <p>1973년부터 이어진 전국 기온 기록 속에서 나의 생일, 특별한 날짜, 역사적인 순간의 날씨를 만나보세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 데이터 불러오기
# =========================================================
def find_default_csv() -> Path | None:
    """app.py와 같은 폴더에서 기온 CSV를 자동으로 찾는다."""
    base_dir = Path(__file__).resolve().parent

    for filename in PREFERRED_FILES:
        candidate = base_dir / filename
        if candidate.exists():
            return candidate

    # 파일명이 조금 달라도 '기온'이 들어간 CSV를 우선 선택
    csv_files = list(base_dir.glob("*.csv"))
    temp_files = [p for p in csv_files if "기온" in p.name]
    if temp_files:
        return sorted(temp_files)[0]
    if csv_files:
        return sorted(csv_files)[0]
    return None


def decode_uploaded_file(raw: bytes) -> str:
    """한글 CSV에서 자주 쓰는 인코딩을 순서대로 시도한다."""
    for encoding in ("cp949", "euc-kr", "utf-8-sig", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 파일의 문자 인코딩을 확인할 수 없습니다.")


def detect_header_line(text: str) -> int:
    """'날짜'와 기온 열이 있는 실제 CSV 머리글 행을 자동으로 찾는다."""
    for index, line in enumerate(text.splitlines()):
        cleaned = line.strip().lstrip("\ufeff")
        if "날짜" in cleaned and "평균기온" in cleaned and "," in cleaned:
            return index
    return 0


@st.cache_data(show_spinner=False)
def load_temperature_data_from_text(text: str) -> pd.DataFrame:
    header_line = detect_header_line(text)
    df = pd.read_csv(io.StringIO(text), skiprows=header_line)

    # 열 이름과 값에 들어간 불필요한 공백 제거
    df.columns = [str(col).strip() for col in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # 열 이름이 조금 달라도 핵심 열을 찾을 수 있게 처리
    rename_map = {}
    for col in df.columns:
        compact = re.sub(r"\s+", "", col)
        if "날짜" in compact:
            rename_map[col] = "날짜"
        elif "평균기온" in compact:
            rename_map[col] = "평균기온"
        elif "최저기온" in compact:
            rename_map[col] = "최저기온"
        elif "최고기온" in compact:
            rename_map[col] = "최고기온"
        elif "지점" in compact or "지역" in compact:
            rename_map[col] = "지점"
    df = df.rename(columns=rename_map)

    required = ["날짜", "평균기온", "최저기온", "최고기온"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"필수 열을 찾을 수 없습니다: {', '.join(missing)}")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    for col in ["평균기온", "최저기온", "최고기온"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["날짜"]).copy()
    df = df.sort_values("날짜").drop_duplicates(subset=["날짜"], keep="last")
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day
    df["월일"] = df["날짜"].dt.strftime("%m-%d")
    return df.reset_index(drop=True)


def load_local_file(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    return load_temperature_data_from_text(decode_uploaded_file(raw))


# 기본 CSV 자동 읽기 + 업로드 대체 기능
local_csv = find_default_csv()
with st.sidebar:
    st.header("🗂️ 데이터 설정")
    uploaded_file = st.file_uploader(
        "다른 기온 CSV 사용",
        type=["csv"],
        help="업로드하지 않으면 app.py와 같은 폴더의 CSV를 자동 사용합니다.",
    )

try:
    if uploaded_file is not None:
        data = load_temperature_data_from_text(decode_uploaded_file(uploaded_file.getvalue()))
        source_name = uploaded_file.name
    elif local_csv is not None:
        data = load_local_file(local_csv)
        source_name = local_csv.name
    else:
        st.error("app.py와 같은 폴더에서 CSV 파일을 찾지 못했습니다. 왼쪽에서 파일을 업로드해 주세요.")
        st.stop()
except Exception as error:
    st.error(f"데이터를 읽는 중 오류가 발생했습니다: {error}")
    st.stop()

min_date = data["날짜"].min().date()
max_date = data["날짜"].max().date()

with st.sidebar:
    st.success(f"사용 중인 파일: {source_name}")
    st.caption(f"기간: {min_date:%Y-%m-%d} ~ {max_date:%Y-%m-%d}")
    st.caption(f"총 {len(data):,}일의 기온 기록")
    st.divider()
    menu = st.radio(
        "시간여행 메뉴",
        ["🎂 내 생일이 얼마나 더워졌을까", "⏳ 기온 타임머신", "🏛️ 역사 속 날씨"],
    )

# =========================================================
# 공통 함수
# =========================================================
def temperature_label(value: float) -> str:
    if pd.isna(value):
        return "자료 없음"
    return f"{value:.1f}℃"


def climate_message(change: float) -> tuple[str, str]:
    if pd.isna(change):
        return "비교할 자료가 충분하지 않습니다.", "small-note"
    if change >= 2:
        return f"🔥 최근 기온이 과거보다 {change:.1f}℃ 높아졌어요.", "warm"
    if change >= 0.5:
        return f"🌡️ 최근 기온이 과거보다 {change:.1f}℃ 높아졌어요.", "warm"
    if change <= -0.5:
        return f"❄️ 최근 기온이 과거보다 {abs(change):.1f}℃ 낮아졌어요.", "cool"
    return "🙂 과거와 최근의 평균기온 차이가 크지 않아요.", "small-note"


def nearest_weather(target: pd.Timestamp):
    """해당 날짜가 없을 때 가장 가까운 날짜의 자료를 반환한다."""
    idx = (data["날짜"] - target).abs().idxmin()
    return data.loc[idx]


def weather_for_date(target_date: date):
    target = pd.Timestamp(target_date)
    exact = data[data["날짜"] == target]
    if not exact.empty:
        return exact.iloc[0], True
    return nearest_weather(target), False


def render_weather_metrics(row):
    c1, c2, c3 = st.columns(3)
    c1.metric("평균기온", temperature_label(row["평균기온"]))
    c2.metric("최저기온", temperature_label(row["최저기온"]))
    c3.metric("최고기온", temperature_label(row["최고기온"]))

# =========================================================
# 1. 내 생일이 얼마나 더워졌을까
# =========================================================
if menu == "🎂 내 생일이 얼마나 더워졌을까":
    st.subheader("🎂 내 생일이 얼마나 더워졌을까?")
    st.write("생일의 기온이 오랜 시간 동안 어떻게 달라졌는지 확인해 보세요.")

    col1, col2 = st.columns(2)
    with col1:
        birth_month = st.selectbox("태어난 달", range(1, 13), index=4)
    with col2:
        max_day = 29 if birth_month == 2 else (30 if birth_month in [4, 6, 9, 11] else 31)
        birth_day = st.selectbox("태어난 날", range(1, max_day + 1), index=min(14, max_day - 1))

    birthday_data = data[(data["월"] == birth_month) & (data["일"] == birth_day)].copy()
    birthday_data = birthday_data.dropna(subset=["평균기온"])

    if birthday_data.empty:
        st.warning("선택한 날짜의 기온 자료가 없습니다.")
    else:
        first_n = birthday_data.head(min(10, len(birthday_data)))
        last_n = birthday_data.tail(min(10, len(birthday_data)))
        old_avg = first_n["평균기온"].mean()
        recent_avg = last_n["평균기온"].mean()
        change = recent_avg - old_avg
        hottest = birthday_data.loc[birthday_data["최고기온"].idxmax()]
        coldest = birthday_data.loc[birthday_data["최저기온"].idxmin()]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("과거 10회 평균", f"{old_avg:.1f}℃")
        m2.metric("최근 10회 평균", f"{recent_avg:.1f}℃", delta=f"{change:+.1f}℃")
        m3.metric("가장 더웠던 생일", f"{hottest['최고기온']:.1f}℃", f"{int(hottest['연도'])}년")
        m4.metric("가장 추웠던 생일", f"{coldest['최저기온']:.1f}℃", f"{int(coldest['연도'])}년")

        message, css_class = climate_message(change)
        st.markdown(
            f"<div class='info-card'><b>{birth_month}월 {birth_day}일 시간여행 결과</b>"
            f"<div class='big-number {css_class}'>{message}</div>"
            f"<div class='small-note'>초기 최대 10회와 최근 최대 10회의 평균기온을 비교한 결과입니다.</div></div>",
            unsafe_allow_html=True,
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=birthday_data["연도"], y=birthday_data["평균기온"],
            mode="lines+markers", name="평균기온"
        ))
        if len(birthday_data) >= 2:
            x = birthday_data["연도"].to_numpy()
            y = birthday_data["평균기온"].to_numpy()
            slope, intercept = np.polyfit(x, y, 1)
            fig.add_trace(go.Scatter(
                x=x, y=slope * x + intercept,
                mode="lines", name="장기 추세",
                line=dict(dash="dash")
            ))
        fig.update_layout(
            title=f"{birth_month}월 {birth_day}일의 연도별 평균기온",
            xaxis_title="연도", yaxis_title="기온(℃)",
            hovermode="x unified", height=470,
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 연도별 생일 기온 보기"):
            table = birthday_data[["연도", "평균기온", "최저기온", "최고기온"]].sort_values("연도", ascending=False)
            st.dataframe(table, use_container_width=True, hide_index=True)

# =========================================================
# 2. 기온 타임머신
# =========================================================
elif menu == "⏳ 기온 타임머신":
    st.subheader("⏳ 기온 타임머신")
    st.write("기억 속 날짜를 선택하고 그날의 전국 평균 기온으로 돌아가 보세요.")

    selected_date = st.date_input(
        "시간여행을 떠날 날짜",
        value=max(min(date(2000, 1, 1), max_date), min_date),
        min_value=min_date,
        max_value=max_date,
    )

    row, exact = weather_for_date(selected_date)
    if not exact:
        st.info(f"선택한 날짜의 자료가 없어 가장 가까운 {row['날짜']:%Y-%m-%d} 자료를 표시합니다.")

    st.markdown(f"### 📅 {row['날짜']:%Y년 %m월 %d일}의 날씨")
    render_weather_metrics(row)

    same_day = data[(data["월"] == row["월"]) & (data["일"] == row["일"])].dropna(subset=["평균기온"]).copy()
    selected_avg = row["평균기온"]
    normal_avg = same_day["평균기온"].mean()
    rank_hot = int((same_day["평균기온"] > selected_avg).sum() + 1) if not pd.isna(selected_avg) else None

    c1, c2 = st.columns(2)
    with c1:
        if rank_hot:
            st.markdown(
                f"<div class='info-card'><b>같은 날짜끼리 비교하면</b>"
                f"<div class='big-number warm'>{len(same_day)}개 연도 중 {rank_hot}번째로 따뜻함</div>"
                f"<div class='small-note'>같은 월·일의 평균기온을 높은 순서로 비교했습니다.</div></div>",
                unsafe_allow_html=True,
            )
    with c2:
        diff = selected_avg - normal_avg
        word = "높았습니다" if diff >= 0 else "낮았습니다"
        st.markdown(
            f"<div class='info-card'><b>장기 평균과 비교하면</b>"
            f"<div class='big-number'>{abs(diff):.1f}℃ {word}</div>"
            f"<div class='small-note'>이 날짜의 전체 연도 평균은 {normal_avg:.1f}℃입니다.</div></div>",
            unsafe_allow_html=True,
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=same_day["연도"], y=same_day["평균기온"],
        mode="lines+markers", name="같은 날짜 평균기온"
    ))
    fig.add_hline(y=normal_avg, line_dash="dot", annotation_text=f"전체 평균 {normal_avg:.1f}℃")
    fig.add_trace(go.Scatter(
        x=[row["연도"]], y=[row["평균기온"]],
        mode="markers", name="선택한 날짜", marker=dict(size=15, symbol="star")
    ))
    fig.update_layout(
        title=f"매년 {int(row['월'])}월 {int(row['일'])}일의 평균기온",
        xaxis_title="연도", yaxis_title="기온(℃)", height=470,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🗓️ 선택 날짜 전후 7일")
    around = data[
        (data["날짜"] >= row["날짜"] - pd.Timedelta(days=7)) &
        (data["날짜"] <= row["날짜"] + pd.Timedelta(days=7))
    ]
    fig2 = px.line(
        around, x="날짜", y=["최저기온", "평균기온", "최고기온"],
        markers=True, labels={"value": "기온(℃)", "variable": "구분"}
    )
    fig2.add_vline(x=row["날짜"].timestamp() * 1000, line_dash="dash")
    fig2.update_layout(height=420, hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# 3. 역사 속 날씨
# =========================================================
else:
    st.subheader("🏛️ 역사 속 날씨")
    st.write("역사적인 사건이 일어난 날의 기온을 살펴보고, 당시 계절의 모습을 상상해 보세요.")

    event_mode = st.radio("날짜 선택 방법", ["대표 사건에서 선택", "직접 입력"], horizontal=True)

    if event_mode == "대표 사건에서 선택":
        event_name = st.selectbox("역사적 사건", list(HISTORICAL_EVENTS.keys()))
        event_date = datetime.strptime(HISTORICAL_EVENTS[event_name], "%Y-%m-%d").date()
        st.caption(f"사건 날짜: {event_date:%Y-%m-%d}")
    else:
        event_name = st.text_input("사건 이름", value="나만의 역사적 순간")
        event_date = st.date_input(
            "사건 날짜",
            value=max(min(date(2000, 1, 1), max_date), min_date),
            min_value=min_date,
            max_value=max_date,
            key="history_date",
        )

    row, exact = weather_for_date(event_date)
    if not exact:
        st.info(f"해당 날짜의 자료가 없어 가장 가까운 {row['날짜']:%Y-%m-%d} 자료를 사용합니다.")

    st.markdown(f"### 📜 {event_name}")
    st.markdown(f"**{row['날짜']:%Y년 %m월 %d일}, 전국의 기온 기록**")
    render_weather_metrics(row)

    daily_range = row["최고기온"] - row["최저기온"]
    same_day = data[(data["월"] == row["월"]) & (data["일"] == row["일"])].dropna(subset=["평균기온"])
    percentile = (same_day["평균기온"] <= row["평균기온"]).mean() * 100

    feeling = "매우 더운 날" if row["평균기온"] >= 25 else (
        "포근한 날" if row["평균기온"] >= 15 else (
            "선선한 날" if row["평균기온"] >= 5 else "추운 날"
        )
    )

    st.markdown(
        f"<div class='info-card'><b>그날을 날씨로 읽어 보면</b>"
        f"<div class='big-number'>{feeling}이었어요.</div>"
        f"<div class='small-note'>일교차는 {daily_range:.1f}℃였고, 같은 날짜의 역대 기록 중 "
        f"약 {percentile:.0f}%보다 따뜻한 편이었습니다.</div></div>",
        unsafe_allow_html=True,
    )

    # 같은 해의 월별 평균과 사건 날짜 강조
    year_data = data[data["연도"] == row["연도"]].copy()
    monthly = year_data.groupby("월", as_index=False)[["평균기온", "최저기온", "최고기온"]].mean()
    fig = px.line(
        monthly, x="월", y=["최저기온", "평균기온", "최고기온"], markers=True,
        labels={"value": "월평균 기온(℃)", "variable": "구분"},
        title=f"{int(row['연도'])}년 월별 기온 흐름"
    )
    fig.add_vline(x=int(row["월"]), line_dash="dash", annotation_text="사건이 있었던 달")
    fig.update_xaxes(dtick=1)
    fig.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # 역사 탐구 질문
    st.markdown("#### 🧭 역사·지리 융합 탐구")
    questions = [
        f"{event_name} 당시 사람들의 옷차림과 야외 활동은 날씨의 영향을 받았을까요?",
        f"같은 {row['월']}월 {row['일']}일의 기온은 최근에 어떻게 달라지고 있을까요?",
        "당시 신문 기사나 사진 속 계절 표현과 실제 기온 기록은 일치할까요?",
    ]
    for q in questions:
        st.markdown(f"- {q}")

    with st.expander("🔎 같은 날짜의 역대 기온 기록"):
        history_table = same_day[["연도", "평균기온", "최저기온", "최고기온"]].sort_values("연도", ascending=False)
        st.dataframe(history_table, use_container_width=True, hide_index=True)

st.divider()
st.caption("※ 이 앱은 CSV에 기록된 전국 대표 기온 자료를 활용합니다. 지역별 실제 체감 날씨와는 차이가 있을 수 있습니다.")
