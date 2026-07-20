import html
import io
import math
import os
import random
from pathlib import Path

import folium
from folium.plugins import MarkerCluster
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium


# =========================================================
# 1. 페이지 기본 설정
# =========================================================
st.set_page_config(
    page_title="서울시 공영주차장 정보",
    page_icon="🚗",
    layout="wide",
)

# 프로젝트 폴더에 둘 기본 CSV 파일명
DEFAULT_CSV_NAME = "서울시 공영주차장 안내 정보.csv"

# 지도에 표시할 서울시청 기본 좌표
SEOUL_CITY_HALL = [37.5665, 126.9780]

# 앱에서 반드시 확인할 열
REQUIRED_COLUMNS = [
    "주차장명",
    "주소",
    "주차장 종류명",
    "운영구분명",
    "전화번호",
    "총 주차면",
    "유무료구분명",
    "야간무료개방여부명",
    "평일 운영 시작시각(HHMM)",
    "평일 운영 종료시각(HHMM)",
    "주말 운영 시작시각(HHMM)",
    "주말 운영 종료시각(HHMM)",
    "공휴일 운영 시작시각(HHMM)",
    "공휴일 운영 종료시각(HHMM)",
    "토요일 유,무료 구분명",
    "공휴일 유,무료 구분명",
    "월 정기권 금액",
    "기본 주차 요금",
    "기본 주차 시간(분 단위)",
    "추가 단위 요금",
    "추가 단위 시간(분 단위)",
    "일 최대 요금",
    "위도",
    "경도",
]

NUMERIC_COLUMNS = [
    "총 주차면",
    "월 정기권 금액",
    "기본 주차 요금",
    "기본 주차 시간(분 단위)",
    "추가 단위 요금",
    "추가 단위 시간(분 단위)",
    "일 최대 요금",
    "위도",
    "경도",
]

TIME_COLUMNS = [
    "평일 운영 시작시각(HHMM)",
    "평일 운영 종료시각(HHMM)",
    "주말 운영 시작시각(HHMM)",
    "주말 운영 종료시각(HHMM)",
    "공휴일 운영 시작시각(HHMM)",
    "공휴일 운영 종료시각(HHMM)",
]


# =========================================================
# 2. 화면 디자인 CSS
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f7fbff 0%, #ffffff 42%);
    }
    .main-title {
        padding: 1.15rem 1.3rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #e9f5ff, #fff8dc);
        border: 1px solid #d7ebff;
        box-shadow: 0 8px 24px rgba(30, 80, 120, 0.08);
        margin-bottom: 1rem;
    }
    .main-title h1 {
        margin: 0;
        font-size: 2.15rem;
    }
    .main-title p {
        margin: 0.45rem 0 0;
        color: #4c6072;
        font-size: 1.03rem;
    }
    .info-card {
        height: 100%;
        padding: 1rem 1.05rem;
        background: #ffffff;
        border: 1px solid #e6edf3;
        border-radius: 18px;
        box-shadow: 0 5px 18px rgba(40, 70, 100, 0.07);
    }
    .info-card h3 {
        margin: 0 0 0.55rem;
        font-size: 1.1rem;
        color: #20364a;
    }
    .info-card p {
        margin: 0.25rem 0;
        line-height: 1.55;
        color: #44586a;
    }
    .price-badge {
        display: inline-block;
        padding: 0.28rem 0.65rem;
        margin-bottom: 0.45rem;
        border-radius: 999px;
        background: #e7f7ec;
        color: #157a3a;
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5edf4;
        padding: 0.75rem 0.85rem;
        border-radius: 16px;
        box-shadow: 0 4px 14px rgba(40, 70, 100, 0.06);
    }
    div[data-testid="stSidebar"] {
        background: #f6faff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. 공통 함수
# =========================================================
def clean_text(value, default="정보 없음"):
    """결측치를 안전한 문자열로 바꾼다."""
    if pd.isna(value):
        return default
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    return text


def read_csv_bytes(file_bytes):
    """CSV 바이트를 cp949 우선, utf-8-sig 순서로 읽는다."""
    errors = []
    for encoding in ("cp949", "utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes), encoding=encoding), encoding
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
    raise ValueError("CSV 파일을 읽을 수 없습니다.\n" + "\n".join(errors))


@st.cache_data(show_spinner=False)
def load_default_csv(path_string):
    """프로젝트 폴더의 기본 CSV를 캐시하여 불러온다."""
    path = Path(path_string)
    file_bytes = path.read_bytes()
    return read_csv_bytes(file_bytes)


def format_hhmm(value):
    """900, 1830, 2400 형태를 09:00, 18:30, 24:00으로 바꾼다."""
    if pd.isna(value):
        return "정보 없음"
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return "정보 없음"

    if number == 2400:
        return "24:00"
    if number < 0 or number > 2359:
        return "정보 없음"

    hour, minute = divmod(number, 100)
    if hour > 23 or minute > 59:
        return "정보 없음"
    return f"{hour:02d}:{minute:02d}"


def make_time_range(start, end):
    """시작·종료 시간을 하나의 운영시간 문자열로 만든다."""
    start_text = format_hhmm(start)
    end_text = format_hhmm(end)
    if start_text == "정보 없음" and end_text == "정보 없음":
        return "정보 없음"
    return f"{start_text} ~ {end_text}"


def extract_district(address):
    """주소 첫 단어에서 서울시 자치구를 추출한다."""
    text = clean_text(address, "")
    if not text:
        return "기타"
    first_word = text.split()[0]
    return first_word if first_word.endswith("구") else "기타"


def preprocess_data(raw_df):
    """검색, 계산, 지도 표시에 필요한 전처리를 수행한다."""
    df = raw_df.copy()

    # 열 이름 앞뒤 공백 제거
    df.columns = [str(column).strip() for column in df.columns]

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        return None, missing

    # 문자 열은 공백 제거. 결측치는 이후 표시 함수에서 처리한다.
    text_columns = [
        "주차장명",
        "주소",
        "주차장 종류명",
        "운영구분명",
        "전화번호",
        "유무료구분명",
        "야간무료개방여부명",
        "토요일 유,무료 구분명",
        "공휴일 유,무료 구분명",
    ]
    for column in text_columns:
        df[column] = df[column].fillna("").astype(str).str.strip()

    # 숫자 열 변환
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # 운영시간 원본 열도 숫자로 변환
    for column in TIME_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # 자치구 및 보기 좋은 운영시간 열 생성
    df["자치구"] = df["주소"].apply(extract_district)
    df["평일 운영시간"] = df.apply(
        lambda row: make_time_range(
            row["평일 운영 시작시각(HHMM)"], row["평일 운영 종료시각(HHMM)"]
        ),
        axis=1,
    )
    df["주말 운영시간"] = df.apply(
        lambda row: make_time_range(
            row["주말 운영 시작시각(HHMM)"], row["주말 운영 종료시각(HHMM)"]
        ),
        axis=1,
    )
    df["공휴일 운영시간"] = df.apply(
        lambda row: make_time_range(
            row["공휴일 운영 시작시각(HHMM)"], row["공휴일 운영 종료시각(HHMM)"]
        ),
        axis=1,
    )
    return df, []


def calculate_parking_fee(row, parking_minutes):
    """선택한 주차 시간의 예상 요금을 계산한다."""
    payment_type = clean_text(row.get("유무료구분명"), "")
    if "무료" in payment_type and "유료" not in payment_type:
        return 0.0

    base_fee = row.get("기본 주차 요금")
    base_minutes = row.get("기본 주차 시간(분 단위)")
    extra_fee = row.get("추가 단위 요금")
    extra_minutes = row.get("추가 단위 시간(분 단위)")
    daily_max = row.get("일 최대 요금")

    # 유료 주차장인데 기본 요금 또는 기본 시간이 없으면 계산 불가
    if pd.isna(base_fee) or pd.isna(base_minutes) or base_minutes <= 0:
        return np.nan

    base_fee = max(float(base_fee), 0.0)
    base_minutes = float(base_minutes)

    if parking_minutes <= base_minutes:
        calculated = base_fee
    else:
        # 추가 요금 정보가 없으면 기본 시간 초과분을 계산할 수 없다.
        if (
            pd.isna(extra_fee)
            or pd.isna(extra_minutes)
            or float(extra_minutes) <= 0
        ):
            return np.nan
        extra_units = math.ceil((parking_minutes - base_minutes) / float(extra_minutes))
        calculated = base_fee + extra_units * max(float(extra_fee), 0.0)

    # 일 최대 요금이 실제 양수일 때만 상한 적용
    if not pd.isna(daily_max) and float(daily_max) > 0:
        calculated = min(calculated, float(daily_max))

    return float(calculated)


def format_money(value, missing_text="요금 정보 없음"):
    """금액을 1,000원 형식으로 표시한다."""
    if pd.isna(value):
        return missing_text
    return f"{int(round(float(value))):,}원"


def format_number(value, missing_text="정보 없음"):
    if pd.isna(value):
        return missing_text
    return f"{int(round(float(value))):,}"


def yes_no_filter_options(series):
    """데이터에 실제 존재하는 선택지를 정렬하여 반환한다."""
    values = [clean_text(value, "") for value in series.dropna().unique()]
    return sorted([value for value in values if value])


def card_html(row, title_icon="🅿️"):
    """주차장 한 건을 카드 HTML로 만든다."""
    title = html.escape(clean_text(row.get("주차장명")))
    address = html.escape(clean_text(row.get("주소")))
    parking_type = html.escape(clean_text(row.get("주차장 종류명")))
    phone = html.escape(clean_text(row.get("전화번호")))
    weekday = html.escape(clean_text(row.get("평일 운영시간")))
    saturday = html.escape(clean_text(row.get("토요일 유,무료 구분명")))
    holiday = html.escape(clean_text(row.get("공휴일 유,무료 구분명")))
    night = html.escape(clean_text(row.get("야간무료개방여부명")))
    spaces = format_number(row.get("총 주차면"))
    fee = format_money(row.get("예상 주차요금"))

    return f"""
    <div class="info-card">
        <div class="price-badge">💰 예상 요금 {fee}</div>
        <h3>{title_icon} {title}</h3>
        <p><b>📍 주소</b> {address}</p>
        <p><b>🏢 종류</b> {parking_type} · <b>주차면</b> {spaces}면</p>
        <p><b>🕒 평일 운영</b> {weekday}</p>
        <p><b>🆓 무료 조건</b> 토요일 {saturday} / 공휴일 {holiday}</p>
        <p><b>🌙 야간 개방</b> {night}</p>
        <p><b>☎️ 전화</b> {phone}</p>
    </div>
    """


def make_popup_html(row):
    """Folium 마커 팝업용 HTML을 만든다."""
    fields = {
        "🅿️ 주차장": clean_text(row.get("주차장명")),
        "📍 주소": clean_text(row.get("주소")),
        "💳 구분": clean_text(row.get("유무료구분명")),
        "💵 기본 요금": format_money(row.get("기본 주차 요금")),
        "🧮 예상 요금": format_money(row.get("예상 주차요금")),
        "🚙 주차면": f"{format_number(row.get('총 주차면'))}면",
        "🕒 평일 운영": clean_text(row.get("평일 운영시간")),
        "☎️ 전화": clean_text(row.get("전화번호")),
    }
    lines = [
        f"<div style='width:280px; line-height:1.6'><b>{html.escape(key)}</b>: "
        f"{html.escape(str(value))}</div>"
        for key, value in fields.items()
    ]
    return "".join(lines)


# =========================================================
# 4. 제목과 데이터 불러오기
# =========================================================
st.markdown(
    """
    <div class="main-title">
        <h1>🚗 서울시 공영주차장 정보</h1>
        <p>지역과 이용 조건에 맞는 서울시 공영주차장을 찾아보세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("📂 데이터 및 검색 설정")
    uploaded_file = st.file_uploader("공영주차장 CSV 업로드", type=["csv"])

try:
    if uploaded_file is not None:
        raw_df, used_encoding = read_csv_bytes(uploaded_file.getvalue())
        data_source = f"업로드 파일: {uploaded_file.name}"
    else:
        default_path = Path(__file__).resolve().parent / DEFAULT_CSV_NAME
        if not default_path.exists():
            st.error(
                f"기본 CSV 파일을 찾을 수 없습니다. `{DEFAULT_CSV_NAME}`을 app.py와 같은 폴더에 올리거나, 사이드바에서 파일을 업로드해 주세요."
            )
            st.stop()
        raw_df, used_encoding = load_default_csv(str(default_path))
        data_source = f"기본 파일: {DEFAULT_CSV_NAME}"
except Exception as exc:
    st.error(f"CSV 파일을 불러오는 중 오류가 발생했습니다.\n\n{exc}")
    st.stop()

parking_df, missing_columns = preprocess_data(raw_df)
if missing_columns:
    st.error("필요한 열이 없어 앱을 실행할 수 없습니다.")
    st.write("누락된 열:", missing_columns)
    st.info("첨부된 서울시 공영주차장 원본 CSV 구조를 확인해 주세요.")
    st.stop()

with st.sidebar:
    st.caption(f"✅ {data_source}")
    st.caption(f"문자 인코딩: {used_encoding} · 전체 {len(parking_df):,}건")
    st.divider()


# =========================================================
# 5. 사이드바 필터
# =========================================================
with st.sidebar:
    st.header("🔎 주차장 검색")

    district_options = sorted(
        district for district in parking_df["자치구"].dropna().unique() if district != "기타"
    )
    selected_districts = st.multiselect(
        "자치구 선택",
        options=district_options,
        placeholder="전체 자치구",
    )

    keyword = st.text_input(
        "주차장명 또는 주소 검색",
        placeholder="예: 성동구, 마장동, 공영주차장",
    ).strip()

    payment_options = yes_no_filter_options(parking_df["유무료구분명"])
    selected_payments = st.multiselect(
        "평일 유료·무료 선택",
        options=payment_options,
        placeholder="전체",
        help="CSV에는 평일 전용 무료 열이 없어 전체 유무료 구분을 평일 조건으로 사용합니다.",
    )

    type_options = sorted(
        value for value in parking_df["주차장 종류명"].dropna().unique() if value
    )
    selected_types = st.multiselect(
        "주차장 종류 선택",
        options=type_options,
        placeholder="전체",
    )

    saturday_options = yes_no_filter_options(parking_df["토요일 유,무료 구분명"])
    selected_saturday = st.multiselect(
        "토요일 유료·무료 여부",
        options=saturday_options,
        placeholder="전체",
    )

    holiday_options = yes_no_filter_options(parking_df["공휴일 유,무료 구분명"])
    selected_holiday = st.multiselect(
        "공휴일 유료·무료 여부",
        options=holiday_options,
        placeholder="전체",
    )

    night_options = yes_no_filter_options(parking_df["야간무료개방여부명"])
    selected_night = st.multiselect(
        "야간 무료 개방 여부",
        options=night_options,
        placeholder="전체",
    )

    max_spaces = int(max(parking_df["총 주차면"].fillna(0).max(), 0))
    minimum_spaces = st.number_input(
        "최소 주차면 수",
        min_value=0,
        max_value=max(max_spaces, 1),
        value=0,
        step=10,
    )

    parking_time_labels = {
        "30분": 30,
        "1시간": 60,
        "2시간": 120,
        "3시간": 180,
        "4시간": 240,
    }
    selected_time_label = st.selectbox(
        "예상 주차 시간",
        options=list(parking_time_labels.keys()),
        index=1,
    )
    parking_minutes = parking_time_labels[selected_time_label]


# =========================================================
# 6. 필터 적용 및 요금 계산
# =========================================================
filtered_df = parking_df.copy()

if selected_districts:
    filtered_df = filtered_df[filtered_df["자치구"].isin(selected_districts)]

if keyword:
    keyword_mask = (
        filtered_df["주차장명"].str.contains(keyword, case=False, na=False, regex=False)
        | filtered_df["주소"].str.contains(keyword, case=False, na=False, regex=False)
    )
    filtered_df = filtered_df[keyword_mask]

if selected_payments:
    filtered_df = filtered_df[filtered_df["유무료구분명"].isin(selected_payments)]

if selected_types:
    filtered_df = filtered_df[filtered_df["주차장 종류명"].isin(selected_types)]

if selected_saturday:
    filtered_df = filtered_df[
        filtered_df["토요일 유,무료 구분명"].isin(selected_saturday)
    ]

if selected_holiday:
    filtered_df = filtered_df[
        filtered_df["공휴일 유,무료 구분명"].isin(selected_holiday)
    ]

if selected_night:
    filtered_df = filtered_df[
        filtered_df["야간무료개방여부명"].isin(selected_night)
    ]

filtered_df = filtered_df[
    filtered_df["총 주차면"].fillna(0) >= float(minimum_spaces)
].copy()

filtered_df["예상 주차요금"] = filtered_df.apply(
    calculate_parking_fee,
    axis=1,
    parking_minutes=parking_minutes,
)

# 순서를 안정적으로 유지하기 위한 인덱스 초기화
filtered_df = filtered_df.reset_index(drop=True)


# =========================================================
# 7. 주요 요약 정보
# =========================================================
st.subheader(f"📊 검색 결과 요약 · 예상 주차 {selected_time_label}")

result_count = len(filtered_df)
free_count = int((filtered_df["유무료구분명"] == "무료").sum()) if result_count else 0
total_spaces = int(filtered_df["총 주차면"].fillna(0).sum()) if result_count else 0
average_fee = filtered_df["예상 주차요금"].dropna().mean() if result_count else np.nan
night_free_count = (
    int((filtered_df["야간무료개방여부명"] == "야간 무료개방").sum())
    if result_count
    else 0
)

metric_columns = st.columns(5)
metric_columns[0].metric("🔎 검색 주차장", f"{result_count:,}곳")
metric_columns[1].metric("🆓 무료 주차장", f"{free_count:,}곳")
metric_columns[2].metric("🚙 전체 주차면", f"{total_spaces:,}면")
metric_columns[3].metric("💰 평균 예상 요금", format_money(average_fee))
metric_columns[4].metric("🌙 야간 개방", f"{night_free_count:,}곳")

if filtered_df.empty:
    st.warning("선택한 조건에 맞는 주차장이 없습니다. 사이드바의 필터를 조정해 주세요.")
    st.stop()


# =========================================================
# 8. 가장 저렴한 주차장 추천
# =========================================================
st.subheader("🏆 가장 저렴한 주차장 추천")
valid_fee_df = filtered_df.dropna(subset=["예상 주차요금"]).copy()

if valid_fee_df.empty:
    st.info("현재 검색 결과에는 예상 요금을 계산할 수 있는 주차장이 없습니다.")
else:
    minimum_fee = valid_fee_df["예상 주차요금"].min()
    cheapest_df = valid_fee_df[
        valid_fee_df["예상 주차요금"] == minimum_fee
    ].head(3)

    cheapest_columns = st.columns(len(cheapest_df))
    for column, (_, row) in zip(cheapest_columns, cheapest_df.iterrows()):
        with column:
            st.markdown(card_html(row, "🏆"), unsafe_allow_html=True)


# =========================================================
# 9. 지도 시각화
# =========================================================
st.subheader("🗺️ 공영주차장 지도")

map_df = filtered_df.dropna(subset=["위도", "경도"]).copy()
map_df = map_df[
    map_df["위도"].between(37.0, 38.0)
    & map_df["경도"].between(126.0, 128.0)
]
excluded_map_count = len(filtered_df) - len(map_df)

if excluded_map_count > 0:
    st.caption(f"ℹ️ 좌표가 없거나 유효하지 않아 지도에서 제외된 주차장: {excluded_map_count:,}곳")

if map_df.empty:
    map_center = SEOUL_CITY_HALL
    zoom_start = 11
else:
    map_center = [map_df["위도"].mean(), map_df["경도"].mean()]
    zoom_start = 12 if len(map_df) < 100 else 11

parking_map = folium.Map(
    location=map_center,
    zoom_start=zoom_start,
    tiles="CartoDB positron",
    control_scale=True,
)
cluster = MarkerCluster(name="공영주차장").add_to(parking_map)

for _, row in map_df.iterrows():
    is_free = clean_text(row.get("유무료구분명"), "") == "무료"
    marker_color = "green" if is_free else "blue"
    marker_icon = "gift" if is_free else "car"

    folium.Marker(
        location=[row["위도"], row["경도"]],
        tooltip=clean_text(row.get("주차장명")),
        popup=folium.Popup(make_popup_html(row), max_width=340),
        icon=folium.Icon(color=marker_color, icon=marker_icon, prefix="fa"),
    ).add_to(cluster)

st_folium(parking_map, height=560, use_container_width=True, returned_objects=[])


# =========================================================
# 10. 그래프
# =========================================================
st.subheader("📈 주차장 데이터 시각화")
chart_tab1, chart_tab2, chart_tab3, chart_tab4, chart_tab5 = st.tabs(
    [
        "자치구별 주차장 수",
        "자치구별 주차면",
        "유료·무료 비율",
        "주차장 종류",
        "평균 기본요금",
    ]
)

with chart_tab1:
    chart_data = (
        filtered_df.groupby("자치구", as_index=False)
        .size()
        .rename(columns={"size": "주차장 수"})
        .sort_values("주차장 수", ascending=False)
    )
    fig = px.bar(
        chart_data,
        x="자치구",
        y="주차장 수",
        text_auto=True,
        title="자치구별 공영주차장 수",
    )
    fig.update_layout(xaxis_title="자치구", yaxis_title="주차장 수")
    st.plotly_chart(fig, use_container_width=True)

with chart_tab2:
    chart_data = (
        filtered_df.groupby("자치구", as_index=False)["총 주차면"]
        .sum(min_count=1)
        .fillna(0)
        .sort_values("총 주차면", ascending=False)
    )
    fig = px.bar(
        chart_data,
        x="자치구",
        y="총 주차면",
        text_auto=".0f",
        title="자치구별 전체 주차면 수",
    )
    fig.update_layout(xaxis_title="자치구", yaxis_title="전체 주차면")
    st.plotly_chart(fig, use_container_width=True)

with chart_tab3:
    chart_data = (
        filtered_df["유무료구분명"]
        .replace("", "정보 없음")
        .value_counts()
        .rename_axis("구분")
        .reset_index(name="주차장 수")
    )
    fig = px.pie(
        chart_data,
        names="구분",
        values="주차장 수",
        hole=0.48,
        title="유료·무료 주차장 비율",
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_tab4:
    chart_data = (
        filtered_df["주차장 종류명"]
        .replace("", "정보 없음")
        .value_counts()
        .rename_axis("주차장 종류")
        .reset_index(name="주차장 수")
    )
    fig = px.bar(
        chart_data,
        x="주차장 종류",
        y="주차장 수",
        text_auto=True,
        title="주차장 종류별 개수",
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_tab5:
    chart_data = (
        filtered_df[filtered_df["기본 주차 요금"] > 0]
        .groupby("자치구", as_index=False)["기본 주차 요금"]
        .mean()
        .sort_values("기본 주차 요금", ascending=False)
    )
    if chart_data.empty:
        st.info("평균 기본요금을 계산할 수 있는 데이터가 없습니다.")
    else:
        fig = px.bar(
            chart_data,
            x="자치구",
            y="기본 주차 요금",
            text_auto=".0f",
            title="자치구별 평균 기본 주차요금",
        )
        fig.update_layout(yaxis_title="평균 기본 주차요금(원)")
        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# 11. 랜덤 주차장 추천
# =========================================================
st.subheader("🎲 랜덤 주차장 추천")

# 검색 결과가 달라졌을 때 이전 랜덤 선택이 범위를 벗어나지 않도록 키를 만든다.
filter_signature = (
    tuple(selected_districts),
    keyword,
    tuple(selected_payments),
    tuple(selected_types),
    tuple(selected_saturday),
    tuple(selected_holiday),
    tuple(selected_night),
    minimum_spaces,
    parking_minutes,
    len(filtered_df),
)

if st.session_state.get("filter_signature") != filter_signature:
    st.session_state["filter_signature"] = filter_signature
    st.session_state.pop("random_parking_index", None)

if st.button("🎲 랜덤 주차장 추천", type="primary", use_container_width=True):
    available_indices = list(filtered_df.index)
    previous = st.session_state.get("random_parking_index")
    if len(available_indices) > 1 and previous in available_indices:
        available_indices.remove(previous)
    st.session_state["random_parking_index"] = random.choice(available_indices)

if "random_parking_index" in st.session_state:
    selected_row = filtered_df.loc[st.session_state["random_parking_index"]]
    st.markdown(card_html(selected_row, "🎁"), unsafe_allow_html=True)
else:
    st.caption("버튼을 누르면 현재 검색 결과 중 한 곳을 무작위로 추천합니다.")


# =========================================================
# 12. 검색 결과 표와 다운로드
# =========================================================
st.subheader("📋 검색 결과 상세 정보")

result_columns = [
    "주차장명",
    "자치구",
    "주소",
    "주차장 종류명",
    "유무료구분명",
    "총 주차면",
    "기본 주차 요금",
    "기본 주차 시간(분 단위)",
    "추가 단위 요금",
    "추가 단위 시간(분 단위)",
    "예상 주차요금",
    "일 최대 요금",
    "평일 운영시간",
    "주말 운영시간",
    "공휴일 운영시간",
    "토요일 유,무료 구분명",
    "공휴일 유,무료 구분명",
    "야간무료개방여부명",
    "전화번호",
]

# 화면 표시용 데이터는 금액을 문자열로 바꾼다.
display_df = filtered_df[result_columns].copy()
for money_column in [
    "기본 주차 요금",
    "추가 단위 요금",
    "예상 주차요금",
    "일 최대 요금",
]:
    display_df[money_column] = display_df[money_column].apply(format_money)

display_df["총 주차면"] = display_df["총 주차면"].apply(
    lambda value: f"{format_number(value)}면" if not pd.isna(value) else "정보 없음"
)

# 사용자에게 이해하기 쉬운 표시 열 이름으로만 변경한다.
display_df = display_df.rename(
    columns={
        "기본 주차 시간(분 단위)": "기본 주차 시간(분)",
        "추가 단위 시간(분 단위)": "추가 단위 시간(분)",
        "토요일 유,무료 구분명": "토요일 무료 여부",
        "공휴일 유,무료 구분명": "공휴일 무료 여부",
        "야간무료개방여부명": "야간 무료 개방 여부",
    }
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=520,
)

# 다운로드 파일에는 숫자형 예상 요금과 전처리된 운영시간을 모두 포함한다.
download_df = filtered_df.copy()
download_bytes = download_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="⬇️ 검색 결과 CSV 다운로드",
    data=download_bytes,
    file_name="서울시_공영주차장_검색결과.csv",
    mime="text/csv",
    use_container_width=True,
)

st.caption("서울시 공영주차장 원본 데이터의 좌표·요금·운영시간 정보에 따라 일부 값은 비어 있을 수 있습니다.")
