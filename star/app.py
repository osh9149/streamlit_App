import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 페이지 기본 설정 (우주/밤하늘의 별자리 테마)
st.set_page_config(
    page_title="My Constellation - 디지털 교육 역량 별자리",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 밤하늘/은하수 감성의 웹앱 커스텀 CSS 스타일 데코레이션
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stSidebar"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .stApp {
        background: #060913; /* 깊은 우주 암흑색 */
    }
    h1, h2, h3 {
        color: #ECF0F1 !important;
    }
    .card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 12px;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.5);
    }
    .card-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .badge-strength {
        background-color: rgba(251, 191, 36, 0.2);
        color: #FBBF24;
        border: 1px solid #FBBF24;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
    }
    .badge-weakness {
        background-color: rgba(239, 68, 68, 0.2);
        color: #F87171;
        border: 1px solid #F87171;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. Google Slides 데이터 파싱 로직 (image_55d1e8.png 구조 기준)
# ==========================================

def extract_presentation_id(url):
    """구글 슬라이드 URL 주소에서 고유 Presentation ID를 추출합니다."""
    match = re.search(r'/presentation/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def get_slide_student_info(slide):
    """
    image_55d1e8.png의 우측 상단 '이름(학교)' 형태의 텍스트 박스를 찾아 정보를 추출합니다.
    예: '홍길동(우주고등학교)' 혹은 '이름(학교)' 텍스트 수집 후 제목으로 사용합니다.
    """
    for element in slide.get('pageElements', []):
        if 'shape' in element and element['shape'].get('shapeType') == 'TEXT_BOX':
            text = ""
            for paragraph in element['shape']['text'].get('paragraphs', []):
                for el in paragraph.get('elements', []):
                    if 'textRun' in el:
                        text += el['textRun'].get('content', '')
            text = text.strip()
            
            # 메인 타이틀인 '디지털 교육 역량 자가 진단 표'는 이름 칸이 아니므로 패스합니다.
            if "자가 진단 표" in text or "디지털" in text:
                continue
                
            # 괄호 형태 '이름(학교)' 매칭 검증 또는 텍스트 길이 필터링
            if text and len(text) < 30:
                return text
    return "알 수 없는 별자리"

def get_table_scores_from_image(slide):
    """
    image_55d1e8.png의 표 구조를 분석하여 A~F역량의 나의 점수를 추출합니다.
    - 열 구조: 0열(코드: A~F) | 1열(역량명) | 2열(나의 점수: 1~5)
    """
    scores = {}
    for element in slide.get('pageElements', []):
        if 'table' in element:
            table = element['table']
            rows = table.get('tableRows', [])
            
            for row in rows:
                cells = row.get('tableCells', [])
                if len(cells) < 3:
                    continue  # 최소 3개 열(코드, 역량명, 나의 점수)이 있어야 파싱 진행
                
                # 0열(코드) 텍스트 추출
                code_text = ""
                cell_0 = cells[0]
                if 'text' in cell_0:
                    for p in cell_0['text'].get('paragraphs', []):
                        for el in p.get('elements', []):
                            if 'textRun' in el:
                                code_text += el['textRun'].get('content', '')
                code_clean = code_text.strip().upper()
                
                # 2열(나의 점수) 텍스트 추출
                score_text = ""
                cell_2 = cells[2]
                if 'text' in cell_2:
                    for p in cell_2['text'].get('paragraphs', []):
                        for el in p.get('elements', []):
                            if 'textRun' in el:
                                score_text += el['textRun'].get('content', '')
                score_clean = score_text.strip()
                
                # 코드가 A~F 중 하나인 행의 점수를 수집 (5점 만점 척도 변환)
                if code_clean in ['A', 'B', 'C', 'D', 'E', 'F']:
                    # 숫자 매칭 (정수 및 실수 정규식)
                    num_match = re.search(r'\d+(\.\d+)?', score_clean)
                    if num_match:
                        score_value = float(num_match.group())
                        # 1~5 범위로 안전 바운딩 처리
                        scores[code_clean] = max(1.0, min(5.0, score_value))
            
            # 유효한 역량 점수 데이터셋이 완성되면 즉시 리턴
            if len(scores) >= 5:
                # G역량은 이미지의 표에 없으므로, 전체를 아우르는 최대 보호막 '5.0' 점수로 자동 할당합니다.
                scores['G'] = 5.0
                return scores
                
    return scores

def load_google_slides_to_constellations(presentation_url):
    """GCP Secrets 계정 연동을 활용해 구글 슬라이드 정보를 실시간으로 파싱합니다."""
    presentation_id = extract_presentation_id(presentation_url)
    if not presentation_id:
        st.error("입력하신 구글 슬라이드 주소가 올바르지 않습니다.")
        return []

    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('slides', 'v1', credentials=creds)
        
        presentation = service.presentations().get(presentationId=presentation_id).execute()
        slides = presentation.get('slides', [])
        
        results = []
        for i, slide in enumerate(slides):
            info = get_slide_student_info(slide) or f"슬라이드 {i+1} 학생"
            scores = get_table_scores_from_image(slide)
            if scores:
                results.append({
                    "title": info,
                    "scores": scores
                })
        return results
    except Exception as e:
        st.error(f"구글 API 호출 오류가 발생했습니다: {e}")
        st.info("💡 서비스 계정(JSON) 설정이 완료되었는지, 슬라이드 문서가 해당 서비스 계정 이메일에 공유 완료되었는지 체크해 주세요.")
        return []


# ==========================================
# 2. 나의 별자리 (Constellation) 시각화 엔진
# ==========================================

def draw_beautiful_constellation(name, scores):
    """A~F 역량을 1~5점 척도의 은하수 별자리로 연결하고, G역량을 은은한 메타 구체 보호막으로 우주 테마 시각화합니다."""
    # 6각형 구조 순환을 위해 마지막 좌표에 A 추가
    categories = ['A', 'B', 'C', 'D', 'E', 'F', 'A']
    
    # 이미지 image_55d1e8.png 역량명 명칭 완벽 동기화
    comp_names = {
        'A': 'A. 교육 이해', 
        'B': 'B. 윤리적 실천', 
        'C': 'C. 수업·학습자 분석', 
        'D': 'D. 설계', 
        'E': 'E. 실행', 
        'F': 'F. 평가', 
        'G': 'G. 디지털 메타 역량 (보호막)'
    }
    
    # 1~5점 값 배열 생성
    r_values = [scores.get(cat, 1.0) for cat in ['A', 'B', 'C', 'D', 'E', 'F', 'A']]
    g_score = scores.get('G', 5.0)  # 메타 역량 G는 전체를 감싸도록 최고 레벨인 5.0으로 세팅
    
    # 강점(최댓값) 및 보완점(최솟값) 색출 (G역량 제외)
    core_scores = {k: v for k, v in scores.items() if k != 'G'}
    max_cat = max(core_scores, key=core_scores.get)
    min_cat = min(core_scores, key=core_scores.get)
    
    fig = go.Figure()
    
    # 🌌 1. G역량 초월 메타 보호막 (Outer Meta Shield, 5.0 가득 찬 배경 구체)
    g_values = [g_score] * 7
    fig.add_trace(go.Scatterpolar(
        r=g_values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(139, 92, 246, 0.08)', # 은은한 오로라빛 수호 장막
        line=dict(color='rgba(167, 139, 250, 0.45)', width=2, dash='dot'),
        name="🛡️ G 메타 역량 보호막 (5.0)",
        hoverinfo='skip'
    ))
    
    # ✨ 2. 핵심 자가 진단 별자리 (A~F Constellation Web)
    fig.add_trace(go.Scatterpolar(
        r=r_values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(56, 189, 248, 0.22)', # 푸른빛 성운 공간
        line=dict(color='#38BDF8', width=3),
        mode='lines+markers',
        marker=dict(
            size=[14 if cat == max_cat else 8 for cat in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
            color=['#FBBF24' if cat == max_cat else '#38BDF8' for cat in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
            symbol='star'
        ),
        name="디지털 자가진단 궤도",
        text=[f"{comp_names.get(cat, cat)}: {scores.get(cat, 0.0)}점" for cat in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
        hoverinfo='text'
    ))
    
    # 🎨 3. 레이아웃 고도화 (스타일리시한 우주 테마 디자인)
    fig.update_layout(
        polar=dict(
            bgcolor='rgb(9, 13, 24)', # 완벽한 밤하늘 백그라운드 색상
            radialaxis=dict(
                visible=True,
                range=[0, 5.2],  # 5점 만점 자가 진단 표 척도 반영 
                showline=False,
                gridcolor='rgba(255, 255, 255, 0.09)',
                angle=90,
                tickfont=dict(color='rgba(255, 255, 255, 0.4)', size=11)
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.09)',
                tickfont=dict(color='#E2E8F0', size=12, fontweight='bold'),
                rotation=90,
                direction="clockwise"
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(color="#94A3B8")
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        height=450
    )
    
    return fig, max_cat, min_cat, comp_names


# ==========================================
# 3. Streamlit 대시보드 인터페이스
# ==========================================

st.title("🌌 디지털 교육 역량 별자리 탐색기")
st.markdown("구글 슬라이드의 **자가 진단 표 데이터(1~5점 척도)**를 밤하늘의 나만의 수호성 자리로 빚어내어 해석 보고서를 만듭니다.")

# 사이드바 설정 영역
st.sidebar.header("⚙️ 별 관측소 제어판")

use_demo = st.sidebar.checkbox("🎁 데모 데이터로 가상 분석 체험하기", value=True,
                               help="GCP 서비스 계정 키 입력 없이, 가이드 이미지(image_55d1e8.png) 구조로 가상 생성된 데이터 별자리를 확인해봅니다.")

slide_url = ""
if not use_demo:
    slide_url = st.sidebar.text_input(
        "📂 구글 슬라이드 공유 링크 입력",
        placeholder="https://docs.google.com/presentation/d/.../edit"
    )
    st.sidebar.markdown(f"""
    <div style="font-size:12px; color:#94A3B8; line-height:1.4;">
        <b>💡 매칭 규격 가이드 (image_55d1e8.png):</b><br/>
        1. 우측 상단 <b>이름(학교)</b> 텍스트 박스로부터 대상을 인식합니다.<br/>
        2. 표의 1열 코드가 <b>A~F</b>이고, 3열에 <b>1~5점 점수</b>가 기입된 형태를 찾아 연동합니다.<br/>
        3. 수호 메타 영역 G는 밤하늘 전 범위를 감싸도록 자동 시각화됩니다.
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.success("현재 이미지(image_55d1e8.png) 표 구조를 탑재한 시뮬레이션 데모 모드가 실행 중입니다.")

# 데이터 준비
slides_data = []

if use_demo:
    # 5점 척도 기반의 실감나는 가상 학생 데이터셋 구성
    slides_data = [
        {"title": "김민준 (디지털고등학교)", "scores": {"A": 4.5, "B": 4.8, "C": 3.8, "D": 2.5, "E": 3.2, "F": 3.0, "G": 5.0}},
        {"title": "이서연 (미래사범대학교)", "scores": {"A": 3.5, "B": 3.0, "C": 4.8, "D": 4.2, "E": 4.5, "F": 4.7, "G": 5.0}},
        {"title": "박준우 (성남초등학교 교사)", "scores": {"A": 4.8, "B": 4.5, "C": 2.8, "D": 4.9, "E": 4.0, "F": 3.5, "G": 5.0}},
        {"title": "정다은 (은하교육지원청)", "scores": {"A": 2.8, "B": 3.5, "C": 4.2, "D": 3.2, "E": 4.8, "F": 4.0, "G": 5.0}}
    ]
else:
    if slide_url:
        with st.spinner("구글 자가진단 슬라이드 해석 시스템 가동 중..."):
            slides_data = load_google_slides_to_constellations(slide_url)
    else:
        st.warning("👈 왼쪽 제어판에 구글 슬라이드 링크를 기입하거나, 데모 모드를 켜서 즉시 확인해보세요!")

# 화면 렌더링
if slides_data:
    st.info(f"✨ 슬라이드로부터 총 {len(slides_data)}명의 디지털 교육 역량 별자리가 정상 관측되었습니다.")
    
    # 2열 격자 배치로 출력
    grid_cols = st.columns(2)
    
    for idx, student in enumerate(slides_data):
        col = grid_cols[idx % 2]
        with col:
            # 아름다운 카드 타이틀 바 구성
            st.markdown(f"""
            <div class="card">
                <div class="card-title">⭐ {student['title']} 님의 은하 궤도</div>
            </div>
            """, unsafe_style_html=True)
            
            # 레이더 별자리 차트 생성 및 출력
            fig, max_cat, min_cat, comp_names = draw_beautiful_constellation(student['title'], student['scores'])
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")
            
            # 자가진단 분석 결과 요약 리포트 매칭 출력
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.35); padding: 18px; border-radius: 12px; border: 1px dashed rgba(255,255,255,0.1); margin-bottom: 35px;">
                <p style="margin:0 0 10px 0; font-size:14px; color:#A78BFA;">🔭 <b>성간 자가진단 천체 관측 보고</b></p>
                <div style="display:flex; flex-direction:column; gap:8px; font-size: 14px; color: #E2E8F0;">
                    <div>
                        <span class="badge-strength">가장 크게 부푼 영역(강점)</span> 
                        <b>{comp_names[max_cat]}</b> (<b>{student['scores'][max_cat]}점</b>)
                    </div>
                    <div>
                        <span class="badge-weakness">움푹 들어간 영역(보완점)</span> 
                        <b>{comp_names[min_cat]}</b> (<b>{student['scores'][min_cat]}점</b>)
                    </div>
                    <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 6px; margin-top: 4px;">
                        🛡️ <b>G. 디지털 메타 역량 보호막 (보호 강도: {student['scores']['G']} / 5.0)</b><br/>
                        <span style="color: #94A3B8; font-size: 12px;">전체 별자리를 안전하게 에워싸는 우주 보호막으로 작동하며, 세부 진단 결과(A~F)들을 감싸고 연동하는 최상위 마인드셋 에너지로 시각화되었습니다.</span>
                    </div>
                </div>
            </div>
            """, unsafe_style=html=True)
