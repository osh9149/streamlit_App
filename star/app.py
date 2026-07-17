import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 페이지 기본 설정 (화면을 최대한 넓게 쓰기 위해 와이드 모드 적용 및 사이드바 제거)
st.set_page_config(
    page_title="My Constellation - 5x5 역량 별자리 관측소",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 화면 전체 너비를 100% 활용하고 마진을 최적화하는 프리미엄 우주 테마 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body {
        font-family: 'Noto Sans KR', sans-serif;
    }
    /* Streamlit 기본 좌우/상하 여백 제거하여 풀스크린 구현 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    .stApp {
        background: #060913; 
    }
    h1, h2, h3 {
        color: #ECF0F1 !important;
    }
    /* 상단 컨트롤러 패널 스타일 */
    .control-panel {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 25px;
    }
    /* 별자리 카드 스타일 */
    .card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 10px 15px;
        margin-top: 5px;
        margin-bottom: 0px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #F8FAFC;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* 하단 요약 리포트 박스 */
    .report-box {
        background: rgba(30, 41, 59, 0.3); 
        padding: 8px 10px; 
        border-radius: 8px; 
        border: 1px dashed rgba(255,255,255,0.06); 
        margin-bottom: 15px; 
        font-size: 12px; 
        color: #E2E8F0;
        line-height: 1.5;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. 구글 시트 데이터 연동 로직
# ==========================================

def extract_sheets_id(url):
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def load_data_from_google_sheet(sheets_url):
    sheets_id = extract_sheets_id(sheets_url)
    if not sheets_id:
        st.error("올바르지 않은 구글 시트 링크 주소입니다.")
        return None
        
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('sheets', 'v4', credentials=creds)
        
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheets_id).execute()
        sheets = spreadsheet.get('sheets', [])
        if not sheets:
            st.error("구글 시트 내에 탭을 찾을 수 없습니다.")
            return None
        first_sheet_name = sheets[0]['properties']['title']
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheets_id,
            range=f"'{first_sheet_name}'!A1:H100"
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            st.warning("시트에 읽어올 데이터 행이 부족합니다.")
            return None
            
        max_cols = max(len(row) for row in values)
        if max_cols < 8:
            st.error(f"시트의 열 개수가 부족합니다. (최소 8개 열 필요)")
            return None

        sanitized_values = []
        for row in values:
            if len(row) < max_cols:
                row = row + [""] * (max_cols - len(row))
            sanitized_values.append(row[:max_cols])

        headers = [h.strip() for h in sanitized_values[0]]
        df = pd.DataFrame(sanitized_values[1:], columns=headers)
        
        # C열(인덱스 2)부터 H열(인덱스 7)까지 점수 형변환
        df['A_score'] = pd.to_numeric(df.iloc[:, 2], errors='coerce').fillna(1.0)
        df['B_score'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(1.0)
        df['C_score'] = pd.to_numeric(df.iloc[:, 4], errors='coerce').fillna(1.0)
        df['D_score'] = pd.to_numeric(df.iloc[:, 5], errors='coerce').fillna(1.0)
        df['E_score'] = pd.to_numeric(df.iloc[:, 6], errors='coerce').fillna(1.0)
        df['F_score'] = pd.to_numeric(df.iloc[:, 7], errors='coerce').fillna(1.0)
        
        return df
    except Exception as e:
        st.error(f"구글 시트 연동 실패 원인: {e}")
        return None


# ==========================================
# 2. 풀 스크린 5x5 그리드용 별자리 시각화 엔진 (안전 설계 구조)
# ==========================================

def draw_beautiful_constellation(name, scores):
    categories = ['A', 'B', 'C', 'D', 'E', 'F', 'A']
    
    comp_names = {
        'A': '교육 이해', 
        'B': '윤리적 실천', 
        'C': '수업·학습자 분석',
        'D': '설계', 
        'E': '실행', 
        'F': '평가'
    }
    
    r_values = [scores[cat] for cat in ['A', 'B', 'C', 'D', 'E', 'F', 'A']]
    g_score = 5.0  
    
    keys = ['A', 'B', 'C', 'D', 'E', 'F']
    max_cat = max(keys, key=lambda k: scores[k])
    min_cat = min(keys, key=lambda k: scores[k])
    
    if scores[max_cat] == scores[min_cat]:
        max_cat = 'A'
        min_cat = 'F'
    
    # 🛠️ [에러 원천 방쇄] go.Figure 인자 내에 처음부터 모든 레이아웃 스펙을 빌드하여 
    # 후속 update_layout 시 발생할 수 있는 내부 키 충돌 버그를 100% 방지합니다.
    fig = go.Figure(
        data=[
            # 🌌 1. G역량 메타 보호막
            go.Scatterpolar(
                r=[g_score]*7, 
                theta=categories, 
                fill='toself',
                fillcolor='rgba(139, 92, 246, 0.05)',
                line=dict(color='rgba(167, 139, 250, 0.3)', width=1.5, dash='dot'),
                showlegend=False, 
                hoverinfo='skip'
            ),
            # ✨ 2. 핵심 별자리 궤도
            go.Scatterpolar(
                r=r_values, 
                theta=categories, 
                fill='toself',
                fillcolor='rgba(56, 189, 248, 0.18)', 
                line=dict(color='#38BDF8', width=2.5),
                mode='lines+markers',
                marker=dict(
                    size=[11 if c == max_cat else 6 for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
                    color=['#FBBF24' if c == max_cat else '#38BDF8' for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
                    symbol='star'
                ),
                text=[f"{comp_names[c]}: {scores[c]}점" for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
                hoverinfo='text'
            )
        ],
        layout=go.Layout(
            polar=dict(
                bgcolor='rgb(9, 13, 24)',
                radialaxis=dict(
                    visible=True,
                    range=[0, 5.2],
                    showline=False,
                    gridcolor='rgba(255, 255, 255, 0.06)',
                    angle=90,
                    tickfont=dict(color='gray', size=9)
                ),
                angularaxis=dict(
                    gridcolor='rgba(255, 255, 255, 0.06)',
                    tickfont=dict(color='#ECF0F1', size=11, fontweight='bold'),
                    rotation=90,
                    direction="clockwise"
                )
            ),
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=320
        )
    )
    
    return fig, max_cat, min_cat, comp_names


# ==========================================
# 3. 상단 대시보드 및 풀 스크린 5x5 그리드 구현
# ==========================================

st.title("🌌 25인 디지털 교육 역량 별자리 은하 지도 [5 × 5 Full-Screen]")

# 대시보드 상단 제어 패널 배치
st.markdown('<div class="control-panel">', unsafe_allow_html=True)
sheets_url = st.text_input("📂 연동할 구글 스프레드시트 링크 입력", value="https://docs.google.com/spreadsheets/d/1oITSnXoXMDP8Dbs_L5ZLvwRbhYB6qm2fruyjES3jDfM/edit?usp=sharing")
st.markdown('</div>', unsafe_allow_html=True)

df_data = None
if sheets_url:
    with st.spinner("🌌 성간 데이터 센터와 실시간 동기화 중..."):
        df_data = load_data_from_google_sheet(sheets_url)

if df_data is not None:
    # 최대 25명까지 데이터 추출 제한
    df_data = df_data.head(25)
    total_records = len(df_data)
    
    st.success(f"📊 {total_records}명의 데이터 궤도가 정밀 동기화되었습니다.")
    
    with st.expander("📂 원본 데이터베이스 테이블 확인"):
        st.dataframe(df_data, use_container_width=True)
        
    # 화면 전체 너비를 채우는 5열(Columns) 확장 레이아웃 전개
    grid_cols = st.columns(5)
    
    for idx, row in df_data.iterrows():
        col = grid_cols[idx % 5]
        
        with col:
            # B열(인덱스 1)의 실제 이름을 식별자로 추적하여 타이틀 바인딩
            name_val = row.iloc[1]
            name = str(name_val).strip() if (pd.notna(name_val) and str(name_val).strip() != "") else f"참여자 {idx+1:02d}"
            
            # 시트에 '학교' 열이 존재할 경우 괄호 텍스트 병합 추가
            school_info = ""
            if len(row) > 2 and '학교' in df_data.columns:
                school_info = f" ({row['학교']})"
            
            scores = {
                'A': float(row['A_score']),
                'B': float(row['B_score']),
                'C': float(row['C_score']),
                'D': float(row['D_score']),
                'E': float(row['E_score']),
                'F': float(row['F_score'])
            }
            
            fig, max_cat, min_cat, comp_names = draw_beautiful_constellation(name, scores)
            
            # 5x5 그리드 전용 명찰 카드
            st.markdown(f"""
            <div class="card">
                <div class="card-title">✨ {name}{school_info}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 레이더 차트 플로팅
            st.plotly_chart(fig, use_container_width=True, key=f"grid_chart_{idx}", config={'displayModeBar': False})
            
            # 리포트 요약 박스
            st.markdown(f"""
            <div class="report-box">
                🥇 <b style="color:#FBBF24;">강점:</b> {comp_names[max_cat]} ({scores[max_cat]}점)<br/>
                🎯 <b style="color:#F87171;">보완:</b> {comp_names[min_cat]} ({scores[min_cat]}점)
            </div>
            """, unsafe_allow_html=True)
