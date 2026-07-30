import math
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium


# =========================================================
# 1. 페이지 기본 설정
# =========================================================
st.set_page_config(
    page_title="서울시 공영주차장 정보",
    page_icon="🅿️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f4f9ff 0%, #ffffff 42%);
    }
    .main-title {
        padding: 1.35rem 1.6rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #1677ff, #65b5ff);
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 10px 24px rgba(22,119,255,.20);
    }
    .main-title h1 {
        margin: 0;
        font-size: 2.05rem;
    }
    .main-title p {
        margin: .45rem 0 0 0;
        opacity: .95;
    }
    .recommend-card {
        padding: 1rem 1.15rem;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #dcecff;
        box-shadow: 0 5px 14px rgba(50, 100, 160, .08);
        margin-bottom: .75rem;
    }
    .small-note {
        color: #64748b;
        font-size: .88rem;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5effa;
        padding: .7rem;
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-title">
        <h1>🅿️ 서울시 공영주차장 정보</h1>
        <p>조건별 검색, 지도·그래프 분석, 예상 주차요금 계산과 추천 기능을 한 번에 이용해 보세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 2. 데이터 불러오기
# =========================================================
REQUIRED_COLUMNS = [
    "주차장명", "주소", "주차장 종류명", "운영구분명", "전화번호",
    "총 주차면", "유무료구분명", "야간무료개방여부명",
    "기본 주차 요금", "기본 주차 시간(분 단위)",
    "추가 단위 요금", "추가 단위 시간(분 단위)",
    "일 최대 요금", "위도", "경도",
]


def find_default_csv():
    """app.py와 같은 폴더에서 서울시 공영주차장 CSV를 자동으로 찾음"""
    base = Path(__file__).resolve().parent
    preferred_names = [
        "서울시 공영주차장 안내 정보.csv",
        "서울시 공영주차장 안내 정보(3).csv",
    ]

    for name in preferred_names:
        candidate = base / name
        if candidate.exists():
            return candidate

    parking_files = sorted(base.glob("*주차장*.csv"))
    if parking_files:
        return parking_files[0]

    all_csv_files = sorted(base.glob("*.csv"))
    return all_csv_files[0] if all_csv_files else None


@st.cache_data(show_spinner=False)
def read_csv_safely(file_source):
    """한글 CSV의 여러 인코딩을 순서대로 시도하여 읽음"""
    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]
    last_error = None

    for encoding in encodings:
        try:
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            return pd.read_csv(file_source, encoding=encoding), encoding
        except Exception as error:
            last_error = error

    raise ValueError(f"CSV 파일을 읽을 수 없습니다: {last_error}")


def clean_number(series):
    """쉼표나 문자 등이 포함된 숫자 열을 안전하게 숫자로 변환"""
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def prepare_data(raw_df):
    df = raw_df.copy()
    df.columns = df.columns.astype(str).str.strip()

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error("필수 열이 없습니다: " + ", ".join(missing))
        st.stop()

    numeric_columns = [
        "총 주차면", "기본 주차 요금", "기본 주차 시간(분 단위)",
        "추가 단위 요금", "추가 단위 시간(분 단위)",
        "일 최대 요금", "월 정기권 금액", "위도", "경도",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = clean_number(df[col])

    text_columns = [
        "주차장명", "주소", "주차장 종류명", "운영구분명",
        "유무료구분명", "야간무료개방여부명", "전화번호",
        "토요일 유,무료 구분명", "공휴일 유,무료 구분명",
    ]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna("정보 없음").astype(str).str.strip()

    # 주소의 첫 부분에서 자치구 이름 추출
    df["자치구"] = df["주소"].str.extract(r"((?:서울특별시\s*)?[가-힣]+구)", expand=False)
    df["자치구"] = (
        df["자치구"]
        .str.replace("서울특별시", "", regex=False)
        .str.strip()
        .fillna("기타")
    )

    # 유료/무료 정보가 비어 있는 경우 기본 요금으로 한 번 더 보정
    free_by_price = df["기본 주차 요금"].fillna(0).eq(0)
    df.loc[
        df["유무료구분명"].isin(["정보 없음", "", "nan"]) & free_by_price,
        "유무료구분명",
    ] = "무료"

    return df


default_csv = find_default_csv()

with st.sidebar:
    st.header("📁 데이터")
    uploaded_file = st.file_uploader(
        "다른 공영주차장 CSV 사용",
        type=["csv"],
        help="업로드하지 않으면 app.py와 같은 폴더의 기본 CSV를 자동으로 사용합니다.",
    )

try:
    if uploaded_file is not None:
        raw_df, used_encoding = read_csv_safely(uploaded_file)
        data_source_name = uploaded_file.name
    elif default_csv is not None:
        raw_df, used_encoding = read_csv_safely(default_csv)
        data_source_name = default_csv.name
    else:
        st.warning("기본 CSV를 찾지 못했습니다. 왼쪽에서 CSV 파일을 업로드해 주세요.")
        st.stop()
except Exception as error:
    st.error(str(error))
    st.stop()

df = prepare_data(raw_df)


# =========================================================
# 3. 공통 함수
# =========================================================
def format_won(value):
    if pd.isna(value):
        return "정보 없음"
    return f"{int(round(value)):,}원"


def format_time(value):
    if pd.isna(value):
        return "정보 없음"
    try:
        text = str(int(float(value))).zfill(4)
        if text == "2400":
            return "24:00"
        return f"{text[:2]}:{text[2:]}"
    except Exception:
        return "정보 없음"


def calculate_fee(row, minutes):
    """
    주차 예상요금 계산
    - 무료 주차장 또는 기본 요금 0원: 0원
    - 기본 시간을 초과하면 추가 단위 시간마다 추가 요금 부과
    - 일 최대 요금이 0보다 크면 상한 적용
    """
    base_fee = row.get("기본 주차 요금", np.nan)
    base_minutes = row.get("기본 주차 시간(분 단위)", np.nan)
    add_fee = row.get("추가 단위 요금", np.nan)
    add_minutes = row.get("추가 단위 시간(분 단위)", np.nan)
    daily_max = row.get("일 최대 요금", np.nan)

    if row.get("유무료구분명") == "무료":
        return 0

    if pd.isna(base_fee) or base_fee <= 0:
        return 0

    if pd.isna(base_minutes) or base_minutes <= 0:
        base_minutes = 1

    if minutes <= base_minutes:
        fee = base_fee
    else:
        if pd.isna(add_fee) or add_fee < 0:
            add_fee = base_fee
        if pd.isna(add_minutes) or add_minutes <= 0:
            add_minutes = base_minutes

        extra_minutes = minutes - base_minutes
        extra_units = math.ceil(extra_minutes / add_minutes)
        fee = base_fee + (extra_units * add_fee)

    if pd.notna(daily_max) and daily_max > 0:
        fee = min(fee, daily_max)

    return max(int(round(fee)), 0)


def popup_html(row, estimated_fee=None):
    fee_line = ""
    if estimated_fee is not None:
        fee_line = f"<b>예상 요금:</b> {format_won(estimated_fee)}<br>"

    return f"""
    <div style="width:260px; font-size:13px; line-height:1.55;">
        <b style="font-size:15px;">{row['주차장명']}</b><br>
        <b>주소:</b> {row['주소']}<br>
        <b>종류:</b> {row['주차장 종류명']}<br>
        <b>운영:</b> {row['운영구분명']}<br>
        <b>주차면:</b> {int(row['총 주차면']) if pd.notna(row['총 주차면']) else '정보 없음'}면<br>
        <b>요금:</b> {row['유무료구분명']}<br>
        <b>기본 요금:</b> {format_won(row['기본 주차 요금'])}<br>
        {fee_line}
        <b>전화:</b> {row['전화번호']}
    </div>
    """


# =========================================================
# 4. 검색 조건
# =========================================================
with st.sidebar:
    st.caption(f"사용 파일: {data_source_name}")
    st.caption(f"인코딩: {used_encoding}")
    st.divider()
    st.header("🔎 검색 조건")

    districts = sorted([x for x in df["자치구"].dropna().unique() if x != "기타"])
    selected_districts = st.multiselect(
        "자치구",
        districts,
        placeholder="전체 자치구",
    )

    keyword = st.text_input(
        "주차장명·주소 검색",
        placeholder="예: 강남, 공원, 시장",
    ).strip()

    parking_types = sorted(df["주차장 종류명"].dropna().unique())
    selected_types = st.multiselect(
        "주차장 종류",
        parking_types,
        placeholder="전체 종류",
    )

    fee_options = sorted(df["유무료구분명"].dropna().unique())
    selected_fee_types = st.multiselect(
        "유료·무료",
        fee_options,
        placeholder="전체",
    )

    night_open_only = st.checkbox("🌙 야간 무료개방만")
    weekend_free_only = st.checkbox("📅 토요일 무료만")
    holiday_free_only = st.checkbox("🎉 공휴일 무료만")
    coords_only = st.checkbox("📍 지도 표시 가능한 곳만")

    max_spaces = int(max(df["총 주차면"].fillna(0).max(), 1))
    min_spaces = st.slider(
        "최소 주차면 수",
        min_value=0,
        max_value=max_spaces,
        value=0,
        step=1,
    )

    st.divider()
    st.header("💰 요금 계산 기준")
    parking_minutes = st.number_input(
        "예상 주차 시간(분)",
        min_value=5,
        max_value=1440,
        value=120,
        step=5,
    )


# =========================================================
# 5. 필터 적용
# =========================================================
filtered = df.copy()

if selected_districts:
    filtered = filtered[filtered["자치구"].isin(selected_districts)]

if keyword:
    keyword_mask = (
        filtered["주차장명"].str.contains(keyword, case=False, na=False)
        | filtered["주소"].str.contains(keyword, case=False, na=False)
    )
    filtered = filtered[keyword_mask]

if selected_types:
    filtered = filtered[filtered["주차장 종류명"].isin(selected_types)]

if selected_fee_types:
    filtered = filtered[filtered["유무료구분명"].isin(selected_fee_types)]

if night_open_only:
    filtered = filtered[
        filtered["야간무료개방여부명"].str.contains("개방", na=False)
        & ~filtered["야간무료개방여부명"].str.contains("미개방", na=False)
    ]

if weekend_free_only and "토요일 유,무료 구분명" in filtered.columns:
    filtered = filtered[
        filtered["토요일 유,무료 구분명"].str.contains("무료", na=False)
        & ~filtered["토요일 유,무료 구분명"].str.contains("유료", na=False)
    ]

if holiday_free_only and "공휴일 유,무료 구분명" in filtered.columns:
    filtered = filtered[
        filtered["공휴일 유,무료 구분명"].str.contains("무료", na=False)
        & ~filtered["공휴일 유,무료 구분명"].str.contains("유료", na=False)
    ]

filtered = filtered[filtered["총 주차면"].fillna(0) >= min_spaces]

valid_coords = (
    filtered["위도"].between(33, 39)
    & filtered["경도"].between(124, 132)
)
if coords_only:
    filtered = filtered[valid_coords]

filtered = filtered.copy()
filtered["예상 주차요금"] = filtered.apply(
    lambda row: calculate_fee(row, parking_minutes),
    axis=1,
)


# =========================================================
# 6. 상단 요약
# =========================================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("검색된 주차장", f"{len(filtered):,}곳")
col2.metric(
    "총 주차면",
    f"{int(filtered['총 주차면'].fillna(0).sum()):,}면",
)
col3.metric(
    "무료 주차장",
    f"{int(filtered['유무료구분명'].eq('무료').sum()):,}곳",
)
col4.metric(
    "지도 표시 가능",
    f"{int((filtered['위도'].between(33, 39) & filtered['경도'].between(124, 132)).sum()):,}곳",
)

if filtered.empty:
    st.warning("선택한 조건에 맞는 주차장이 없습니다. 검색 조건을 줄여 보세요.")
    st.stop()


# =========================================================
# 7. 추천 기능
# =========================================================
st.subheader("⭐ 추천 주차장")

recommend_col1, recommend_col2 = st.columns(2)

# 가장 저렴한 주차장: 예상요금 → 기본요금 → 주차면이 많은 순서
cheapest = (
    filtered.sort_values(
        ["예상 주차요금", "기본 주차 요금", "총 주차면"],
        ascending=[True, True, False],
        na_position="last",
    )
    .iloc[0]
)

with recommend_col1:
    st.markdown(
        f"""
        <div class="recommend-card">
            <b>💸 가장 저렴한 주차장</b><br><br>
            <span style="font-size:1.18rem;"><b>{cheapest['주차장명']}</b></span><br>
            {cheapest['주소']}<br>
            예상 {parking_minutes}분 요금:
            <b style="color:#1677ff;">{format_won(cheapest['예상 주차요금'])}</b><br>
            주차면: {int(cheapest['총 주차면']) if pd.notna(cheapest['총 주차면']) else '정보 없음'}면
        </div>
        """,
        unsafe_allow_html=True,
    )

with recommend_col2:
    if "random_seed" not in st.session_state:
        st.session_state.random_seed = 1

    if st.button("🎲 새로운 랜덤 추천", use_container_width=True):
        st.session_state.random_seed += 1

    random_row = filtered.sample(
        n=1,
        random_state=st.session_state.random_seed,
    ).iloc[0]

    st.markdown(
        f"""
        <div class="recommend-card">
            <b>🎁 오늘의 랜덤 주차장</b><br><br>
            <span style="font-size:1.18rem;"><b>{random_row['주차장명']}</b></span><br>
            {random_row['주소']}<br>
            예상 {parking_minutes}분 요금:
            <b style="color:#1677ff;">{format_won(random_row['예상 주차요금'])}</b><br>
            특징: {random_row['주차장 종류명']} · {random_row['유무료구분명']}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 8. 탭 구성
# =========================================================
tab_map, tab_chart, tab_fee, tab_table = st.tabs(
    ["🗺️ 지도", "📊 그래프", "🧮 요금 계산", "📋 검색 결과"]
)


# -------------------------
# 지도 탭
# -------------------------
with tab_map:
    map_df = filtered[
        filtered["위도"].between(33, 39)
        & filtered["경도"].between(124, 132)
    ].copy()

    if map_df.empty:
        st.info("현재 검색 결과에는 지도에 표시할 수 있는 위도·경도 정보가 없습니다.")
    else:
        # 결과가 많을 때도 브라우저가 느려지지 않도록 지도 마커 수 제한
        max_map_markers = st.select_slider(
            "지도에 표시할 최대 주차장 수",
            options=[100, 300, 500, 1000, 1500],
            value=500,
        )

        if len(map_df) > max_map_markers:
            map_df = map_df.nlargest(max_map_markers, "총 주차면")
            st.caption(
                f"검색 결과가 많아 주차면 수가 큰 {max_map_markers:,}곳을 지도에 표시합니다."
            )

        center_lat = float(map_df["위도"].mean())
        center_lon = float(map_df["경도"].mean())

        parking_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles="CartoDB positron",
        )
        marker_cluster = MarkerCluster().add_to(parking_map)

        for _, row in map_df.iterrows():
            is_free = row["유무료구분명"] == "무료"
            icon_color = "green" if is_free else "blue"

            folium.Marker(
                location=[row["위도"], row["경도"]],
                tooltip=f"{row['주차장명']} · {format_won(row['예상 주차요금'])}",
                popup=folium.Popup(
                    popup_html(row, row["예상 주차요금"]),
                    max_width=320,
                ),
                icon=folium.Icon(
                    color=icon_color,
                    icon="car",
                    prefix="fa",
                ),
            ).add_to(marker_cluster)

        st_folium(
            parking_map,
            width=None,
            height=610,
            returned_objects=[],
        )

        st.caption("초록 마커는 무료, 파란 마커는 유료 주차장입니다.")


# -------------------------
# 그래프 탭
# -------------------------
with tab_chart:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        district_summary = (
            filtered.groupby("자치구", as_index=False)
            .agg(
                주차장수=("주차장명", "count"),
                총주차면=("총 주차면", "sum"),
            )
            .sort_values("주차장수", ascending=False)
        )

        fig_district = px.bar(
            district_summary,
            x="자치구",
            y="주차장수",
            hover_data=["총주차면"],
            title="자치구별 검색 주차장 수",
            labels={"주차장수": "주차장 수", "총주차면": "총 주차면"},
        )
        fig_district.update_layout(
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=55, b=20),
        )
        st.plotly_chart(fig_district, use_container_width=True)

    with chart_col2:
        fee_summary = (
            filtered["유무료구분명"]
            .value_counts()
            .rename_axis("요금구분")
            .reset_index(name="주차장수")
        )

        fig_fee = px.pie(
            fee_summary,
            names="요금구분",
            values="주차장수",
            hole=0.48,
            title="유료·무료 주차장 비율",
        )
        st.plotly_chart(fig_fee, use_container_width=True)

    top_capacity = (
        filtered.nlargest(15, "총 주차면")
        [["주차장명", "자치구", "총 주차면"]]
        .sort_values("총 주차면")
    )
    fig_capacity = px.bar(
        top_capacity,
        x="총 주차면",
        y="주차장명",
        orientation="h",
        color="자치구",
        title="주차면 수가 많은 주차장 TOP 15",
        labels={"총 주차면": "주차면 수"},
    )
    fig_capacity.update_layout(
        height=560,
        margin=dict(l=20, r=20, t=55, b=20),
    )
    st.plotly_chart(fig_capacity, use_container_width=True)

    paid_for_scatter = filtered[
        (filtered["기본 주차 요금"].fillna(0) > 0)
        & (filtered["총 주차면"].fillna(0) > 0)
    ].copy()

    if not paid_for_scatter.empty:
        fig_scatter = px.scatter(
            paid_for_scatter,
            x="총 주차면",
            y="예상 주차요금",
            hover_name="주차장명",
            hover_data=["자치구", "주소", "기본 주차 요금"],
            size="총 주차면",
            title=f"주차면 수와 예상 {parking_minutes}분 요금의 관계",
            labels={"예상 주차요금": "예상 요금(원)", "총 주차면": "주차면 수"},
        )
        st.plotly_chart(fig_scatter, use_container_width=True)


# -------------------------
# 요금 계산 탭
# -------------------------
with tab_fee:
    st.info(
        "예상 요금은 CSV의 기본 요금·기본 시간·추가 요금·추가 단위 시간을 이용해 계산하며, "
        "일 최대 요금이 있으면 상한을 적용합니다. 실제 현장 요금과 다를 수 있습니다."
    )

    parking_names = (
        filtered.sort_values(["자치구", "주차장명"])
        .apply(lambda row: f"{row['주차장명']} | {row['주소']}", axis=1)
        .tolist()
    )

    selected_label = st.selectbox(
        "요금을 계산할 주차장",
        parking_names,
    )
    selected_index = parking_names.index(selected_label)
    selected_row = filtered.sort_values(["자치구", "주차장명"]).iloc[selected_index]

    fee_col1, fee_col2, fee_col3, fee_col4 = st.columns(4)
    fee_col1.metric("예상 요금", format_won(selected_row["예상 주차요금"]))
    fee_col2.metric("기본 요금", format_won(selected_row["기본 주차 요금"]))
    fee_col3.metric(
        "기본 시간",
        f"{int(selected_row['기본 주차 시간(분 단위)'])}분"
        if pd.notna(selected_row["기본 주차 시간(분 단위)"])
        else "정보 없음",
    )
    fee_col4.metric("일 최대 요금", format_won(selected_row["일 최대 요금"]))

    details = {
        "주차장명": selected_row["주차장명"],
        "주소": selected_row["주소"],
        "전화번호": selected_row["전화번호"],
        "주차장 종류": selected_row["주차장 종류명"],
        "운영 방식": selected_row["운영구분명"],
        "총 주차면": (
            f"{int(selected_row['총 주차면'])}면"
            if pd.notna(selected_row["총 주차면"])
            else "정보 없음"
        ),
        "평일 운영시간": (
            f"{format_time(selected_row.get('평일 운영 시작시각(HHMM)'))}"
            f" ~ {format_time(selected_row.get('평일 운영 종료시각(HHMM)'))}"
        ),
        "주말 운영시간": (
            f"{format_time(selected_row.get('주말 운영 시작시각(HHMM)'))}"
            f" ~ {format_time(selected_row.get('주말 운영 종료시각(HHMM)'))}"
        ),
        "야간 무료개방": selected_row["야간무료개방여부명"],
    }

    st.dataframe(
        pd.DataFrame(details.items(), columns=["항목", "내용"]),
        hide_index=True,
        use_container_width=True,
    )

    compare_minutes = [30, 60, 120, 180, 300, 480]
    fee_curve = pd.DataFrame(
        {
            "주차 시간": compare_minutes,
            "예상 요금": [
                calculate_fee(selected_row, minute)
                for minute in compare_minutes
            ],
        }
    )
    fig_fee_curve = px.line(
        fee_curve,
        x="주차 시간",
        y="예상 요금",
        markers=True,
        title=f"{selected_row['주차장명']} 시간별 예상 요금",
        labels={"주차 시간": "주차 시간(분)", "예상 요금": "예상 요금(원)"},
    )
    st.plotly_chart(fig_fee_curve, use_container_width=True)


# -------------------------
# 결과 표 및 다운로드 탭
# -------------------------
with tab_table:
    display_columns = [
        "자치구", "주차장명", "주소", "주차장 종류명", "운영구분명",
        "유무료구분명", "야간무료개방여부명", "총 주차면",
        "기본 주차 요금", "기본 주차 시간(분 단위)",
        "추가 단위 요금", "추가 단위 시간(분 단위)",
        "일 최대 요금", "예상 주차요금", "전화번호",
    ]
    display_columns = [col for col in display_columns if col in filtered.columns]

    sort_option = st.selectbox(
        "정렬 기준",
        ["예상 요금 낮은 순", "주차면 많은 순", "주차장명 순"],
    )

    if sort_option == "예상 요금 낮은 순":
        result_df = filtered.sort_values(
            ["예상 주차요금", "기본 주차 요금"],
            ascending=[True, True],
        )
    elif sort_option == "주차면 많은 순":
        result_df = filtered.sort_values("총 주차면", ascending=False)
    else:
        result_df = filtered.sort_values("주차장명")

    st.dataframe(
        result_df[display_columns],
        use_container_width=True,
        hide_index=True,
        height=580,
        column_config={
            "기본 주차 요금": st.column_config.NumberColumn(format="%d원"),
            "추가 단위 요금": st.column_config.NumberColumn(format="%d원"),
            "일 최대 요금": st.column_config.NumberColumn(format="%d원"),
            "예상 주차요금": st.column_config.NumberColumn(format="%d원"),
            "총 주차면": st.column_config.NumberColumn(format="%d면"),
        },
    )

    # 엑셀에서 한글이 깨지지 않도록 UTF-8 BOM 포함
    csv_data = result_df[display_columns].to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")

    st.download_button(
        "⬇️ 검색 결과 CSV 다운로드",
        data=csv_data,
        file_name="서울시_공영주차장_검색결과.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =========================================================
# 9. 하단 안내
# =========================================================
st.divider()
st.caption(
    "※ 데이터의 운영시간과 요금은 변동될 수 있으므로 방문 전 주차장 운영기관에 확인하세요. "
    "지도에는 CSV에 정상적인 위도·경도가 있는 주차장만 표시됩니다."
)
