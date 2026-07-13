import random
import textwrap

import requests
import streamlit as st


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="오늘 뭐 먹지?",
    page_icon="🍽️",
    layout="wide",
)


# =========================================================
# 화면 디자인
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
            radial-gradient(circle at 12% 8%, #fff1f7 0, transparent 25%),
            radial-gradient(circle at 88% 15%, #fff8dd 0, transparent 25%),
            linear-gradient(135deg, #fffafd 0%, #f4f8ff 100%);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .main-title {
        text-align: center;
        font-size: 3.2rem;
        color: #ff4f85;
        text-shadow: 3px 3px 0 #ffe0eb;
        margin-bottom: 0.25rem;
    }

    .sub-title {
        text-align: center;
        color: #6f6f82;
        font-size: 1.1rem;
        margin-bottom: 1.8rem;
    }

    .weather-card {
        background: rgba(255, 255, 255, 0.95);
        border: 2px solid #ffd7e5;
        border-radius: 28px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(60, 60, 90, 0.10);
        margin-bottom: 20px;
    }

    .weather-layout {
        display: grid;
        grid-template-columns: 0.9fr 1.1fr 1.5fr;
        gap: 22px;
        align-items: center;
    }

    .weather-emoji {
        font-size: 5rem;
        text-align: center;
    }

    .weather-main {
        border-right: 1px dashed #dedee8;
        padding-right: 18px;
    }

    .location {
        font-size: 1.45rem;
        color: #323244;
        margin-bottom: 8px;
    }

    .weather-name {
        display: inline-block;
        background: #ffe7ef;
        color: #ff4f85;
        border-radius: 18px;
        padding: 5px 12px;
        font-size: 1rem;
        margin-bottom: 10px;
    }

    .temperature {
        font-size: 2.8rem;
        color: #ff4f85;
        margin: 8px 0 4px 0;
    }

    .feels-like {
        color: #66667a;
        font-size: 1rem;
    }

    .weather-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
    }

    .detail-item {
        background: #fafbff;
        border: 1px solid #ececf4;
        border-radius: 16px;
        padding: 14px;
        text-align: center;
        color: #555568;
    }

    .detail-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #333345;
        margin-top: 4px;
    }

    .recommend-title {
        text-align: center;
        color: #2f2f42;
        font-size: 2rem;
        margin-top: 28px;
        margin-bottom: 10px;
    }

    .recommend-message {
        text-align: center;
        background: #fff8df;
        border: 1.5px solid #ffd768;
        color: #6a5a2b;
        border-radius: 24px;
        padding: 11px;
        margin-bottom: 18px;
    }

    .food-card {
        background: rgba(255, 255, 255, 0.98);
        border: 2px solid #ffd48a;
        border-radius: 24px;
        padding: 16px;
        min-height: 570px;
        box-shadow: 0 8px 24px rgba(80, 80, 110, 0.10);
        overflow: hidden;
    }

    .food-image {
        display: block;
        width: 100%;
        height: 215px;
        object-fit: cover;
        border-radius: 18px;
    }

    .food-name {
        text-align: center;
        font-size: 1.7rem;
        font-weight: bold;
        color: #ff668f;
        margin-top: 16px;
        margin-bottom: 10px;
    }

    .food-reason {
        text-align: center;
        color: #626274;
        line-height: 1.55;
        min-height: 55px;
        padding: 0 8px;
    }

    .calorie-wrapper {
        text-align: center;
        margin: 14px 0 16px 0;
    }

    .calorie {
        display: inline-block;
        background: #fff1c7;
        color: #936224;
        border-radius: 22px;
        padding: 8px 18px;
        font-size: 1rem;
    }

    .nutrition-list {
        margin-top: 8px;
        padding: 0 5px;
    }

    .nutrition-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 11px 5px;
        color: #545467;
        border-bottom: 1px dashed #dddde6;
    }

    .nutrition-row:last-child {
        border-bottom: none;
    }

    .nutrition-row strong {
        color: #353546;
    }

    .notice {
        margin-top: 24px;
        padding: 14px;
        text-align: center;
        color: #725c26;
        background: #fff8dd;
        border: 1.5px solid #f0c65a;
        border-radius: 18px;
    }

    .stButton > button {
        width: 100%;
        border: none;
        border-radius: 18px;
        padding: 0.8rem;
        color: white;
        font-size: 1.08rem;
        background: linear-gradient(90deg, #ff3f81, #ff9b53);
        box-shadow: 0 5px 14px rgba(255, 80, 120, 0.22);
    }

    .stButton > button:hover {
        border: none;
        color: white;
        transform: translateY(-2px);
    }

    @media (max-width: 900px) {
        .weather-layout {
            grid-template-columns: 1fr;
        }

        .weather-main {
            border-right: none;
            padding-right: 0;
            text-align: center;
        }
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 서울 위치
# =========================================================
SEOUL_LATITUDE = 37.5665
SEOUL_LONGITUDE = 126.9780


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
    61: ("약한 비", "🌧️", "rainy"),
    63: ("비", "🌧️", "rainy"),
    65: ("강한 비", "☔", "rainy"),
    71: ("약한 눈", "🌨️", "snowy"),
    73: ("눈", "❄️", "snowy"),
    75: ("강한 눈", "☃️", "snowy"),
    80: ("약한 소나기", "🌦️", "rainy"),
    81: ("소나기", "🌧️", "rainy"),
    82: ("강한 소나기", "☔", "rainy"),
    85: ("약한 눈보라", "🌨️", "snowy"),
    86: ("강한 눈보라", "☃️", "snowy"),
    95: ("천둥번개", "⛈️", "stormy"),
    96: ("우박을 동반한 천둥번개", "⛈️", "stormy"),
    99: ("강한 천둥번개", "⛈️", "stormy"),
}


# =========================================================
# 메뉴 데이터
# =========================================================
MENU_DATA = {
    "hot": [
        {
            "name": "포케",
            "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
            "calories": 510,
            "carbs": 62,
            "protein": 31,
            "fat": 17,
            "sodium": 740,
            "reason": "채소와 단백질을 골고루 먹을 수 있는 산뜻한 메뉴예요.",
        },
        {
            "name": "물냉면",
            "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=80",
            "calories": 480,
            "carbs": 87,
            "protein": 18,
            "fat": 7,
            "sodium": 1450,
            "reason": "더운 날에는 시원하고 새콤한 냉면이 잘 어울려요.",
        },
        {
            "name": "초밥",
            "image": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=80",
            "calories": 520,
            "carbs": 78,
            "protein": 29,
            "fat": 12,
            "sodium": 980,
            "reason": "깔끔하고 산뜻해서 더운 날에도 부담이 적어요.",
        },
        {
            "name": "치킨 샐러드",
            "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?auto=format&fit=crop&w=900&q=80",
            "calories": 390,
            "carbs": 24,
            "protein": 36,
            "fat": 17,
            "sodium": 690,
            "reason": "가볍고 신선하게 즐길 수 있는 건강한 메뉴예요.",
        },
    ],
    "cold": [
        {
            "name": "김치찌개",
            "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=900&q=80",
            "calories": 450,
            "carbs": 38,
            "protein": 27,
            "fat": 21,
            "sodium": 1720,
            "reason": "쌀쌀한 날에는 얼큰하고 뜨끈한 찌개가 좋아요.",
        },
        {
            "name": "칼국수",
            "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=80",
            "calories": 560,
            "carbs": 96,
            "protein": 22,
            "fat": 10,
            "sodium": 1510,
            "reason": "따뜻한 국물과 부드러운 면이 추위를 녹여줘요.",
        },
        {
            "name": "갈비탕",
            "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=900&q=80",
            "calories": 590,
            "carbs": 45,
            "protein": 48,
            "fat": 24,
            "sodium": 1570,
            "reason": "진하고 따뜻한 국물이 몸을 든든하게 해줘요.",
        },
        {
            "name": "소고기전골",
            "image": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80",
            "calories": 590,
            "carbs": 44,
            "protein": 43,
            "fat": 27,
            "sodium": 1390,
            "reason": "채소와 고기를 따뜻한 국물과 함께 즐겨보세요.",
        },
    ],
    "rainy": [
        {
            "name": "해물파전",
            "image": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?auto=format&fit=crop&w=900&q=80",
            "calories": 610,
            "carbs": 69,
            "protein": 25,
            "fat": 27,
            "sodium": 1190,
            "reason": "빗소리와 지글지글 파전은 잘 어울리는 조합이에요.",
        },
        {
            "name": "수제비",
            "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=80",
            "calories": 490,
            "carbs": 87,
            "protein": 17,
            "fat": 8,
            "sodium": 1430,
            "reason": "비 오는 날에는 따뜻한 수제비 국물이 좋아요.",
        },
        {
            "name": "떡볶이",
            "image": "https://images.unsplash.com/photo-1635363638580-c2809d049eee?auto=format&fit=crop&w=900&q=80",
            "calories": 540,
            "carbs": 103,
            "protein": 13,
            "fat": 9,
            "sodium": 1580,
            "reason": "매콤달콤한 떡볶이로 처진 기분을 깨워보세요.",
        },
        {
            "name": "우동",
            "image": "https://images.unsplash.com/photo-1618841557871-b4664fbf0cb3?auto=format&fit=crop&w=900&q=80",
            "calories": 460,
            "carbs": 78,
            "protein": 18,
            "fat": 9,
            "sodium": 1690,
            "reason": "따뜻한 국물과 탱글한 면이 비 오는 날에 잘 어울려요.",
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
            "reason": "맑은 날 나들이하며 먹기 좋은 간편한 메뉴예요.",
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
            "image": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80",
            "calories": 650,
            "carbs": 86,
            "protein": 35,
            "fat": 20,
            "sodium": 1250,
            "reason": "달콤하고 든든해서 활동하기 좋은 날에 잘 어울려요.",
        },
        {
            "name": "포케",
            "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
            "calories": 510,
            "carbs": 62,
            "protein": 31,
            "fat": 17,
            "sodium": 740,
            "reason": "신선한 채소와 곡물을 가볍게 즐겨보세요.",
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
            "reason": "흐린 날에는 바삭하고 든든한 메뉴가 좋아요.",
        },
        {
            "name": "오므라이스",
            "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=80",
            "calories": 690,
            "carbs": 91,
            "protein": 25,
            "fat": 26,
            "sodium": 1120,
            "reason": "부드러운 달걀과 따뜻한 밥이 편안함을 줘요.",
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
            "reason": "향긋한 카레 향으로 흐린 날의 기분을 깨워보세요.",
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
            "reason": "눈 오는 날에는 뜨끈하고 푸짐한 찌개가 좋아요.",
        },
        {
            "name": "갈비탕",
            "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=900&q=80",
            "calories": 590,
            "carbs": 45,
            "protein": 48,
            "fat": 24,
            "sodium": 1570,
            "reason": "진하고 따뜻한 국물이 추위를 녹여줘요.",
        },
        {
            "name": "만두전골",
            "image": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=900&q=80",
            "calories": 630,
            "carbs": 69,
            "protein": 31,
            "fat": 26,
            "sodium": 1810,
            "reason": "눈 내리는 날 따뜻한 만두전골을 즐겨보세요.",
        },
        {
            "name": "군고구마",
            "image": "https://images.unsplash.com/photo-1596097635121-14b63b7a0c19?auto=format&fit=crop&w=900&q=80",
            "calories": 240,
            "carbs": 57,
            "protein": 4,
            "fat": 1,
            "sodium": 70,
            "reason": "달콤하고 따뜻한 겨울 간식으로 좋아요.",
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
            "reason": "천둥번개가 치는 날에는 집에서 따뜻한 라면이 좋아요.",
        },
        {
            "name": "닭볶음탕",
            "image": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?auto=format&fit=crop&w=900&q=80",
            "calories": 680,
            "carbs": 56,
            "protein": 47,
            "fat": 29,
            "sodium": 1720,
            "reason": "거친 날씨에는 매콤하고 든든한 메뉴가 잘 어울려요.",
        },
        {
            "name": "김치볶음밥",
            "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=80",
            "calories": 620,
            "carbs": 89,
            "protein": 20,
            "fat": 21,
            "sodium": 1380,
            "reason": "외출하기 어려운 날 간편하게 먹기 좋은 메뉴예요.",
        },
        {
            "name": "짜장면",
            "image": "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=80",
            "calories": 760,
            "carbs": 112,
            "protein": 24,
            "fat": 25,
            "sodium": 1840,
            "reason": "비바람이 강한 날 편안하게 즐기는 배달 메뉴예요.",
        },
    ],
}


# =========================================================
# 날씨 API
# =========================================================
@st.cache_data(ttl=600, show_spinner=False)
def get_seoul_weather():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": SEOUL_LATITUDE,
        "longitude": SEOUL_LONGITUDE,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": "Asia/Seoul",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_menu_category(weather_category, temperature):
    if weather_category in ["rainy", "snowy", "stormy"]:
        return weather_category

    if temperature >= 28:
        return "hot"

    if temperature <= 10:
        return "cold"

    return weather_category


def get_recommendations(category):
    menus = MENU_DATA.get(category, MENU_DATA["sunny"])
    return random.sample(menus, 3)


# =========================================================
# 세션 상태
# =========================================================
if "recommendation_number" not in st.session_state:
    st.session_state.recommendation_number = 0


# =========================================================
# 화면 출력
# =========================================================
st.markdown(
    """
    <div class="main-title">🍽️ 오늘 뭐 먹지? 🌈</div>
    <div class="sub-title">
        서울의 오늘 날씨에 딱 맞는 메뉴를 추천해 드려요!
    </div>
    """,
    unsafe_allow_html=True,
)


try:
    with st.spinner("서울의 오늘 날씨를 확인하는 중이에요... ☁️"):
        weather_data = get_seoul_weather()

    current = weather_data.get("current", {})

    if not current:
        st.error("현재 날씨 정보를 가져오지 못했습니다.")
        st.stop()

    temperature = float(current.get("temperature_2m", 0))
    apparent_temperature = float(current.get("apparent_temperature", temperature))
    humidity = int(current.get("relative_humidity_2m", 0))
    precipitation = float(current.get("precipitation", 0))
    wind_speed = float(current.get("wind_speed_10m", 0))
    weather_code = int(current.get("weather_code", 0))
    current_time = current.get("time", "").replace("T", " ")

    weather_name, weather_icon, weather_category = WEATHER_CODES.get(
        weather_code,
        ("알 수 없는 날씨", "🌈", "cloudy"),
    )

    weather_html = textwrap.dedent(
        f"""
        <div class="weather-card">
            <div class="weather-layout">
                <div class="weather-emoji">{weather_icon}</div>

                <div class="weather-main">
                    <div class="location">📍 서울특별시</div>
                    <div class="weather-name">{weather_name}</div>
                    <div class="temperature">{temperature:.1f}℃</div>
                    <div class="feels-like">체감온도 {apparent_temperature:.1f}℃</div>
                </div>

                <div class="weather-details">
                    <div class="detail-item">
                        💧 습도
                        <div class="detail-value">{humidity}%</div>
                    </div>

                    <div class="detail-item">
                        🌧️ 강수량
                        <div class="detail-value">{precipitation:.1f}mm</div>
                    </div>

                    <div class="detail-item">
                        🌬️ 풍속
                        <div class="detail-value">{wind_speed:.1f}km/h</div>
                    </div>

                    <div class="detail-item">
                        🕒 업데이트
                        <div class="detail-value" style="font-size:1rem;">
                            {current_time}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    ).strip()

    st.markdown(weather_html, unsafe_allow_html=True)

    category = get_menu_category(weather_category, temperature)

    category_messages = {
        "hot": "더위를 시원하게 날려줄 메뉴예요! 🧊",
        "cold": "몸과 마음을 따뜻하게 해줄 메뉴예요! 🔥",
        "rainy": "빗소리와 잘 어울리는 메뉴예요! ☔",
        "sunny": "화창한 날 즐기기 좋은 메뉴예요! 🌼",
        "cloudy": "흐린 기분을 채워줄 든든한 메뉴예요! ☁️",
        "snowy": "눈 오는 날 생각나는 따뜻한 메뉴예요! ⛄",
        "stormy": "집에서 편안하게 즐기기 좋은 메뉴예요! ⚡",
    }

    st.markdown(
        '<div class="recommend-title">🍚 오늘의 추천 메뉴 💕</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="recommend-message">{category_messages.get(category)}</div>',
        unsafe_allow_html=True,
    )

    random.seed(
        f"{weather_code}-{round(temperature)}-"
        f"{st.session_state.recommendation_number}"
    )

    recommendations = get_recommendations(category)
    menu_columns = st.columns(3)

    for column, menu in zip(menu_columns, recommendations):
        with column:
            menu_card = textwrap.dedent(
                f"""
                <div class="food-card">
                    <img
                        class="food-image"
                        src="{menu['image']}"
                        alt="{menu['name']}"
                    >

                    <div class="food-name">{menu['name']}</div>

                    <div class="food-reason">
                        {menu['reason']}
                    </div>

                    <div class="calorie-wrapper">
                        <span class="calorie">
                            🔥 약 {menu['calories']} kcal
                        </span>
                    </div>

                    <div class="nutrition-list">
                        <div class="nutrition-row">
                            <span>🍚 탄수화물</span>
                            <strong>{menu['carbs']}g</strong>
                        </div>

                        <div class="nutrition-row">
                            <span>🥩 단백질</span>
                            <strong>{menu['protein']}g</strong>
                        </div>

                        <div class="nutrition-row">
                            <span>🥑 지방</span>
                            <strong>{menu['fat']}g</strong>
                        </div>

                        <div class="nutrition-row">
                            <span>🧂 나트륨</span>
                            <strong>{menu['sodium']}mg</strong>
                        </div>
                    </div>
                </div>
                """
            ).strip()

            st.markdown(menu_card, unsafe_allow_html=True)

    st.write("")

    if st.button("🎲 다른 메뉴 추천받기"):
        st.session_state.recommendation_number += 1
        st.rerun()

    st.markdown(
        """
        <div class="notice">
            💡 칼로리와 영양소는 일반적인 1인분을 기준으로 한 참고용 수치입니다.
            재료와 조리 방법에 따라 달라질 수 있어요.
        </div>
        """,
        unsafe_allow_html=True,
    )

except requests.exceptions.Timeout:
    st.error("날씨 서버의 응답이 늦어지고 있습니다. 다시 시도해 주세요.")

except requests.exceptions.ConnectionError:
    st.error("인터넷 연결을 확인해 주세요.")

except requests.exceptions.HTTPError as error:
    st.error(f"날씨 정보를 불러오는 중 오류가 발생했습니다: {error}")

except Exception as error:
    st.error(f"오류가 발생했습니다: {error}")
