import html
import random
from datetime import date, datetime, timedelta
from urllib.parse import unquote

import pandas as pd
import plotly.express as px
import pydeck as pdk
import requests
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="대한민국 축제 탐험대",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=1200&q=80"

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

MONTH_NAMES = {
    1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월",
    7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"
}


# =========================================================
# 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(255, 220, 150, .22), transparent 25%),
            radial-gradient(circle at 90% 5%, rgba(255, 150, 180, .18), transparent 22%),
            linear-gradient(180deg, #fffaf2 0%, #fff 42%);
    }
    .hero {
        padding: 34px 30px;
        border-radius: 26px;
        background: linear-gradient(135deg, #ff6b6b 0%, #ff9f43 52%, #ffd166 100%);
        color: white;
        box-shadow: 0 15px 36px rgba(240, 100, 70, .22);
        margin-bottom: 18px;
    }
    .hero h1 {
        font-size: 2.35rem;
        margin: 0 0 8px 0;
        line-height: 1.2;
    }
    .hero p {
        margin: 0;
        font-size: 1.05rem;
        opacity: .96;
    }
    .festival-card {
        height: 100%;
        border: 1px solid #f0e6d8;
        background: white;
        border-radius: 22px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(70, 50, 30, .09);
        margin-bottom: 18px;
    }
    .festival-image {
        width: 100%;
        height: 220px;
        object-fit: cover;
        display: block;
    }
    .festival-body {
        padding: 18px 18px 20px 18px;
    }
    .festival-title {
        font-size: 1.18rem;
        font-weight: 800;
        color: #342b25;
        min-height: 58px;
        margin-bottom: 8px;
    }
    .festival-meta {
        color: #6c625b;
        font-size: .93rem;
        line-height: 1.65;
    }
    .status-open, .status-soon, .status-end {
        display: inline-block;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: .78rem;
        font-weight: 800;
        margin-bottom: 9px;
    }
    .status-open { background: #e6fff1; color: #087a43; }
    .status-soon { background: #fff5d9; color: #9b6200; }
    .status-end { background: #f1f1f1; color: #666; }
    .random-box {
        border: 2px dashed #ff9f43;
        border-radius: 24px;
        background: #fff9ef;
        padding: 20px;
    }
    .small-note {
        font-size: .84rem;
        color: #756b65;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.86);
        border: 1px solid #f1e7dc;
        border-radius: 18px;
        padding: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API 및 데이터 처리 함수
# =========================================================
def get_api_key() -> str:
    """Streamlit Secrets에서 API 키를 불러온다."""
    try:
        key = st.secrets["TOUR_API_KEY"]
    except Exception:
        return ""
    # 인코딩 인증키를 넣은 경우 한 번 풀어서 requests가 안전하게 다시 인코딩하도록 한다.
    return unquote(str(key).strip())


def normalize_items(data) -> list:
    """TourAPI 응답의 item이 1개 또는 여러 개여도 항상 리스트로 반환한다."""
    try:
        items = data["response"]["body"]["items"]["item"]
    except (KeyError, TypeError):
        return []

    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []


@st.cache_data(ttl=1800, show_spinner=False)
def request_tour_api(endpoint: str, api_key: str, params: dict) -> tuple[list, str]:
    """TourAPI를 호출하고 (목록, 오류 메시지)를 반환한다."""
    query = {
        "serviceKey": api_key,
        "MobileOS": "ETC",
        "MobileApp": "FestivalExplorer",
        "_type": "json",
        **params,
    }

    try:
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=query,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return [], f"API 연결 중 오류가 발생했습니다: {exc}"

    try:
        data = response.json()
    except ValueError:
        preview = response.text[:250]
        return [], f"JSON 응답을 받지 못했습니다. 인증키 또는 API 주소를 확인하세요. 응답: {preview}"

    header = data.get("response", {}).get("header", {})
    result_code = str(header.get("resultCode", ""))
    if result_code and result_code != "0000":
        return [], f"TourAPI 오류: {header.get('resultMsg', '알 수 없는 오류')} ({result_code})"

    return normalize_items(data), ""


@st.cache_data(ttl=1800, show_spinner=False)
def load_festivals(
    api_key: str,
    start_date: str,
    end_date: str,
    area_code: str,
    rows: int,
) -> tuple[pd.DataFrame, str]:
    params = {
        "eventStartDate": start_date,
        "eventEndDate": end_date,
        "arrange": "Q",
        "numOfRows": rows,
        "pageNo": 1,
    }
    if area_code:
        params["areaCode"] = area_code

    items, error = request_tour_api("searchFestival2", api_key, params)
    if error:
        return pd.DataFrame(), error
    if not items:
        return pd.DataFrame(), ""

    df = pd.DataFrame(items)

    wanted = [
        "contentid", "title", "addr1", "addr2", "eventstartdate", "eventenddate",
        "firstimage", "firstimage2", "mapx", "mapy", "tel", "areacode", "sigungucode",
    ]
    for col in wanted:
        if col not in df.columns:
            df[col] = ""

    df = df[wanted].copy()
    df["title"] = df["title"].fillna("").astype(str)
    df["addr1"] = df["addr1"].fillna("").astype(str)
    df["addr2"] = df["addr2"].fillna("").astype(str)
    df["tel"] = df["tel"].fillna("").astype(str)
    df["firstimage"] = df["firstimage"].fillna("").astype(str)
    df["firstimage2"] = df["firstimage2"].fillna("").astype(str)
    df["image"] = df["firstimage"].where(df["firstimage"] != "", df["firstimage2"])
    df["image"] = df["image"].where(df["image"] != "", DEFAULT_IMAGE)

    df["start_dt"] = pd.to_datetime(df["eventstartdate"], format="%Y%m%d", errors="coerce")
    df["end_dt"] = pd.to_datetime(df["eventenddate"], format="%Y%m%d", errors="coerce")
    df["latitude"] = pd.to_numeric(df["mapy"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["mapx"], errors="coerce")
    df["month"] = df["start_dt"].dt.month
    df["period"] = (
        df["start_dt"].dt.strftime("%Y.%m.%d").fillna("날짜 미정")
        + " ~ "
        + df["end_dt"].dt.strftime("%Y.%m.%d").fillna("날짜 미정")
    )

    today = pd.Timestamp(date.today())
    df["status"] = "종료"
    df.loc[df["start_dt"] > today, "status"] = "개막 예정"
    df.loc[(df["start_dt"] <= today) & (df["end_dt"] >= today), "status"] = "진행 중"

    return df.sort_values(["start_dt", "title"], na_position="last").reset_index(drop=True), ""


def festival_status_html(status: str) -> str:
    if status == "진행 중":
        return '<span class="status-open">🟢 진행 중</span>'
    if status == "개막 예정":
        return '<span class="status-soon">🟡 개막 예정</span>'
    return '<span class="status-end">⚪ 종료</span>'


def festival_card(row: pd.Series) -> str:
    title = html.escape(str(row.get("title", "축제명 없음")))
    address = html.escape((str(row.get("addr1", "")) + " " + str(row.get("addr2", ""))).strip())
    period = html.escape(str(row.get("period", "날짜 정보 없음")))
    image = html.escape(str(row.get("image", DEFAULT_IMAGE)), quote=True)
    tel = html.escape(str(row.get("tel", "")).strip())
    tel_line = f"<div>☎️ {tel}</div>" if tel else ""

    return f"""
    <div class="festival-card">
        <img class="festival-image" src="{image}" alt="{title}">
        <div class="festival-body">
            {festival_status_html(str(row.get("status", "")))}
            <div class="festival-title">🎉 {title}</div>
            <div class="festival-meta">
                <div>📅 {period}</div>
                <div>📍 {address or "주소 정보 없음"}</div>
                {tel_line}
            </div>
        </div>
    </div>
    """


def keyword_filter(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    keyword = keyword.strip()
    if not keyword:
        return df
    mask = (
        df["title"].str.contains(keyword, case=False, na=False)
        | df["addr1"].str.contains(keyword, case=False, na=False)
    )
    return df[mask]


# =========================================================
# 제목
# =========================================================
st.markdown(
    """
    <div class="hero">
        <h1>🎪 대한민국 축제 탐험대</h1>
        <p>한국관광공사 TourAPI로 전국 축제를 검색하고, 지도에서 보고, 오늘의 축제를 뽑아보세요!</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API 키 확인
# =========================================================
api_key = get_api_key()

if not api_key:
    st.error("API 키가 설정되지 않았습니다.")
    st.code('TOUR_API_KEY = "여기에_한국관광공사_API_인증키"', language="toml")
    st.info(
        "Streamlit Cloud 앱의 Settings → Secrets에 위 내용을 넣으세요. "
        "공개 GitHub 저장소의 app.py나 일반 파일에는 인증키를 직접 넣지 않는 것이 안전합니다."
    )
    st.stop()


# =========================================================
# 검색 조건
# =========================================================
today = date.today()
default_end = today + timedelta(days=180)

with st.sidebar:
    st.header("🔎 축제 찾기")
    selected_area = st.selectbox("지역", list(AREA_CODES.keys()))
    start_date = st.date_input("검색 시작일", value=today)
    end_date = st.date_input("검색 종료일", value=default_end)
    rows = st.slider("가져올 축제 수", 20, 300, 100, 20)
    keyword = st.text_input("축제명·주소 검색", placeholder="예: 불꽃, 벚꽃, 서울")
    status_filter = st.multiselect(
        "진행 상태",
        ["진행 중", "개막 예정", "종료"],
        default=["진행 중", "개막 예정"],
    )
    st.caption("검색 기간이 너무 길면 결과 수 제한 때문에 일부 축제가 보이지 않을 수 있습니다.")

if start_date > end_date:
    st.warning("검색 시작일은 종료일보다 늦을 수 없습니다.")
    st.stop()

with st.spinner("전국의 축제 정보를 불러오는 중입니다..."):
    festivals, error = load_festivals(
        api_key,
        start_date.strftime("%Y%m%d"),
        end_date.strftime("%Y%m%d"),
        AREA_CODES[selected_area],
        rows,
    )

if error:
    st.error(error)
    st.stop()

if festivals.empty:
    st.warning("선택한 조건에 해당하는 축제 정보가 없습니다. 날짜나 지역을 바꿔보세요.")
    st.stop()

filtered = keyword_filter(festivals, keyword)
if status_filter:
    filtered = filtered[filtered["status"].isin(status_filter)]
else:
    filtered = filtered.iloc[0:0]

if filtered.empty:
    st.warning("세부 검색 조건에 맞는 축제가 없습니다.")
    st.stop()


# =========================================================
# 요약 지표
# =========================================================
ongoing_count = int((filtered["status"] == "진행 중").sum())
upcoming_count = int((filtered["status"] == "개막 예정").sum())
map_count = int(filtered[["latitude", "longitude"]].dropna().shape[0])

m1, m2, m3, m4 = st.columns(4)
m1.metric("검색된 축제", f"{len(filtered)}개")
m2.metric("지금 진행 중", f"{ongoing_count}개")
m3.metric("개막 예정", f"{upcoming_count}개")
m4.metric("지도 표시 가능", f"{map_count}개")


# =========================================================
# 탭 구성
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["🎉 축제 카드", "🗺️ 축제 지도", "🎲 랜덤 축제", "📊 축제 분석"]
)


# ---------------------------------------------------------
# 탭 1: 카드
# ---------------------------------------------------------
with tab1:
    st.subheader("축제 한눈에 보기")
    sort_option = st.radio(
        "정렬",
        ["개막일 빠른 순", "개막일 늦은 순", "이름 순"],
        horizontal=True,
    )

    card_df = filtered.copy()
    if sort_option == "개막일 늦은 순":
        card_df = card_df.sort_values("start_dt", ascending=False, na_position="last")
    elif sort_option == "이름 순":
        card_df = card_df.sort_values("title")
    else:
        card_df = card_df.sort_values("start_dt", na_position="last")

    display_count = st.slider("화면에 표시할 카드 수", 6, min(60, len(card_df)), min(12, len(card_df)), 3)

    for start in range(0, display_count, 3):
        cols = st.columns(3)
        rows_slice = card_df.iloc[start:start + 3]
        for col, (_, row) in zip(cols, rows_slice.iterrows()):
            with col:
                st.markdown(festival_card(row), unsafe_allow_html=True)
                query = requests.utils.quote(str(row["title"]))
                st.link_button(
                    "🔍 자세히 검색",
                    f"https://search.naver.com/search.naver?query={query}",
                    use_container_width=True,
                )


# ---------------------------------------------------------
# 탭 2: 지도
# ---------------------------------------------------------
with tab2:
    st.subheader("전국 축제 지도")
    map_df = filtered.dropna(subset=["latitude", "longitude"]).copy()

    if map_df.empty:
        st.info("현재 검색 결과에는 위치 좌표가 없습니다.")
    else:
        map_df["address"] = (map_df["addr1"] + " " + map_df["addr2"]).str.strip()
        map_df["tooltip_title"] = map_df["title"].str.replace('"', "'", regex=False)

        view_state = pdk.ViewState(
            latitude=float(map_df["latitude"].mean()),
            longitude=float(map_df["longitude"].mean()),
            zoom=6.3 if selected_area == "전국" else 9,
            pitch=0,
        )

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[longitude, latitude]",
            get_radius=350,
            radius_min_pixels=6,
            radius_max_pixels=18,
            get_fill_color=[255, 92, 92, 190],
            get_line_color=[255, 255, 255],
            line_width_min_pixels=2,
            pickable=True,
        )

        tooltip = {
            "html": "<b>🎪 {title}</b><br/>📅 {period}<br/>📍 {address}<br/>상태: {status}",
            "style": {
                "backgroundColor": "#3b302a",
                "color": "white",
                "fontSize": "13px",
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
        st.caption("지도 위 점에 마우스를 올리면 축제명, 기간, 주소가 표시됩니다.")


# ---------------------------------------------------------
# 탭 3: 랜덤 추천
# ---------------------------------------------------------
with tab3:
    st.subheader("오늘 어디로 떠날까요?")
    st.write("결정을 못 하겠다면 버튼 한 번으로 오늘의 축제를 뽑아보세요.")

    c1, c2 = st.columns([1, 2])
    with c1:
        mood = st.selectbox(
            "오늘의 여행 취향",
            ["아무거나 좋아요", "사진 찍기 좋은 곳", "가족과 함께", "먹거리 탐험", "야간 분위기"],
        )
        spin = st.button("🎰 축제 룰렛 돌리기", type="primary", use_container_width=True)

    # API에 축제 테마 분류가 충분하지 않으므로 제목 키워드를 재미 요소로 활용한다.
    mood_keywords = {
        "사진 찍기 좋은 곳": ["꽃", "빛", "불꽃", "문화", "예술", "정원", "야경"],
        "가족과 함께": ["가족", "어린이", "체험", "전통", "농촌", "과학"],
        "먹거리 탐험": ["음식", "먹거리", "한우", "수산", "커피", "차", "맥주", "과일", "축산"],
        "야간 분위기": ["밤", "야간", "빛", "불빛", "불꽃", "별빛"],
    }

    pool = filtered.copy()
    if mood != "아무거나 좋아요":
        pattern = "|".join(mood_keywords[mood])
        themed = pool[pool["title"].str.contains(pattern, case=False, na=False)]
        if not themed.empty:
            pool = themed

    if "random_contentid" not in st.session_state:
        st.session_state.random_contentid = None

    if spin or st.session_state.random_contentid is None:
        chosen = pool.sample(1).iloc[0]
        st.session_state.random_contentid = chosen["contentid"]

    selected_rows = pool[pool["contentid"] == st.session_state.random_contentid]
    if selected_rows.empty:
        chosen = pool.sample(1).iloc[0]
        st.session_state.random_contentid = chosen["contentid"]
    else:
        chosen = selected_rows.iloc[0]

    with c2:
        st.markdown('<div class="random-box">', unsafe_allow_html=True)
        st.image(chosen["image"], use_container_width=True)
        st.markdown(f"### 🎊 {chosen['title']}")
        st.write(f"📅 **기간:** {chosen['period']}")
        st.write(f"📍 **장소:** {(chosen['addr1'] + ' ' + chosen['addr2']).strip() or '주소 정보 없음'}")
        st.success(f"오늘의 추천 이유: **{mood}** 취향으로 뽑은 행운의 축제입니다!")
        nav_query = requests.utils.quote(f"{chosen['title']} {chosen['addr1']}")
        st.link_button(
            "🧭 길찾기·정보 검색",
            f"https://map.naver.com/p/search/{nav_query}",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 탭 4: 분석
# ---------------------------------------------------------
with tab4:
    st.subheader("축제 데이터 분석")
    analysis_df = filtered.dropna(subset=["month"]).copy()

    left, right = st.columns(2)

    with left:
        month_counts = (
            analysis_df.groupby("month")
            .size()
            .reindex(range(1, 13), fill_value=0)
            .reset_index(name="축제 수")
        )
        month_counts["월"] = month_counts["month"].map(MONTH_NAMES)
        fig_month = px.bar(
            month_counts,
            x="월",
            y="축제 수",
            title="월별 축제 개막 수",
            text_auto=True,
        )
        fig_month.update_layout(showlegend=False)
        st.plotly_chart(fig_month, use_container_width=True)

    with right:
        status_counts = filtered["status"].value_counts().reset_index()
        status_counts.columns = ["상태", "축제 수"]
        fig_status = px.pie(
            status_counts,
            names="상태",
            values="축제 수",
            title="진행 상태 비율",
            hole=0.48,
        )
        st.plotly_chart(fig_status, use_container_width=True)

    st.subheader("📅 축제 일정표")
    schedule = filtered[["title", "period", "addr1", "status"]].rename(
        columns={
            "title": "축제명",
            "period": "기간",
            "addr1": "주소",
            "status": "상태",
        }
    )
    st.dataframe(schedule, use_container_width=True, hide_index=True)


# =========================================================
# 하단 안내
# =========================================================
st.divider()
st.caption(
    "축제 정보와 이미지는 한국관광공사 TourAPI에서 제공됩니다. "
    "행사 일정은 현지 사정에 따라 변경될 수 있으므로 방문 전 공식 안내를 확인하세요."
)

