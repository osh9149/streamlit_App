import base64
import html
import random
from datetime import datetime
from urllib.parse import quote_plus

import requests
import streamlit as st


st.set_page_config(
    page_title="오늘 뭐 입고 뭐 듣지?",
    page_icon="🌤️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1150px; padding-top: 2rem;}
    .hero {
        padding: 1.5rem 1.7rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #eef7ff, #fff3e9);
        margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0 0 .35rem 0;}
    .weather-card, .recommend-card {
        background: rgba(255,255,255,.92);
        border: 1px solid rgba(130,140,160,.18);
        border-radius: 20px;
        padding: 1.25rem;
        box-shadow: 0 8px 24px rgba(40,60,90,.07);
        height: 100%;
    }
    .metric-value {font-size: 1.75rem; font-weight: 800;}
    .muted {color: #687386;}
    .tag {
        display: inline-block;
        padding: .35rem .7rem;
        margin: .2rem .15rem .2rem 0;
        border-radius: 999px;
        background: #f1f5f9;
        font-size: .9rem;
    }
    .music-card {
        border: 1px solid rgba(130,140,160,.18);
        border-radius: 16px;
        padding: .8rem;
        margin-bottom: .8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


WEATHER_CODES = {
    0: ("맑음", "☀️"),
    1: ("대체로 맑음", "🌤️"),
    2: ("부분적으로 흐림", "⛅"),
    3: ("흐림", "☁️"),
    45: ("안개", "🌫️"),
    48: ("서리 안개", "🌫️"),
    51: ("약한 이슬비", "🌦️"),
    53: ("이슬비", "🌦️"),
    55: ("강한 이슬비", "🌧️"),
    56: ("약한 어는 이슬비", "🌧️"),
    57: ("강한 어는 이슬비", "🌧️"),
    61: ("약한 비", "🌦️"),
    63: ("비", "🌧️"),
    65: ("강한 비", "🌧️"),
    66: ("약한 어는 비", "🌧️"),
    67: ("강한 어는 비", "🌧️"),
    71: ("약한 눈", "🌨️"),
    73: ("눈", "❄️"),
    75: ("강한 눈", "❄️"),
    77: ("싸락눈", "🌨️"),
    80: ("약한 소나기", "🌦️"),
    81: ("소나기", "🌧️"),
    82: ("강한 소나기", "⛈️"),
    85: ("약한 눈 소나기", "🌨️"),
    86: ("강한 눈 소나기", "❄️"),
    95: ("천둥번개", "⛈️"),
    96: ("우박을 동반한 천둥번개", "⛈️"),
    99: ("강한 우박·천둥번개", "⛈️"),
}


@st.cache_data(ttl=3600, show_spinner=False)
def geocode_city(city_name: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 8,
        "language": "ko",
        "format": "json",
    }
    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()
    return response.json().get("results", [])


@st.cache_data(ttl=900, show_spinner=False)
def get_weather(latitude: float, longitude: float, timezone: str):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone or "auto",
        "forecast_days": 1,
        "current": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "precipitation",
                "rain",
                "weather_code",
                "cloud_cover",
                "wind_speed_10m",
                "wind_gusts_10m",
            ]
        ),
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_probability_max",
                "weather_code",
                "sunrise",
                "sunset",
            ]
        ),
    }
    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()
    return response.json()


def recommend_outfit(weather: dict):
    current = weather["current"]
    daily = weather["daily"]

    apparent = float(current["apparent_temperature"])
    t_min = float(daily["temperature_2m_min"][0])
    t_max = float(daily["temperature_2m_max"][0])
    rain_prob = int(daily["precipitation_probability_max"][0] or 0)
    precipitation = float(current["precipitation"] or 0)
    wind = float(current["wind_speed_10m"] or 0)
    code = int(current["weather_code"])

    if apparent >= 28:
        level = "hot"
        title = "한여름 가벼운 코디"
        items = ["반팔 티셔츠", "반바지 또는 얇은 치마", "통풍 좋은 운동화·샌들"]
        tip = "밝은 색과 통기성 좋은 소재를 선택하고 자외선 차단제를 챙기세요."
    elif apparent >= 23:
        level = "warm"
        title = "따뜻한 날의 산뜻한 코디"
        items = ["반팔 또는 얇은 셔츠", "면바지·얇은 청바지", "가벼운 운동화"]
        tip = "실내 냉방이 강할 수 있으니 얇은 가디건을 가방에 넣어도 좋습니다."
    elif apparent >= 17:
        level = "mild"
        title = "선선한 날의 레이어드 코디"
        items = ["긴팔 티셔츠·셔츠", "가디건 또는 얇은 재킷", "면바지·청바지"]
        tip = "아침저녁 기온 차에 대비해 벗기 쉬운 겉옷을 선택하세요."
    elif apparent >= 12:
        level = "cool"
        title = "쌀쌀한 날의 가벼운 아우터"
        items = ["니트·맨투맨", "트렌치코트·재킷", "긴바지"]
        tip = "목 주변이 추우면 얇은 스카프를 더하면 체감온도를 높일 수 있습니다."
    elif apparent >= 6:
        level = "cold"
        title = "초겨울 보온 코디"
        items = ["도톰한 니트", "코트·경량 패딩", "기모 또는 두꺼운 긴바지"]
        tip = "바람을 막아 주는 겉옷과 얇은 내복을 함께 활용하세요."
    else:
        level = "freezing"
        title = "한겨울 방한 코디"
        items = ["발열 내의·두꺼운 니트", "롱패딩·두꺼운 코트", "목도리·장갑·모자"]
        tip = "노출되는 피부를 줄이고 미끄럼이 적은 신발을 선택하세요."

    extras = []
    if rain_prob >= 40 or precipitation > 0 or code in range(51, 68) or code in range(80, 83):
        extras += ["우산", "방수 신발 또는 여분 양말"]
    if code in range(71, 78) or code in range(85, 87):
        extras += ["방수 부츠", "장갑"]
    if wind >= 25:
        extras += ["바람막이"]
    if t_max - t_min >= 9:
        extras += ["큰 일교차 대비 겉옷"]

    return {
        "level": level,
        "title": title,
        "items": items,
        "tip": tip,
        "extras": list(dict.fromkeys(extras)),
        "apparent": apparent,
    }


def music_profile(weather: dict):
    current = weather["current"]
    code = int(current["weather_code"])
    temp = float(current["temperature_2m"])
    wind = float(current["wind_speed_10m"] or 0)

    if code in range(95, 100):
        return "집중되는 감성 재즈", "천둥번개 치는 날 듣기 좋은 재즈 플레이리스트"
    if code in list(range(51, 68)) + list(range(80, 83)):
        return "비 오는 날 감성 음악", "비 오는 날 듣기 좋은 감성 음악 플레이리스트"
    if code in list(range(71, 78)) + list(range(85, 87)):
        return "포근한 겨울 음악", "눈 오는 날 듣기 좋은 겨울 감성 플레이리스트"
    if code in [0, 1] and temp >= 24:
        return "청량한 여름 음악", "맑은 여름날 드라이브 음악 플레이리스트"
    if code in [0, 1]:
        return "기분 좋은 산책 음악", "맑은 날 산책할 때 듣기 좋은 음악 플레이리스트"
    if code in [2, 3, 45, 48]:
        return "차분한 로파이", "흐린 날 듣기 좋은 로파이 음악 플레이리스트"
    if wind >= 25:
        return "에너지 있는 팝", "바람 부는 날 에너지 팝 플레이리스트"
    return "오늘의 편안한 음악", "편안한 하루 음악 플레이리스트"


@st.cache_data(ttl=1800, show_spinner=False)
def youtube_search(query: str, api_key: str, max_results: int = 3):
    if not api_key:
        return []

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoEmbeddable": "true",
        "safeSearch": "moderate",
        "order": "relevance",
        "maxResults": max_results,
        "key": api_key,
    }
    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()

    videos = []
    for item in response.json().get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if video_id:
            videos.append(
                {
                    "video_id": video_id,
                    "title": html.unescape(snippet.get("title", "추천 음악")),
                    "channel": html.unescape(snippet.get("channelTitle", "")),
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                }
            )
    return videos


def outfit_svg(level: str, rainy: bool = False):
    palettes = {
        "hot": ("#FFE26F", "#5CC8FF", "#FFFFFF", "#5B6B7A"),
        "warm": ("#FFB570", "#FFF4DF", "#5FA8D3", "#59636E"),
        "mild": ("#9FD8CB", "#FFF7E8", "#507DBC", "#4C5661"),
        "cool": ("#D5B3FF", "#FFF4E6", "#6F78A8", "#3E4650"),
        "cold": ("#A9C7E8", "#F4F7FB", "#667A9B", "#38414B"),
        "freezing": ("#BCD7F0", "#FFFFFF", "#5E6F88", "#303841"),
    }
    bg, top, bottom, line = palettes[level]
    umbrella = """
      <path d="M238 103 Q290 42 342 103 Q290 82 238 103" fill="#ff708d" stroke="#4b5563" stroke-width="4"/>
      <path d="M290 102 V230 Q290 252 311 252" fill="none" stroke="#4b5563" stroke-width="5" stroke-linecap="round"/>
    """ if rainy else ""

    if level == "hot":
        outer = ""
        sleeves = '<path d="M154 132 L106 175 L128 198 L174 162" fill="{top}" stroke="{line}" stroke-width="4"/><path d="M246 132 L294 175 L272 198 L226 162" fill="{top}" stroke="{line}" stroke-width="4"/>'
        lower = '<path d="M163 255 L145 365 L191 365 L201 281 L211 365 L257 365 L237 255 Z" fill="{bottom}" stroke="{line}" stroke-width="4"/>'
    elif level in ("warm", "mild"):
        outer = '<path d="M145 135 Q200 108 255 135 L244 265 H156 Z" fill="{top}" stroke="{line}" stroke-width="4"/>'
        sleeves = '<path d="M151 140 L101 229 L133 246 L170 174" fill="{top}" stroke="{line}" stroke-width="4"/><path d="M249 140 L299 229 L267 246 L230 174" fill="{top}" stroke="{line}" stroke-width="4"/>'
        lower = '<path d="M162 256 L152 390 L193 390 L201 280 L209 390 L250 390 L238 256 Z" fill="{bottom}" stroke="{line}" stroke-width="4"/>'
    else:
        outer = '<path d="M137 131 Q200 98 263 131 L254 285 H146 Z" fill="{top}" stroke="{line}" stroke-width="4"/><path d="M200 123 V285" stroke="{line}" stroke-width="4"/>'
        sleeves = '<path d="M145 140 L91 263 L127 278 L173 172" fill="{top}" stroke="{line}" stroke-width="4"/><path d="M255 140 L309 263 L273 278 L227 172" fill="{top}" stroke="{line}" stroke-width="4"/>'
        lower = '<path d="M160 278 L151 405 L194 405 L201 300 L208 405 L251 405 L240 278 Z" fill="{bottom}" stroke="{line}" stroke-width="4"/>'

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 400 450">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{bg}"/>
          <stop offset="100%" stop-color="#ffffff"/>
        </linearGradient>
      </defs>
      <rect width="400" height="450" rx="32" fill="url(#bg)"/>
      <circle cx="200" cy="78" r="43" fill="#F4C7A1" stroke="{line}" stroke-width="4"/>
      <path d="M159 76 Q162 28 202 31 Q243 34 242 80 Q225 55 184 57 Q174 72 159 76" fill="#4A3B34"/>
      {sleeves.format(top=top, line=line)}
      {outer.format(top=top, line=line)}
      {lower.format(bottom=bottom, line=line)}
      <path d="M152 405 Q173 393 195 405 V424 H146 Q142 413 152 405" fill="#ffffff" stroke="{line}" stroke-width="4"/>
      <path d="M207 405 Q230 393 252 405 Q260 414 254 424 H205 Z" fill="#ffffff" stroke="{line}" stroke-width="4"/>
      {umbrella}
      <circle cx="62" cy="65" r="22" fill="#ffffff" opacity=".7"/>
      <circle cx="330" cy="355" r="32" fill="#ffffff" opacity=".5"/>
    </svg>
    """
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("utf-8")


def safe_secret(name: str, default: str = ""):
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


st.markdown(
    """
    <div class="hero">
      <h1>🌤️ 오늘 뭐 입고 뭐 듣지?</h1>
      <div class="muted">도시의 오늘 날씨를 확인하고, 알맞은 옷차림과 유튜브 음악을 추천받아 보세요.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("📍 지역 설정")
    city = st.text_input("도시 또는 지역명", value="서울", placeholder="예: 서울, 부산, Tokyo")
    search_clicked = st.button("오늘의 추천 보기", type="primary", use_container_width=True)
    st.caption("날씨: Open-Meteo · 음악: YouTube")

if "city_results" not in st.session_state:
    st.session_state.city_results = []
if "last_city" not in st.session_state:
    st.session_state.last_city = ""

if search_clicked or (city and not st.session_state.city_results):
    try:
        with st.spinner("도시를 찾고 있습니다..."):
            st.session_state.city_results = geocode_city(city.strip())
            st.session_state.last_city = city.strip()
    except requests.RequestException as exc:
        st.error(f"도시 검색 중 네트워크 오류가 발생했습니다: {exc}")
        st.stop()

results = st.session_state.city_results
if not results:
    st.warning("검색 결과가 없습니다. 도시 이름을 조금 더 구체적으로 입력해 주세요.")
    st.stop()

labels = []
for r in results:
    region = r.get("admin1") or r.get("admin2") or ""
    country = r.get("country") or ""
    labels.append(f"{r.get('name', '')} · {region} · {country}".replace(" ·  · ", " · "))

selected_label = st.selectbox("검색된 지역", labels, index=0)
place = results[labels.index(selected_label)]

try:
    with st.spinner("오늘 날씨를 불러오는 중입니다..."):
        weather = get_weather(
            float(place["latitude"]),
            float(place["longitude"]),
            place.get("timezone", "auto"),
        )
except requests.RequestException as exc:
    st.error(f"날씨 정보를 불러오지 못했습니다: {exc}")
    st.stop()

current = weather["current"]
daily = weather["daily"]
code = int(current["weather_code"])
weather_text, weather_icon = WEATHER_CODES.get(code, ("알 수 없음", "🌡️"))
outfit = recommend_outfit(weather)
music_mood, music_query = music_profile(weather)

rainy = (
    int(daily["precipitation_probability_max"][0] or 0) >= 40
    or float(current["precipitation"] or 0) > 0
    or code in list(range(51, 68)) + list(range(80, 83))
)

place_name = place.get("name", selected_label)
country = place.get("country", "")
st.subheader(f"{weather_icon} {place_name}, {country}의 오늘 날씨")
st.caption(f"관측 기준: {current.get('time', '')} · 현지 시간대: {weather.get('timezone', '')}")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("현재 기온", f"{current['temperature_2m']:.1f}℃")
m2.metric("체감 온도", f"{current['apparent_temperature']:.1f}℃")
m3.metric("최고 / 최저", f"{daily['temperature_2m_max'][0]:.1f} / {daily['temperature_2m_min'][0]:.1f}℃")
m4.metric("강수 확률", f"{int(daily['precipitation_probability_max'][0] or 0)}%")
m5.metric("바람", f"{current['wind_speed_10m']:.1f} km/h")

st.markdown(
    f"""
    <div class="weather-card">
      <div style="font-size:1.25rem;font-weight:800;">{weather_icon} {weather_text}</div>
      <div class="muted" style="margin-top:.35rem;">
        습도 {current['relative_humidity_2m']}% · 구름 {current['cloud_cover']}% ·
        일출 {daily['sunrise'][0][-5:]} · 일몰 {daily['sunset'][0][-5:]}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
left, right = st.columns([1, 1.15], gap="large")

with left:
    st.subheader("👕 추천 옷차림")
    st.image(
        outfit_svg(outfit["level"], rainy),
        caption="현재 날씨를 바탕으로 만든 코디 일러스트",
        use_container_width=True,
    )

with right:
    st.markdown(
        f"""
        <div class="recommend-card">
          <div class="muted">체감온도 {outfit['apparent']:.1f}℃ 기준</div>
          <h3 style="margin-top:.4rem;">{outfit['title']}</h3>
          <div>
            {''.join(f'<span class="tag">{html.escape(item)}</span>' for item in outfit['items'])}
          </div>
          <p style="margin-top:1rem;"><b>코디 팁</b><br>{html.escape(outfit['tip'])}</p>
          {
            '<p><b>추가 준비물</b><br>' +
            ' · '.join(html.escape(x) for x in outfit['extras']) +
            '</p>' if outfit['extras'] else
            '<p><b>추가 준비물</b><br>특별히 필요한 준비물은 없습니다.</p>'
          }
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.subheader(f"🎵 음악 추천 · {music_mood}")
st.write(f"오늘 날씨에는 **‘{music_query}’** 검색 결과가 잘 어울립니다.")

youtube_api_key = safe_secret("YOUTUBE_API_KEY")
videos = []
youtube_error = ""

if youtube_api_key:
    try:
        videos = youtube_search(music_query, youtube_api_key, 3)
    except requests.RequestException as exc:
        youtube_error = str(exc)

if videos:
    cols = st.columns(len(videos))
    for col, video in zip(cols, videos):
        with col:
            st.video(f"https://www.youtube.com/watch?v={video['video_id']}")
            st.markdown(f"**{video['title']}**")
            st.caption(video["channel"])
else:
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(music_query)}"
    st.info(
        "YouTube API 키가 설정되지 않았거나 검색 결과를 가져오지 못해 "
        "유튜브 검색 링크를 제공합니다."
    )
    st.link_button(
        "▶️ 유튜브에서 추천 음악 찾기",
        search_url,
        type="primary",
        use_container_width=True,
    )
    if youtube_error:
        with st.expander("YouTube 검색 오류 확인"):
            st.code(youtube_error)

with st.expander("추천 기준 보기"):
    st.write(
        """
        - 체감온도 구간을 기준으로 기본 옷차림을 정합니다.
        - 강수 확률, 실제 강수량, 눈, 바람, 일교차에 따라 준비물을 추가합니다.
        - 날씨 코드와 기온에 따라 맑은 날, 비 오는 날, 눈 오는 날 등의 음악 검색어를 만듭니다.
        """
    )

st.caption(
    "날씨 데이터: Open-Meteo (CC BY 4.0) · 음악 영상 및 썸네일: YouTube"
)
