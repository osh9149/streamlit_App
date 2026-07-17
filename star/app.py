import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 페이지 기본 설정 (화면을 최대한 넓게 쓰기 위해 와이드 모드 적용)
st.set_page_config(
    page_title="My Constellation - 5x5 역량 별자리 관측소",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 화면 전체 너비를 100% 활용하고 여백을 없애는 프리미엄 우주 테마 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stSidebar"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    /* Streamlit 기본 여백 강제 제거 및 화면 전체 사용 */
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
    /* 컨트롤러 박스 스타일 */
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
    /* 하단 분석 스크립트 박스 */
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
# 2. 풀 스크린 5x5 그리드용 별자리 시각화 엔진
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
        fillcolor='rgba(56, 189, 248, 0.18)', line=dict(color='#38BDF8', width=2.5),
        mode='lines+markers',
        marker=dict(
            size=[11 if c == max_cat else 6 for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
            color=['#FBBF24' if c == max_cat else '#38BDF8' for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
            symbol='star'
        ),
        text=[f"{comp_names[c]}: {scores[c]}점" for c in ['A', 'B', 'C', 'D', 'E', 'F', 'A']],
        hoverinfo='text'
    ))
    
    # 화면을 넓게 쓰기 때문에 폰트와 스케일을 시원하게 업그레이드
    fig.update_layout(
        polar=dict(
            bgcolor='rgb(9, 13, 24)',
            radialaxis=dict(visible=True, range=[0, 5.2], showline=False, gridcolor='rgba(255,255,255,0.06)', angle=90, tickfont=dict(color='gray', size=9)),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont=dict(color='#ECF0F1', size=11, fontweight='bold'), rotation=90, direction="clockwise")
        ),
        showlegend=False, margin=dict(l=30, r=30, t=30, b=30),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320 # 차트 크기를 조금 더 키움
    )
    return fig, max_cat, min_cat, comp_names


# ==========================================
# 3. 상단 대시보드 및 5x5 그리드 구현
# ==========================================

st.title("🌌 25인 디지털 교육 역량 별자리 은하 지도 [5 × 5 Full-Screen]")

# 🛠️ 화면 상단에 정렬되는 제어 대시보드 패널 생성
st.markdown('<div class="control-panel">', unsafe_allow_html=True)
top_col1, top_col2 = st.columns([1, 3])

with top_col1:
    use_demo = st.checkbox("🎁 25인 가상 데모 시뮬레이션 작동", value=True)

with top_col2:
    if not use_demo:
        sheets_url = st.text_input("📂 연동할 구글 스프레드시트 링크 입력", value="https://docs.google.com/spreadsheets/d/1oITSnXoXMDP8Dbs_L5ZLvwRbhYB6qm2fruyjES3jDfM/edit?usp=sharing")
    else:
        st.markdown("<p style='color:#A78BFA; padding-top:8px; margin:0; font-size:14px;'>현재 시뮬레이션 은하계가 가동 중입니다. 실무 데이터 연동 시 왼쪽 체크박스를 꺼주세요.</p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 데이터 로드 프로세스
df_data = None
if not use_demo:
    if sheets_url:
        with st.spinner("🌌 성간 데이터 센터와 실시간 동기화 중..."):
            df_data = load_data_from_google_sheet(sheets_url)
else:
    demo_rows = []
    for i in range(1, 26):
        demo_rows.append({
            "이름": f"참여자 {i:02d}", "학교": "선도학교",
            "A_score": np.round(np.random.uniform(2.0, 5.0), 1), "B_score": np.round(np.random.uniform(2.0, 5.0), 1),
            "C_score": np.round(np.random.uniform(2.0, 5.0), 1), "D_score": np.round(np.random.uniform(2.0, 5.0), 1),
            "E_score": np.round(np.random.uniform(2.0, 5.0), 1), "F_score": np.round(np.random.uniform(2.0, 5.0), 1)
        })
    df_data = pd.DataFrame(demo_rows)

# 시각화 화면 렌더링 (그아래 넓게 배치)
if df_data is not None:
    df_data = df_data.head(25)
    
    with st.expander("📂 원본 데이터베이스 테이블 확인"):
        st.dataframe(df_data, use_container_width=True)
        
    # 🌟 화면 전체를 꽉 채우는 완전한 5열(Columns) 스크린 전개
    grid_cols = st.columns(5)
    
    for idx, row in df_data.iterrows():
        # 인덱스를 5로 나눈 나머지로 정확하게 바둑판 정렬 구현
        col = grid_cols[idx % 5]
        
        with col:
            # 이름 설정 로직
            name_val = row.iloc[1] if use_demo is False else row["이름"]
            name = str(name_val).strip() if (pd.notna(name_val) and str(name_val).strip() != "") else f"참여자 {idx+1:02d}"
            
            school_info = ""
            if not use_demo and len(row) > 2 and '학교' in df_data.columns:
                school_info = f" ({row['학교']})"
            
            scores = {
                'A': float(row['A_score']), 'B': float(row['B_score']), 'C': float(row['C_score']),
                'D': float(row['D_score']), 'E': float(row['E_score']), 'F': float(row['F_score'])
            }
            
            fig, max_cat, min_cat, comp_names = draw_beautiful_constellation(name, scores)
            
            # 카드 타이틀 바
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
