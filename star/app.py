import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 페이지 기본 설정 (5x5 배치를 위해 와이드 레이아웃 적용)
st.set_page_config(
    page_title="My Constellation - 5x5 역량 별자리 관측소",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 깊은 밤하늘 느낌의 우주 테마 CSS 스타일 적용
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
# 1. 구글 시트 데이터 연동 로직
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
        
        # 이름, 학교 데이터 및 C열~H열 역량 데이터 전체를 안전하게 가져옵니다.
        result = service.spreadsheets().values().get(
            spreadsheetId=sheets_id,
            range="디지털 교육 역량 자가진단 데이터!A1:H26"  # 제공된 시트 명칭 반영
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            return None
            
        # 첫 번째 행을 컬럼명으로 처리
        headers = values[0]
        df = pd.DataFrame(values[1:], columns=headers)
        
        # 제공된 시트 구조와 매핑: C열[2]부터 H열[7]까지 순서대로 A~F 매칭
        # 사용자가 편하게 인덱싱할 수 있도록 알파벳 컬럼 가상 매핑
        df['A_score'] = pd.to_numeric(df.iloc[:, 2], errors='coerce').fillna(1.0) # C열
        df['B_score'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(1.0) # D열
        df['C_score'] = pd.to_numeric(df.iloc[:, 4], errors='coerce').fillna(1.0) # E열
        df['D_score'] = pd.to_numeric(df.iloc[:, 5], errors='coerce').fillna(1.0) # F열
        df['E_score'] = pd.to_numeric(df.iloc[:, 6], errors='coerce').fillna(1.0) # G열
        df['F_score'] = pd.to_numeric(df.iloc[:, 7], errors='coerce').fillna(1.0) # H열
        
        return df
    except Exception as e:
        st.sidebar.error(f"구글 시트 연동 실패: {e}")
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
    g_score = 5.0  # 메타 역량 보호막은 최고점(5.0) 크기로 전체를 감싸 안음
    
    max_cat = max(['A', 'B', 'C', 'D', 'E', 'F'], key=lambda k: scores[k])
    min_cat = min(['A', 'B', 'C', 'D', 'E', 'F'], key=lambda k: scores[k])
    
    fig = go.Figure()
    
    # 🌌 1. G역량 메타 보호막 (배경 구체 보호막)
    fig.add_trace(go.Scatterpolar(
        r=[g_score]*7, theta=categories, fill='toself',
        fillcolor='rgba(139, 92, 246, 0.05)',
        line=dict(color='rgba(167, 139, 250, 0.3)', width=1.5, dash='dot'),
        showlegend=False, hoverinfo='skip'
    ))
    
    # ✨ 2. 나의 별자리 디자인 (A~F 연결)
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
    
    # 5x5 컴팩트 배치를 위해 마진 및 글자 크기 최적화
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
# 3. Streamlit 대시보드 렌더링 (5x5 그리드)
# ==========================================

st.title("🌌 25인 자가진단 역량 별자리 [5 × 5 한눈에 보기]")
st.markdown("구글 스프레드시트의 **C열~H열 점수**를 기반으로 25명 전체의 디지털 자가진단 궤도를 5x5 스크린으로 일괄 관측합니다.")

# 사이드바 설정
st.sidebar.header("🛸 별 관측 제어판")
use_demo = st.sidebar.checkbox("🎁 25인 가상 데모 시뮬레이션", value=True, 
                               help="체크를 풀고 구글 시트 주소를 넣으면 실제 연동이 시작됩니다.")

sheets_url = ""
df_data = None

if not use_demo:
    sheets_url = st.sidebar.text_input("📂 구글 스프레드시트 링크 입력", value="https://docs.google.com/spreadsheets/d/1oITSnXoXMDP8Dbs_L5ZLvwRbhYB6qm2fruyjES3jDfM/edit?usp=sharing")
    if sheets_url:
        with st.spinner("구글 시트 연동 및 역량 매핑 시스템 기동 중..."):
            df_data = load_data_from_google_sheet(sheets_url)
else:
    st.sidebar.success("현재 시뮬레이션 데이터가 활성화되었습니다.")
    # 25인 난수 데이터 실시간 생성
    demo_rows = []
    for i in range(1, 26):
        demo_rows.append({
            "이름": f"교사 {i:02d}", "학교": "선도학교",
            "A_score": np.round(np.random.uniform(2.0, 5.0), 1), "B_score": np.round(np.random.uniform(2.0, 5.0), 1),
            "C_score": np.round(np.random.uniform(2.0, 5.0), 1), "D_score": np.round(np.random.uniform(2.0, 5.0), 1),
            "E_score": np.round(np.random.uniform(2.0, 5.0), 1), "F_score": np.round(np.random.uniform(2.0, 5.0), 1)
        })
    df_data = pd.DataFrame(demo_rows)

if df_data is not None:
    # 25명 데이터 규격 맞춤 슬라이싱 (데이터가 더 많아도 딱 25명만 표시되도록 안전 바운딩)
    df_data = df_data.head(25)
    
    st.success(f"📊 {len(df_data)}명의 역량 데이터 레코드가 5×5 은하 지도에 매핑되었습니다.")
    
    # 정밀한 5열(5 columns) 격자 구성
    grid_cols = st.columns(5)
    
    for idx, row in df_data.iterrows():
        # idx % 5 구조를 이용하여 한 줄에 정확히 5개씩 나누어 할당
        col = grid_cols[idx % 5]
        
        with col:
            # 이름 데이터 파싱 (시트에 이름 열이 비어있다면 순번 처리)
            raw_name = row.get("이름", "")
            name = raw_name if (raw_name and str(raw_name).strip() != "") else f"참여자 {idx+1:02d}"
            
            # 가상 컬럼에서 A~F 점수 딕셔너리 빌드
            scores = {
                'A': float(row['A_score']),
                'B': float(row['B_score']),
                'C': float(row['C_score']),
                'D': float(row['D_score']),
                'E': float(row['E_score']),
                'F': float(row['F_score'])
            }
            
            # 별자리 드로잉
            fig, max_cat, min_cat, comp_names = draw_beautiful_constellation(name, scores)
            
            # 카드 상단 네임 태그
            st.markdown(f"""
            <div class="card">
                <div class="card-title">✨ {name}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 레이더 차트 플로팅
            st.plotly_chart(fig, use_container_width=True, key=f"grid_chart_{idx}", config={'displayModeBar': False})
            
            # 강점 / 보완점 압축 리포트 (5x5 화면에 맞춰 글자 크기 축소 최적화)
            st.markdown(f"""
            <div class="report-box">
                🥇 <b style="color:#FBBF24;">강점:</b> {max_cat} ({scores[max_cat]}점)<br/>
                🎯 <b style="color:#F87171;">보완:</b> {min_cat} ({scores[min_cat]}점)
            </div>
            """, unsafe_allow_html=True)
