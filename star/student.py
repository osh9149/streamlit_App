import streamlit as st
import plotly.graph_objects as go

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="연수과정 돌아보기",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================================================
# 데이터
# =========================================================
competencies = [
    {
        "code": "A",
        "icon": "①",
        "title": "본질 이해",
        "subtitle": "AI 시대 교육 방향·역할 매트릭스",
        "description": "AI 시대 교육의 본질과 역할을 이해하는 역량",
        "prompt": "AI 시대 교육의 본질과 내 역할 변화에 대해 한 줄로 남겨주세요.",
        "color": "#4F67E8",
    },
    {
        "code": "B",
        "icon": "②③",
        "title": "가치관·윤리",
        "subtitle": "가치관 선언문·윤리 체크리스트",
        "description": "가치관 선언과 윤리적 기준을 세우는 역량",
        "prompt": "나만의 교육 가치관과 윤리적 기준에 대한 한 줄 회고를 적어주세요.",
        "color": "#5BA4E6",
    },
    {
        "code": "C",
        "icon": "④",
        "title": "데이터·설계",
        "subtitle": "데이터 해석·수업 설계 구조",
        "description": "데이터를 해석하고 수업 설계 뼈대를 세우는 역량",
        "prompt": "데이터를 해석하고 수업 설계를 구성하며 배운 점을 적어주세요.",
        "color": "#62B8A9",
    },
    {
        "code": "D",
        "icon": "⑤",
        "title": "도구·평가",
        "subtitle": "도구 활용·과정중심평가 설계",
        "description": "도구를 맥락에 맞게 활용하고 과정중심평가를 설계하는 역량",
        "prompt": "도구 활용과 과정중심평가 설계에서 느낀 점을 적어주세요.",
        "color": "#6861EF",
    },
    {
        "code": "E",
        "icon": "⑥",
        "title": "집합 실행",
        "subtitle": "팀 설계·마이크로티칭 실행",
        "description": "팀을 설계하고 마이크로티칭을 실행하는 역량",
        "prompt": "팀 설계와 마이크로티칭 실행 과정에서 배운 점을 적어주세요.",
        "color": "#8558F4",
    },
    {
        "code": "F",
        "icon": "⑦",
        "title": "분석·환류",
        "subtitle": "학습 데이터 분석·환류 설계",
        "description": "학습 데이터를 분석하고 환류를 설계하는 역량",
        "prompt": "학습 데이터 분석과 환류 설계에 대한 한 줄 회고를 적어주세요.",
        "color": "#4B9C8F",
    },
]

# =========================================================
# 세션 상태
# =========================================================
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "score"

if "scores" not in st.session_state:
    st.session_state.scores = {}

if "show_result" not in st.session_state:
    st.session_state.show_result = False

# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --page-bg: #F6F8FC;
        --card-border: #DFE5EF;
        --text-main: #202A3D;
        --text-sub: #748099;
        --primary: #4F67E8;
    }

    .stApp {
        background: var(--page-bg);
    }

    .block-container {
        max-width: 930px;
        padding-top: 46px;
        padding-bottom: 80px;
    }

    header, footer, #MainMenu {
        visibility: hidden;
    }

    /* 상단 */
    .top-icon-wrap {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }

    .top-icon {
        width: 70px;
        height: 70px;
        border-radius: 18px;
        background: var(--primary);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 32px;
        box-shadow: 0 12px 24px rgba(79, 103, 232, 0.22);
    }

    .page-title {
        text-align: center;
        color: #19233A;
        font-size: 2.15rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        margin-bottom: 12px;
    }

    .page-description {
        max-width: 650px;
        margin: 0 auto 44px;
        color: #66728A;
        text-align: center;
        font-size: 1rem;
        line-height: 1.85;
    }

    /* 탭 */
    .tab-shell {
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 18px;
        padding: 8px;
        box-shadow: 0 8px 20px rgba(30, 41, 59, 0.08);
        margin-bottom: 28px;
    }

    .stButton > button {
        border-radius: 14px;
        min-height: 54px;
        font-size: 0.98rem;
        font-weight: 800;
        border: 1px solid #DDE3ED;
        background: #F9FAFC;
        color: #4B5568;
        transition: all 0.18s ease;
    }

    .stButton > button:hover {
        border-color: var(--primary);
        color: var(--primary);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: var(--primary);
        color: #FFFFFF;
        border-color: var(--primary);
        box-shadow: 0 8px 18px rgba(79, 103, 232, 0.20);
    }

    /* 진행 상태 */
    .status-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 15px;
        padding: 14px 20px;
        box-shadow: 0 7px 18px rgba(30, 41, 59, 0.07);
        margin-bottom: 34px;
    }

    .status-left {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #60708B;
        font-size: 0.93rem;
        font-weight: 700;
    }

    .step-dot {
        width: 29px;
        height: 10px;
        border-radius: 999px;
        background: #E4E9F2;
        display: inline-block;
    }

    .step-dot.active {
        background: var(--primary);
    }

    .status-right {
        padding-left: 18px;
        border-left: 2px solid #E4E9F2;
        color: #60708B;
        font-size: 0.93rem;
        font-weight: 700;
    }

    /* 섹션 제목 */
    .section-title {
        color: var(--text-main);
        font-size: 1.25rem;
        font-weight: 900;
        margin-bottom: 8px;
    }

    .section-description {
        color: #71809A;
        font-size: 0.95rem;
        margin-bottom: 28px;
    }

    /* st.container(border=True)를 카드로 사용 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF;
        border: 1px solid var(--card-border) !important;
        border-radius: 20px !important;
        box-shadow: 0 9px 24px rgba(30, 41, 59, 0.08);
        padding: 0 !important;
        margin-bottom: 24px;
        overflow: hidden;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 26px 30px 22px !important;
    }

    /* 카드 헤더 */
    .reflection-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 17px;
    }

    .reflection-icon {
        width: 55px;
        height: 55px;
        border-radius: 14px;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.94rem;
        font-weight: 900;
        flex-shrink: 0;
    }

    .reflection-meta {
        min-width: 0;
    }

    .reflection-title {
        color: #273044;
        font-size: 1.06rem;
        font-weight: 900;
        margin-bottom: 5px;
    }

    .reflection-subtitle {
        color: #748099;
        font-size: 0.88rem;
        line-height: 1.45;
    }

    /* 회고 입력창 */
    div[data-testid="stTextArea"] {
        margin: 0 !important;
    }

    div[data-testid="stTextArea"] textarea {
        min-height: 90px !important;
        height: 90px !important;
        border-radius: 15px !important;
        border: 1px solid #DCE3ED !important;
        background: #F8FAFD !important;
        color: #273044 !important;
        font-size: 0.96rem !important;
        line-height: 1.65 !important;
        padding: 17px 19px !important;
        resize: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(79, 103, 232, 0.10) !important;
        outline: none !important;
    }

    div[data-testid="stTextArea"] textarea::placeholder {
        color: #A3AEC0 !important;
        opacity: 1 !important;
    }

    /* Streamlit 기본 글자 수 숨김 */
    div[data-testid="stTextArea"] small {
        display: none !important;
    }

    .char-count {
        text-align: right;
        color: #9AA6BA;
        font-size: 0.88rem;
        font-weight: 700;
        margin-top: 7px;
    }

    /* 점수 카드 */
    .score-info {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .score-title {
        color: #273044;
        font-size: 1.05rem;
        font-weight: 900;
        margin-bottom: 5px;
    }

    .score-desc {
        color: #748099;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    /* 결과 */
    .constellation-wrap {
        background: #080B16;
        border: 1px solid #1D2436;
        border-radius: 22px;
        padding: 18px 18px 22px;
        margin-top: 24px;
        box-shadow: 0 14px 34px rgba(8, 11, 22, 0.22);
    }

    .result-heading {
        text-align: center;
        color: #FFFFFF;
        font-size: 1.25rem;
        font-weight: 900;
        margin: 6px 0 2px;
    }

    .result-subheading {
        text-align: center;
        color: #A8B0C3;
        font-size: 0.87rem;
    }

    .analysis-card {
        background: #101421;
        border: 1px dashed #2B3245;
        border-radius: 13px;
        padding: 17px 20px;
        margin-top: 8px;
        color: #F8FAFC;
        line-height: 1.75;
        font-size: 0.98rem;
    }

    .analysis-strength {
        color: #FFD166;
        font-weight: 900;
    }

    .analysis-growth {
        color: #FF6B8A;
        font-weight: 900;
    }

    @media (max-width: 700px) {
        .block-container {
            padding: 24px 14px 60px;
        }

        .page-title {
            font-size: 1.75rem;
        }

        .page-description {
            font-size: 0.92rem;
        }

        .step-dot {
            width: 18px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 22px 18px 18px !important;
        }

        .reflection-icon {
            width: 50px;
            height: 50px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 상단 영역
# =========================================================
st.markdown(
    """
    <div class="top-icon-wrap">
        <div class="top-icon">✓</div>
    </div>
    <div class="page-title">연수과정 돌아보기</div>
    <div class="page-description">
        이번 연수를 지나오며 내가 느낀 성장의 깊이를 점수로 표현해보고,
        과정별 배움을 한 줄 회고로 남겨보세요.
        모든 작성이 끝나면 나만의 회고 대시보드와 카드가 완성됩니다.
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 탭
# =========================================================
st.markdown('<div class="tab-shell">', unsafe_allow_html=True)
tab1, tab2 = st.columns(2)

with tab1:
    if st.button(
        "▥  역량 점수 평가",
        use_container_width=True,
        type="primary" if st.session_state.active_tab == "score" else "secondary",
    ):
        st.session_state.active_tab = "score"
        st.rerun()

with tab2:
    if st.button(
        "✎  한 줄 회고",
        use_container_width=True,
        type="primary" if st.session_state.active_tab == "reflection" else "secondary",
    ):
        st.session_state.active_tab = "reflection"
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 진행률
# =========================================================
score_count = len(st.session_state.scores)
reflection_count = sum(
    1
    for item in competencies
    if st.session_state.get(f"reflection_{item['code']}", "").strip()
)

dots = ""
current_count = score_count if st.session_state.active_tab == "score" else reflection_count

for i in range(6):
    active = "active" if i < current_count else ""
    dots += f'<span class="step-dot {active}"></span>'

st.markdown(
    f"""
    <div class="status-card">
        <div class="status-left">
            {dots}
            <span style="margin-left:4px;">
                {'역량' if st.session_state.active_tab == 'score' else '회고'}
                {current_count}/6
            </span>
        </div>
        <div class="status-right">
            {'회고' if st.session_state.active_tab == 'score' else '역량'}
            {reflection_count if st.session_state.active_tab == 'score' else score_count}/6
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 역량 점수 평가 탭
# =========================================================
if st.session_state.active_tab == "score":
    st.markdown(
        """
        <div class="section-title">역량 점수 평가</div>
        <div class="section-description">
            각 역량 항목에 대해 1~5점을 선택해주세요. (1: 미흡 ~ 5: 최우수)
        </div>
        """,
        unsafe_allow_html=True,
    )

    for item in competencies:
        with st.container(border=True):
            left, right = st.columns([1.35, 1])

            with left:
                st.markdown(
                    f"""
                    <div class="score-info">
                        <div class="reflection-icon" style="background:{item['color']};">
                            {item['code']}
                        </div>
                        <div>
                            <div class="score-title">{item['title']}</div>
                            <div class="score-desc">{item['description']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with right:
                cols = st.columns(5)
                for score in range(1, 6):
                    with cols[score - 1]:
                        selected = st.session_state.scores.get(item["code"]) == score
                        if st.button(
                            str(score),
                            key=f"score_{item['code']}_{score}",
                            type="primary" if selected else "secondary",
                            use_container_width=True,
                        ):
                            st.session_state.scores[item["code"]] = score
                            st.session_state.show_result = False
                            st.rerun()

    if st.button("결과 보기", use_container_width=True, type="primary"):
        if len(st.session_state.scores) < 6:
            st.warning("6개 역량의 점수를 모두 선택해 주세요.")
        else:
            st.session_state.show_result = True

    if st.session_state.show_result:
        average = sum(st.session_state.scores.values()) / 6
        max_score = max(st.session_state.scores.values())
        min_score = min(st.session_state.scores.values())

        strengths = [
            item for item in competencies
            if st.session_state.scores[item["code"]] == max_score
        ]
        growths = [
            item for item in competencies
            if st.session_state.scores[item["code"]] == min_score
        ]

        strength_text = ", ".join(
            f"{item['title']} ({max_score:.1f}점)" for item in strengths
        )
        growth_text = ", ".join(
            f"{item['title']} ({min_score:.1f}점)" for item in growths
        )

        categories = [item["code"] for item in competencies]
        scores = [st.session_state.scores[item["code"]] for item in competencies]

        closed_categories = categories + [categories[0]]
        closed_scores = scores + [scores[0]]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=[5] * 7,
                theta=closed_categories,
                mode="lines",
                line=dict(color="rgba(255,255,255,0.22)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatterpolar(
                r=closed_scores,
                theta=closed_categories,
                mode="lines+markers",
                fill="toself",
                fillcolor="rgba(91,176,255,0.22)",
                line=dict(color="#69B8FF", width=3),
                marker=dict(
                    size=[14 if s == max_score else 8 for s in closed_scores],
                    color=["#FFD166" if s == max_score else "#69B8FF" for s in closed_scores],
                    symbol=["star" if s == max_score else "circle" for s in closed_scores],
                    line=dict(color="#D8EEFF", width=1),
                ),
                text=[
                    f"{item['code']} · {item['title']}: "
                    f"{st.session_state.scores[item['code']]}점"
                    for item in competencies
                ] + [
                    f"{competencies[0]['code']} · {competencies[0]['title']}: "
                    f"{st.session_state.scores[competencies[0]['code']]}점"
                ],
                hovertemplate="%{text}<extra></extra>",
                showlegend=False,
            )
        )

        fig.update_layout(
            height=430,
            margin=dict(l=52, r=52, t=45, b=35),
            paper_bgcolor="#080B16",
            plot_bgcolor="#080B16",
            font=dict(color="#F8FAFC", size=14),
            polar=dict(
                bgcolor="#080B16",
                radialaxis=dict(
                    visible=True,
                    range=[0, 5.2],
                    tickvals=[0, 1, 2, 3, 4, 5],
                    gridcolor="rgba(255,255,255,0.10)",
                    tickfont=dict(color="rgba(255,255,255,0.55)", size=10),
                    angle=90,
                ),
                angularaxis=dict(
                    tickfont=dict(color="#FFFFFF", size=14),
                    gridcolor="rgba(255,255,255,0.13)",
                    rotation=90,
                    direction="clockwise",
                ),
            ),
        )

        st.markdown(
            f"""
            <div class="constellation-wrap">
                <div class="result-heading">나의 역량 별자리</div>
                <div class="result-subheading">전체 평균 {average:.1f}점 · 5점 만점</div>
            """,
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown(
            f"""
                <div class="analysis-card">
                    🥇 <span class="analysis-strength">강점:</span> {strength_text}<br>
                    🎯 <span class="analysis-growth">보완:</span> {growth_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =========================================================
# 한 줄 회고 탭
# =========================================================
else:
    st.markdown(
        """
        <div class="section-title">과정별 한 줄 회고</div>
        <div class="section-description">
            각 과정의 핵심 배움을 확인하고, 한 줄로 회고를 작성해주세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for item in competencies:
        key = f"reflection_{item['code']}"

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="reflection-header">
                    <div class="reflection-icon" style="background:{item['color']};">
                        {item['icon']}
                    </div>
                    <div class="reflection-meta">
                        <div class="reflection-title">{item['title']}</div>
                        <div class="reflection-subtitle">{item['subtitle']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            value = st.text_area(
                f"{item['title']} 회고",
                value=st.session_state.get(key, ""),
                placeholder=item["prompt"],
                max_chars=120,
                height=90,
                key=key,
                label_visibility="collapsed",
            )

            st.markdown(
                f'<div class="char-count">{len(value)} / 120</div>',
                unsafe_allow_html=True,
            )

    if st.button(
        "회고 작성 완료",
        use_container_width=True,
        type="primary",
    ):
        completed = sum(
            1
            for item in competencies
            if st.session_state.get(f"reflection_{item['code']}", "").strip()
        )

        if completed < 6:
            st.warning("6개 항목의 한 줄 회고를 모두 작성해 주세요.")
        else:
            st.success("한 줄 회고 작성이 완료되었습니다.")
