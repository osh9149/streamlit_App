import re
import time
from io import StringIO

import pandas as pd
import pydeck as pdk
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="주차장 요금 안내",
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
        .sub-text {
            color: #666;
            margin-bottom: 1.3rem;
        }
        .fee-card {
            padding: 1rem 1.2rem;
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 14px;
            margin-bottom: 0.7rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 열 이름 자동 탐색
# ---------------------------------------------------------
COLUMN_ALIASES = {
    "name": [
        "주차장명", "주차장 이름", "주차장", "명칭", "시설명",
        "parking_name", "name"
    ],
    "address": [
        "주소", "도로명주소", "소재지도로명주소", "소재지지번주소",
        "지번주소", "주차장주소", "address"
    ],
    "fee": [
        "주차요금", "요금", "기본요금", "주차기본요금",
        "평일운영시작시각", "parking_fee", "fee"
    ],
    "basic_time": [
        "기본주차시간", "주차기본시간", "기본시간",
        "basic_time", "base_time"
    ],
    "basic_fee": [
        "기본주차요금", "주차기본요금", "기본요금",
        "basic_fee", "base_fee"
    ],
    "extra_time": [
        "추가단위시간", "추가주차시간", "추가시간",
        "extra_time", "unit_time"
    ],
    "extra_fee": [
        "추가단위요금", "추가주차요금", "추가요금",
        "extra_fee", "unit_fee"
    ],
    "daily_fee": [
        "1일주차권요금적용시간", "1일주차요금", "일주차요금",
        "일일최대요금", "daily_fee", "day_fee"
    ],
    "lat": [
        "위도", "lat", "latitude", "y", "Y좌표"
    ],
    "lon": [
        "경도", "lng", "lon", "longitude", "x", "X좌표"
    ],
}


def normalize_text(value):
    return re.sub(r"[\s_\-()]+", "", str(value)).lower()


def find_column(columns, aliases):
    normalized_columns = {normalize_text(col): col for col in columns}

    # 완전 일치 우선
    for alias in aliases:
        key = normalize_text(alias)
        if key in normalized_columns:
            return normalized_columns[key]

    # 부분 일치
    for alias in aliases:
        alias_key = normalize_text(alias)
        for normalized_col, original_col in normalized_columns.items():
            if alias_key in normalized_col or normalized_col in alias_key:
                return original_col

    return None


def detect_columns(df):
    return {
        key: find_column(df.columns, aliases)
        for key, aliases in COLUMN_ALIASES.items()
    }


# ---------------------------------------------------------
# CSV 읽기
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def read_csv_file(file_bytes):
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]

    for encoding in encodings:
        try:
            text = file_bytes.decode(encoding)
            return pd.read_csv(StringIO(text))
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue

    raise ValueError("CSV 파일의 인코딩 또는 형식을 확인해주세요.")


# ---------------------------------------------------------
# 숫자·요금 처리
# ---------------------------------------------------------
def to_number(value):
    if pd.isna(value):
        return None

    text = str(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return None

    return float(match.group())


def format_number(value):
    number = to_number(value)

    if number is None:
        return "정보 없음"

    if number.is_integer():
        return f"{int(number):,}"

    return f"{number:,.1f}"


def make_fee_text(row, col_map):
    # CSV에 완성된 요금 설명 열이 있는 경우
    fee_col = col_map.get("fee")
    if fee_col and pd.notna(row.get(fee_col)):
        fee_value = str(row.get(fee_col)).strip()
        if fee_value and fee_value.lower() != "nan":
            number = to_number(fee_value)

            if number is not None and re.fullmatch(r"[\d,\s원₩.]+", fee_value):
                return f"{format_number(fee_value)}원"

            return fee_value

    parts = []

    basic_time_col = col_map.get("basic_time")
    basic_fee_col = col_map.get("basic_fee")
    extra_time_col = col_map.get("extra_time")
    extra_fee_col = col_map.get("extra_fee")
    daily_fee_col = col_map.get("daily_fee")

    basic_time = row.get(basic_time_col) if basic_time_col else None
    basic_fee = row.get(basic_fee_col) if basic_fee_col else None
    extra_time = row.get(extra_time_col) if extra_time_col else None
    extra_fee = row.get(extra_fee_col) if extra_fee_col else None
    daily_fee = row.get(daily_fee_col) if daily_fee_col else None

    if to_number(basic_fee) is not None:
        if to_number(basic_time) is not None:
            parts.append(
                f"기본 {format_number(basic_time)}분 "
                f"{format_number(basic_fee)}원"
            )
        else:
            parts.append(f"기본요금 {format_number(basic_fee)}원")

    if to_number(extra_fee) is not None:
        if to_number(extra_time) is not None:
            parts.append(
                f"추가 {format_number(extra_time)}분당 "
                f"{format_number(extra_fee)}원"
            )
        else:
            parts.append(f"추가요금 {format_number(extra_fee)}원")

    if to_number(daily_fee) is not None:
        parts.append(f"1일 최대 {format_number(daily_fee)}원")

    return " / ".join(parts) if parts else "요금 정보 없음"


# ---------------------------------------------------------
# 주소 → 좌표 변환
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def geocode_addresses(addresses):
    geolocator = Nominatim(
        user_agent="streamlit-parking-info-app",
        timeout=10,
    )
    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1,
        swallow_exceptions=True,
    )

    result = []

    for address in addresses:
        if not address or pd.isna(address):
            result.append((None, None))
            continue

        location = geocode(
            str(address),
            country_codes="kr",
            language="ko",
        )

        if location:
            result.append((location.latitude, location.longitude))
        else:
            result.append((None, None))

    return result


def prepare_map_data(df, col_map):
    data = df.copy()

    name_col = col_map.get("name")
    address_col = col_map.get("address")
    lat_col = col_map.get("lat")
    lon_col = col_map.get("lon")

    data["주차장명_표시"] = (
        data[name_col].fillna("이름 없음").astype(str)
        if name_col
        else "이름 없음"
    )

    data["주소_표시"] = (
        data[address_col].fillna("주소 정보 없음").astype(str)
        if address_col
        else "주소 정보 없음"
    )

    data["요금_표시"] = data.apply(
        lambda row: make_fee_text(row, col_map),
        axis=1,
    )

    if lat_col and lon_col:
        data["latitude"] = pd.to_numeric(data[lat_col], errors="coerce")
        data["longitude"] = pd.to_numeric(data[lon_col], errors="coerce")
    else:
        data["latitude"] = pd.NA
        data["longitude"] = pd.NA

    return data


# ---------------------------------------------------------
# 화면
# ---------------------------------------------------------
st.markdown('<div class="main-title">🅿️ 주차장 요금 안내 앱</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-text">'
    'CSV 파일을 업로드하면 주소 검색, 주차요금 안내, 지도 시각화를 제공합니다.'
    '</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("1. CSV 파일 업로드")

    uploaded_file = st.file_uploader(
        "주차장 정보 CSV",
        type=["csv"],
        help="주소, 주차요금, 위도, 경도 등의 열이 포함된 CSV를 업로드하세요.",
    )

    st.caption(
        "권장 열: 주차장명, 주소, 기본주차시간, 기본요금, "
        "추가단위시간, 추가단위요금, 위도, 경도"
    )

if uploaded_file is None:
    st.info("왼쪽 메뉴에서 주차장 정보 CSV 파일을 업로드해주세요.")

    sample_df = pd.DataFrame(
        {
            "주차장명": ["서울시청 주차장", "광화문 공영주차장"],
            "주소": ["서울특별시 중구 세종대로 110", "서울특별시 종로구 세종대로 189"],
            "기본주차시간": [30, 30],
            "기본요금": [1000, 1500],
            "추가단위시간": [10, 10],
            "추가단위요금": [500, 500],
            "위도": [37.5663, 37.5716],
            "경도": [126.9779, 126.9769],
        }
    )

    st.subheader("CSV 형식 예시")
    st.dataframe(sample_df, use_container_width=True, hide_index=True)
    st.stop()


try:
    raw_df = read_csv_file(uploaded_file.getvalue())
except Exception as error:
    st.error(f"CSV 파일을 읽을 수 없습니다: {error}")
    st.stop()

if raw_df.empty:
    st.warning("CSV 파일에 데이터가 없습니다.")
    st.stop()

col_map = detect_columns(raw_df)
address_col = col_map.get("address")

if not address_col:
    st.error(
        "주소 열을 찾지 못했습니다. 열 이름을 '주소', '도로명주소', "
        "'소재지도로명주소' 중 하나로 변경해주세요."
    )
    st.write("현재 열 이름:", list(raw_df.columns))
    st.stop()

map_df = prepare_map_data(raw_df, col_map)

with st.sidebar:
    st.header("2. 검색 설정")

    search_text = st.text_input(
        "주소 검색",
        placeholder="예: 강남구, 세종대로, 왕십리로",
    )

    search_target = st.radio(
        "검색 방식",
        ["주소 포함 검색", "주소와 주차장명 검색"],
        horizontal=False,
    )

    max_map_points = st.slider(
        "지도에 표시할 최대 주차장 수",
        min_value=50,
        max_value=1000,
        value=300,
        step=50,
    )

# 검색
filtered_df = map_df.copy()

if search_text.strip():
    keyword = search_text.strip()

    address_mask = filtered_df["주소_표시"].str.contains(
        keyword,
        case=False,
        na=False,
        regex=False,
    )

    if search_target == "주소와 주차장명 검색":
        name_mask = filtered_df["주차장명_표시"].str.contains(
            keyword,
            case=False,
            na=False,
            regex=False,
        )
        filtered_df = filtered_df[address_mask | name_mask]
    else:
        filtered_df = filtered_df[address_mask]

# 요약
metric1, metric2, metric3 = st.columns(3)

metric1.metric("전체 주차장", f"{len(map_df):,}개")
metric2.metric("검색 결과", f"{len(filtered_df):,}개")
metric3.metric(
    "좌표 보유",
    f"{filtered_df[['latitude', 'longitude']].dropna().shape[0]:,}개",
)

tab1, tab2, tab3 = st.tabs(
    ["📍 지도", "💰 주소별 요금", "📄 전체 데이터"]
)

# ---------------------------------------------------------
# 지도 탭
# ---------------------------------------------------------
with tab1:
    st.subheader("주차장 위치 지도")

    map_ready_df = filtered_df.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    if map_ready_df.empty:
        st.warning(
            "지도에 표시할 위도·경도 정보가 없습니다. "
            "CSV에 위도/경도 열을 넣거나 아래 버튼으로 주소를 좌표로 변환하세요."
        )

        max_geocode = min(len(filtered_df), 100)

        st.caption(
            "무료 주소 변환 서비스는 속도가 느리고 일부 국내 주소를 찾지 못할 수 있습니다. "
            "한 번에 최대 100개까지만 변환합니다."
        )

        if st.button(
            f"검색 결과 앞 {max_geocode}개 주소를 좌표로 변환",
            type="primary",
        ):
            targets = (
                filtered_df.head(max_geocode)["주소_표시"]
                .fillna("")
                .astype(str)
                .tolist()
            )

            with st.spinner("주소를 좌표로 변환하고 있습니다..."):
                coordinates = geocode_addresses(targets)

            temp_df = filtered_df.head(max_geocode).copy()
            temp_df["latitude"] = [item[0] for item in coordinates]
            temp_df["longitude"] = [item[1] for item in coordinates]

            map_ready_df = temp_df.dropna(
                subset=["latitude", "longitude"]
            )

            if map_ready_df.empty:
                st.error(
                    "좌표를 찾지 못했습니다. CSV에 위도와 경도를 추가하는 방식을 권장합니다."
                )
            else:
                st.success(
                    f"{len(map_ready_df)}개 주차장의 좌표를 찾았습니다."
                )

    if not map_ready_df.empty:
        map_ready_df = map_ready_df.head(max_map_points)

        center_lat = float(map_ready_df["latitude"].mean())
        center_lon = float(map_ready_df["longitude"].mean())

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_ready_df,
            get_position="[longitude, latitude]",
            get_radius=55,
            radius_min_pixels=5,
            radius_max_pixels=18,
            pickable=True,
            auto_highlight=True,
            get_fill_color=[30, 130, 230, 190],
            get_line_color=[255, 255, 255, 220],
            line_width_min_pixels=1,
            stroked=True,
        )

        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=11,
            pitch=0,
        )

        tooltip = {
            "html": """
                <div style="font-size:14px; line-height:1.6;">
                    <b>{주차장명_표시}</b><br/>
                    📍 {주소_표시}<br/>
                    💰 {요금_표시}
                </div>
            """,
            "style": {
                "backgroundColor": "rgba(25, 25, 25, 0.92)",
                "color": "white",
                "borderRadius": "8px",
                "padding": "8px",
            },
        }

        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style=None,
        )

        st.pydeck_chart(deck, use_container_width=True)

        st.caption(
            "지도 위의 점에 마우스를 올리면 주차장명, 주소, 주차요금을 확인할 수 있습니다."
        )


# ---------------------------------------------------------
# 주소별 요금 탭
# ---------------------------------------------------------
with tab2:
    st.subheader("주소에 따른 주차요금 안내")

    if filtered_df.empty:
        st.warning("검색 조건과 일치하는 주차장이 없습니다.")
    else:
        display_limit = min(len(filtered_df), 100)

        st.caption(
            f"검색 결과 {len(filtered_df):,}개 중 앞 {display_limit:,}개를 표시합니다."
        )

        for _, row in filtered_df.head(display_limit).iterrows():
            st.markdown(
                f"""
                <div class="fee-card">
                    <b>🅿️ {row['주차장명_표시']}</b><br/>
                    <span>📍 {row['주소_표시']}</span><br/>
                    <span>💰 {row['요금_표시']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------
# 데이터 탭
# ---------------------------------------------------------
with tab3:
    st.subheader("업로드 데이터")

    table_columns = [
        "주차장명_표시",
        "주소_표시",
        "요금_표시",
        "latitude",
        "longitude",
    ]

    table_df = filtered_df[
        [col for col in table_columns if col in filtered_df.columns]
    ].rename(
        columns={
            "주차장명_표시": "주차장명",
            "주소_표시": "주소",
            "요금_표시": "주차요금",
            "latitude": "위도",
            "longitude": "경도",
        }
    )

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = table_df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")

    st.download_button(
        "검색 결과 CSV 다운로드",
        data=csv_data,
        file_name="parking_search_result.csv",
        mime="text/csv",
    )

with st.expander("자동으로 인식된 CSV 열 확인"):
    st.json(col_map)
