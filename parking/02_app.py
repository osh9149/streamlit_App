import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st


st.set_page_config(
    page_title="서울 공영주차장 찾기",
    page_icon="🅿️",
    layout="wide",
)

DEFAULT_DATA_PATHS = [
    Path("서울시 공영주차장 안내 정보(2).csv"),
    Path("data/서울시 공영주차장 안내 정보(2).csv"),
]


# -----------------------------
# 화면 스타일
# -----------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    [data-testid="stMetricValue"] {font-size: 1.55rem;}
    .parking-card {
        padding: 1rem 1.1rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px;
        margin-bottom: .8rem;
    }
    .small-note {font-size: .88rem; opacity: .78;}
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# 데이터 불러오기
# -----------------------------
def read_csv_safely(file_or_path) -> pd.DataFrame:
    """한글 CSV의 여러 인코딩을 순서대로 시도한다."""
    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]

    if hasattr(file_or_path, "getvalue"):
        raw = file_or_path.getvalue()
        for encoding in encodings:
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
    else:
        for encoding in encodings:
            try:
                return pd.read_csv(file_or_path, encoding=encoding)
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

    raise ValueError("CSV 파일의 인코딩을 확인할 수 없습니다. CP949 또는 UTF-8 CSV인지 확인해 주세요.")


@st.cache_data(show_spinner=False)
def load_default_csv(path_string: str) -> pd.DataFrame:
    return read_csv_safely(path_string)


def find_default_file():
    for path in DEFAULT_DATA_PATHS:
        if path.exists():
            return path
    return None


# -----------------------------
# 데이터 정리
# -----------------------------
REQUIRED_COLUMNS = [
    "주차장명", "주소", "유무료구분명", "기본 주차 요금",
    "기본 주차 시간(분 단위)", "추가 단위 요금",
    "추가 단위 시간(분 단위)", "위도", "경도"
]


def format_hhmm(value) -> str:
    if pd.isna(value):
        return "정보 없음"
    try:
        number = int(float(value))
        if number == 2400:
            return "24:00"
        return f"{number // 100:02d}:{number % 100:02d}"
    except (TypeError, ValueError):
        return str(value)


def won(value) -> str:
    if pd.isna(value):
        return "정보 없음"
    try:
        return f"{int(round(float(value))):,}원"
    except (TypeError, ValueError):
        return "정보 없음"


def clean_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError("필수 열이 없습니다: " + ", ".join(missing))

    text_columns = [
        "주차장명", "주소", "주차장 종류명", "운영구분명",
        "유무료구분명", "야간무료개방여부명",
        "토요일 유,무료 구분명", "공휴일 유,무료 구분명", "전화번호"
    ]
    for col in text_columns:
        if col not in df.columns:
            df[col] = "정보 없음"
        df[col] = df[col].fillna("정보 없음").astype(str).str.strip()

    numeric_columns = [
        "총 주차면", "기본 주차 요금", "기본 주차 시간(분 단위)",
        "추가 단위 요금", "추가 단위 시간(분 단위)",
        "일 최대 요금", "월 정기권 금액", "위도", "경도",
        "평일 운영 시작시각(HHMM)", "평일 운영 종료시각(HHMM)",
        "주말 운영 시작시각(HHMM)", "주말 운영 종료시각(HHMM)",
        "공휴일 운영 시작시각(HHMM)", "공휴일 운영 종료시각(HHMM)"
    ]
    for col in numeric_columns:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 주소 첫 부분에서 서울 자치구 추출
    df["자치구"] = df["주소"].str.extract(r"((?:종로|중|용산|성동|광진|동대문|중랑|성북|강북|도봉|노원|은평|서대문|마포|양천|강서|구로|금천|영등포|동작|관악|서초|강남|송파|강동)구)", expand=False)
    df["자치구"] = df["자치구"].fillna("기타/확인 필요")

    # 지도용 좌표 검증
    df["좌표유효"] = (
        df["위도"].between(37.0, 38.0)
        & df["경도"].between(126.0, 128.0)
    )

    # 보기 좋은 운영시간 문자열
    df["평일 운영시간"] = (
        df["평일 운영 시작시각(HHMM)"].apply(format_hhmm)
        + " ~ "
        + df["평일 운영 종료시각(HHMM)"].apply(format_hhmm)
    )
    df["주말 운영시간"] = (
        df["주말 운영 시작시각(HHMM)"].apply(format_hhmm)
        + " ~ "
        + df["주말 운영 종료시각(HHMM)"].apply(format_hhmm)
    )
    df["공휴일 운영시간"] = (
        df["공휴일 운영 시작시각(HHMM)"].apply(format_hhmm)
        + " ~ "
        + df["공휴일 운영 종료시각(HHMM)"].apply(format_hhmm)
    )

    # 툴팁용 텍스트
    df["기본요금표시"] = df["기본 주차 요금"].apply(won)
    df["기본시간표시"] = df["기본 주차 시간(분 단위)"].apply(
        lambda x: "정보 없음" if pd.isna(x) else f"{int(x)}분"
    )
    df["주말정보"] = (
        "토요일 " + df["토요일 유,무료 구분명"]
        + " / " + df["주말 운영시간"]
    )
    return df


def calculate_estimated_fee(row: pd.Series, minutes: int) -> float:
    """예상 주차시간에 따른 승용차 요금을 계산한다."""
    if row.get("유무료구분명") == "무료":
        return 0.0

    base_fee = row.get("기본 주차 요금")
    base_minutes = row.get("기본 주차 시간(분 단위)")
    extra_fee = row.get("추가 단위 요금")
    extra_minutes = row.get("추가 단위 시간(분 단위)")

    if pd.isna(base_fee):
        return np.nan

    base_fee = max(float(base_fee), 0)
    if pd.isna(base_minutes) or float(base_minutes) <= 0:
        estimated = base_fee
    elif minutes <= float(base_minutes):
        estimated = base_fee
    elif pd.isna(extra_fee) or pd.isna(extra_minutes) or float(extra_minutes) <= 0:
        # 추가 요금 정보가 없으면 기본요금만 표시
        estimated = base_fee
    else:
        extra_count = np.ceil((minutes - float(base_minutes)) / float(extra_minutes))
        estimated = base_fee + extra_count * float(extra_fee)

    daily_max = row.get("일 최대 요금")
    if pd.notna(daily_max) and float(daily_max) > 0:
        estimated = min(estimated, float(daily_max))

    return float(estimated)


def estimated_fee_note(row: pd.Series) -> str:
    if row["유무료구분명"] == "무료":
        return "무료"
    base = f"{won(row['기본 주차 요금'])} / {int(row['기본 주차 시간(분 단위)']) if pd.notna(row['기본 주차 시간(분 단위)']) else '?'}분"
    if pd.notna(row["추가 단위 요금"]) and pd.notna(row["추가 단위 시간(분 단위)"]):
        base += f", 이후 {won(row['추가 단위 요금'])} / {int(row['추가 단위 시간(분 단위)'])}분"
    if pd.notna(row["일 최대 요금"]) and row["일 최대 요금"] > 0:
        base += f", 일 최대 {won(row['일 최대 요금'])}"
    return base


# -----------------------------
# 헤더 및 파일 업로드
# -----------------------------
st.title("🅿️ 서울 공영주차장 정보")
st.caption("자치구·요금·주말 운영 여부를 비교하고, 지도에서 주차장 위치를 확인하세요.")

with st.sidebar:
    st.header("데이터")
    uploaded_file = st.file_uploader(
        "서울시 공영주차장 CSV 업로드",
        type=["csv"],
        help="CP949, EUC-KR, UTF-8 인코딩을 자동으로 확인합니다."
    )

default_path = find_default_file()

try:
    if uploaded_file is not None:
        raw_df = read_csv_safely(uploaded_file)
        source_name = uploaded_file.name
    elif default_path is not None:
        raw_df = load_default_csv(str(default_path))
        source_name = default_path.name
    else:
        st.warning("기본 CSV가 없습니다. 왼쪽 메뉴에서 CSV 파일을 업로드해 주세요.")
        st.stop()

    df = clean_data(raw_df)
except Exception as error:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {error}")
    st.stop()


# -----------------------------
# 검색 및 필터
# -----------------------------
with st.sidebar:
    st.success(f"불러온 파일: {source_name}")
    st.divider()
    st.header("검색 조건")

    district_options = sorted(df["자치구"].dropna().unique().tolist())
    district = st.selectbox("자치구", ["전체"] + district_options)

    search_text = st.text_input(
        "주차장명 또는 주소 검색",
        placeholder="예: 성수, 강남역, 종로"
    )

    fee_filter = st.multiselect(
        "유·무료 구분",
        options=sorted(df["유무료구분명"].unique()),
        default=sorted(df["유무료구분명"].unique())
    )

    type_options = sorted([
        value for value in df["주차장 종류명"].unique()
        if value and value != "정보 없음"
    ])
    selected_types = st.multiselect(
        "주차장 종류",
        options=type_options,
        default=type_options
    )

    weekend_free_only = st.checkbox("토요일 무료만 보기")
    holiday_free_only = st.checkbox("공휴일 무료만 보기")
    night_open_only = st.checkbox("야간 무료개방만 보기")

    parking_minutes = st.slider(
        "예상 주차시간",
        min_value=10,
        max_value=720,
        value=120,
        step=10,
        format="%d분"
    )

    min_spaces = st.number_input(
        "최소 주차면 수",
        min_value=0,
        max_value=1000,
        value=0,
        step=10
    )


filtered = df.copy()

if district != "전체":
    filtered = filtered[filtered["자치구"] == district]

if search_text.strip():
    keyword = re.escape(search_text.strip())
    filtered = filtered[
        filtered["주차장명"].str.contains(keyword, case=False, na=False)
        | filtered["주소"].str.contains(keyword, case=False, na=False)
    ]

if fee_filter:
    filtered = filtered[filtered["유무료구분명"].isin(fee_filter)]
else:
    filtered = filtered.iloc[0:0]

if selected_types:
    filtered = filtered[filtered["주차장 종류명"].isin(selected_types)]
elif type_options:
    filtered = filtered.iloc[0:0]

if weekend_free_only:
    filtered = filtered[filtered["토요일 유,무료 구분명"] == "무료"]

if holiday_free_only:
    filtered = filtered[filtered["공휴일 유,무료 구분명"] == "무료"]

if night_open_only:
    filtered = filtered[filtered["야간무료개방여부명"].str.contains("개방", na=False)]
    filtered = filtered[~filtered["야간무료개방여부명"].str.contains("미개방", na=False)]

filtered = filtered[
    filtered["총 주차면"].fillna(0) >= min_spaces
].copy()

filtered["예상요금"] = filtered.apply(
    calculate_estimated_fee,
    axis=1,
    minutes=parking_minutes
)
filtered["예상요금표시"] = filtered["예상요금"].apply(won)
filtered["요금안내"] = filtered.apply(estimated_fee_note, axis=1)


# -----------------------------
# 핵심 정보
# -----------------------------
map_df = filtered[filtered["좌표유효"]].copy()
known_fee_df = filtered[filtered["예상요금"].notna()].copy()

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("검색된 주차장", f"{len(filtered):,}곳")
metric2.metric("지도 표시 가능", f"{len(map_df):,}곳")
metric3.metric("무료 주차장", f"{(filtered['유무료구분명'] == '무료').sum():,}곳")
metric4.metric(
    f"{parking_minutes}분 최저 예상요금",
    won(known_fee_df["예상요금"].min()) if not known_fee_df.empty else "정보 없음"
)

if filtered.empty:
    st.info("선택한 조건에 맞는 주차장이 없습니다. 검색 조건을 넓혀 보세요.")
    st.stop()


# -----------------------------
# 최저가 추천
# -----------------------------
st.subheader("💰 가장 저렴한 주차장 추천")

if known_fee_df.empty:
    st.info("요금 정보가 있는 주차장이 없습니다.")
else:
    min_fee = known_fee_df["예상요금"].min()
    cheapest = known_fee_df[known_fee_df["예상요금"] == min_fee].sort_values(
        ["총 주차면", "주차장명"],
        ascending=[False, True]
    )

    best = cheapest.iloc[0]
    st.markdown(
        f"""
        <div class="parking-card">
            <b>{best['주차장명']}</b><br>
            📍 {best['주소']}<br>
            💳 예상요금: <b>{best['예상요금표시']}</b> ({parking_minutes}분 기준)<br>
            🕒 기본 요금표: {best['요금안내']}<br>
            🅿️ 주차면: {int(best['총 주차면']) if pd.notna(best['총 주차면']) else '정보 없음'}면 ·
            토요일 {best['토요일 유,무료 구분명']} · 공휴일 {best['공휴일 유,무료 구분명']}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if len(cheapest) > 1:
        st.caption(f"같은 최저 예상요금의 주차장이 총 {len(cheapest)}곳 있습니다.")


# -----------------------------
# 지도
# -----------------------------
st.subheader("🗺️ 주차장 지도")

if map_df.empty:
    st.warning("현재 검색 결과에는 유효한 위도·경도 정보가 없습니다.")
else:
    # 요금별 마커 크기를 동일하게 유지하고 무료 여부를 색으로 구분
    map_df["marker_color"] = map_df["유무료구분명"].map(
        {"무료": [35, 170, 90, 210], "유료": [50, 110, 220, 200]}
    )
    map_df["marker_color"] = map_df["marker_color"].apply(
        lambda x: x if isinstance(x, list) else [120, 120, 120, 200]
    )

    if district == "전체":
        center_lat, center_lon, zoom = 37.5665, 126.9780, 10.5
    else:
        center_lat = float(map_df["위도"].median())
        center_lon = float(map_df["경도"].median())
        zoom = 12.2

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[경도, 위도]",
        get_fill_color="marker_color",
        get_radius=55,
        radius_min_pixels=5,
        radius_max_pixels=12,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=0,
    )

    tooltip = {
        "html": """
        <b>{주차장명}</b><br/>
        주소: {주소}<br/>
        유·무료: {유무료구분명}<br/>
        예상요금: {예상요금표시}<br/>
        기본요금: {기본요금표시} / {기본시간표시}<br/>
        토요일: {토요일 유,무료 구분명} ({주말 운영시간})<br/>
        공휴일: {공휴일 유,무료 구분명} ({공휴일 운영시간})<br/>
        주차면: {총 주차면}
        """,
        "style": {
            "backgroundColor": "rgba(20, 25, 35, 0.94)",
            "color": "white",
            "fontSize": "13px",
            "padding": "10px",
        },
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style=None,
        ),
        use_container_width=True,
    )
    st.caption("초록색은 무료, 파란색은 유료 주차장입니다. 마커에 마우스를 올리면 상세 정보가 표시됩니다.")


# -----------------------------
# 결과표
# -----------------------------
st.subheader("📋 주차장 상세 비교")

sort_option = st.selectbox(
    "정렬 기준",
    [
        "예상요금 낮은 순",
        "주차면 많은 순",
        "주차장명 순",
        "기본요금 낮은 순",
    ],
    horizontal=True,
)

if sort_option == "예상요금 낮은 순":
    table_df = filtered.sort_values(["예상요금", "총 주차면"], ascending=[True, False], na_position="last")
elif sort_option == "주차면 많은 순":
    table_df = filtered.sort_values("총 주차면", ascending=False, na_position="last")
elif sort_option == "기본요금 낮은 순":
    table_df = filtered.sort_values("기본 주차 요금", ascending=True, na_position="last")
else:
    table_df = filtered.sort_values("주차장명")

display_columns = [
    "주차장명", "자치구", "주소", "주차장 종류명", "유무료구분명",
    "예상요금", "기본 주차 요금", "기본 주차 시간(분 단위)",
    "토요일 유,무료 구분명", "공휴일 유,무료 구분명",
    "주말 운영시간", "총 주차면", "전화번호"
]
display_columns = [col for col in display_columns if col in table_df.columns]

st.dataframe(
    table_df[display_columns],
    use_container_width=True,
    hide_index=True,
    column_config={
        "예상요금": st.column_config.NumberColumn(
            f"{parking_minutes}분 예상요금",
            format="%d원",
        ),
        "기본 주차 요금": st.column_config.NumberColumn(
            "기본요금",
            format="%d원",
        ),
        "기본 주차 시간(분 단위)": st.column_config.NumberColumn(
            "기본시간",
            format="%d분",
        ),
        "총 주차면": st.column_config.NumberColumn(
            "주차면",
            format="%d면",
        ),
    }
)

download_columns = [
    "주차장코드", "주차장명", "자치구", "주소", "주차장 종류명",
    "유무료구분명", "예상요금", "기본 주차 요금",
    "기본 주차 시간(분 단위)", "추가 단위 요금",
    "추가 단위 시간(분 단위)", "일 최대 요금",
    "토요일 유,무료 구분명", "공휴일 유,무료 구분명",
    "평일 운영시간", "주말 운영시간", "공휴일 운영시간",
    "총 주차면", "전화번호", "위도", "경도"
]
download_columns = [col for col in download_columns if col in table_df.columns]

csv_bytes = table_df[download_columns].to_csv(
    index=False,
    encoding="utf-8-sig"
).encode("utf-8-sig")

st.download_button(
    "검색 결과 CSV 다운로드",
    data=csv_bytes,
    file_name="서울_공영주차장_검색결과.csv",
    mime="text/csv",
)

with st.expander("데이터 및 요금 계산 안내"):
    st.markdown(
        """
        - 예상요금은 **기본요금 + 추가 단위요금** 방식으로 계산합니다.
        - 일 최대요금이 0보다 큰 경우 해당 금액을 상한으로 적용합니다.
        - 추가요금 정보가 비어 있으면 기본요금만 표시하므로 실제 요금과 차이가 날 수 있습니다.
        - 지도에는 서울 범위의 유효한 위도·경도가 있는 주차장만 표시합니다.
        - 실제 운영시간과 요금은 현장 사정에 따라 달라질 수 있으므로 방문 전 전화 확인을 권장합니다.
        """
    )
