import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 페이지 기본 설정
st.set_page_config(
    page_title="My Constellation - 5x5 역량 별자리 관측소",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 밤하늘 테마 CSS 
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stSidebar"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .stApp {
        background: #060913; 
    }
    h1, h2, h3 {
        color: #ECF0F1 !important;
    }
    .card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 10px 15px;
        margin-top: 10px;
        margin-bottom: 0px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .report-box {
        background: rgba(30, 41, 59, 0.3); 
        padding: 8px; 
        border-radius: 8px; 
        border: 1px dashed rgba(255,255,255,0.06); 
        margin-bottom: 20px; 
        font-size: 11px; 
        color: #E2E8F0;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. 구글 시트 데이터 연동 로직 (안전성 강화)
# ==========================================

def extract_sheets_id(url):
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def load_data_from_google_sheet(sheets_url):
    sheets_id = extract_sheets_id(sheets_url)
    if not sheets_id:
        st.sidebar.error("올바르지 않은 구글 시트 링크 주소입니다.")
        return None
        
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('sheets', 'v4', credentials=creds)
        
        # 1. 시트의 정확한 탭 이름(첫 번째 시트명)을 먼저 가져옵니다.
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheets_id).execute()
        sheets = spreadsheet.get('sheets', [])
        if not sheets:
            st.sidebar.error("구글 시트 내에 탭을 찾을 수 없습니다.")
            return None
        first_sheet_name = sheets[0]['properties']['title']
        
        # 2. 첫 번째 탭의 A1:H100 데이터 호출
        result = service.spreadsheets().values().get(
            spreadsheetId=sheets_id,
            range=f"'{first_sheet_name}'!A1:H100"
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            st.sidebar.warning("시트에 읽어올 데이터 행이 부족합니다. (최소 헤더 포함 2줄 이상 필요)")
            return None
            
        # 3. 데이터 행들의 열 개수가 일치하는지 확인 및 패딩 처리
        max_cols = max(len(row) for row in values)
        if max_cols < 8:
            st.sidebar.error(f"시트의 열 개수가 부족합니다. (현재 최대 열 개수: {max_cols}개, 최소 8개 열 필요: 이름, 학교, A~F)")
            return None

        # 모든 행의 길이를 동일하게 맞춰 데이터프레임 빌드 시 에러 방지
        sanitized_values = []
        for row in values:
            if len(row) < max_cols:
                row = row + [""] * (max_cols - len(row))
            sanitized_values.append(row[:max_cols])

        headers = [h.strip() for h in sanitized_values[0]]
        df = pd.DataFrame(sanitized_values[1:], columns=headers)
        
        # C열(인덱스 2)부터 H열(인덱스 7)까지 숫자로 안전하게 파싱
        df['A_score'] = pd.to_numeric(df.iloc[:, 2], errors='coerce').fillna(1.0)
        df['B_score'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(1.0)
        df['C_score'] = pd.to_numeric(df.iloc[:, 4], errors='coerce').fillna(1.0)
        df['D_score'] = pd.to_numeric(df.iloc[:, 5], errors='coerce').fillna(1.0)
        df['E_score'] = pd.to_numeric(df.iloc[:, 6], errors='coerce').fillna(1.0)
        df['F_score'] = pd.to_numeric(df.iloc[:, 7], errors='coerce').fillna(1.0)
        
        return df
    except Exception as e:
        st.sidebar.error(f"구글 시트 연동 실패 원인: {e}")
        st.sidebar.info("💡 해결 가이드: '공유' 버튼을 눌러 서비스 계정 이메일(slides-reader@...)이 '뷰어'로 추가되어 있는지 다시 한 번 확인해 주세요.")
        return None


# ==========================================
# 2. 5x5 그리드용 별자리 시각화 엔진
# ==========================================

def draw_beautiful_constellation(name, scores):
    categories = ['A', 'B', 'C', 'D', 'E', 'F', 'A']
    comp_names = {
        'A': 'A. 교육 이해', 'B': 'B. 윤리적 실천', 'C': 'C. 수업·학습자 분석',
        'D': 'D. 설계', 'E': 'E. 실행', 'F': 'F. 평가'
    }
    
    r_values = [scores[cat] for cat in ['A', 'B', 'C', 'D', 'E', 'F', 'A']]
    g_score = 5.0  
    
    max_cat = max(['A', 'B', 'C', 'D', 'E', 'F'], key=lambda k: scores[k])
    min_cat = min(['A', 'B', 'C', 'D', 'E', 'F'], key=lambda k: scores[k])
    
    fig = go.Figure()
    
    # G역량 메타 보호막
    fig.add_trace(go.Scatterpolar(
        r=[g_score]*7, theta=categories, fill='toself',
        fillcolor='rgba(139, 92, 246, 0.05)',
        line=dict(color='rgba(167, 139, 250, 0.3)', width=1.5, dash='dot'),
        showlegend=False, hoverinfo='skip'
    ))
    
    # 핵심 별자리
    fig.add_trace(go.Scatterpolar(
        r=r_values, theta=categories, fill='toself',
        fillcolor='rgba(56, 189, 248, 0.18)', line=dict(color='#38BDF8', width=2),
        mode='lines+markers',
        marker=dict(
            size=[10 if c == max_cat else 5 for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
            color=['#FBBF24' if c == max_cat else '#38BDF8' for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
            symbol='star'
        ),
        text=[f"{comp_names[c]}: {scores[c]}점" for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
        hoverinfo='text'
    ))
    
    fig.update_layout(
        polar=dict(
            bgcolor='rgb(9, 13, 24)',
            radialaxis=dict(visible=True, range=[0, 5.2], showline=False, gridcolor='rgba(255,255,255,0.06)', angle=90, tickfont=dict(color='gray', size=8)),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont=dict(color='#ECF0F1', size=9), rotation=90, direction="clockwise")
        ),
        showlegend=False, margin=dict(l=25, r=25, t=25, b=25),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=260
    )
    return fig, max_cat, min_cat, comp_names


# ==========================================
# 3. Streamlit 대시보드 렌더링
# ==========================================

st.title("🌌 25인 자가진단 역량 별자리 [5 × 5 한눈에 보기]")
st.markdown("구글 스프레드시트의 데이터를 실시간 매핑하여 밤하늘의 고유 성좌 지도를 구성합니다.")

st.sidebar.header("🛸 별 관측 제어판")
use_demo = st.sidebar.checkbox("🎁 25인 가상 데모 시뮬레이션", value=True)

sheets_url = ""
df_data = None

if not use_demo:
    sheets_url = st.sidebar.text_input("📂 구글 스프레드시트 링크 입력", value="https://docs.google.com/spreadsheets/d/1oITSnXoXMDP8Dbs_L5ZLvwRbhYB6qm2fruyjES3jDfM/edit?usp=sharing")
    if sheets_url:
        with st.spinner("구글 데이터 허브 동기화 중..."):
            df_data = load_data_from_google_sheet(sheets_url)
    else:
        st.warning("👈 왼쪽 제어판에 구글 스프레드시트 주소를 붙여넣어 주세요.")
else:
    st.sidebar.success("현재 데모 데이터가 작동 중입니다.")
    demo_rows = []
    for i in range(1, 26):
        demo_rows.append({
            "이름": f"참여자 {i:02d}", "학교": "선도학교",
            "A_score": np.round(np.random.uniform(2.0, 5.0), 1), "B_score": np.round(np.random.uniform(2.0, 5.0), 1),
            "C_score": np.round(np.random.uniform(2.0, 5.0), 1), "D_score": np.round(np.random.uniform(2.0, 5.0), 1),
            "E_score": np.round(np.random.uniform(2.0, 5.0), 1), "F_score": np.round(np.random.uniform(2.0, 5.0), 1)
        })
    df_data = pd.DataFrame(demo_rows)

if df_data is not None:
    # 안전하게 최대 25명까지만 컷팅
    df_data = df_data.head(25)
    total_records = len(df_data)
    
    st.success(f"📊 {total_records}명의 데이터 궤도가 정밀 동기화되었습니다.")
    
    with st.expander("📂 로드된 데이터프레임 검증 테이블"):
        st.dataframe(df_data, use_container_width=True)
    
    # 5열 그리드 구성
    grid_cols = st.columns(5)
    
    for idx, row in df_data.iterrows():
        col = grid_cols[idx % 5]
        
        with col:
            # 첫 번째 열(이름) 추출 안전 예외 처리
            name_val = row.iloc[0]
            name = str(name_val).strip() if (pd.notna(name_val) and str(name_val).strip() != "") else f"참여자 {idx+1:02d}"
            
            scores = {
                'A': float(row['A_score']),
                'B': float(row['B_score']),
                'C': float(row['C_score']),
                'D': float(row['D_score']),
                'E': float(row['E_score']),
                'F': float(row['F_score'])
            }
            
            fig, max_cat, min_cat, comp_names = draw_beautiful_constellation(name, scores)
            
            st.markdown(f"""
            <div class="card">
                <div class="card-title">✨ {name}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.plotly_chart(fig, use_container_width=True, key=f"grid_chart_{idx}", config={'displayModeBar': False})
            
            st.markdown(f"""
            <div class="report-box">
                🥇 <b style="color:#FBBF24;">강점:</b> {max_cat} ({scores[max_cat]}점)<br/>
                🎯 <b style="color:#F87171;">보완:</b> {min_cat} ({scores[min_cat]}점)
            </div>
            """, unsafe_allow_html=True)
