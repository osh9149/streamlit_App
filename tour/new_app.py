import html
import random
from datetime import date, datetime, timedelta

import folium
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static


# ---------------------------------------------------------
# Streamlit 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="전국 축제 검색",
    page_icon="🎉",
    layout="wide",
)


# ---------------------------------------------------------
# 화면 디자인
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* 전체 화면 */
        .stApp {
            background:
                radial-gradient(circle at 8% 10%, rgba(255, 214, 224, 0.45), transparent 24%),
                radial-gradient(circle at 92% 12%, rgba(255, 235, 170, 0.38), transparent 22%),
                linear-gradient(180deg, #fffaf5 0%, #ffffff 52%);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1450px;
        }

        /* 왼쪽 사이드바 */
        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, #fff1f5 0%, #fff8e8 55%, #f3fbff 100%);
            border-right: 1px solid rgba(255, 153, 172, 0.25);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.1rem;
        }

        .sidebar-logo {
            text-align: center;
            font-size: 3rem;
            line-height: 1;
            margin-bottom: 0.35rem;
        }

        .sidebar-title {
            text-align: center;
            font-size: 1.45rem;
            font-weight: 900;
            color: #e84f75;
            margin-bottom: 0.2rem;
        }

        .sidebar-subtitle {
            text-align: center;
            color: #765e67;
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 1rem;
        }

        .sidebar-tip {
            padding: 0.85rem;
            margin-top: 0.9rem;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px dashed #ff9eb3;
            color: #6d5960;
            font-size: 0.86rem;
            line-height: 1.55;
        }

        /* 메인 히어로 */
        .hero-box {
            position: relative;
            overflow: hidden;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1.2rem;
            border-radius: 26px;
            background:
                linear-gradient(135deg, rgba(255, 230, 236, 0.96), rgba(255, 247, 213, 0.95));
            border: 1px solid rgba(255, 156, 178, 0.35);
            box-shadow: 0 12px 30px rgba(166, 91, 112, 0.10);
        }

        .hero-box::after {
            content: "🎈  🎊  ✨  🎪";
            position: absolute;
            right: 1.2rem;
            top: 1rem;
            font-size: 2rem;
            opacity: 0.78;
        }

        .hero-title {
            font-size: 2.15rem;
            font-weight: 900;
            color: #be365d;
            margin-bottom: 0.35rem;
        }

        .hero-description {
            color: #715861;
            font-size: 1rem;
            line-height: 1.6;
            max-width: 760px;
        }

        /* 검색 결과 요약 카드 */
        .summary-card {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid #f2dedf;
            box-shadow: 0 7px 18px rgba(80, 50, 40, 0.06);
            text-align: center;
        }

        .summary-value {
            font-size: 1.7rem;
            font-weight: 900;
            color: #e34e73;
        }

        .summary-label {
            color: #76626a;
            font-size: 0.88rem;
            margin-top: 0.2rem;
        }

        /* 축제 카드 */
        .festival-card {
            min-height: 430px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid #f2ded8;
            border-radius: 22px;
            background-color: rgba(255, 255, 255, 0.96);
            box-shadow: 0 10px 25px rgba(94, 60, 45, 0.08);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .festival-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 14px 30px rgba(94, 60, 45, 0.13);
        }

        .festival-card h3 {
            margin-top: 0.8rem;
            margin-bottom: 0.7rem;
            font-size: 1.25rem;
            color: #c84067;
        }

        .festival-card p {
            margin: 0.35rem 0;
            line-height: 1.55;
            color: #5f5558;
        }

        .festival-image {
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 16px;
        }

        .no-image {
            height: 240px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            border-radius: 16px;
            background: linear-gradient(135deg, #FFE7F2, #FFF7CC, #E8F7FF);
            color: #444;
            text-align: center;
        }

        /* 랜덤 추천 */
        .recommend-box {
            padding: 1.3rem;
            margin: 0.8rem 0 1.5rem 0;
            border: 2px solid #ffbd59;
            border-radius: 22px;
            background: linear-gradient(135deg, #fff6d9, #fff1f5);
            box-shadow: 0 10px 24px rgba(207, 148, 59, 0.10);
        }

        .recommend-box h2 {
            margin-top: 0;
        }

        /* 버튼 */
        div[data-testid="stButton"] button {
            min-height: 3rem;
            border-radius: 14px;
            font-weight: 800;
            border: 0;
            box-shadow: 0 7px 16px rgba(214, 83, 118, 0.15);
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            background: linear-gradient(90deg, #ff6f91, #ff9f68);
            color: white;
        }

        /* 입력창 */
        div[data-baseweb="select"] > div,
        div[data-testid="stDateInput"] input,
        div[data-testid="stTextInput"] input {
            border-radius: 12px !important;
        }

        /* 탭 */
        button[data-baseweb="tab"] {
            font-weight: 800;
            font-size: 0.98rem;
        }

        /* 모바일 */
        @media (max-width: 900px) {
            .hero-box::after {
                display: none;
            }

            .hero-title {
                font-size: 1.7rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 지역명과 한국관광공사 areaCode 연결
# ---------------------------------------------------------
AREA_CODES = {
    "전국": "",
    "서울": "1",
    "인천": "2",
    "대전": "3",
    "대구": "4",
    "광주": "5",
    "부산": "6",
    "울산": "7",
    "세종": "8",
    "경기도": "31",
    "강원특별자치도": "32",
    "충청북도": "33",
    "충청남도": "34",
    "경상북도": "35",
    "경상남도": "36",
    "전북특별자치도": "37",
    "전라남도": "38",
    "제주특별자치도": "39",
}

API_URL = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"


# ---------------------------------------------------------
# 세션 상태 초기화
# ---------------------------------------------------------
if "festival_df" not in st.session_state:
    st.session_state.festival_df = pd.DataFrame()

if "recommended_festival" not in st.session_state:
    st.session_state.recommended_festival = None

if "has_searched" not in st.session_state:
    st.session_state.has_searched = False

if "search_message" not in st.session_state:
    st.session_state.search_message = ""


# ---------------------------------------------------------
# 공통 함수
# ---------------------------------------------------------
def safe_text(value, default="정보 없음"):
    """결측값과 빈 문자열을 안전한 표시용 문자열로 변환한다."""
    if value is None or pd.isna(value):
        return default

    text = str(value).strip()
    return text if text else default


def format_festival_date(value):
    """YYYYMMDD 형식의 날짜를 YYYY.MM.DD 형식으로 변환한다."""
    text = safe_text(value, "")

    if len(text) != 8 or not text.isdigit():
        return "날짜 정보 없음"

    try:
        return datetime.strptime(text, "%Y%m%d").strftime("%Y.%m.%d")
    except ValueError:
        return "날짜 정보 없음"


def format_period(row):
    """축제 시작일과 종료일을 하나의 기간 문자열로 만든다."""
    start = format_festival_date(row.get("eventstartdate", ""))
    end = format_festival_date(row.get("eventenddate", ""))

    if start == "날짜 정보 없음" and end == "날짜 정보 없음":
        return "기간 정보 없음"
    if end == "날짜 정보 없음":
        return start
    if start == "날짜 정보 없음":
        return end

    return f"{start} ~ {end}"


def extract_api_error(payload):
    """공공데이터포털의 일반적인 오류 응답에서 오류 내용을 찾는다."""
    if not isinstance(payload, dict):
        return None

    # 정상 응답의 header 확인
    response = payload.get("response")
    if isinstance(response, dict):
        header = response.get("header", {})
        result_code = str(header.get("resultCode", "0000"))
        result_message = safe_text(header.get("resultMsg"), "")

        if result_code not in ("0000", "00"):
            return result_message or f"API 오류 코드: {result_code}"

    # 인증 오류 등이 별도의 OpenAPI_ServiceResponse 형태로 올 수 있음
    service_response = payload.get("OpenAPI_ServiceResponse")
    if isinstance(service_response, dict):
        cmm_msg_header = service_response.get("cmmMsgHeader", {})
        return (
            safe_text(cmm_msg_header.get("returnAuthMsg"), "")
            or safe_text(cmm_msg_header.get("errMsg"), "")
            or "API 인증 또는 요청 처리 중 오류가 발생했습니다."
        )

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def request_festivals(
    service_key,
    area_code,
    start_date_text,
    end_date_text,
    result_count,
):
    """TourAPI를 호출하고 축제 목록과 오류 메시지를 반환한다."""
    params = {
        "serviceKey": service_key,
        "MobileOS": "ETC",
        "MobileApp": "FestivalSearchApp",
        "_type": "json",
        "pageNo": 1,
        "numOfRows": int(result_count),
        "arrange": "A",
        "eventStartDate": start_date_text,
        "eventEndDate": end_date_text,
    }

    # 전국 검색일 때는 areaCode를 보내지 않는다.
    if area_code:
        params["areaCode"] = area_code

    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return [], "API 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
    except requests.exceptions.ConnectionError:
        return [], "네트워크 연결을 확인해 주세요."
    except requests.exceptions.HTTPError:
        return [], f"API 서버가 HTTP 오류를 반환했습니다. 상태 코드: {response.status_code}"
    except requests.exceptions.RequestException:
        return [], "API 요청 중 오류가 발생했습니다."

    # 응답이 JSON인지 확인한다.
    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError:
        return [], "API가 JSON 형식이 아닌 응답을 반환했습니다. 인증키와 요청 조건을 확인해 주세요."
    except ValueError:
        return [], "API 응답을 JSON으로 해석할 수 없습니다."

    api_error = extract_api_error(payload)
    if api_error:
        return [], f"API 요청에 실패했습니다: {api_error}"

    # 정상 응답에서 item을 안전하게 꺼낸다.
    try:
        body = payload.get("response", {}).get("body", {})
        items_container = body.get("items", {})
    except AttributeError:
        return [], "API 응답 구조가 예상한 형식과 다릅니다."

    if not items_container:
        return [], ""

    if isinstance(items_container, dict):
        items = items_container.get("item", [])
    else:
        items = []

    # item이 한 건이면 딕셔너리, 여러 건이면 리스트로 올 수 있다.
    if isinstance(items, dict):
        items = [items]
    elif not isinstance(items, list):
        items = []

    return items, ""


def prepare_dataframe(items, keyword):
    """API 결과를 DataFrame으로 변환하고 화면 표시용 열을 정리한다."""
    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items).copy()

    required_columns = [
        "title",
        "addr1",
        "firstimage",
        "eventstartdate",
        "eventenddate",
        "mapx",
        "mapy",
    ]

    # 일부 열이 누락되어도 앱이 중단되지 않게 빈 열을 만든다.
    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    # 축제명 키워드는 API 호출 후 DataFrame에서 필터링한다.
    keyword = keyword.strip()
    if keyword:
        df = df[
            df["title"]
            .fillna("")
            .astype(str)
            .str.contains(keyword, case=False, na=False, regex=False)
        ]

    df = df.reset_index(drop=True)

    if df.empty:
        return df

    df["축제명"] = df["title"].apply(lambda x: safe_text(x, "축제명 없음"))
    df["주소"] = df["addr1"].apply(lambda x: safe_text(x, "주소 정보 없음"))
    df["기간"] = df.apply(format_period, axis=1)

    # 숫자로 변환할 수 없는 좌표는 NaN으로 처리한다.
    df["경도"] = pd.to_numeric(df["mapx"], errors="coerce")
    df["위도"] = pd.to_numeric(df["mapy"], errors="coerce")

    # 주소의 첫 번째 단어를 지역명으로 사용한다.
    df["지역"] = df["주소"].apply(
        lambda value: value.split()[0]
        if value and value != "주소 정보 없음"
        else "지역 정보 없음"
    )

    # 시작일을 날짜로 변환해 월별 집계에 사용한다.
    df["시작일"] = pd.to_datetime(
        df["eventstartdate"].astype(str),
        format="%Y%m%d",
        errors="coerce",
    )
    df["시작월"] = df["시작일"].dt.month

    return df


def festival_card_html(row):
    """축제 한 건을 카드 형태의 HTML로 만든다."""
    title = html.escape(safe_text(row.get("축제명"), "축제명 없음"))
    period = html.escape(safe_text(row.get("기간"), "기간 정보 없음"))
    address = html.escape(safe_text(row.get("주소"), "주소 정보 없음"))
    image_url = safe_text(row.get("firstimage"), "")

    if image_url:
        safe_image_url = html.escape(image_url, quote=True)
        image_section = (
            f'<img class="festival-image" src="{safe_image_url}" '
            f'alt="{title}" loading="lazy">'
        )
    else:
        image_section = """
        <div class="no-image">
            <div style="font-size:70px;">🎆</div>
            <div style="font-size:42px; margin-top:8px;">
                🎪 🎈 🎊
            </div>
            <div style="font-size:20px; font-weight:bold; margin-top:14px; color:#E6517A;">
                축제 이미지 준비중
            </div>
            <div style="font-size:15px; color:#666; margin-top:8px;">
                즐거운 축제를 만나보세요 😊
            </div>
        </div>
        """

    return f"""
        <div class="festival-card">
            {image_section}
            <h3>🎪 {title}</h3>
            <p><strong>📅 기간</strong><br>{period}</p>
            <p><strong>📍 주소</strong><br>{address}</p>
        </div>
    """


def show_festival_cards(df):
    """축제 검색 결과를 두 열의 카드 형태로 표시한다."""
    for start_index in range(0, len(df), 2):
        columns = st.columns(2)

        for column_index, column in enumerate(columns):
            row_index = start_index + column_index
            if row_index >= len(df):
                continue

            with column:
                st.markdown(
                    festival_card_html(df.iloc[row_index]),
                    unsafe_allow_html=True,
                )


def show_recommendation(row):
    """랜덤 추천 축제를 크게 표시한다."""
    title = safe_text(row.get("축제명"), "축제명 없음")
    period = safe_text(row.get("기간"), "기간 정보 없음")
    address = safe_text(row.get("주소"), "주소 정보 없음")
    image_url = safe_text(row.get("firstimage"), "")

    st.markdown('<div class="recommend-box">', unsafe_allow_html=True)
    st.subheader(f"✨ 오늘의 추천: {title}")

    image_column, info_column = st.columns([1.2, 1])

    with image_column:
        if image_url:
            st.image(image_url, use_container_width=True)
        else:
            st.info("이미지가 제공되지 않습니다.")

    with info_column:
        st.markdown(f"### 🎪 {title}")
        st.markdown(f"**📅 축제 기간**  \n{period}")
        st.markdown(f"**📍 주소**  \n{address}")

    st.markdown("</div>", unsafe_allow_html=True)


def build_festival_map(df):
    """좌표가 있는 축제를 대한민국 중심의 Folium 지도에 표시한다."""
    map_df = df.dropna(subset=["위도", "경도"]).copy()

    # 대한민국 주변의 정상적인 좌표만 사용한다.
    map_df = map_df[
        map_df["위도"].between(33, 39)
        & map_df["경도"].between(124, 132)
    ]

    if map_df.empty:
        return None, 0

    # 대한민국 중심 좌표를 고정하여 지도를 생성한다.
    # fit_bounds()를 사용하지 않아 세계지도 수준으로 축소되는 현상을 방지한다.
    festival_map = folium.Map(
        location=[36.35, 127.8],
        zoom_start=7,
        min_zoom=6,
        max_zoom=18,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    marker_cluster = MarkerCluster().add_to(festival_map)

    for _, row in map_df.iterrows():
        title = html.escape(safe_text(row.get("축제명"), "축제명 없음"))
        period = html.escape(safe_text(row.get("기간"), "기간 정보 없음"))
        address = html.escape(safe_text(row.get("주소"), "주소 정보 없음"))

        popup_html = f"""
            <div style="width:260px;">
                <h4 style="margin-bottom:8px;">{title}</h4>
                <b>기간</b><br>{period}<br><br>
                <b>주소</b><br>{address}
            </div>
        """

        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=title,
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(marker_cluster)

    return festival_map, len(map_df)


def show_charts(df):
    """지역별 축제 수와 월별 축제 수 그래프를 표시한다."""
    if df.empty:
        st.info("분석할 축제 데이터가 없습니다.")
        return

    st.subheader("지역별 축제 수")
    region_counts = (
        df["지역"]
        .value_counts()
        .rename_axis("지역")
        .reset_index(name="축제 수")
        .sort_values("축제 수", ascending=True)
    )

    if region_counts.empty:
        st.info("지역별 그래프를 만들 수 있는 주소 정보가 없습니다.")
    else:
        region_figure = px.bar(
            region_counts,
            x="축제 수",
            y="지역",
            orientation="h",
            text="축제 수",
            title="지역별 축제 수",
        )
        region_figure.update_layout(
            xaxis_title="축제 수",
            yaxis_title="지역",
            height=max(420, len(region_counts) * 36),
        )
        region_figure.update_traces(textposition="outside")
        st.plotly_chart(region_figure, use_container_width=True)

    st.subheader("월별 축제 수")
    month_df = df.dropna(subset=["시작월"]).copy()

    if month_df.empty:
        st.info("월별 그래프를 만들 수 있는 시작일 정보가 없습니다.")
    else:
        month_counts = (
            month_df["시작월"]
            .astype(int)
            .value_counts()
            .sort_index()
            .reindex(range(1, 13), fill_value=0)
            .rename_axis("월")
            .reset_index(name="축제 수")
        )
        month_counts["월 표시"] = month_counts["월"].astype(str) + "월"

        month_figure = px.bar(
            month_counts,
            x="월 표시",
            y="축제 수",
            text="축제 수",
            title="축제 시작 월별 축제 수",
        )
        month_figure.update_layout(
            xaxis_title="시작 월",
            yaxis_title="축제 수",
        )
        month_figure.update_traces(textposition="outside")
        st.plotly_chart(month_figure, use_container_width=True)


# ---------------------------------------------------------
# 왼쪽 대시보드와 오른쪽 결과 화면
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero-box">
        <div class="hero-title">🎉 전국 축제 탐험대</div>
        <div class="hero-description">
            지역과 날짜를 골라 전국의 축제를 찾아보세요.
            사진 카드, 대한민국 지도, 축제 통계와 랜덤 추천까지 한 화면에서 즐길 수 있어요.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# API 키 읽기
# ---------------------------------------------------------
try:
    SERVICE_KEY = st.secrets["TOUR_API_KEY"].strip()
except (KeyError, FileNotFoundError, AttributeError):
    SERVICE_KEY = ""


# ---------------------------------------------------------
# 왼쪽 검색 대시보드
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🎪</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-title">축제 검색 대시보드</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="sidebar-subtitle">
            원하는 조건을 선택한 뒤<br>
            축제 검색 버튼을 눌러주세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 📍 지역")
    selected_area = st.selectbox(
        "지역 선택",
        options=list(AREA_CODES.keys()),
        label_visibility="collapsed",
    )

    st.markdown("#### 📅 축제 기간")
    start_date = st.date_input(
        "축제 검색 시작일",
        value=date.today(),
    )
    end_date = st.date_input(
        "축제 검색 종료일",
        value=date.today() + timedelta(days=90),
    )

    st.markdown("#### 🔤 축제명")
    keyword = st.text_input(
        "축제명 키워드",
        placeholder="예: 벚꽃, 음악, 불꽃",
        label_visibility="collapsed",
    )

    st.markdown("#### 🔢 결과 개수")
    result_count = st.select_slider(
        "결과 개수",
        options=[10, 20, 30, 50],
        value=20,
        label_visibility="collapsed",
    )

    search_clicked = st.button(
        "🔍 축제 검색하기",
        type="primary",
        use_container_width=True,
    )

    st.markdown(
        """
        <div class="sidebar-tip">
            💡 <b>검색 팁</b><br>
            ‘전국’을 선택하면 여러 지역의 축제를 한 번에 볼 수 있어요.<br>
            축제명은 일부 단어만 입력해도 검색할 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# 검색 버튼 처리
# ---------------------------------------------------------
if search_clicked:
    st.session_state.has_searched = True
    st.session_state.recommended_festival = None
    st.session_state.search_message = ""

    if not SERVICE_KEY:
        st.session_state.festival_df = pd.DataFrame()
        st.session_state.search_message = (
            "API 키가 등록되어 있지 않습니다. "
            "Streamlit Secrets에 TOUR_API_KEY를 등록해 주세요."
        )
    elif end_date < start_date:
        st.session_state.festival_df = pd.DataFrame()
        st.session_state.search_message = (
            "검색 종료일은 검색 시작일보다 빠를 수 없습니다."
        )
    else:
        api_start_date = start_date.strftime("%Y%m%d")
        api_end_date = end_date.strftime("%Y%m%d")
        selected_area_code = AREA_CODES[selected_area]

        with st.spinner("전국의 축제 정보를 불러오는 중입니다..."):
            items, error_message = request_festivals(
                SERVICE_KEY,
                selected_area_code,
                api_start_date,
                api_end_date,
                result_count,
            )

        if error_message:
            st.session_state.festival_df = pd.DataFrame()
            st.session_state.search_message = error_message
        else:
            result_df = prepare_dataframe(items, keyword)
            st.session_state.festival_df = result_df

            if result_df.empty:
                if keyword.strip() and items:
                    st.session_state.search_message = (
                        "API 결과는 있으나 입력한 키워드와 일치하는 축제가 없습니다."
                    )
                else:
                    st.session_state.search_message = (
                        "선택한 조건에 해당하는 축제가 없습니다."
                    )


# ---------------------------------------------------------
# 검색 결과 및 오류 메시지
# ---------------------------------------------------------
if st.session_state.search_message:
    st.warning(st.session_state.search_message)

festival_df = st.session_state.festival_df

if st.session_state.has_searched and not festival_df.empty:
    st.success(f"🎊 총 {len(festival_df)}개의 축제를 찾았습니다.")

    # 검색 결과 요약 대시보드
    coordinate_count = int(
        festival_df.dropna(subset=["위도", "경도"]).shape[0]
    )
    region_count = int(
        festival_df["지역"].replace("지역 정보 없음", pd.NA).dropna().nunique()
    )

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-value">🎪 {len(festival_df)}</div>
                <div class="summary-label">검색된 축제</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with summary_col2:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-value">🗺️ {coordinate_count}</div>
                <div class="summary-label">지도 표시 가능</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with summary_col3:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-value">📍 {region_count}</div>
                <div class="summary-label">검색된 지역</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    # 랜덤 추천 버튼
    if st.button("🎁 오늘의 랜덤 축제 추천", use_container_width=True):
        random_index = random.randrange(len(festival_df))
        st.session_state.recommended_festival = (
            festival_df.iloc[random_index].to_dict()
        )

    if st.session_state.recommended_festival is not None:
        show_recommendation(st.session_state.recommended_festival)

    # 검색 결과 탭
    list_tab, map_tab, analysis_tab = st.tabs(
        ["🎪 축제 목록", "🗺️ 축제 지도", "📊 축제 분석"]
    )

    with list_tab:
        show_festival_cards(festival_df)

    with map_tab:
        festival_map, marker_count = build_festival_map(festival_df)

        if festival_map is None:
            st.info("위도와 경도 정보가 있는 축제가 없어 지도를 표시할 수 없습니다.")
        else:
            st.caption(f"지도에 표시된 축제: {marker_count}개")
            folium_static(
                festival_map,
                width=1200,
                height=620,
            )

    with analysis_tab:
        show_charts(festival_df)

elif not st.session_state.has_searched:
    st.info("👈 왼쪽 대시보드에서 검색 조건을 선택한 뒤 ‘축제 검색하기’를 눌러주세요.")
