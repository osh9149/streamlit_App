import random
from datetime import datetime

import requests
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="오늘 뭐 먹지?",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# 귀여운 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');

        html, body, [class*="css"] {
            font-family: 'Jua', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 10%, #fff0f6 0, transparent 25%),
                radial-gradient(circle at 90% 20%, #fff7d6 0, transparent 25%),
                linear-gradient(135deg, #fff9fc 0%, #f3f8ff 100%);
        }

        .main .block-container {
            max-width: 1150px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .main-title {
            text-align: center;
            font-size: 3.1rem;
            font-weight: 800;
            color: #ff5d8f;
            margin-bottom: 0;
            text-shadow: 3px 3px 0 #ffe1ec;
        }

        .sub-title {
            text-align: center;
            font-size: 1.15rem;
            color: #6f6f80;
            margin-top: 0.4rem;
            margin-bottom: 2rem;
        }

        .weather-box {
            background: rgba(255, 255, 255, 0.9);
            border: 3px solid #ffd3e1;
            border-radius: 28px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 10px 28px rgba(255, 93, 143, 0.13);
            margin: 15px 0 25px 0;
        }

        .weather-icon {
            font-size: 4.5rem;
            line-height: 1.1;
        }

        .weather-location {
            font-size: 1.6rem;
            font-weight: 700;
            color: #555568;
            margin-top: 8px;
        }

        .weather-description {
            font-size: 1.25rem;
            color: #ff5d8f;
            margin-top: 7px;
        }

        .temperature {
            font-size: 2.7rem;
            font-weight: 800;
            color: #4f79d8;
            margin: 6px 0;
        }

        .weather-detail {
            font-size: 1rem;
            color: #727285;
        }

        .recommend-title {
            text-align: center;
            font-size: 2rem;
            color: #555568;
            margin: 22px 0;
        }

        .food-card {
            background-color: rgba(255, 255, 255, 0.96);
            border: 2px solid #ffe1aa;
            border-radius: 24px;
            padding: 18px;
            min-height: 520px;
            box-shadow: 0 8px 24px rgba(90, 90, 120, 0.10);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .food-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 14px 30px rgba(90, 90, 120, 0.16);
        }

        .food-image {
            width: 100%;
            height: 210px;
            object-fit: cover;
            border-radius: 18px;
        }

        .food-name {
            font-size: 1.7rem;
            color: #ff6b81;
            text-align: center;
            margin-top: 13px;
            margin-bottom: 4px;
        }

        .food-reason {
            color: #6c6c7e;
            text-align: center;
            min-height: 50px;
            line-height: 1.5;
        }

        .calorie-badge {
            display: inline-block;
            background: #fff0b8;
            color: #b06e00;
            border-radius: 20px;
            padding: 7px 14px;
            font-size: 1.05rem;
            margin: 8px 0 12px 0;
        }

        .nutrition-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 8px;
        }

        .nutrition-item {
            background: #f8f5ff;
            border-radius: 13px;
            padding: 9px 6px;
            text-align: center;
            color: #5e5873;
        }

        .notice-box {
            background: #fff8de;
            border: 2px dashed #f4c95d;
            border-radius: 18px;
            padding: 14px 18px;
            color: #735d28;
            margin-top: 25px;
            text-align: center;
        }

        .stTextInput input {
            border: 2px solid #ffc4d7;
            border-radius: 18px;
            padding: 12px 15px;
            background-color: white;
        }

        .stButton > button {
            width: 100%;
            border: none;
            border-radius: 18px;
            padding: 0.75rem 1rem;
            background: linear-gradient(90deg, #ff82a9, #ffb36b);
            color: white;
            font-size: 1.1rem;
            font-weight: 700;
            box-shadow: 0 5px 15px rgba(255, 130, 169, 0.3);
        }

        .stButton > button:hover {
            color: white;
            border: none;
            transform: translateY(-2px);
        }

        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.85);
            border: 2px solid #e7e2ff;
            border-radius: 18px;
            padding: 12px;
        }

        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 날씨 코드
# =========================================================
WEATHER_CODES = {
    0: ("맑음", "☀️", "sunny"),
    1: ("대체로 맑음", "🌤️", "sunny"),
    2: ("구름 조금", "⛅", "cloudy"),
    3: ("흐림", "☁️", "cloudy"),
    45: ("안개", "🌫️", "cloudy"),
    48: ("짙은 안개", "🌫️", "cloudy"),
    51: ("약한 이슬비", "🌦️", "rainy"),
    53: ("이슬비", "🌦️", "rainy"),
    55: ("강한 이슬비", "🌧️", "rainy"),
    56: ("어는 이슬비", "🌧️", "rainy"),
    57: ("강한 어는 이슬비", "🌧️", "rainy"),
    61: ("약한 비", "🌧️", "rainy"),
    63: ("비", "🌧️", "rainy"),
    65: ("강한 비", "☔", "rainy"),
    66: ("어는 비", "🌧️", "rainy"),
    67: ("강한 어는 비", "🌧️", "rainy"),
    71: ("약한 눈", "🌨️", "snowy"),
    73: ("눈", "❄️", "snowy"),
    75: ("강한 눈", "☃️", "snowy"),
    77: ("싸락눈", "🌨️", "snowy"),
    80: ("약한 소나기", "🌦️", "rainy"),
    81: ("소나기", "🌧️", "rainy"),
    82: ("강한 소나기", "☔", "rainy"),
    85: ("약한 눈보라", "🌨️", "snowy"),
    86: ("강한 눈보라", "☃️", "snowy"),
    95: ("천둥번개", "⛈️", "stormy"),
    96: ("우박을 동반한 천둥번개", "⛈️", "stormy"),
    99: ("강한 우박과 천둥번개", "⛈️", "stormy"),
}


# =========================================================
# 메뉴 데이터
# 영양 정보는 일반적인 1인분 기준의 예시 값입니다.
# =========================================================
MENU_DATA = {
    "hot": [
        {
            "name": "냉면",
            "image": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=900&q=80",
            "calories": 480,
            "carbs": 87,
            "protein": 18,
            "fat": 7,
            "sodium": 1450,
            "reason": "더운 날에는 시원하고 새콤한 냉면으로 입맛을 살려보세요.",
        },
        {
            "name": "초밥",
            "image": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=80",
            "calories": 520,
            "carbs": 78,
            "protein": 29,
            "fat": 12,
            "sodium": 980,
            "reason": "깔끔하고 산뜻해서 더운 날에도 부담 없이 즐길 수 있어요.",
        },
        {
            "name": "치킨 샐러드",
            "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?auto=format&fit=crop&w=900&q=80",
            "calories": 390,
            "carbs": 24,
            "protein": 36,
            "fat": 17,
            "sodium": 690,
            "reason": "신선한 채소와 단백질을 함께 섭취할 수 있는 가벼운 메뉴예요.",
        },
        {
            "name": "비빔국수",
            "image": "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=900&q=80",
            "calories": 510,
            "carbs": 91,
            "protein": 14,
            "fat": 10,
            "sodium": 1280,
            "reason": "매콤달콤한 양념이 더위로 잃은 입맛을 되찾아 줘요.",
        },
    ],
    "cold": [
        {
            "name": "김치찌개",
            "image": "https://images.unsplash.com/photo-1583224994076-2cc47c04b770?auto=format&fit=crop&w=900&q=80",
            "calories": 450,
            "carbs": 38,
            "protein": 27,
            "fat": 21,
            "sodium": 1720,
            "reason": "추운 날에는 얼큰하고 뜨끈한 찌개가 몸을 따뜻하게 해줘요.",
        },
        {
            "name": "칼국수",
            "image": "https://images.unsplash.com/photo-1569058242253-92a9c755a0ec?auto=format&fit=crop&w=900&q=80",
            "calories": 560,
            "carbs": 96,
            "protein": 22,
            "fat": 10,
            "sodium": 1510,
            "reason": "따뜻한 국물과 부드러운 면이 쌀쌀한 날씨에 잘 어울려요.",
        },
        {
            "name": "소고기전골",
            "image": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80",
            "calories": 590,
            "carbs": 44,
            "protein": 43,
            "fat": 27,
            "sodium": 1390,
            "reason": "채소와 고기를 따뜻한 국물과 함께 푸짐하게 즐겨보세요.",
        },
        {
            "name": "붕어빵과 어묵",
            "image": "https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=900&q=80",
            "calories": 430,
            "carbs": 72,
            "protein": 16,
            "fat": 10,
            "sodium": 1050,
            "reason": "추운 날 생각나는 따뜻하고 정겨운 겨울 간식 조합이에요.",
        },
    ],
    "rainy": [
        {
            "name": "해물파전",
            "image": "https://images.unsplash.com/photo-1627308595186-e6bb36712645?auto=format&fit=crop&w=900&q=80",
            "calories": 610,
            "carbs": 69,
            "protein": 25,
            "fat": 27,
            "sodium": 1190,
            "reason": "빗소리와 지글지글 파전 굽는 소리는 언제나 좋은 조합이에요.",
        },
        {
            "name": "수제비",
            "image": "https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?auto=format&fit=crop&w=900&q=80",
            "calories": 490,
            "carbs": 87,
            "protein": 17,
            "fat": 8,
            "sodium": 1430,
            "reason": "비 오는 날에는 따뜻하고 쫄깃한 수제비 국물이 잘 어울려요.",
        },
        {
            "name": "떡볶이",
            "image": "https://images.unsplash.com/photo-1635363638580-c2809d049eee?auto=format&fit=crop&w=900&q=80",
            "calories": 540,
            "carbs": 103,
            "protein": 13,
            "fat": 9,
            "sodium": 1580,
            "reason": "축축한 날씨에는 매콤달콤한 떡볶이로 기분을 전환해 보세요.",
        },
        {
            "name": "우동",
            "image": "https://images.unsplash.com/photo-1618841557871-b4664fbf0cb3?auto=format&fit=crop&w=900&q=80",
            "calories": 460,
            "carbs": 78,
            "protein": 18,
            "fat": 9,
            "sodium": 1690,
            "reason": "따뜻한 국물과 탱글한 면이 비 오는 날의 쌀쌀함을 달래줘요.",
        },
    ],
    "sunny": [
        {
            "name": "김밥",
            "image": "https://images.unsplash.com/photo-1580651315530-69c8e0026377?auto=format&fit=crop&w=900&q=80",
            "calories": 480,
            "carbs": 76,
            "protein": 17,
            "fat": 13,
            "sodium": 980,
            "reason": "맑은 날 나들이나 산책을 하며 먹기 좋은 간편한 메뉴예요.",
        },
        {
            "name": "샌드위치",
            "image": "https://images.unsplash.com/photo-1553909489-cd47e0907980?auto=format&fit=crop&w=900&q=80",
            "calories": 420,
            "carbs": 48,
            "protein": 24,
            "fat": 15,
            "sodium": 820,
            "reason": "화창한 날 가볍게 즐기기 좋은 산뜻한 한 끼예요.",
        },
        {
            "name": "불고기 덮밥",
            "image": "https://images.unsplash.com/photo-1590301157890-4810ed352733?auto=format&fit=crop&w=900&q=80",
            "calories": 650,
            "carbs": 86,
            "protein": 35,
            "fat": 20,
            "sodium": 1250,
            "reason": "달콤하고 든든해서 활동하기 좋은 맑은 날에 잘 어울려요.",
        },
        {
            "name": "포케",
            "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
            "calories": 510,
            "carbs": 62,
            "protein": 31,
            "fat": 17,
            "sodium": 740,
            "reason": "신선한 채소와 곡물, 단백질을 골고루 먹을 수 있어요.",
        },
    ],
    "cloudy": [
        {
            "name": "돈가스",
            "image": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=80",
            "calories": 780,
            "carbs": 88,
            "protein": 36,
            "fat": 32,
            "sodium": 1340,
            "reason": "흐린 날에는 바삭하고 든든한 메뉴로 기분을 채워보세요.",
        },
        {
            "name": "오므라이스",
            "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=80",
            "calories": 690,
            "carbs": 91,
            "protein": 25,
            "fat": 26,
            "sodium": 1120,
            "reason": "부드러운 달걀과 따뜻한 밥이 편안한 기분을 만들어 줘요.",
        },
        {
            "name": "크림 파스타",
            "image": "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=900&q=80",
            "calories": 760,
            "carbs": 82,
            "protein": 24,
            "fat": 38,
            "sodium": 1080,
            "reason": "구름 낀 날에는 부드럽고 고소한 파스타가 잘 어울려요.",
        },
        {
            "name": "카레라이스",
            "image": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=80",
            "calories": 670,
            "carbs": 104,
            "protein": 21,
            "fat": 19,
            "sodium": 1310,
            "reason": "향긋한 카레 향으로 흐린 날의 처진 기분을 깨워보세요.",
        },
    ],
    "snowy": [
        {
            "name": "부대찌개",
            "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=900&q=80",
            "calories": 720,
            "carbs": 62,
            "protein": 39,
            "fat": 35,
            "sodium": 2350,
            "reason": "눈 오는 날에는 여러 재료가 듬뿍 들어간 뜨끈한 찌개가 좋아요.",
        },
        {
            "name": "갈비탕",
            "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=900&q=80",
            "calories": 590,
            "carbs": 45,
            "protein": 48,
            "fat": 24,
            "sodium": 1570,
            "reason": "진하고 따뜻한 국물이 추위에 지친 몸을 든든하게 해줘요.",
        },
        {
            "name": "만두전골",
            "image": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=900&q=80",
            "calories": 630,
            "carbs": 69,
            "protein": 31,
            "fat": 26,
            "sodium": 1810,
            "reason": "눈 내리는 풍경을 보며 따끈한 만두전골을 즐겨보세요.",
        },
        {
            "name": "호빵과 군고구마",
            "image": "https://images.unsplash.com/photo-1596097635121-14b63b7a0c19?auto=format&fit=crop&w=900&q=80",
            "calories": 390,
            "carbs": 81,
            "protein": 8,
            "fat": 5,
            "sodium": 350,
            "reason": "포근하고 달콤한 겨울 간식으로 눈 오는 날의 분위기를 즐겨보세요.",
        },
    ],
    "stormy": [
        {
            "name": "라면",
            "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=80",
            "calories": 520,
            "carbs": 79,
            "protein": 11,
            "fat": 17,
            "sodium": 1790,
            "reason": "천둥번개가 치는 날에는 집에서 따뜻한 라면이 간편하고 좋아요.",
        },
        {
            "name": "닭볶음탕",
            "image": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?auto=format&fit=crop&w=900&q=80",
            "calories": 680,
            "carbs": 56,
            "protein": 47,
            "fat": 29,
            "sodium": 1720,
            "reason": "거친 날씨에는 매콤하고 든든한 닭볶음탕이 잘 어울려요.",
        },
        {
            "name": "김치볶음밥",
            "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=80",
            "calories": 620,
            "carbs": 89,
            "protein": 20,
            "fat": 21,
            "sodium": 1380,
            "reason": "외출하기 어려운 날 냉장고 재료로 간편하게 만들기 좋아요.",
        },
        {
            "name": "짜장면",
            "image": "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=80",
            "calories": 760,
            "carbs": 112,
            "protein": 24,
            "fat": 25,
            "sodium": 1840,
            "reason": "비바람이 강한 날에는 집에서 편안하게 즐기는 배달 메뉴가 좋아요.",
        },
    ],
}


# =========================================================
# API 함수
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def search_city(city_name):
    """도시 이름을 위도와 경도로 변환합니다."""
    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city_name,
        "count": 5,
        "language": "ko",
        "format": "json",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json().get("results", [])


@st.cache_data(ttl=600, show_spinner=False)
def get_weather(latitude, longitude):
    """현재 날씨 정보를 가져옵니다."""
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


# =========================================================
# 메뉴 분류 함수
# =========================================================
def get_menu_category(weather_category, temperature):
    """
    날씨 상태와 온도를 사용하여 메뉴 분류를 결정합니다.
    강수·눈·천둥 상태를 먼저 반영합니다.
    """
    if weather_category in ["rainy", "snowy", "stormy"]:
        return weather_category

    if temperature >= 28:
        return "hot"

    if temperature <= 10:
        return "cold"

    return weather_category


def get_recommendations(category, count=3):
    """해당 날씨 분류에서 메뉴를 무작위로 선택합니다."""
    menus = MENU_DATA.get(category, MENU_DATA["sunny"])
    return random.sample(menus, min(count, len(menus)))


def format_location(city):
    """도시 정보를 보기 좋게 표시합니다."""
    name = city.get("name", "")
    admin1 = city.get("admin1", "")
    country = city.get("country", "")

    parts = [name]

    if admin1 and admin1 != name:
        parts.append(admin1)

    if country:
        parts.append(country)

    return ", ".join(parts)


# =========================================================
# 세션 상태
# =========================================================
if "recommendation_key" not in st.session_state:
    st.session_state.recommendation_key = 0

if "selected_city" not in st.session_state:
    st.session_state.selected_city = "서울"


# =========================================================
# 앱 상단
# =========================================================
st.markdown(
    """
    <div class="main-title">🍽️ 오늘 뭐 먹지? 🌈</div>
    <div class="sub-title">
        오늘의 날씨에 꼭 맞는 맛있는 메뉴를 추천해 드려요!
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 도시 검색
# =========================================================
input_col, button_col = st.columns([4, 1])

with input_col:
    city_input = st.text_input(
        "📍 날씨를 확인할 도시",
        value=st.session_state.selected_city,
        placeholder="예: 서울, 부산, 제주, Tokyo",
        label_visibility="collapsed",
    )

with button_col:
    search_button = st.button("🔍 메뉴 추천")


if search_button and city_input.strip():
    st.session_state.selected_city = city_input.strip()
    st.session_state.recommendation_key += 1


city_name = st.session_state.selected_city


# =========================================================
# 날씨 조회
# =========================================================
try:
    with st.spinner("구름에게 오늘 날씨를 물어보는 중이에요... ☁️"):
        city_results = search_city(city_name)

    if not city_results:
        st.error(
            "도시를 찾지 못했어요. 도시 이름을 다시 확인해 주세요. "
            "예: 서울, 부산, 제주, 도쿄"
        )
        st.stop()

    # 검색 결과가 여러 개일 경우 선택
    if len(city_results) > 1:
        city_options = {
            format_location(city): city
            for city in city_results
        }

        selected_label = st.selectbox(
            "검색된 지역 중 원하는 곳을 선택하세요.",
            options=list(city_options.keys()),
        )

        selected_city = city_options[selected_label]
    else:
        selected_city = city_results[0]

    latitude = selected_city["latitude"]
    longitude = selected_city["longitude"]

    weather_data = get_weather(latitude, longitude)
    current = weather_data.get("current", {})

    if not current:
        st.error("현재 날씨 정보를 가져오지 못했어요.")
        st.stop()

    temperature = float(current.get("temperature_2m", 0))
    apparent_temperature = float(
        current.get("apparent_temperature", temperature)
    )
    humidity = int(current.get("relative_humidity_2m", 0))
    precipitation = float(current.get("precipitation", 0))
    wind_speed = float(current.get("wind_speed_10m", 0))
    weather_code = int(current.get("weather_code", 0))

    weather_name, weather_icon, weather_category = WEATHER_CODES.get(
        weather_code,
        ("알 수 없는 날씨", "🌈", "cloudy"),
    )

    location_name = format_location(selected_city)
    timezone = weather_data.get("timezone", "")
    current_time = current.get(
        "time",
        datetime.now().strftime("%Y-%m-%dT%H:%M"),
    ).replace("T", " ")

    # =====================================================
    # 현재 날씨 카드
    # =====================================================
    st.markdown(
        f"""
        <div class="weather-box">
            <div class="weather-icon">{weather_icon}</div>
            <div class="weather-location">📍 {location_name}</div>
            <div class="weather-description">{weather_name}</div>
            <div class="temperature">{temperature:.1f}℃</div>
            <div class="weather-detail">
                체감온도 {apparent_temperature:.1f}℃ ·
                습도 {humidity}% ·
                바람 {wind_speed:.1f}km/h ·
                강수량 {precipitation:.1f}mm
            </div>
            <div class="weather-detail" style="margin-top:8px;">
                🕒 {current_time} · {timezone}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 날씨 요약 지표
    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("🌡️ 현재 기온", f"{temperature:.1f}℃")
    metric2.metric("🤗 체감 온도", f"{apparent_temperature:.1f}℃")
    metric3.metric("💧 습도", f"{humidity}%")
    metric4.metric("🌬️ 풍속", f"{wind_speed:.1f}km/h")

    # =====================================================
    # 메뉴 추천
    # =====================================================
    category = get_menu_category(weather_category, temperature)

    # 추천 버튼을 누를 때마다 결과가 바뀌도록 시드 설정
    random.seed(
        f"{location_name}-{weather_code}-"
        f"{round(temperature)}-"
        f"{st.session_state.recommendation_key}"
    )

    recommendations = get_recommendations(category)

    category_messages = {
        "hot": "더위를 시원하게 날려줄 메뉴예요! 🧊",
        "cold": "몸과 마음을 따뜻하게 해줄 메뉴예요! 🔥",
        "rainy": "빗소리와 잘 어울리는 메뉴예요! ☔",
        "sunny": "화창한 날 즐기기 좋은 메뉴예요! 🌼",
        "cloudy": "흐린 기분을 포근하게 채워줄 메뉴예요! ☁️",
        "snowy": "눈 오는 날 생각나는 따뜻한 메뉴예요! ⛄",
        "stormy": "집에서 든든하게 즐기기 좋은 메뉴예요! ⚡",
    }

    st.markdown(
        f"""
        <div class="recommend-title">
            오늘의 추천 메뉴 💕<br>
            <span style="font-size:1.1rem; color:#77778a;">
                {category_messages.get(category, "오늘 날씨에 어울리는 메뉴예요!")}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    menu_columns = st.columns(3)

    for column, menu in zip(menu_columns, recommendations):
        with column:
            st.markdown(
                f"""
                <div class="food-card">
                    <img
                        class="food-image"
                        src="{menu['image']}"
                        alt="{menu['name']}"
                    >
                    <div class="food-name">{menu['name']}</div>
                    <div class="food-reason">{menu['reason']}</div>

                    <div style="text-align:center;">
                        <span class="calorie-badge">
                            🔥 약 {menu['calories']} kcal
                        </span>
                    </div>

                    <div class="nutrition-grid">
                        <div class="nutrition-item">
                            🍚 탄수화물<br>
                            <b>{menu['carbs']}g</b>
                        </div>
                        <div class="nutrition-item">
                            🥩 단백질<br>
                            <b>{menu['protein']}g</b>
                        </div>
                        <div class="nutrition-item">
                            🥑 지방<br>
                            <b>{menu['fat']}g</b>
                        </div>
                        <div class="nutrition-item">
                            🧂 나트륨<br>
                            <b>{menu['sodium']}mg</b>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    if st.button("🎲 다른 메뉴도 추천해 주세요"):
        st.session_state.recommendation_key += 1
        st.rerun()

    st.markdown(
        """
        <div class="notice-box">
            💡 표시된 칼로리와 영양소는 일반적인 1인분을 기준으로 한
            참고용 수치입니다. 재료와 조리법에 따라 달라질 수 있어요.
        </div>
        """,
        unsafe_allow_html=True,
    )

except requests.exceptions.Timeout:
    st.error(
        "날씨 서버의 응답이 늦어지고 있어요. 잠시 후 다시 시도해 주세요."
    )

except requests.exceptions.ConnectionError:
    st.error(
        "인터넷 연결을 확인해 주세요. 날씨 정보를 가져오지 못했어요."
    )

except requests.exceptions.HTTPError as error:
    st.error(f"날씨 정보를 가져오는 중 오류가 발생했어요: {error}")

except Exception as error:
    st.error(f"예상하지 못한 오류가 발생했어요: {error}")
