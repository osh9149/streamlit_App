import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="기온으로 떠나는 시간여행", page_icon="🌡️", layout="wide")
DEFAULT_FILE = "전국기온데이터(1973-2026).csv"

st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#f6fbff 0%,#fffaf4 100%);}
.title {text-align:center;font-size:2.5rem;font-weight:800;color:#17324d;}
.subtitle {text-align:center;color:#607284;margin-bottom:1.3rem;}
.card {padding:1.1rem 1.2rem;border-radius:16px;background:white;
border:1px solid #e3ebf3;box-shadow:0 4px 15px rgba(30,60,90,.07);margin:.7rem 0;}
.history {padding:1.2rem;border-radius:16px;background:#fff9eb;
border-left:6px solid #f0a500;margin:.7rem 0 1rem;}
div[data-testid="stMetric"] {background:white;border:1px solid #e3ebf3;
padding:12px;border-radius:14px;}
</style>
""", unsafe_allow_html=True)


# -------------------- 데이터 불러오기 --------------------
def read_csv_file(source):
    raw = source.getvalue() if hasattr(source, "getvalue") else Path(source).read_bytes()
    last_error = None

    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            text = raw.decode(encoding)
            lines = text.splitlines()
            header_index = 0

            for i, line in enumerate(lines):
                clean = line.strip().replace("\t", "")
                if clean.startswith("날짜,") and "평균기온" in clean:
                    header_index = i
                    break

            table_text = "\n".join(lines[header_index:])
            df = pd.read_csv(io.StringIO(table_text))
            df.columns = [str(c).strip() for c in df.columns]
            df["날짜"] = df["날짜"].astype(str).str.strip()
            return df
        except Exception as e:
            last_error = e

    raise ValueError(f"CSV 파일을 읽지 못했습니다: {last_error}")


@st.cache_data
def load_default(path):
    return read_csv_file(path)


def clean_data(df):
    rename = {}
    for col in df.columns:
        c = str(col).replace(" ", "")
        if c == "날짜":
            rename[col] = "날짜"
        elif c == "지점":
            rename[col] = "지점"
        elif "평균기온" in c:
            rename[col] = "평균기온"
        elif "최저기온" in c:
            rename[col] = "최저기온"
        elif "최고기온" in c:
            rename[col] = "최고기온"

    df = df.rename(columns=rename).copy()
    needed = ["날짜", "평균기온", "최저기온", "최고기온"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError("필수 열 없음: " + ", ".join(missing))

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    for col in ["평균기온", "최저기온", "최고기온"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"]).sort_values("날짜")
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day
    df["월일"] = df["날짜"].dt.strftime("%m-%d")
    df["일교차"] = df["최고기온"] - df["최저기온"]
    return df.reset_index(drop=True)


def get_record(df, date_value):
    result = df[df["날짜"] == pd.Timestamp(date_value)]
    return None if result.empty else result.iloc[0]


def change_text(change):
    if pd.isna(change):
        return "비교할 자료가 충분하지 않습니다."
    if change >= 0.5:
        return f"과거보다 약 {change:.1f}℃ 높아졌습니다. 🔥"
    if change <= -0.5:
        return f"과거보다 약 {abs(change):.1f}℃ 낮아졌습니다. ❄️"
    return "과거와 비교해 큰 차이가 없습니다. 🙂"


# -------------------- 역사 사건 --------------------
EVENTS = [
    ("1979-10-26", "10·26 사건", "정치", "대한민국 현대 정치사의 큰 전환점이 된 사건입니다."),
    ("1980-05-18", "5·18 민주화운동 시작", "민주화", "광주에서 전개된 민주화운동입니다."),
    ("1987-06-10", "6월 민주항쟁 시작", "민주화", "대통령 직선제와 민주화를 요구한 시민운동입니다."),
    ("1988-09-17", "서울 올림픽 개막", "스포츠", "서울에서 열린 제24회 하계 올림픽의 개막일입니다."),
    ("1991-09-17", "남북한 유엔 동시 가입", "외교", "대한민국과 북한이 유엔에 동시에 가입한 날입니다."),
    ("1993-08-12", "금융실명제 실시", "경제", "금융 거래를 실제 이름으로 하도록 한 제도가 시행되었습니다."),
    ("1995-06-29", "삼풍백화점 붕괴", "사회", "안전과 책임의 중요성을 되새기게 한 대형 재난입니다."),
    ("1997-12-03", "IMF 구제금융 합의", "경제", "외환위기 속에서 IMF 구제금융 지원에 합의했습니다."),
    ("2000-06-13", "제1차 남북정상회담 시작", "남북관계", "평양에서 첫 남북정상회담이 시작되었습니다."),
    ("2002-06-22", "대한민국 월드컵 4강 진출", "스포츠", "대한민국이 스페인을 꺾고 월드컵 4강에 진출했습니다."),
    ("2007-12-07", "태안 기름 유출 사고", "환경", "충남 태안 앞바다에서 대규모 원유 유출 사고가 발생했습니다."),
    ("2010-11-23", "연평도 포격 사건", "남북관계", "연평도 포격으로 군인과 민간인 피해가 발생했습니다."),
    ("2014-04-16", "세월호 참사", "사회", "전남 진도 인근 해상에서 세월호가 침몰한 참사입니다."),
    ("2016-03-09", "이세돌과 알파고 첫 대국", "과학기술", "인공지능 알파고와 이세돌 9단의 대결이 시작되었습니다."),
    ("2018-02-09", "평창 동계올림픽 개막", "스포츠", "평창을 중심으로 열린 동계 올림픽의 개막일입니다."),
    ("2018-04-27", "판문점 남북정상회담", "남북관계", "판문점에서 남북 정상 간 회담이 열렸습니다."),
    ("2020-01-20", "국내 코로나19 첫 확진자 확인", "보건", "대한민국에서 코로나19 첫 확진자가 확인되었습니다."),
    ("2021-10-21", "누리호 1차 발사", "과학기술", "한국형 발사체 누리호가 처음 발사되었습니다."),
    ("2022-06-21", "누리호 2차 발사 성공", "과학기술", "누리호가 성능검증위성을 목표 궤도에 올렸습니다."),
]
history = pd.DataFrame(EVENTS, columns=["날짜", "사건", "분야", "설명"])
history["날짜"] = pd.to_datetime(history["날짜"])


# -------------------- 화면 상단과 데이터 설정 --------------------
st.markdown('<div class="title">🌡️ 기온으로 떠나는 시간여행</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">생일 기온 변화 · 연도 비교 · 역사적 사건의 날씨</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("📂 데이터 설정")
    upload = st.file_uploader("전국 기온 CSV 업로드", type=["csv"])

    try:
        if upload is not None:
            raw_df = read_csv_file(upload)
            source_name = upload.name
        elif Path(DEFAULT_FILE).exists():
            raw_df = load_default(DEFAULT_FILE)
            source_name = DEFAULT_FILE
        else:
            st.error(f"`{DEFAULT_FILE}`을 찾을 수 없습니다.")
            st.stop()

        data = clean_data(raw_df)
    except Exception as error:
        st.error(f"데이터 오류: {error}")
        st.stop()

    st.success(f"사용 데이터: {source_name}")
    st.caption(f"{data['날짜'].min():%Y-%m-%d} ~ {data['날짜'].max():%Y-%m-%d}")
    st.caption(f"총 {len(data):,}일")
    st.info("전국 대표 기온이므로 특정 도시의 실제 기온과 다를 수 있습니다.")


tab1, tab2, tab3 = st.tabs([
    "🎂 내 생일은 얼마나 더워졌을까?",
    "⏳ 기온 타임머신",
    "📜 역사 속 그날의 날씨",
])


# ==================== 1. 생일 기온 ====================
with tab1:
    st.subheader("🎂 내 생일은 얼마나 더워졌을까?")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        month = st.selectbox("생일 월", list(range(1, 13)))
    max_day = 29 if month == 2 else (30 if month in [4, 6, 9, 11] else 31)
    with c2:
        day = st.selectbox("생일 일", list(range(1, max_day + 1)))
    with c3:
        period = st.slider("과거·최근 평균 기간", 5, 20, 10)

    bday = data[(data["월"] == month) & (data["일"] == day)].copy()

    if bday.empty:
        st.warning("선택한 날짜의 자료가 없습니다.")
    else:
        bday = bday.sort_values("연도")
        n = min(period, len(bday) // 2)

        early = bday.head(n)["평균기온"].mean() if n >= 2 else np.nan
        recent = bday.tail(n)["평균기온"].mean() if n >= 2 else np.nan
        diff = recent - early if n >= 2 else np.nan

        warm = bday.loc[bday["평균기온"].idxmax()]
        cold = bday.loc[bday["평균기온"].idxmin()]
        latest = bday.iloc[-1]

        st.markdown(
            f'<div class="card"><h3>📅 {month}월 {day}일</h3><p>{change_text(diff)}</p></div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"초기 {n}개년 평균", "-" if pd.isna(early) else f"{early:.1f}℃")
        m2.metric(f"최근 {n}개년 평균", "-" if pd.isna(recent) else f"{recent:.1f}℃",
                  None if pd.isna(diff) else f"{diff:+.1f}℃")
        m3.metric("가장 더웠던 생일", f"{warm['평균기온']:.1f}℃", f"{int(warm['연도'])}년")
        m4.metric("가장 추웠던 생일", f"{cold['평균기온']:.1f}℃", f"{int(cold['연도'])}년")

        trend = bday.dropna(subset=["평균기온"]).copy()
        if len(trend) >= 2:
            slope, intercept = np.polyfit(trend["연도"], trend["평균기온"], 1)
            trend["추세선"] = slope * trend["연도"] + intercept
        else:
            slope = np.nan

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend["연도"], y=trend["평균기온"],
            mode="lines+markers", name="생일 평균기온",
            line=dict(color="#f39c12", width=2)
        ))
        if len(trend) >= 2:
            fig.add_trace(go.Scatter(
                x=trend["연도"], y=trend["추세선"],
                mode="lines", name="장기 추세",
                line=dict(color="#c0392b", width=3, dash="dash")
            ))
        fig.update_layout(
            title=f"{month}월 {day}일의 연도별 평균기온",
            xaxis_title="연도", yaxis_title="기온(℃)", hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        if not pd.isna(slope):
            st.info(f"📈 단순 선형 추세: 10년당 약 **{slope * 10:+.2f}℃**")

        rank = int(bday["평균기온"].rank(method="min", ascending=False).loc[latest.name])
        st.write(
            f"최근 자료인 **{int(latest['연도'])}년**의 평균기온은 "
            f"**{latest['평균기온']:.1f}℃**, 더운 순서로 **{rank}위**입니다."
        )

        with st.expander("연도별 생일 기온 보기"):
            show = bday[["날짜", "평균기온", "최저기온", "최고기온", "일교차"]].copy()
            show["날짜"] = show["날짜"].dt.strftime("%Y-%m-%d")
            st.dataframe(show, use_container_width=True, hide_index=True)


# ==================== 2. 기온 타임머신 ====================
with tab2:
    st.subheader("⏳ 기온 타임머신")

    years = sorted(data["연도"].unique().tolist())
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        year1 = st.selectbox("첫 번째 연도", years, index=0, key="y1")
    with c2:
        year2 = st.selectbox("두 번째 연도", years, index=max(0, len(years)-2), key="y2")
    with c3:
        month_range = st.slider("비교할 월", 1, 12, (1, 12))

    filtered = data[
        data["연도"].isin([year1, year2])
        & data["월"].between(month_range[0], month_range[1])
    ].copy()

    y1 = filtered[filtered["연도"] == year1]
    y2 = filtered[filtered["연도"] == year2]

    if y1.empty or y2.empty:
        st.warning("비교 자료가 충분하지 않습니다.")
    else:
        avg1 = y1["평균기온"].mean()
        avg2 = y2["평균기온"].mean()
        avg_diff = avg2 - avg1

        st.markdown(
            f'<div class="card"><h3>{year1}년 vs {year2}년</h3>'
            f'<p>{month_range[0]}~{month_range[1]}월 평균기온 차이: '
            f'<strong>{avg_diff:+.1f}℃</strong></p></div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"{year1} 평균", f"{avg1:.1f}℃")
        m2.metric(f"{year2} 평균", f"{avg2:.1f}℃", f"{avg_diff:+.1f}℃")
        m3.metric(f"{year1} 최고 기록", f"{y1['최고기온'].max():.1f}℃")
        m4.metric(f"{year2} 최고 기록", f"{y2['최고기온'].max():.1f}℃")

        frames = []
        for year in [year1, year2]:
            temp = filtered[filtered["연도"] == year].copy()
            temp["비교날짜"] = pd.to_datetime(
                "2000-" + temp["날짜"].dt.strftime("%m-%d"), errors="coerce"
            )
            temp["선택연도"] = str(year)
            frames.append(temp)

        compare = pd.concat(frames).dropna(subset=["비교날짜"])
        fig = px.line(
            compare, x="비교날짜", y="평균기온", color="선택연도",
            title=f"{year1}년과 {year2}년 일별 평균기온",
            labels={"비교날짜": "월·일", "평균기온": "기온(℃)", "선택연도": "연도"}
        )
        fig.update_xaxes(tickformat="%m월 %d일")
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        monthly = filtered.groupby(["연도", "월"])["평균기온"].mean().reset_index()
        monthly["연도"] = monthly["연도"].astype(str)
        fig2 = px.bar(
            monthly, x="월", y="평균기온", color="연도", barmode="group",
            title="월별 평균기온 비교",
            labels={"평균기온": "기온(℃)"}
        )
        fig2.update_xaxes(dtick=1)
        st.plotly_chart(fig2, use_container_width=True)

        d1 = y1[["월일", "평균기온"]].rename(columns={"평균기온": str(year1)})
        d2 = y2[["월일", "평균기온"]].rename(columns={"평균기온": str(year2)})
        merged = pd.merge(d1, d2, on="월일")
        merged["기온차"] = merged[str(year2)] - merged[str(year1)]

        if not merged.empty:
            highest = merged.loc[merged["기온차"].idxmax()]
            lowest = merged.loc[merged["기온차"].idxmin()]
            c1, c2 = st.columns(2)
            c1.success(f"🔥 차이가 가장 큰 날: **{highest['월일']}**, {highest['기온차']:+.1f}℃")
            c2.info(f"❄️ 반대 차이가 가장 큰 날: **{lowest['월일']}**, {lowest['기온차']:+.1f}℃")


# ==================== 3. 역사 속 날씨 ====================
with tab3:
    st.subheader("📜 역사 속 그날의 날씨")

    usable = history[history["날짜"].between(data["날짜"].min(), data["날짜"].max())].copy()
    c1, c2 = st.columns([1, 2])

    with c1:
        categories = ["전체"] + sorted(usable["분야"].unique().tolist())
        category = st.selectbox("분야", categories)

    options = usable if category == "전체" else usable[usable["분야"] == category]
    options = options.copy()
    options["표시"] = options["날짜"].dt.strftime("%Y-%m-%d") + " | " + options["사건"]

    with c2:
        selected = st.selectbox("역사적 사건", options["표시"].tolist())

    event = options[options["표시"] == selected].iloc[0]
    date = event["날짜"]
    weather = get_record(data, date)

    st.markdown(
        f'<div class="history"><h2>📌 {event["사건"]}</h2>'
        f'<p><b>날짜:</b> {date:%Y년 %m월 %d일} · <b>분야:</b> {event["분야"]}</p>'
        f'<p>{event["설명"]}</p></div>',
        unsafe_allow_html=True,
    )

    if weather is None:
        st.warning("이 날짜의 기온 자료가 없습니다.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("평균기온", f"{weather['평균기온']:.1f}℃")
        m2.metric("최고기온", f"{weather['최고기온']:.1f}℃")
        m3.metric("최저기온", f"{weather['최저기온']:.1f}℃")
        m4.metric("일교차", f"{weather['일교차']:.1f}℃")

        window = data[data["날짜"].between(
            date - pd.Timedelta(days=7), date + pd.Timedelta(days=7)
        )].copy()

        fig = go.Figure()
        for col, name, color in [
            ("최고기온", "최고기온", "#e74c3c"),
            ("평균기온", "평균기온", "#f39c12"),
            ("최저기온", "최저기온", "#2980b9"),
        ]:
            fig.add_trace(go.Scatter(
                x=window["날짜"], y=window[col], mode="lines+markers",
                name=name, line=dict(color=color)
            ))
        fig.add_vline(x=date, line_width=3, line_dash="dash", line_color="#8e44ad")
        fig.update_layout(
            title=f"{event['사건']} 전후 7일 기온",
            xaxis_title="날짜", yaxis_title="기온(℃)", hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        same_day = data[(data["월"] == date.month) & (data["일"] == date.day)].copy()
        event_index = same_day[same_day["날짜"] == date].index
        if len(event_index) > 0:
            rank = int(same_day["평균기온"].rank(method="min", ascending=False).loc[event_index[0]])
            normal = same_day["평균기온"].mean()
            st.info(
                f"같은 월·일의 역대 평균은 **{normal:.1f}℃**입니다. "
                f"사건 당일은 이보다 **{weather['평균기온'] - normal:+.1f}℃**, "
                f"더운 순서로 **{rank}위**입니다."
            )

        fig2 = px.line(
            same_day, x="연도", y="평균기온", markers=True,
            title=f"역대 {date.month}월 {date.day}일 평균기온",
            labels={"평균기온": "기온(℃)"}
        )
        fig2.add_scatter(
            x=[date.year], y=[weather["평균기온"]], mode="markers",
            name="사건 당일", marker=dict(size=15, symbol="star", color="#8e44ad")
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("#### 🔍 날짜 직접 탐색")
    custom = st.date_input(
        "확인할 날짜",
        value=date.date(),
        min_value=data["날짜"].min().date(),
        max_value=data["날짜"].max().date(),
    )
    custom_weather = get_record(data, custom)

    if custom_weather is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("평균기온", f"{custom_weather['평균기온']:.1f}℃")
        c2.metric("최저기온", f"{custom_weather['최저기온']:.1f}℃")
        c3.metric("최고기온", f"{custom_weather['최고기온']:.1f}℃")
    else:
        st.warning("선택한 날짜의 자료가 없습니다.")

    with st.expander("역사 사건을 추가하는 방법"):
        st.write("app.py 위쪽의 EVENTS 목록에 아래 형식으로 한 줄을 추가합니다.")
        st.code(
            '("2002-06-22", "사건 이름", "분야", "사건 설명"),',
            language="python"
        )

st.divider()
st.caption(
    "※ 전국 대표 기온 자료를 이용한 학습용 앱입니다. "
    "특정 지역의 실제 관측값과는 차이가 있을 수 있습니다."
)
