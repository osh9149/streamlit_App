import html
import random
from datetime import datetime

import isodate
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# =========================================================
# Streamlit 기본 설정
# =========================================================
st.set_page_config(
    page_title="랜덤 유튜브 보물찾기",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# 밝고 귀여운 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    /* 전체 배경 */
    .stApp {
        background:
            radial-gradient(circle at 10% 10%, #fff5c8 0, transparent 24%),
            radial-gradient(circle at 90% 20%, #dff7ff 0, transparent 26%),
            linear-gradient(135deg, #fffdf5 0%, #f7f4ff 55%, #eefcff 100%);
    }

    /* 페이지 최대 폭 */
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* 제목 영역 */
    .hero-card {
        padding: 34px 24px;
        margin-bottom: 24px;
        text-align: center;
        border: 3px solid rgba(255, 196, 61, 0.65);
        border-radius: 30px;
        background:
            linear-gradient(
                135deg,
                rgba(255, 246, 179, 0.96),
                rgba(255, 225, 244, 0.96),
                rgba(219, 244, 255, 0.96)
            );
        box-shadow: 0 12px 28px rgba(113, 88, 170, 0.14);
    }

    .hero-title {
        margin: 0;
        color: #4d3a74;
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 900;
        letter-spacing: -2px;
    }

    .hero-description {
        margin: 12px 0 0 0;
        color: #65577e;
        font-size: clamp(1rem, 2vw, 1.25rem);
        font-weight: 700;
    }

    .sparkle-line {
        margin-top: 12px;
        font-size: 1.3rem;
        letter-spacing: 8px;
    }

    /* 검색 안내 */
    .search-guide {
        margin: 6px 0 12px;
        color: #625876;
        text-align: center;
        font-size: 0.96rem;
        font-weight: 600;
    }

    /* 입력창 */
    div[data-testid="stTextInput"] input {
        min-height: 52px;
        border: 2px solid #dfd1ff;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.95);
        font-size: 1.05rem;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #8e6de7;
        box-shadow: 0 0 0 3px rgba(142, 109, 231, 0.15);
    }

    /* 버튼 공통 */
    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        min-height: 48px;
        border: 0;
        border-radius: 16px;
        background: linear-gradient(135deg, #8b72e8, #ff73ae);
        color: white;
        font-weight: 800;
        box-shadow: 0 7px 16px rgba(123, 92, 203, 0.2);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        border: 0;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(123, 92, 203, 0.28);
    }

    div.stButton > button:active,
    div[data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(0);
    }

    /* 추천 검색어 버튼 */
    .keyword-label {
        margin-top: 8px;
        margin-bottom: 8px;
        color: #574b6f;
        font-weight: 800;
    }

    /* 검색 완료 배지 */
    .result-badge {
        display: inline-block;
        padding: 8px 15px;
        margin-bottom: 14px;
        border: 2px solid #b9e9d2;
        border-radius: 999px;
        background: #edfff6;
        color: #277756;
        font-size: 0.94rem;
        font-weight: 800;
    }

    /* 보물 영상 제목 */
    .treasure-heading {
        margin: 20px 0 14px;
        text-align: center;
        color: #4b3971;
        font-size: clamp(1.7rem, 4vw, 2.5rem);
        font-weight: 900;
    }

    /* 영상 정보 */
    .video-title {
        margin: 4px 0 10px;
        color: #3f3455;
        font-size: clamp(1.4rem, 3vw, 2rem);
        font-weight: 900;
        line-height: 1.35;
    }

    .channel-name {
        display: inline-block;
        padding: 7px 12px;
        margin-bottom: 15px;
        border-radius: 999px;
        background: #f1ebff;
        color: #674caa;
        font-weight: 800;
    }

    .video-description {
        padding: 15px 17px;
        border-left: 5px solid #ffc861;
        border-radius: 6px 15px 15px 6px;
        background: #fffaf0;
        color: #625a69;
        font-size: 0.97rem;
        line-height: 1.7;
        white-space: pre-wrap;
    }

    .upload-date {
        margin-top: 12px;
        color: #7a7186;
        font-size: 0.94rem;
        font-weight: 700;
    }

    /* 정보 카드 */
    .info-card {
        height: 100%;
        min-height: 112px;
        padding: 18px 10px;
        border: 2px solid rgba(203, 190, 237, 0.6);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.88);
        text-align: center;
        box-shadow: 0 7px 16px rgba(91, 69, 145, 0.08);
    }

    .info-icon {
        margin-bottom: 5px;
        font-size: 1.55rem;
    }

    .info-label {
        color: #756985;
        font-size: 0.85rem;
        font-weight: 800;
    }

    .info-value {
        margin-top: 4px;
        color: #46395d;
        font-size: clamp(1.05rem, 2vw, 1.35rem);
        font-weight: 900;
    }

    /* 하단 안내 */
    .bottom-message {
        padding: 18px;
        margin-top: 24px;
        border: 2px dashed #d5c7f8;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.7);
        color: #665a79;
        text-align: center;
        font-weight: 700;
    }

    /* Streamlit 기본 bordered container 꾸미기 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid rgba(213, 199, 248, 0.85);
        border-radius: 26px;
        background: rgba(255, 255, 255, 0.88);
        box-shadow: 0 12px 28px rgba(91, 69, 145, 0.1);
    }

    /* 이미지 둥근 모서리 */
    div[data-testid="stImage"] img {
        border-radius: 22px;
    }

    /* 모바일 화면 */
    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }

        .hero-card {
            padding: 25px 14px;
            border-radius: 24px;
        }

        .hero-title {
            letter-spacing: -1px;
        }

        .info-card {
            min-height: 100px;
            padding: 14px 6px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 세션 상태 초기화
# 버튼을 눌러 Streamlit이 다시 실행되어도 데이터를 유지한다.
# =========================================================
DEFAULT_SESSION_VALUES = {
    "search_results": [],
    "current_video": None,
    "current_index": None,
    "search_keyword": "",
    "search_input": "",
    "searched": False,
    "last_error": "",
}

for key, default_value in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# =========================================================
# 보조 함수
# =========================================================
def safe_text(value, default="정보 없음"):
    """None이나 빈 문자열을 안전한 문자열로 바꾼다."""
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


def format_number(value):
    """숫자를 1,234,567 형태로 표시한다."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "정보 없음"


def format_upload_date(date_text):
    """YouTube 날짜를 YYYY년 MM월 DD일 형태로 변환한다."""
    if not date_text:
        return "정보 없음"

    try:
        upload_datetime = datetime.fromisoformat(
            date_text.replace("Z", "+00:00")
        )
        return upload_datetime.strftime("%Y년 %m월 %d일")
    except (ValueError, TypeError):
        return date_text[:10]


def format_duration(duration_text):
    """
    ISO 8601 형식의 영상 길이를 보기 쉬운 형태로 변환한다.
    예: PT1H2M5S → 1시간 02분 05초
    """
    if not duration_text:
        return "정보 없음"

    try:
        duration = isodate.parse_duration(duration_text)
        total_seconds = int(duration.total_seconds())

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}시간 {minutes:02d}분 {seconds:02d}초"

        if minutes > 0:
            return f"{minutes}분 {seconds:02d}초"

        return f"{seconds}초"

    except (ValueError, TypeError, AttributeError):
        return "정보 없음"


def shorten_description(description, max_length=320):
    """영상 설명이 너무 길면 일부만 표시한다."""
    description = safe_text(description, "영상 설명이 없습니다.")

    if len(description) <= max_length:
        return description

    return description[:max_length].rstrip() + "..."


def select_random_video():
    """
    저장된 검색 결과 중 하나를 무작위로 선택한다.
    현재 영상은 후보에서 제외하여 같은 영상이 연속으로 나오지 않게 한다.
    """
    results = st.session_state.search_results

    if not results:
        st.session_state.current_video = None
        st.session_state.current_index = None
        return

    # 영상이 한 개뿐이면 그 영상을 그대로 선택한다.
    if len(results) == 1:
        selected_index = 0

    else:
        candidate_indices = [
            index
            for index in range(len(results))
            if index != st.session_state.current_index
        ]

        selected_index = random.choice(candidate_indices)

    st.session_state.current_index = selected_index
    st.session_state.current_video = results[selected_index]


def set_recommended_keyword(keyword):
    """추천 검색어 버튼을 누르면 검색창에 해당 단어를 입력한다."""
    st.session_state.search_input = keyword


def reset_search():
    """현재 검색 결과를 지우고 새로운 검색을 준비한다."""
    st.session_state.search_results = []
    st.session_state.current_video = None
    st.session_state.current_index = None
    st.session_state.search_keyword = ""
    st.session_state.search_input = ""
    st.session_state.searched = False
    st.session_state.last_error = ""


def get_youtube_client(api_key):
    """YouTube Data API 클라이언트를 생성한다."""
    return build(
        "youtube",
        "v3",
        developerKey=api_key,
        cache_discovery=False,
    )


def search_youtube_videos(youtube, keyword):
    """
    YouTube에서 최대 50개의 일반 동영상을 검색한다.

    1. search().list()로 영상 ID 50개를 가져온다.
    2. videos().list()로 50개 영상의 상세정보를 한꺼번에 가져온다.
    """
    search_response = (
        youtube.search()
        .list(
            part="snippet",
            q=keyword,
            type="video",          # 채널과 재생목록 제외
            maxResults=50,
            safeSearch="moderate", # 학생용 앱이므로 제한 검색 사용
        )
        .execute()
    )

    video_ids = [
        item.get("id", {}).get("videoId")
        for item in search_response.get("items", [])
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return []

    # 영상 ID를 쉼표로 묶어 상세정보를 한 번에 요청한다.
    details_response = (
        youtube.videos()
        .list(
            part="snippet,statistics,contentDetails,status",
            id=",".join(video_ids),
        )
        .execute()
    )

    videos = []

    for item in details_response.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        status = item.get("status", {})

        video_id = item.get("id")

        # 비공개 영상이나 재생할 수 없는 항목은 결과에서 제외한다.
        if not video_id:
            continue

        if status.get("privacyStatus") != "public":
            continue

        if not status.get("embeddable", True):
            continue

        thumbnails = snippet.get("thumbnails", {})

        # 가능한 한 큰 썸네일을 선택한다.
        thumbnail_url = (
            thumbnails.get("maxres", {}).get("url")
            or thumbnails.get("standard", {}).get("url")
            or thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or ""
        )

        videos.append(
            {
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "title": safe_text(snippet.get("title"), "제목 없음"),
                "channel": safe_text(
                    snippet.get("channelTitle"),
                    "채널 정보 없음",
                ),
                "description": safe_text(
                    snippet.get("description"),
                    "영상 설명이 없습니다.",
                ),
                "published_at": snippet.get("publishedAt", ""),
                "thumbnail_url": thumbnail_url,
                "view_count": statistics.get("viewCount"),
                "like_count": statistics.get("likeCount"),
                "comment_count": statistics.get("commentCount"),
                "duration": content_details.get("duration"),
            }
        )

    # search API가 반환한 영상 순서에 최대한 맞춘다.
    video_order = {
        video_id: index for index, video_id in enumerate(video_ids)
    }

    videos.sort(
        key=lambda video: video_order.get(
            video["video_id"],
            len(video_order),
        )
    )

    return videos


def get_api_error_message(error):
    """YouTube API 오류를 학생도 이해하기 쉬운 한글로 변환한다."""
    status_code = getattr(error.resp, "status", None)

    error_text = str(error).lower()

    if status_code == 400:
        return (
            "YouTube API 요청 형식에 문제가 있습니다. "
            "검색어를 바꿔 다시 시도해 주세요."
        )

    if status_code == 403:
        if "quota" in error_text:
            return (
                "오늘 사용할 수 있는 YouTube API 사용량을 모두 사용했습니다. "
                "잠시 후 또는 다음 날 다시 시도해 주세요."
            )

        if "key" in error_text or "accessnotconfigured" in error_text:
            return (
                "YouTube API 키가 올바르지 않거나 "
                "YouTube Data API v3가 활성화되지 않았습니다. "
                "Google Cloud Console의 API 설정을 확인해 주세요."
            )

        return (
            "YouTube API에 접근할 수 없습니다. "
            "API 키와 API 사용 설정을 확인해 주세요."
        )

    if status_code == 404:
        return "요청한 영상 정보를 찾을 수 없습니다."

    return (
        "YouTube 정보를 불러오는 중 문제가 발생했습니다. "
        "잠시 후 다시 시도해 주세요."
    )


def display_stat_card(icon, label, value):
    """조회수, 좋아요 수 등의 작은 정보 카드를 표시한다."""
    safe_icon = html.escape(str(icon))
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-icon">{safe_icon}</div>
            <div class="info-label">{safe_label}</div>
            <div class="info-value">{safe_value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 제목
# =========================================================
st.markdown(
    """
    <div class="hero-card">
        <h1 class="hero-title">🎁 랜덤 유튜브 보물찾기</h1>
        <p class="hero-description">
            검색어를 입력하고 나만의 보물 영상을 찾아보세요!
        </p>
        <div class="sparkle-line">✨ ⭐ 🎲 ⭐ ✨</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API 키 불러오기
# =========================================================
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]

except (KeyError, FileNotFoundError):
    st.error("🔑 YouTube API 키가 등록되지 않았습니다.")

    st.markdown(
        """
        Streamlit Cloud의 앱 설정에서 **Secrets** 메뉴를 열고  
        다음 내용을 입력한 뒤 저장해 주세요.

        ```toml
        YOUTUBE_API_KEY = "발급받은_API_키"
        ```

        로컬 컴퓨터에서 실행할 때는 프로젝트 폴더 안에
        `.streamlit/secrets.toml` 파일을 만들고 같은 내용을 저장하면 됩니다.
        """
    )

    st.stop()


# =========================================================
# 검색 영역
# =========================================================
if not st.session_state.searched:
    st.markdown(
        """
        <div class="search-guide">
            게임, 여행, 코딩, 음악, 과학, 요리, 동물처럼
            관심 있는 단어를 입력해 보세요! 🔍
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 추천 검색어 버튼
    st.markdown(
        '<div class="keyword-label">⭐ 추천 검색어</div>',
        unsafe_allow_html=True,
    )

    recommended_keywords = [
        ("🎮 게임", "게임"),
        ("✈️ 여행", "여행"),
        ("💻 코딩", "코딩"),
        ("🎵 음악", "음악"),
        ("🔬 과학", "과학"),
        ("🍳 요리", "요리"),
        ("🐶 동물", "동물"),
    ]

    keyword_columns = st.columns(4)

    for index, (button_label, keyword) in enumerate(
        recommended_keywords
    ):
        with keyword_columns[index % 4]:
            st.button(
                button_label,
                key=f"recommended_keyword_{index}",
                use_container_width=True,
                on_click=set_recommended_keyword,
                args=(keyword,),
            )

    # 검색창과 검색 버튼을 하나의 폼으로 구성한다.
    with st.form("youtube_search_form"):
        keyword = st.text_input(
            "검색어",
            key="search_input",
            placeholder="예: 재미있는 과학 실험",
            label_visibility="collapsed",
        )

        search_submitted = st.form_submit_button(
            "🔍 보물 영상 검색하기",
            use_container_width=True,
        )

    if search_submitted:
        cleaned_keyword = keyword.strip()

        if not cleaned_keyword:
            st.warning("검색어를 먼저 입력해 주세요. 😊")

        else:
            try:
                with st.spinner(
                    "🧭 유튜브 보물 지도를 탐색하고 있어요..."
                ):
                    youtube = get_youtube_client(API_KEY)

                    results = search_youtube_videos(
                        youtube,
                        cleaned_keyword,
                    )

                if not results:
                    st.session_state.search_results = []
                    st.session_state.current_video = None
                    st.session_state.current_index = None
                    st.session_state.search_keyword = cleaned_keyword
                    st.session_state.searched = False

                    st.warning(
                        "검색된 영상이 없습니다. "
                        "조금 더 간단하거나 다른 검색어를 입력해 주세요."
                    )

                else:
                    st.session_state.search_results = results
                    st.session_state.search_keyword = cleaned_keyword
                    st.session_state.searched = True
                    st.session_state.current_video = None
                    st.session_state.current_index = None
                    st.session_state.last_error = ""

                    select_random_video()
                    st.rerun()

            except HttpError as error:
                st.error(f"⚠️ {get_api_error_message(error)}")

            except Exception:
                st.error(
                    "⚠️ 예상하지 못한 오류가 발생했습니다. "
                    "인터넷 연결과 API 설정을 확인한 뒤 다시 시도해 주세요."
                )


# =========================================================
# 추천 결과 화면
# =========================================================
if st.session_state.searched and st.session_state.current_video:
    current_video = st.session_state.current_video
    result_count = len(st.session_state.search_results)

    safe_keyword = html.escape(st.session_state.search_keyword)
    safe_title = html.escape(current_video["title"])
    safe_channel = html.escape(current_video["channel"])
    safe_description = html.escape(
        shorten_description(current_video["description"])
    )

    upload_date = format_upload_date(current_video["published_at"])

    view_count = format_number(current_video["view_count"])
    like_count = format_number(current_video["like_count"])
    comment_count = format_number(current_video["comment_count"])
    duration = format_duration(current_video["duration"])

    st.markdown(
        f"""
        <div class="result-badge">
            🗺️ '{safe_keyword}' 검색 결과 {result_count}개의 보물을 찾았어요!
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="treasure-heading">
            🏆 오늘의 보물 영상 ✨
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 큰 둥근 카드 안에 추천 영상 정보를 표시한다.
    with st.container(border=True):
        if current_video["thumbnail_url"]:
            st.image(
                current_video["thumbnail_url"],
                use_container_width=True,
            )

        st.markdown(
            f"""
            <div class="video-title">{safe_title}</div>
            <div class="channel-name">📺 {safe_channel}</div>
            <div class="video-description">{safe_description}</div>
            <div class="upload-date">
                📅 업로드 날짜: {html.escape(upload_date)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 🌟 보물 영상 정보")

        stat_columns = st.columns(4)

        with stat_columns[0]:
            display_stat_card("👀", "조회수", view_count)

        with stat_columns[1]:
            display_stat_card("👍", "좋아요", like_count)

        with stat_columns[2]:
            display_stat_card("💬", "댓글", comment_count)

        with stat_columns[3]:
            display_stat_card("⏱️", "영상 길이", duration)

        st.markdown("#### ▶️ 보물 영상 재생")

        # YouTube 영상 재생
        st.video(current_video["video_url"])

    st.write("")

    # 다른 영상 또는 새로운 검색 버튼
    action_column_1, action_column_2 = st.columns(2)

    with action_column_1:
        if st.button(
            "🎲 다른 보물 찾기",
            use_container_width=True,
            type="primary",
        ):
            # API를 다시 호출하지 않고 저장된 결과에서 선택한다.
            select_random_video()
            st.rerun()

    with action_column_2:
        if st.button(
            "🔍 새로운 검색어로 찾기",
            use_container_width=True,
        ):
            reset_search()
            st.rerun()

    st.markdown(
        """
        <div class="bottom-message">
            💎 마음에 들지 않으면 주사위를 다시 굴려 보세요!<br>
            이미 찾은 영상 목록 안에서 새로운 보물을 골라 드립니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
