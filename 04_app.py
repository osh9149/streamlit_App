import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="글로벌 시가총액 TOP 10 주식 대시보드",
    page_icon="📈",
    layout="wide",
)

# 상위 기업 순위는 시점에 따라 달라질 수 있습니다.
# 아래 목록은 앱에서 비교할 글로벌 초대형 상장기업 10개입니다.
# 필요하면 기업명과 티커를 수정하세요.
COMPANIES = {
    "NVIDIA": "NVDA",
    "Apple": "AAPL",
    "Alphabet": "GOOG",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Broadcom": "AVGO",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "TSMC": "TSM",
    "Tesla": "TSLA",
}

TICKER_TO_NAME = {ticker: name for name, ticker in COMPANIES.items()}


# ---------------------------------------------------------
# 화면 스타일
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f7fb;
    }
    .main-title {
        font-size: 2.25rem;
        font-weight: 800;
        color: #172033;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #657086;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }
    .info-box {
        background: white;
        border: 1px solid #e4e8f0;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 16px;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e4e8f0;
        border-radius: 14px;
        padding: 14px;
    }
    div[data-testid="stPlotlyChart"] {
        background: white;
        border-radius: 14px;
        padding: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">🌍 글로벌 시가총액 TOP 10 주식 대시보드</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">최근 1년 주가 변화, 누적수익률, 거래량과 개별 종목 흐름을 비교합니다.</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_stock_data(tickers, start_date, end_date):
    """Yahoo Finance에서 여러 종목의 최근 주가 데이터를 내려받습니다."""
    raw = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date + timedelta(days=1),
        auto_adjust=False,
        progress=False,
        group_by="column",
        threads=True,
    )

    if raw.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def extract_field(field):
        if isinstance(raw.columns, pd.MultiIndex):
            if field not in raw.columns.get_level_values(0):
                return pd.DataFrame()
            frame = raw[field].copy()
        else:
            if field not in raw.columns:
                return pd.DataFrame()
            frame = raw[[field]].copy()
            frame.columns = [tickers[0]]

        if isinstance(frame, pd.Series):
            frame = frame.to_frame()

        return frame.sort_index().dropna(how="all")

    close = extract_field("Close")
    open_price = extract_field("Open")
    high = extract_field("High")
    low = extract_field("Low")
    volume = extract_field("Volume")

    # 수정주가가 있으면 장기 수익률 계산에는 수정주가를 우선 사용
    adj_close = extract_field("Adj Close")
    if adj_close.empty:
        adj_close = close.copy()

    return close, adj_close, volume, pd.concat(
        {"Open": open_price, "High": high, "Low": low, "Close": close},
        axis=1,
    )


def first_valid(series):
    valid = series.dropna()
    return valid.iloc[0] if not valid.empty else np.nan


def last_valid(series):
    valid = series.dropna()
    return valid.iloc[-1] if not valid.empty else np.nan


def make_summary(adj_close):
    rows = []

    for ticker in adj_close.columns:
        series = adj_close[ticker].dropna()
        if len(series) < 2:
            continue

        first_price = series.iloc[0]
        last_price = series.iloc[-1]
        annual_return = (last_price / first_price - 1) * 100

        daily_returns = series.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        max_price = series.max()
        min_price = series.min()

        rows.append(
            {
                "기업": TICKER_TO_NAME.get(ticker, ticker),
                "티커": ticker,
                "시작 종가": first_price,
                "최근 종가": last_price,
                "1년 수익률(%)": annual_return,
                "연환산 변동성(%)": volatility,
                "1년 최고가": max_price,
                "1년 최저가": min_price,
            }
        )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values("1년 수익률(%)", ascending=False)


# ---------------------------------------------------------
# 사이드바
# ---------------------------------------------------------
today = datetime.now().date()
default_start = today - timedelta(days=365)

with st.sidebar:
    st.header("⚙️ 조회 설정")

    selected_names = st.multiselect(
        "비교할 기업",
        options=list(COMPANIES.keys()),
        default=list(COMPANIES.keys()),
    )

    start_date = st.date_input(
        "시작일",
        value=default_start,
        max_value=today,
    )
    end_date = st.date_input(
        "종료일",
        value=today,
        min_value=start_date,
        max_value=today,
    )

    chart_mode = st.radio(
        "기본 비교 방식",
        ["누적 변화율", "실제 종가"],
        index=0,
    )

    st.caption("데이터는 Yahoo Finance에서 가져오며 최대 1시간 동안 캐시됩니다.")

if not selected_names:
    st.warning("사이드바에서 한 개 이상의 기업을 선택해 주세요.")
    st.stop()

selected_tickers = [COMPANIES[name] for name in selected_names]

with st.spinner("주식 데이터를 불러오는 중입니다..."):
    close, adj_close, volume, ohlc = load_stock_data(
        selected_tickers,
        start_date,
        end_date,
    )

if adj_close.empty:
    st.error(
        "주가 데이터를 불러오지 못했습니다. 잠시 후 새로고침하거나 "
        "조회 기간과 종목 티커를 확인해 주세요."
    )
    st.stop()

# 실제로 데이터가 내려온 티커만 유지
available_tickers = [ticker for ticker in selected_tickers if ticker in adj_close.columns]
adj_close = adj_close[available_tickers].dropna(how="all")
close = close.reindex(columns=available_tickers)
volume = volume.reindex(columns=available_tickers)

summary = make_summary(adj_close)

if summary.empty:
    st.error("비교에 사용할 충분한 데이터가 없습니다.")
    st.stop()


# ---------------------------------------------------------
# 핵심 지표
# ---------------------------------------------------------
best = summary.iloc[0]
worst = summary.iloc[-1]
average_return = summary["1년 수익률(%)"].mean()
average_volatility = summary["연환산 변동성(%)"].mean()

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "수익률 1위",
    best["기업"],
    f'{best["1년 수익률(%)"]:.2f}%',
)
metric2.metric(
    "수익률 최하위",
    worst["기업"],
    f'{worst["1년 수익률(%)"]:.2f}%',
)
metric3.metric(
    "평균 수익률",
    f"{average_return:.2f}%",
)
metric4.metric(
    "평균 변동성",
    f"{average_volatility:.2f}%",
)

st.markdown("### 📊 최근 1년 주가 비교")

# ---------------------------------------------------------
# 종합 비교 차트
# ---------------------------------------------------------
if chart_mode == "누적 변화율":
    normalized = adj_close.apply(
        lambda col: col / first_valid(col) * 100 if pd.notna(first_valid(col)) else col
    )
    chart_df = (
        normalized.rename(columns=TICKER_TO_NAME)
        .reset_index()
        .melt(id_vars="Date", var_name="기업", value_name="지수")
    )

    fig_main = px.line(
        chart_df,
        x="Date",
        y="지수",
        color="기업",
        labels={"Date": "날짜", "지수": "기준 지수", "기업": "기업"},
        title="첫 거래일을 100으로 환산한 주가 변화",
    )
    fig_main.add_hline(
        y=100,
        line_dash="dash",
        line_color="gray",
        annotation_text="기준값 100",
    )
else:
    price_df = (
        adj_close.rename(columns=TICKER_TO_NAME)
        .reset_index()
        .melt(id_vars="Date", var_name="기업", value_name="종가")
    )

    fig_main = px.line(
        price_df,
        x="Date",
        y="종가",
        color="기업",
        labels={"Date": "날짜", "종가": "종가", "기업": "기업"},
        title="기업별 실제 종가 변화",
    )

fig_main.update_layout(
    height=570,
    hovermode="x unified",
    legend_title_text="기업",
    margin=dict(l=20, r=20, t=60, b=20),
)
fig_main.update_xaxes(rangeslider_visible=True)
st.plotly_chart(fig_main, use_container_width=True)


# ---------------------------------------------------------
# 수익률 및 변동성
# ---------------------------------------------------------
left, right = st.columns(2)

with left:
    return_fig = px.bar(
        summary.sort_values("1년 수익률(%)"),
        x="1년 수익률(%)",
        y="기업",
        orientation="h",
        text_auto=".2f",
        title="기간 수익률 순위",
    )
    return_fig.add_vline(x=0, line_color="gray", line_dash="dash")
    return_fig.update_layout(
        height=470,
        xaxis_title="수익률(%)",
        yaxis_title="",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(return_fig, use_container_width=True)

with right:
    risk_return_fig = px.scatter(
        summary,
        x="연환산 변동성(%)",
        y="1년 수익률(%)",
        text="티커",
        hover_name="기업",
        size=np.maximum(summary["연환산 변동성(%)"], 1),
        title="위험 대비 수익률",
    )
    risk_return_fig.add_hline(y=0, line_color="gray", line_dash="dash")
    risk_return_fig.update_traces(textposition="top center")
    risk_return_fig.update_layout(
        height=470,
        xaxis_title="연환산 변동성(%)",
        yaxis_title="기간 수익률(%)",
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )
    st.plotly_chart(risk_return_fig, use_container_width=True)


# ---------------------------------------------------------
# 개별 종목 상세 분석
# ---------------------------------------------------------
st.markdown("### 🔎 개별 종목 상세 분석")

detail_name = st.selectbox(
    "상세 종목 선택",
    options=[TICKER_TO_NAME[ticker] for ticker in available_tickers],
)
detail_ticker = COMPANIES[detail_name]

detail_close = close[detail_ticker].dropna()
detail_volume = volume[detail_ticker].dropna() if detail_ticker in volume.columns else pd.Series(dtype=float)

if isinstance(ohlc.columns, pd.MultiIndex):
    try:
        detail_ohlc = pd.DataFrame(
            {
                "Open": ohlc[("Open", detail_ticker)],
                "High": ohlc[("High", detail_ticker)],
                "Low": ohlc[("Low", detail_ticker)],
                "Close": ohlc[("Close", detail_ticker)],
            }
        ).dropna()
    except KeyError:
        detail_ohlc = pd.DataFrame()
else:
    detail_ohlc = pd.DataFrame()

detail_row = summary.loc[summary["티커"] == detail_ticker].iloc[0]

d1, d2, d3, d4 = st.columns(4)
d1.metric("최근 종가", f'{detail_row["최근 종가"]:,.2f}')
d2.metric("기간 수익률", f'{detail_row["1년 수익률(%)"]:.2f}%')
d3.metric("기간 최고가", f'{detail_row["1년 최고가"]:,.2f}')
d4.metric("기간 최저가", f'{detail_row["1년 최저가"]:,.2f}')

if not detail_ohlc.empty:
    candle = go.Figure(
        data=[
            go.Candlestick(
                x=detail_ohlc.index,
                open=detail_ohlc["Open"],
                high=detail_ohlc["High"],
                low=detail_ohlc["Low"],
                close=detail_ohlc["Close"],
                name=detail_name,
            )
        ]
    )
    candle.update_layout(
        title=f"{detail_name} ({detail_ticker}) 캔들 차트",
        xaxis_title="날짜",
        yaxis_title="가격",
        height=520,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(candle, use_container_width=True)
else:
    fallback = px.line(
        x=detail_close.index,
        y=detail_close.values,
        labels={"x": "날짜", "y": "종가"},
        title=f"{detail_name} ({detail_ticker}) 종가",
    )
    st.plotly_chart(fallback, use_container_width=True)

if not detail_volume.empty:
    volume_fig = px.bar(
        x=detail_volume.index,
        y=detail_volume.values,
        labels={"x": "날짜", "y": "거래량"},
        title=f"{detail_name} 거래량",
    )
    volume_fig.update_layout(
        height=330,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(volume_fig, use_container_width=True)


# ---------------------------------------------------------
# 데이터 표와 다운로드
# ---------------------------------------------------------
st.markdown("### 📋 종목별 요약")

display_summary = summary.copy()
numeric_columns = [
    "시작 종가",
    "최근 종가",
    "1년 수익률(%)",
    "연환산 변동성(%)",
    "1년 최고가",
    "1년 최저가",
]
display_summary[numeric_columns] = display_summary[numeric_columns].round(2)

st.dataframe(
    display_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "1년 수익률(%)": st.column_config.NumberColumn(format="%.2f%%"),
        "연환산 변동성(%)": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

csv = display_summary.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "📥 요약 데이터 CSV 다운로드",
    data=csv,
    file_name="global_top10_stock_summary.csv",
    mime="text/csv",
)

st.markdown(
    """
    <div class="info-box">
    <b>안내</b><br>
    • 시가총액 순위는 주가와 환율에 따라 계속 달라질 수 있습니다.<br>
    • Saudi Aramco는 사우디 거래소 티커 <code>2222.SR</code>를 사용합니다.<br>
    • 서로 다른 통화의 실제 종가를 직접 비교할 때는 주의해야 합니다.<br>
    • 이 대시보드는 교육용이며 투자 권유나 투자 자문이 아닙니다.
    </div>
    """,
    unsafe_allow_html=True,
)
