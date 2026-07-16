import io
import math
import re

import pandas as pd
import pydeck as pdk
import streamlit as st


st.set_page_config(
    page_title="주차장 정보 안내",
    page_icon="🅿️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #666;
        margin-bottom: 1.3rem;
    }
    .parking-card {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        background: white;
    }
    .free-badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        font-weight: 700;
        font-size: 0.82rem;
    }
    .paid-badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        background: #fee2e2;
        color: #991b1b;
        font-weight: 700;
        font-size: 0.82rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


COLUMN_CANDIDATES = {
    "name": ["주차장명", "주차장 이름", "주차장", "명칭", "parking_name", "name"],
    "address": ["주소", "소재지도로명주소", "도로명주소", "소재지지번주소", "지번주소", "address"],
    "district": ["자치구", "구명", "시군구", "시군구명", "구", "district"],
    "type": ["주차장종류", "주차장 종류", "주차장구분", "주차장 구분", "유형", "type"],
    "fee_type": ["요금정보", "유무료구분", "유료무료", "무료구분", "급지구분", "fee_type"],
    "lat": ["위도", "lat", "latitude", "Y좌표", "y좌표"],
    "lon": ["경도", "lon", "lng", "longitude", "X좌표", "x좌표"],
    "basic_time": ["기본주차시간", "기본 시간", "기본시간", "기본주차시간(분)", "basic_time"],
    "basic_fee": ["기본주차요금", "기본 요금", "기본요금", "기본주차요금(원)", "basic_fee"],
    "add_time": ["추가단위시간", "추가 시간", "추가시간", "단위시간", "add_time"],
    "add_fee": ["추가단위요금", "추가 요금", "추가요금", "단위요금", "add_fee"],
    "daily_max": ["일최대요금", "1일주차권요금", "일일최대요금", "일주차요금", "daily_max"],
    "capacity": ["주차구획수", "주차면수", "총주차면", "주차대수", "capacity"],
}


def normalize_text(value):
    return re.sub(r"[\s_\-()]+", "", str(value)).lower()


def find_column(df, candidates):
    normalized = {normalize_text(col): col for col in df.columns}

    for candidate in candidates:
        key = normalize_text(candidate)
        if key in normalized:
            return normalized[key]

    for col in df.columns:
        col_key = normalize_text(col)
        for candidate in candidates:
            candidate_key = normalize_text(candidate)
            if candidate_key in col_key or col_key in candidate_key:
                return col
    return None


def read_uploaded_csv(uploaded_file):
    raw = uploaded_file.getvalue()
    errors = []

    # 사용자가 요청한 cp949를 가장 먼저 적용합니다.
    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=encoding), encoding
        except Exception as error:
            errors.append(f"{encoding}: {error}")

    raise ValueError("CSV 파일을 읽을 수 없습니다.\n" + "\n".join(errors))


def to_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("원", "", regex=False)
        .str.replace("분", "", regex=False)
        .str.extract(r"(-?\d+(?:\.\d+)?)", expand=False),
        errors="coerce",
    )


def infer_district_from_address(address):
    match = re.search(r"([가-힣]+구)", str(address))
    return match.group(1) if match else "구 정보 없음"


def is_free_value(value):
    text = normalize_text(value)
    free_keywords = ["무료", "free", "무상", "0원"]
    return any(keyword in text for keyword in free_keywords)


def calculate_fee(row, parking_minutes):
    if row["is_free"]:
        return 0

    basic_time = row["basic_time"]
    basic_fee = row["basic_fee"]
    add_time = row["add_time"]
    add_fee = row["add_fee"]
    daily_max = row["daily_max"]

    if pd.isna(basic_fee):
        return math.nan

    basic_time = 0 if pd.isna(basic_time) else max(float(basic_time), 0)
    basic_fee = max(float(basic_fee), 0)

    if parking_minutes <= basic_time or pd.isna(add_time) or pd.isna(add_fee) or add_time <= 0:
        total = basic_fee
    else:
        extra_minutes = parking_minutes - basic_time
        extra_units = math.ceil(extra_minutes / float(add_time))
        total = basic_fee + extra_units * max(float(add_fee), 0)

    if not pd.isna(daily_max) and daily_max > 0:
        # 24시간이 넘는 경우에도 일 최대요금을 반복 적용합니다.
        full_days = parking_minutes // 1440
        remaining_minutes = parking_minutes % 1440

        if full_days >= 1:
            day_cost = full_days * float(daily_max)
            if remaining_minutes == 0:
                total = day_cost
            else:
                if remaining_minutes <= basic_time or pd.isna(add_time) or pd.isna(add_fee) or add_time <= 0:
                    remaining_cost = basic_fee
                else:
                    units = math.ceil((remaining_minutes - basic_time) / float(add_time))
                    remaining_cost = basic_fee + units * max(float(add_fee), 0)
                total = day_cost + min(remaining_cost, float(daily_max))
        else:
            total = min(total, float(daily_max))

    return int(round(total))


def prepare_data(df):
    mapping = {
        key: find_column(df, candidates)
        for key, candidates in COLUMN_CANDIDATES.items()
    }

    required = ["name", "address", "lat", "lon"]
    missing = [key for key in required if mapping[key] is None]
    if missing:
        korean_names = {
            "name": "주차장명",
            "address": "주소",
            "lat": "위도",
            "lon": "경도",
        }
        missing_text = ", ".join(korean_names[key] for key in missing)
        raise ValueError(
            f"필수 열을 찾지 못했습니다: {missing_text}\n"
            "CSV에 주차장명, 주소, 위도, 경도 열이 있는지 확인해 주세요."
        )

    result = pd.DataFrame()
    result["name"] = df[mapping["name"]].fillna("이름 없음").astype(str)
    result["address"] = df[mapping["address"]].fillna("주소 없음").astype(str)
    result["lat"] = to_number(df[mapping["lat"]])
    result["lon"] = to_number(df[mapping["lon"]])

    if mapping["district"]:
        result["district"] = df[mapping["district"]].fillna("").astype(str).str.strip()
        empty_mask = result["district"].eq("")
        result.loc[empty_mask, "district"] = result.loc[empty_mask, "address"].apply(
            infer_district_from_address
        )
    else:
        result["district"] = result["address"].apply(infer_district_from_address)

    result["parking_type"] = (
        df[mapping["type"]].fillna("종류 정보 없음").astype(str)
        if mapping["type"]
        else "종류 정보 없음"
    )

    fee_type_text = (
        df[mapping["fee_type"]].fillna("").astype(str)
        if mapping["fee_type"]
        else pd.Series("", index=df.index)
    )

    for key in ["basic_time", "basic_fee", "add_time", "add_fee", "daily_max", "capacity"]:
        if mapping[key]:
            result[key] = to_number(df[mapping[key]])
        else:
            result[key] = math.nan

    result["is_free"] = fee_type_text.apply(is_free_value)
    result.loc[result["basic_fee"].fillna(-1).eq(0), "is_free"] = True
    result["fee_category"] = result["is_free"].map({True: "무료", False: "유료"})

    result = result.dropna(subset=["lat", "lon"])
    result = result[
        result["lat"].between(33, 39)
        & result["lon"].between(124, 132)
    ].copy()

    return result, mapping


def won(value):
    if pd.isna(value):
        return "요금 정보 없음"
    return f"{int(value):,}원"


st.markdown('<div class="main-title">🅿️ 주차장 정보 안내</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">CSV 데이터를 업로드하고 조건에 맞는 주차장과 예상 주차요금을 확인하세요.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("📁 데이터 업로드")
    uploaded_file = st.file_uploader(
        "주차장 CSV 파일",
        type=["csv"],
        help="한글 CSV 파일은 cp949 인코딩으로 먼저 읽습니다.",
    )

    st.caption(
        "필수 열: 주차장명, 주소, 위도, 경도\n\n"
        "권장 열: 자치구, 주차장종류, 요금정보, 기본주차시간, "
        "기본주차요금, 추가단위시간, 추가단위요금, 일최대요금"
    )

if uploaded_file is None:
    st.info("왼쪽 메뉴에서 주차장 정보 CSV 파일을 업로드해 주세요.")

    with st.expander("CSV 열 구성 예시"):
        sample = pd.DataFrame(
            {
                "주차장명": ["한강공영주차장", "서울숲주차장"],
                "주소": ["서울특별시 성동구 예시로 1", "서울특별시 성동구 예시로 2"],
                "자치구": ["성동구", "성동구"],
                "주차장종류": ["노외", "부설"],
                "요금정보": ["유료", "무료"],
                "위도": [37.55, 37.54],
                "경도": [127.04, 127.05],
                "기본주차시간": [30, 0],
                "기본주차요금": [1000, 0],
                "추가단위시간": [10, 0],
                "추가단위요금": [500, 0],
                "일최대요금": [20000, 0],
            }
        )
        st.dataframe(sample, use_container_width=True)
    st.stop()

try:
    raw_df, used_encoding = read_uploaded_csv(uploaded_file)
    parking_df, column_mapping = prepare_data(raw_df)
except Exception as error:
    st.error(str(error))
    st.stop()

if parking_df.empty:
    st.error("표시 가능한 위도·경도 데이터가 없습니다.")
    st.stop()

st.success(
    f"CSV 파일을 {used_encoding} 인코딩으로 읽었습니다. "
    f"지도에 표시 가능한 주차장 {len(parking_df):,}개를 찾았습니다."
)

with st.sidebar:
    st.divider()
    st.header("🔎 검색 조건")

    district_options = ["전체"] + sorted(parking_df["district"].dropna().unique().tolist())
    selected_district = st.selectbox("자치구 선택", district_options)

    type_options = ["전체"] + sorted(parking_df["parking_type"].dropna().unique().tolist())
    selected_type = st.selectbox("주차장 종류", type_options)

    selected_fee_type = st.radio(
        "무료·유료 구분",
        ["전체", "무료", "유료"],
        horizontal=True,
    )

    hours = st.number_input(
        "예상 주차시간(시간)",
        min_value=0,
        max_value=72,
        value=1,
        step=1,
    )
    minutes = st.selectbox("추가 시간(분)", [0, 10, 20, 30, 40, 50])
    parking_minutes = int(hours * 60 + minutes)

    keyword = st.text_input("주차장명 또는 주소 검색", placeholder="예: 서울숲")

filtered = parking_df.copy()

if selected_district != "전체":
    filtered = filtered[filtered["district"] == selected_district]

if selected_type != "전체":
    filtered = filtered[filtered["parking_type"] == selected_type]

if selected_fee_type != "전체":
    filtered = filtered[filtered["fee_category"] == selected_fee_type]

if keyword.strip():
    search_mask = (
        filtered["name"].str.contains(keyword, case=False, na=False)
        | filtered["address"].str.contains(keyword, case=False, na=False)
    )
    filtered = filtered[search_mask]

filtered = filtered.copy()
filtered["estimated_fee"] = filtered.apply(
    lambda row: calculate_fee(row, parking_minutes),
    axis=1,
)

known_fee = filtered.dropna(subset=["estimated_fee"])
cheapest = None
if not known_fee.empty:
    cheapest = known_fee.sort_values(
        ["estimated_fee", "name"],
        ascending=[True, True],
    ).iloc[0]

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("검색된 주차장", f"{len(filtered):,}개")
metric2.metric("무료 주차장", f"{int(filtered['is_free'].sum()):,}개")
metric3.metric("유료 주차장", f"{int((~filtered['is_free']).sum()):,}개")
metric4.metric(
    "예상 주차시간",
    f"{parking_minutes // 60}시간 {parking_minutes % 60}분",
)

if filtered.empty:
    st.warning("선택한 조건에 맞는 주차장이 없습니다.")
    st.stop()

if cheapest is not None:
    st.markdown("### 💰 가장 저렴한 주차장")
    st.success(
        f"**{cheapest['name']}** · 예상 요금 **{won(cheapest['estimated_fee'])}**\n\n"
        f"{cheapest['address']} · {cheapest['fee_category']} · {cheapest['parking_type']}"
    )
else:
    st.warning("현재 검색 결과에는 계산 가능한 요금 정보가 없습니다.")

tab_map, tab_list, tab_data = st.tabs(["🗺️ 지도", "📋 주차장 목록", "🧾 데이터 확인"])

with tab_map:
    map_df = filtered.copy()
    map_df["예상요금"] = map_df["estimated_fee"].apply(won)
    map_df["기본요금"] = map_df["basic_fee"].apply(won)
    map_df["marker_color"] = map_df["is_free"].apply(
        lambda value: [34, 197, 94, 190] if value else [239, 68, 68, 190]
    )

    center_lat = float(map_df["lat"].mean())
    center_lon = float(map_df["lon"].mean())

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_fill_color="marker_color",
        get_radius=70,
        radius_min_pixels=5,
        radius_max_pixels=14,
        pickable=True,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
    )

    deck = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=11,
            pitch=0,
        ),
        layers=[layer],
        tooltip={
            "html": """
                <b>{name}</b><br/>
                주소: {address}<br/>
                자치구: {district}<br/>
                종류: {parking_type}<br/>
                구분: {fee_category}<br/>
                예상 요금: {예상요금}<br/>
                기본 요금: {기본요금}
            """,
            "style": {
                "backgroundColor": "rgba(20, 20, 20, 0.92)",
                "color": "white",
            },
        },
    )

    st.pydeck_chart(deck, use_container_width=True)
    st.caption("초록색은 무료, 빨간색은 유료 주차장입니다. 마커에 마우스를 올리면 상세 정보가 표시됩니다.")

with tab_list:
    sort_option = st.selectbox(
        "정렬 기준",
        ["예상 요금 낮은 순", "주차장명 순", "자치구 순"],
        key="sort_option",
    )

    list_df = filtered.copy()
    if sort_option == "예상 요금 낮은 순":
        list_df = list_df.sort_values(
            ["estimated_fee", "name"],
            na_position="last",
        )
    elif sort_option == "주차장명 순":
        list_df = list_df.sort_values("name")
    else:
        list_df = list_df.sort_values(["district", "name"])

    max_cards = min(len(list_df), 100)
    st.caption(f"최대 100개까지 표시합니다. 현재 {max_cards}개 표시 중입니다.")

    for _, row in list_df.head(100).iterrows():
        badge_class = "free-badge" if row["is_free"] else "paid-badge"
        capacity_text = (
            f"{int(row['capacity']):,}면"
            if not pd.isna(row["capacity"])
            else "정보 없음"
        )
        st.markdown(
            f"""
            <div class="parking-card">
                <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
                    <div>
                        <div style="font-size:1.08rem; font-weight:800;">{row['name']}</div>
                        <div style="color:#666; margin-top:5px;">{row['address']}</div>
                    </div>
                    <span class="{badge_class}">{row['fee_category']}</span>
                </div>
                <hr style="border:none; border-top:1px solid #eee; margin:12px 0;">
                <div><b>예상 요금:</b> {won(row['estimated_fee'])}</div>
                <div><b>주차장 종류:</b> {row['parking_type']}</div>
                <div><b>자치구:</b> {row['district']}</div>
                <div><b>주차면수:</b> {capacity_text}</div>
                <div><b>요금 기준:</b> 기본 {row['basic_time'] if not pd.isna(row['basic_time']) else '-'}분 /
                    {won(row['basic_fee'])},
                    추가 {row['add_time'] if not pd.isna(row['add_time']) else '-'}분 /
                    {won(row['add_fee'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_data:
    display_df = filtered[
        [
            "name",
            "address",
            "district",
            "parking_type",
            "fee_category",
            "estimated_fee",
            "basic_time",
            "basic_fee",
            "add_time",
            "add_fee",
            "daily_max",
            "capacity",
            "lat",
            "lon",
        ]
    ].rename(
        columns={
            "name": "주차장명",
            "address": "주소",
            "district": "자치구",
            "parking_type": "주차장종류",
            "fee_category": "무료·유료",
            "estimated_fee": "예상요금",
            "basic_time": "기본주차시간",
            "basic_fee": "기본주차요금",
            "add_time": "추가단위시간",
            "add_fee": "추가단위요금",
            "daily_max": "일최대요금",
            "capacity": "주차면수",
            "lat": "위도",
            "lon": "경도",
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    download_csv = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "검색 결과 CSV 다운로드",
        data=download_csv,
        file_name="주차장_검색결과.csv",
        mime="text/csv",
    )

    with st.expander("자동 인식된 원본 CSV 열"):
        mapping_table = pd.DataFrame(
            {
                "앱에서 사용하는 항목": list(column_mapping.keys()),
                "인식된 CSV 열": [
                    column_mapping[key] if column_mapping[key] else "없음"
                    for key in column_mapping
                ],
            }
        )
        st.dataframe(mapping_table, use_container_width=True, hide_index=True)
