import html
import random
import re
from urllib.parse import unquote

import pandas as pd
import requests
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="랜덤 국내여행 뽑기",
    page_icon="🎁",
    layout="wide",
)

API_BASE_URL = "https://apis.data.go.kr/B551011/KorService2"
MOBILE_OS = "ETC"
MOBILE_APP = "RandomKoreaTrip"

# 한국관광공사 TourAPI 지역 코드
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
    "경기": "31",
    "강원": "32",
    "충북": "33",
    "충남": "34",
    "경북": "35",
    "경남": "36",
    "전북": "37",
    "전남": "38",
    "제주": "39",
}

# 관광 타입 코드
CONTENT_TYPES = {
    "관광지": "12",
    "문화시설": "14",
    "축제·행사": "15",
    "레포츠": "28",
    "숙박": "32",
    "쇼핑": "38",
    "음식점": "39",
}

TYPE_EMOJI = {
    "12": "🏞️",
    "14": "🏛️",
    "15": "🎉",
    "28": "🚴",
    "32": "🏨",
    "38": "🛍️",
    "39": "🍽️",
}


# =========================================================
# 디자인
# =========================================================
st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 10% 10%, #fff4cf 0, transparent 28%),
                radial-gradient(circle at 90% 15%, #dff5ff 0, transparent 28%),
                linear-gradient(180deg, #fffdf7 0%, #f7fbff 100%);
        }

        .block-container {
            max-width: 1100px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .hero {
            padding: 2.1rem 1.4rem;
            border-radius: 28px;
            text-align: center;
            background: linear-gradient(135deg, #ff7a8a, #ffb45c);
            box-shadow: 0 14px 35px rgba(255, 122, 138, 0.24);
            color: white;
            margin-bottom: 1.2rem;
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(2rem, 5vw, 3.4rem);
            letter-spacing: -0.06em;
        }

        .hero p {
            margin: 0.7rem 0 0;
            font-size: 1.05rem;
            opacity: 0.96;
        }

        .result-card {
            padding: 1.5rem;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(236, 217, 198, 0.85);
            box-shadow: 0 12px 32px rgba(62, 80, 110, 0.12);
        }

        .destination-title {
            margin: 0 0 0.65rem;
            color: #26334d;
            font-size: clamp(1.7rem, 4vw, 2.6rem);
            line-height: 1.25;
            letter-spacing: -0.04em;
        }

        .badge {
            display: inline-block;
            padding: 0.35rem 0.72rem;
            margin: 0 0.35rem 0.45rem 0;
            border-radius: 999px;
            background: #fff0e5;
            color: #d85f3b;
            font-weight: 700;
            font-size: 0.9rem;
        }

        .info-box {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: #f6f8fc;
            margin: 0.65rem 0;
            color: #33415c;
        }

        .description {
            line-height: 1.85;
            color: #46536a;
            word-break: keep-all;
        }

        .empty-image {
            height: 340px;
            border-radius: 22px;
            background: linear-gradient(135deg, #dff3ff, #ffe8c8);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            font-size: 5rem;
            border: 1px solid #e8e8e8;
        }

        div.stButton > button {
            width: 100%;
            min-height: 3.25rem;
            border: 0;
            border-radius: 16px;
            font-weight: 800;
            font-size: 1.05rem;
            color: white;
            background: linear-gradient(135deg, #ff647c, #ff9b4a);
            box-shadow: 0 8px 20px rgba(255, 100, 124, 0.22);
        }

        div.stButton > button:hover {
            color: white;
            border: 0;
            transform: translateY(-1px);
        }

        [data-testid="stSidebar"] {
            background: #fffaf3;
        }

        .small-note {
            color: #758098;
            font-size: 0.88rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 공통 함수
# =========================================================
def get_service_key():
    """Streamlit Secrets에서 API 키를 가져온다."""
    try:
        key = st.secrets["TOUR_API_KEY"]
    except (KeyError, FileNotFoundError):
        return ""

    # 인코딩 키와 디코딩 키 중 어느 것을 넣어도 최대한 동작하도록 처리
    return unquote(str(key).strip())


def clean_text(value, default="정보 없음"):
    """None, NaN, 빈 문자열을 안전하게 처리한다."""
    if value is None:
        return default

    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    return text


def remove_html_tags(text):
    """API 설명에 들어 있는 HTML 태그를 제거한다."""
    if not text:
        return ""

    text = re.sub(r"<br\s*/?>", "\n", str(text), flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def normalize_items(items):
    """API가 항목 1개를 dict로 주는 경우와 여러 개를 list로 주는 경우를 통일한다."""
    if not items:
        return []

    if isinstance(items, dict):
        return [items]

    if isinstance(items, list):
        return items

    return []


def extract_response(json_data):
    """TourAPI 응답에서 결과 코드, 전체 개수, 항목을 추출한다."""
    response = json_data.get("response", {})
    header = response.get("header", {})
    body = response.get("body", {})

    result_code = str(header.get("resultCode", ""))
    result_message = str(header.get("resultMsg", ""))

    if result_code != "0000":
        raise RuntimeError(f"API 오류 {result_code}: {result_message}")

    total_count = int(body.get("totalCount", 0) or 0)
    items = normalize_items(body.get("items", {}).get("item", []))
    return total_count, items


@st.cache_data(ttl=1800, show_spinner=False)
def call_tour_api(endpoint, params_tuple):
    """TourAPI 호출 결과를 30분 동안 캐시에 저장한다."""
    params = dict(params_tuple)
    response = requests.get(
        f"{API_BASE_URL}/{endpoint}",
        params=params,
        timeout=15,
    )
    response.raise_for_status()

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as error:
        preview = response.text[:200]
        raise RuntimeError(
            "API가 JSON이 아닌 응답을 반환했습니다. "
            f"인증키 또는 요청 주소를 확인하세요. 응답: {preview}"
        ) from error


def base_params(service_key):
    return {
        "serviceKey": service_key,
        "MobileOS": MOBILE_OS,
        "MobileApp": MOBILE_APP,
        "_type": "json",
    }


def fetch_random_candidates(service_key, area_code, content_type_id):
    """
    조건에 맞는 전체 결과 수를 확인한 뒤,
    무작위 페이지 하나를 골라 후보 최대 40개를 가져온다.
    """
    page_size = 40

    first_params = base_params(service_key)
    first_params.update(
        {
            "numOfRows": page_size,
            "pageNo": 1,
            "arrange": "R",  # 생성일순
            "areaCode": area_code,
            "contentTypeId": content_type_id,
        }
    )

    first_json = call_tour_api(
        "areaBasedList2",
        tuple(sorted(first_params.items())),
    )
    total_count, first_items = extract_response(first_json)

    if total_count <= page_size:
        return first_items

    max_page = min((total_count + page_size - 1) // page_size, 100)
    random_page = random.randint(1, max_page)

    if random_page == 1:
        return first_items

    random_params = first_params.copy()
    random_params["pageNo"] = random_page

    random_json = call_tour_api(
        "areaBasedList2",
        tuple(sorted(random_params.items())),
    )
    _, random_items = extract_response(random_json)
    return random_items


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_detail(service_key, content_id):
    """선택된 여행지의 상세 설명을 가져온다."""
    params = base_params(service_key)
    params.update(
        {
            "contentId": content_id,
        }
    )

    json_data = call_tour_api(
        "detailCommon2",
        tuple(sorted(params.items())),
    )
    _, items = extract_response(json_data)

    if not items:
        return {}
    return items[0]


def pick_destination(candidates):
    """사진 또는 좌표가 있는 항목을 우선하여 무작위 선택한다."""
    valid = [
        item
        for item in candidates
        if clean_text(item.get("title"), "") and (
            clean_text(item.get("firstimage"), "")
            or (
                clean_text(item.get("mapx"), "")
                and clean_text(item.get("mapy"), "")
            )
        )
    ]

    pool = valid if valid else candidates
    return random.choice(pool) if pool else None


def build_map_dataframe(item):
    """지도 표시용 데이터프레임을 만든다."""
    try:
        latitude = float(item.get("mapy"))
        longitude = float(item.get("mapx"))
    except (TypeError, ValueError):
        return None

    return pd.DataFrame(
        {
            "lat": [latitude],
            "lon": [longitude],
        }
    )


# =========================================================
# 화면 상단
# =========================================================
st.markdown(
    """
    <div class="hero">
        <h1>🎁 랜덤 국내여행 뽑기</h1>
        <p>지역과 여행 유형을 고르고, 오늘 떠날 여행지를 뽑아보세요!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

service_key = get_service_key()

if not service_key:
    st.error("TourAPI 인증키가 설정되지 않았습니다.")
    st.code(
        'TOUR_API_KEY = "공공데이터포털에서 발급받은 일반 인증키"',
        language="toml",
    )
    st.info(
        "Streamlit Cloud의 App settings → Secrets에 위 내용을 저장한 뒤 "
        "앱을 다시 실행하세요."
    )
    st.stop()


# =========================================================
# 검색 조건
# =========================================================
with st.sidebar:
    st.header("🧳 여행 조건")

    selected_area = st.selectbox(
        "어디로 떠날까요?",
        list(AREA_CODES.keys()),
        index=0,
    )

    selected_type = st.selectbox(
        "무엇을 즐길까요?",
        list(CONTENT_TYPES.keys()),
        index=0,
    )

    image_only = st.checkbox(
        "사진이 있는 장소만 추천",
        value=True,
    )

    st.divider()
    st.caption(
        "관광정보와 이미지는 한국관광공사 TourAPI에서 불러옵니다."
    )

control_col1, control_col2 = st.columns([2, 1])

with control_col1:
    draw_clicked = st.button(
        "🎲 여행지 뽑기",
        type="primary",
        use_container_width=True,
    )

with control_col2:
    clear_clicked = st.button(
        "🧹 결과 지우기",
        use_container_width=True,
    )

if clear_clicked:
    st.session_state.pop("destination", None)
    st.session_state.pop("detail", None)
    st.session_state.pop("selection_text", None)
    st.rerun()


# =========================================================
# 여행지 뽑기
# =========================================================
if draw_clicked:
    try:
        with st.spinner("전국의 여행지를 섞고 있어요... 🎁"):
            candidates = fetch_random_candidates(
                service_key=service_key,
                area_code=AREA_CODES[selected_area],
                content_type_id=CONTENT_TYPES[selected_type],
            )

            if image_only:
                candidates = [
                    item
                    for item in candidates
                    if clean_text(item.get("firstimage"), "")
                ]

            destination = pick_destination(candidates)

            if destination is None:
                st.warning(
                    "선택한 조건에 맞는 여행지가 없습니다. "
                    "지역이나 여행 유형을 바꿔 다시 시도해 주세요."
                )
            else:
                detail = fetch_detail(
                    service_key,
                    clean_text(destination.get("contentid"), ""),
                )

                st.session_state["destination"] = destination
                st.session_state["detail"] = detail
                st.session_state["selection_text"] = (
                    f"{selected_area} · {selected_type}"
                )

    except requests.exceptions.Timeout:
        st.error("관광정보 서버의 응답이 늦습니다. 잠시 후 다시 뽑아 주세요.")
    except requests.exceptions.RequestException as error:
        st.error(f"관광정보를 불러오지 못했습니다: {error}")
    except (RuntimeError, ValueError) as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"예상하지 못한 오류가 발생했습니다: {error}")


# =========================================================
# 결과 화면
# =========================================================
if "destination" not in st.session_state:
    st.markdown("### ✨ 오늘의 여행지를 뽑아보세요")
    st.info(
        "왼쪽에서 지역과 여행 유형을 선택한 다음 "
        "‘여행지 뽑기’ 버튼을 눌러주세요."
    )
    st.markdown(
        """
        #### 이렇게 활용할 수 있어요
        - 수업 시작 전 랜덤 여행지 퀴즈
        - 친구·가족과 주말 여행지 정하기
        - 국내 관광지 탐색 프로젝트
        """
    )
    st.stop()

destination = st.session_state["destination"]
detail = st.session_state.get("detail", {})

title = clean_text(destination.get("title"), "이름 없는 여행지")
address = " ".join(
    part
    for part in [
        clean_text(destination.get("addr1"), ""),
        clean_text(destination.get("addr2"), ""),
    ]
    if part
).strip() or "주소 정보 없음"

image_url = clean_text(destination.get("firstimage"), "")
thumbnail_url = clean_text(destination.get("firstimage2"), "")
image_url = image_url or thumbnail_url

content_type_id = clean_text(destination.get("contenttypeid"), "")
emoji = TYPE_EMOJI.get(content_type_id, "📍")
selection_text = st.session_state.get("selection_text", "랜덤 여행")

overview = remove_html_tags(detail.get("overview", ""))
homepage = clean_text(detail.get("homepage"), "")
tel = clean_text(
    detail.get("tel") or destination.get("tel"),
    "",
)
zipcode = clean_text(
    detail.get("zipcode") or destination.get("zipcode"),
    "",
)

st.success(f"🎉 오늘의 여행지가 선정되었습니다!  ·  {selection_text}")

left_col, right_col = st.columns([1.15, 1], gap="large")

with left_col:
    if image_url:
        st.image(
            image_url,
            caption=f"{title} 관광 이미지",
            use_container_width=True,
        )
    else:
        st.markdown(
            f"""
            <div class="empty-image">
                <div>{emoji}</div>
                <div style="font-size:1rem; margin-top:0.5rem;">
                    제공된 이미지가 없습니다
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with right_col:
    safe_title = html.escape(title)
    safe_address = html.escape(address)
    safe_zipcode = html.escape(zipcode)
    safe_tel = html.escape(tel)

    st.markdown(
        f"""
        <div class="result-card">
            <span class="badge">{emoji} {html.escape(selection_text)}</span>
            <h2 class="destination-title">{safe_title}</h2>
            <div class="info-box">📍 <strong>주소</strong><br>{safe_address}</div>
            {
                f'<div class="info-box">☎️ <strong>전화</strong><br>{safe_tel}</div>'
                if tel else ''
            }
            {
                f'<div class="info-box">📮 <strong>우편번호</strong><br>{safe_zipcode}</div>'
                if zipcode else ''
            }
        </div>
        """,
        unsafe_allow_html=True,
    )

    mapx = clean_text(destination.get("mapx"), "")
    mapy = clean_text(destination.get("mapy"), "")

    if mapx and mapy:
        naver_map_url = (
            "https://map.naver.com/p/search/"
            + requests.utils.quote(title)
        )
        st.link_button(
            "🗺️ 네이버 지도에서 보기",
            naver_map_url,
            use_container_width=True,
        )

    if homepage and homepage != "정보 없음":
        # homepage 필드에 HTML 링크가 포함될 수 있으므로 그대로 출력
        st.markdown("🌐 **관련 홈페이지**")
        st.markdown(homepage, unsafe_allow_html=True)

st.divider()

st.subheader("📖 여행지 소개")
if overview:
    safe_overview = html.escape(overview).replace("\n", "<br>")
    st.markdown(
        f'<div class="result-card description">{safe_overview}</div>',
        unsafe_allow_html=True,
    )
else:
    st.info("이 여행지에는 상세 소개가 등록되어 있지 않습니다.")

map_df = build_map_dataframe(destination)
if map_df is not None:
    st.subheader("🗺️ 위치")
    st.map(map_df, zoom=11, use_container_width=True)

st.caption(
    "※ 여행 전 운영시간, 휴무일, 이용요금 등 최신 정보를 관련 기관에 확인하세요."
)
