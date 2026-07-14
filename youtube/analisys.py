import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from datetime import datetime
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# 1. Page Configuration & CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("📊 YouTube 댓글 분석 및 시각화 대시보드")
st.markdown("유튜브 영상 링크를 입력하여 실시간 댓글 추이, 반응도 및 키워드를 분석해 보세요!")

# -----------------------------------------------------------------------------
# 2. YouTube API 로드 (Secrets 사용 혹은 입력 받기)
# -----------------------------------------------------------------------------
# Streamlit Secrets에 저장되어 있는지 확인하고, 없으면 사이드바에서 입력받습니다.
if "YOUTUBE_API_KEY" in st.secrets:
    api_key = st.secrets["AIzaSyDjVDpNMP-FsJV6uWUcms8kJ3adAiypAyo"]
else:
    api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password")
    st.sidebar.info("구글 클라우드 콘솔에서 YouTube Data API v3 키를 발급받아 입력해주세요.")

# -----------------------------------------------------------------------------
# 3. Helper Functions
# -----------------------------------------------------------------------------
def extract_video_id(url):
    """유튜브 URL에서 Video ID를 추출하는 함수"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_comments(video_id, api_key, max_results=200):
    """YouTube API를 사용하여 댓글 수집"""
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        comments = []
        
        # 첫 번째 페이지 요청
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_results, 100), # 한 번에 최대 100개
            textFormat="plainText"
        )
        response = request.execute()

        while response and len(comments) < max_results:
            for item in response['items']:
                comment_data = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment_data['authorDisplayName'],
                    'published_at': comment_data['publishedAt'],
                    'text': comment_data['textDisplay'],
                    'like_count': comment_data['likeCount']
                })
            
            # 다음 페이지가 있고 목표 수량(max_results)을 채우지 못한 경우 계속 수집
            if 'nextPageToken' in response and len(comments) < max_results:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    pageToken=response['nextPageToken'],
                    maxResults=min(max_results - len(comments), 100),
                    textFormat="plainText"
                )
                response = request.execute()
            else:
                break
                
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

def clean_text(text):
    """단어 분석을 위해 특수문자 제거 및 공백 기준 토큰화"""
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', str(text))
    return text

# -----------------------------------------------------------------------------
# 4. Main App Interface
# -----------------------------------------------------------------------------
if not api_key:
    st.warning("🔑 서비스를 이용하려면 YouTube API Key가 필요합니다. 사이드바 혹은 Streamlit Secrets에 등록해 주세요.")
else:
    # 사용자 입력 폼
    with st.form("search_form"):
        video_url = st.text_input("유튜브 영상 링크를 입력하세요:", placeholder="https://www.youtube.com/watch?v=...")
        max_comments = st.slider("수집할 댓글 개수 설정 (최대)", min_value=50, max_value=1000, value=200, step=50)
        submitted = st.form_submit_with_clicks = st.form_submit_button("분석 시작")

    if submitted:
        if not video_url:
            st.error("영상 링크를 입력해 주세요!")
        else:
            video_id = extract_video_id(video_url)
            if not video_id:
                st.error("올바른 YouTube URL 형식이 아닙니다.")
            else:
                with st.spinner("🚀 댓글 데이터를 수집하는 중입니다..."):
                    df = get_youtube_comments(video_id, api_key, max_results=max_comments)
                
                if df.empty:
                    st.info("수집된 댓글이 없거나, API 키 설정을 다시 확인해 주세요.")
                else:
                    # 데이터 전처리
                    df['published_at'] = pd.to_datetime(df['published_at'])
                    # 한국 표준시(KST)로 변환 (필요시 사용)
                    df['published_at'] = df['published_at'].dt.tz_convert('Asia/Seoul')
                    df['date'] = df['published_at'].dt.date
                    df['hour'] = df['published_at'].dt.hour
                    
                    st.success(f"총 {len(df)}개의 댓글 수집 완료!")
                    
                    # ---------------------------------------------------------
                    # Metric 요약 정보
                    # ---------------------------------------------------------
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 댓글 수", f"{len(df)} 개")
                    with col2:
                        st.metric("평균 좋아요 수", f"{df['like_count'].mean():.1f} 개")
                    with col3:
                        st.metric("가장 많은 좋아요를 받은 댓글", f"{df['like_count'].max()} 개")
                    
                    st.markdown("---")
                    
                    # Layout 2 Column 분할
                    left_column, right_column = st.columns(2)
                    
                    # ---------------------------------------------------------
                    # 좌측 열: 시계열 분석 (시간대별 추이)
                    # ---------------------------------------------------------
                    with left_column:
                        st.subheader("⏰ 시간대별 댓글 작성 추이")
                        
                        # 일자별 트렌드
                        daily_df = df.groupby('date').size().reset_index(name='count')
                        fig_daily = px.line(
                            daily_df, x='date', y='count', 
                            title='일자별 작성 추이',
                            labels={'date': '날짜', 'count': '댓글 수'},
                            markers=True
                        )
                        fig_daily.update_layout(hovermode="x unified")
                        st.plotly_chart(fig_daily, use_container_width=True)
                        
                        # 시간(Hour)별 분포
                        hourly_df = df.groupby('hour').size().reset_index(name='count')
                        fig_hourly = px.bar(
                            hourly_df, x='hour', y='count',
                            title='하루 중 시간대별 작성 분포 (시)',
                            labels={'hour': '시간 (시)', 'count': '댓글 수'},
                        )
                        fig_hourly.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
                        st.plotly_chart(fig_hourly, use_container_width=True)

                    # ---------------------------------------------------------
                    # 우측 열: 반응도(좋아요) 및 워드클라우드
                    # ---------------------------------------------------------
                    with right_column:
                        st.subheader("❤️ 댓글 반응도 분석")
                        
                        # 좋아요 수 기준 Top 5 댓글
                        top_comments = df.sort_values(by='like_count', ascending=False).head(5)
                        st.write("👍 **가장 반응이 좋았던 댓글 Top 5**")
                        for idx, row in top_comments.iterrows():
                            st.info(f"**{row['author']}** (좋아요 {row['like_count']}개)\n\n{row['text']}")
                        
                        st.markdown("---")
                        
                        st.subheader("🔤 자주 등장하는 핵심 단어 (Word Cloud)")
                        
                        # 텍스트 정제 및 병합
                        cleaned_texts = df['text'].apply(clean_text)
                        all_text = " ".join(cleaned_texts)
                        
                        # 단어가 충분하지 않을 경우를 대비한 가이드
                        if len(all_text.strip()) < 5:
                            st.write("워드클라우드를 생성할 만큼 충분한 텍스트 데이터가 없습니다.")
                        else:
                            # 폰트 다운로드 안내 (한글 깨짐 방지용 기본 폰트 설정)
                            # Streamlit Cloud 환경에서 작동하도록 기본 Sans-serif 계열 폰트 사용 또는 미지정
                            # 한글이 깨지지 않게 하려면 나눔고딕 등 무료 폰트를 레포지토리에 동봉하여 사용하면 좋습니다.
                            try:
                                # 리눅스 환경(Streamlit Cloud)에서 자주 지원하는 폰트 예시 적용
                                wordcloud = WordCloud(
                                    font_path='/usr/share/fonts/truetype/nanum/NanumGothic.ttf', # 한글 폰트 예시
                                    width=800, height=400,
                                    background_color='white',
                                    colormap='viridis',
                                    max_words=100
                                ).generate(all_text)
                            except:
                                # 폰트 경로가 없으면 기본 폰트로 폴백 수행
                                wordcloud = WordCloud(
                                    width=800, height=400,
                                    background_color='white',
                                    max_words=100
                                ).generate(all_text)
                            
                            # Matplotlib으로 워드클라우드 출력
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                            
                    # ---------------------------------------------------------
                    # 최하단: 원본 데이터 테이블 제공
                    # ---------------------------------------------------------
                    st.markdown("---")
                    st.subheader("📋 수집된 댓글 원본 데이터")
                    st.dataframe(df[['author', 'published_at', 'text', 'like_count']], use_container_width=True)
