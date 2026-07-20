import os
import re
from collections import Counter
from datetime import timezone
from urllib.parse import parse_qs, urlparse

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from wordcloud import WordCloud


st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="📺",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    .main-title {
        font-size: 2.25rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #666;
        margin-bottom: 1.2rem;
    }
    div[data-testid="stMetric"] {
        background: #f7f8fb;
        border: 1px solid #e8eaf0;
        padding: 14px;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
DEFAULT_FONT_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/"
    "NotoSansKR%5Bwght%5D.ttf"
)

STOPWORDS = {
    "정말", "진짜", "너무", "영상", "댓글", "유튜브", "유투브", "이거", "저거",
    "그냥", "그리고", "하지만", "그래서", "때문", "하는", "하면", "해서", "있다",
    "있는", "없는", "같다", "같은", "것도", "것은", "수가", "저는", "제가", "우리",
    "여기", "오늘", "이번", "많이", "아주", "완전", "ㅋㅋ", "ㅎㅎ", "ㅠㅠ",
}


def extract_video_id(url_or_id: str) -> str | None:
    """YouTube URL 또는 11자리 영상 ID에서 videoId를 추출합니다."""
    value = url_or_id.strip()

    if re.fullmatch(r"[\w-]{11}", value):
        return value

    try:
        parsed = urlparse(value)
        host = parsed.netloc.lower().replace("www.", "")

        if host == "youtu.be":
            candidate = parsed.path.strip("/").split("/")[0]
        elif host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
            if parsed.path == "/watch":
                candidate = parse_qs(parsed.query).get("v", [""])[0]
            elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
                candidate = parsed.path.strip("/").split("/")[1]
            else:
                candidate = ""
        else:
            candidate = ""

        return candidate if re.fullmatch(r"[\w-]{11}", candidate) else None
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def download_korean_font(font_url: str) -> str:
    """워드클라우드용 한글 폰트를 내려받아 로컬 경로를 반환합니다."""
    local_candidates = [
        "fonts/NanumGothic.ttf",
        "fonts/NotoSansKR-Regular.ttf",
        "NanumGothic.ttf",
        "NotoSansKR-Regular.ttf",
    ]

    for path in local_candidates:
        if os.path.exists(path):
            return path

    font_dir = "fonts"
    os.makedirs(font_dir, exist_ok=True)
    font_path = os.path.join(font_dir, "NotoSansKR.ttf")

    if not os.path.exists(font_path):
        response = requests.get(font_url, timeout=30)
        response.raise_for_status()
        with open(font_path, "wb") as file:
            file.write(response.content)

    return font_path


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_comments(api_key: str, video_id: str, max_comments: int) -> pd.DataFrame:
    """YouTube Data API에서 공개된 최상위 댓글을 수집합니다."""
    rows = []
    next_page_token = None

    while len(rows) < max_comments:
        page_size = min(100, max_comments - len(rows))
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": api_key,
            "maxResults": page_size,
            "order": "time",
            "textFormat": "plainText",
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(YOUTUBE_API_URL, params=params, timeout=30)

        if response.status_code != 200:
            try:
                error_data = response.json()
                message = error_data["error"]["message"]
            except Exception:
                message = response.text or "알 수 없는 API 오류"
            raise RuntimeError(message)

        data = response.json()

        for item in data.get("items", []):
            thread_snippet = item.get("snippet", {})
            comment = thread_snippet.get("topLevelComment", {}).get("snippet", {})

            rows.append(
                {
                    "작성자": comment.get("authorDisplayName", ""),
                    "댓글": comment.get("textDisplay", ""),
                    "좋아요": int(comment.get("likeCount", 0)),
                    "답글수": int(thread_snippet.get("totalReplyCount", 0)),
                    "작성시각": comment.get("publishedAt", ""),
                    "수정시각": comment.get("updatedAt", ""),
                }
            )

            if len(rows) >= max_comments:
                break

        next_page_token = data.get("nextPageToken")
        if not next_page_token or not data.get("items"):
            break

    df = pd.DataFrame(rows)

    if not df.empty:
        df["작성시각"] = pd.to_datetime(df["작성시각"], utc=True, errors="coerce")
        df["수정시각"] = pd.to_datetime(df["수정시각"], utc=True, errors="coerce")
        df["반응점수"] = df["좋아요"] + (df["답글수"] * 2)

    return df


def tokenize_korean(text_series: pd.Series, extra_stopwords: set[str]) -> Counter:
    """설치가 무거운 형태소 분석기 없이 한글 중심 키워드를 추출합니다."""
    text = " ".join(text_series.fillna("").astype(str))
    words = re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}", text.lower())

    stopwords = STOPWORDS | {word.strip().lower() for word in extra_stopwords if word.strip()}
    filtered = [
        word for word in words
        if word not in stopwords and not word.isdigit()
    ]
    return Counter(filtered)


def render_wordcloud(frequencies: Counter, font_path: str):
    wc = WordCloud(
        font_path=font_path,
        width=1400,
        height=700,
        background_color="white",
        max_words=150,
        collocations=False,
        prefer_horizontal=0.9,
        random_state=42,
    ).generate_from_frequencies(frequencies)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    plt.tight_layout(pad=0)
    return fig


st.markdown('<div class="main-title">📺 YouTube 댓글 분석기</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">영상 댓글의 작성 추이, 반응도, 핵심 키워드를 한 번에 분석합니다.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ 분석 설정")

    secret_key = st.secrets.get("YOUTUBE_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input(
        "YouTube Data API 키",
        value=secret_key,
        type="password",
        help="앱에 직접 입력하거나 Streamlit Secrets의 YOUTUBE_API_KEY에 저장할 수 있습니다.",
    )

    max_comments = st.slider(
        "가져올 댓글 수",
        min_value=10,
        max_value=1000,
        value=200,
        step=10,
    )

    time_unit = st.selectbox(
        "댓글 작성 추이 단위",
        ["시간별", "일별", "요일별"],
        index=1,
    )

    extra_stopwords_text = st.text_area(
        "추가 제외 단어",
        placeholder="쉼표로 구분: 채널명, 출연자명, 반복 단어",
    )
    extra_stopwords = {
        word.strip() for word in extra_stopwords_text.split(",") if word.strip()
    }

    font_url = st.text_input(
        "한글 폰트 URL",
        value=DEFAULT_FONT_URL,
        help="GitHub의 raw TTF/OTF 주소로 바꿀 수 있습니다.",
    )

video_url = st.text_input(
    "YouTube 영상 링크",
    placeholder="https://www.youtube.com/watch?v=...",
)

video_id = extract_video_id(video_url) if video_url else None

if video_url and not video_id:
    st.error("올바른 YouTube 영상 링크 또는 11자리 영상 ID를 입력해 주세요.")

if video_id:
    st.video(f"https://www.youtube.com/watch?v={video_id}")

analyze = st.button(
    "🔍 댓글 분석 시작",
    type="primary",
    use_container_width=True,
)

if analyze:
    if not api_key:
        st.error("YouTube Data API 키를 입력해 주세요.")
        st.stop()

    if not video_id:
        st.error("올바른 YouTube 영상 링크를 입력해 주세요.")
        st.stop()

    try:
        with st.spinner("댓글을 불러오고 분석하고 있습니다..."):
            df = fetch_comments(api_key, video_id, max_comments)

        if df.empty:
            st.warning(
                "가져올 수 있는 공개 댓글이 없습니다. 댓글이 비활성화되었거나 공개 댓글이 없을 수 있습니다."
            )
            st.stop()

        st.success(f"댓글 {len(df):,}개를 불러왔습니다.")

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("수집 댓글", f"{len(df):,}개")
        metric2.metric("총 좋아요", f"{df['좋아요'].sum():,}개")
        metric3.metric("총 답글", f"{df['답글수'].sum():,}개")
        metric4.metric("평균 반응점수", f"{df['반응점수'].mean():.1f}")

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📈 작성 추이", "💬 댓글 반응도", "☁️ 워드클라우드", "📋 원본 댓글"]
        )

        with tab1:
            trend_df = df.dropna(subset=["작성시각"]).copy()

            if time_unit == "시간별":
                trend_df["구간"] = trend_df["작성시각"].dt.tz_convert("Asia/Seoul").dt.hour
                chart_df = trend_df.groupby("구간").size().reset_index(name="댓글수")
                chart_df["구간"] = chart_df["구간"].astype(str) + "시"
                title = "시간대별 댓글 작성 수"
            elif time_unit == "일별":
                trend_df["구간"] = (
                    trend_df["작성시각"]
                    .dt.tz_convert("Asia/Seoul")
                    .dt.date
                    .astype(str)
                )
                chart_df = trend_df.groupby("구간").size().reset_index(name="댓글수")
                title = "날짜별 댓글 작성 수"
            else:
                weekday_order = ["월", "화", "수", "목", "금", "토", "일"]
                trend_df["구간"] = (
                    trend_df["작성시각"]
                    .dt.tz_convert("Asia/Seoul")
                    .dt.dayofweek
                    .map(dict(enumerate(weekday_order)))
                )
                chart_df = (
                    trend_df.groupby("구간").size()
                    .reindex(weekday_order, fill_value=0)
                    .reset_index(name="댓글수")
                )
                title = "요일별 댓글 작성 수"

            fig_trend = px.bar(
                chart_df,
                x="구간",
                y="댓글수",
                title=title,
                text_auto=True,
            )
            fig_trend.update_layout(
                xaxis_title="작성 구간",
                yaxis_title="댓글 수",
                hovermode="x unified",
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with tab2:
            col1, col2 = st.columns([1.4, 1])

            with col1:
                reaction_fig = px.scatter(
                    df,
                    x="좋아요",
                    y="답글수",
                    size="반응점수",
                    hover_name="작성자",
                    hover_data={"댓글": True, "반응점수": True},
                    title="댓글별 좋아요와 답글 반응",
                    size_max=45,
                )
                reaction_fig.update_layout(
                    xaxis_title="좋아요 수",
                    yaxis_title="답글 수",
                )
                st.plotly_chart(reaction_fig, use_container_width=True)

            with col2:
                top_reactions = df.nlargest(10, "반응점수")[
                    ["작성자", "댓글", "좋아요", "답글수", "반응점수"]
                ].copy()
                top_reactions["댓글"] = top_reactions["댓글"].str.slice(0, 80)
                st.subheader("🔥 반응이 큰 댓글 TOP 10")
                st.dataframe(
                    top_reactions,
                    use_container_width=True,
                    hide_index=True,
                )

        with tab3:
            frequencies = tokenize_korean(df["댓글"], extra_stopwords)

            if not frequencies:
                st.warning("워드클라우드를 만들 수 있는 단어가 없습니다.")
            else:
                try:
                    font_path = download_korean_font(font_url)
                    wc_fig = render_wordcloud(frequencies, font_path)
                    st.pyplot(wc_fig, use_container_width=True)
                    plt.close(wc_fig)

                    keyword_df = pd.DataFrame(
                        frequencies.most_common(30),
                        columns=["키워드", "빈도"],
                    )
                    keyword_fig = px.bar(
                        keyword_df.head(20).sort_values("빈도"),
                        x="빈도",
                        y="키워드",
                        orientation="h",
                        title="주요 키워드 TOP 20",
                        text_auto=True,
                    )
                    st.plotly_chart(keyword_fig, use_container_width=True)
                except Exception as font_error:
                    st.error(
                        "한글 폰트를 불러오지 못했습니다. "
                        "GitHub 저장소에 TTF/OTF 폰트를 올린 뒤 raw 주소를 입력해 주세요."
                    )
                    st.code(str(font_error))

        with tab4:
            display_df = df.copy()
            display_df["작성시각"] = (
                display_df["작성시각"]
                .dt.tz_convert("Asia/Seoul")
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇️ 댓글 CSV 다운로드",
                data=csv_data,
                file_name=f"youtube_comments_{video_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    except requests.exceptions.RequestException as error:
        st.error(f"네트워크 또는 폰트 다운로드 오류가 발생했습니다: {error}")
    except RuntimeError as error:
        error_message = str(error)
        st.error(f"YouTube API 오류: {error_message}")

        if "commentsDisabled" in error_message or "disabled comments" in error_message.lower():
            st.info("해당 영상은 댓글 사용이 중지되어 있습니다.")
        elif "quota" in error_message.lower():
            st.info("API 일일 할당량을 확인해 주세요.")
        elif "key" in error_message.lower():
            st.info("API 키가 올바른지, YouTube Data API v3가 활성화되어 있는지 확인해 주세요.")
    except Exception as error:
        st.error(f"분석 중 오류가 발생했습니다: {error}")
