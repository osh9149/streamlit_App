import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(
    page_title="글로벌 시가총액 Top 10 주식 대시보드",
    page_icon="📈",
    layout="wide"
)

st.title("📈 글로벌 시가총액 Top 10 주식 대시보드")
st.markdown("최근 1년 동안의 글로벌 탑 기업들의 주가 추이와 누적 수익률을 비교합니다.")

# 2. 글로벌 시가총액 Top 10 기업 데이터 정의 (티커 및 기업명)
# * 시가총액 순위는 시장 상황에 따라 변동될 수 있습니다.
ticker_dict = {
    "Microsoft (MSFT)": "MSFT",
    "Apple (AAPL)": "AAPL",
    "NVIDIA (NVDA)": "NVDA",
    "Alphabet / Google (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN",
    "Saudi Aramco (2222.SR)": "2222.SR",
    "Meta Platforms (META)": "META",
    "TSMC (TSM)": "TSM",
    "Berkshire Hathaway (BRK-B)": "BRK-B",
    "Tesla (TSLA)": "TSLA"
}

# 사이드바 설정
st.sidebar.header("🔍 설정")
selected_companies = st.sidebar.multiselect(
    "비교할 기업을 선택하세요 (다중 선택 가능):",
    options=list(ticker_dict.keys()),
    default=list(ticker_dict.keys())[:5]  # 기본값으로 상위 5개 선택
)

# 데이터 기간 설정 (최근 1년)
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 데이터 수집 함수 (캐싱 처리로 속도 향상)
@st.cache_data(ttl=3600)
def load_data(tickers, start, end):
    data = pd.DataFrame()
    for name, ticker in tickers.items():
        try:
            stock = yf.download(ticker, start=start, end=end)
            if not stock.empty:
                # yfinance의 MultiIndex 또는 단일 종가 처리 안전하게 호환
                close_prices = stock['Close']
                if isinstance(close_prices, pd.DataFrame):
                    close_prices = close_prices.iloc[:, 0]
                data[name] = close_prices
        except Exception as e:
            st.error(f"{name} 데이터를 가져오는 중 오류 발생: {e}")
    return data

# 3. 데이터 로드 및 시각화
if selected_companies:
    # 선택된 기업의 티커 딕셔너리 필터링
    filtered_tickers = {k: ticker_dict[k] for k in selected_companies}
    
    with st.spinner("야후 파이낸스에서 데이터를 가져오는 중..."):
        df = load_data(filtered_tickers, start_date, end_date)
    
    if not df.empty:
        # 결측치 처리 (주말/휴일 등 국가별 시장 차이 보정)
        df = df.ffill().bfill()
        
        # 탭을 나누어 두 가지 형태의 차트 제공
        tab1, tab2, tab3 = st.tabs(["📊 수정종가 기준 추이", "📈 누적 수익률 (%)", "📋 데이터 테이블"])
        
        # Tab 1: 단순 주가 추이
        with tab1:
            st.subheader("일별 수정종가 (USD / 해당국가 통화)")
            fig1 = go.Figure()
            for col in df.columns:
                fig1.add_trace(go.Scatter(x=df.index, y=df[col], mode='l', name=col))
            
            fig1.update_layout(
                hovermode="x unified",
                xaxis_title="날짜",
                yaxis_title="주가",
                margin=dict(l=20, r=20, t=20, b=20),
                height=600
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        # Tab 2: 누적 수익률 비교 (첫 거래일 기준 0%로 맞춤)
        with tab2:
            st.subheader("1년 전 대비 누적 수익률 비교")
            df_returns = ((df / df.iloc[0]) - 1) * 100
            
            fig2 = go.Figure()
            for col in df_returns.columns:
                fig2.add_trace(go.Scatter(x=df_returns.index, y=df[col], mode='l', name=col))
                
            fig2.update_layout(
                hovermode="x unified",
                xaxis_title="날짜",
                yaxis_title="수익률 (%)",
                margin=dict(l=20, r=20, t=20, b=20),
                height=600
            )
            st.plotly_chart(fig2, use_container_width=True)
            
        # Tab 3: Raw Data
        with tab3:
            st.subheader("최근 데이터 확인")
            st.dataframe(df.tail(30), use_container_width=True)
            
    else:
        st.warning("데이터를 불러오지 못했습니다. 티커나 네트워크 상태를 확인하세요.")
else:
    st.info("왼쪽 사이드바에서 비교할 기업을 하나 이상 선택해 주세요.")
