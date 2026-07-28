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
# 설문 항목
# =========================================================
competencies = [
    {
        "code": "A",
        "title": "본질 이해",
        "description": "AI 시대 교육의 본질과 역할을 이해하는 역량",
        "color": "#4F67E8",
    },
    {
        "code": "B",
        "title": "가치관·윤리",
        "description": "가치관 선언과 윤리적 기준을 세우는 역량",
        "color": "#5BA4E6",
    },
    {
        "code": "C",
        "title": "데이터·설계",
        "description": "데이터를 해석하고 수업 설계 뼈대를 세우는 역량",
        "color": "#62B8A9",
    },
    {
        "code": "D",
        "title": "도구·평가",
        "description": "도구를 맥락에 맞게 활용하고 과정중심평가를 설계하는 역량",
        "color": "#6861EF",
    },
    {
        "code": "E",
        "title": "집합 실행",
        "description": "팀을 설계하고 마이크로티칭을 실행하는 역량",
        "color": "#8558F4",
    },
    {
        "code": "F",
        "title": "분석·환류",
        "description": "학습 데이터를 분석하고 환류를 설계하는 역량",
        "color": "#4B9C8F",
    },
]

# =========================================================
# 세션 상태 초기화
# =========================================================
if "scores" not in st.session_state:
    st.session_state.scores = {}

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "score"

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>
    /* 전체 화면 */
    .stApp {
        background: #F6F8FC;
    }

    .block-container {
        max-width: 920px;
        padding-top: 48px;
        padding-bottom: 80px;
    }

    header,
    footer,
    #MainMenu {
        visibility: hidden;
    }

    /* 상단 아이콘 */
    .top-icon-wrap {
        display: flex;
        justify-content: center;
        margin-bottom: 22px;
    }

    .top-icon {
        width: 70px;
        height: 70px;
        border-radius: 19px;
        background: #4F67E8;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 34px;
        box-shadow: 0 12px 24px rgba(79, 103, 232, 0.23);
    }

    /* 제목 */
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
        margin: 0 auto 46px auto;
        color: #66728A;
        text-align: center;
        font-size: 1rem;
        line-height: 1.85;
    }

    /* 탭 박스 */
    .tab-shell {
        background: white;
        border: 1px solid #DFE5EF;
        border-radius: 18px;
        padding: 8px;
        box-shadow: 0 8px 20px rgba(30, 41, 59, 0.08);
        margin-bottom: 30px;
    }

    /* 진행 상태 */
    .status-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: white;
        border: 1px solid #DFE5EF;
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
        background: #4F67E8;
    }

    .status-right {
        padding-left: 18px;
        border-left: 2px solid #E4E9F2;
        color: #60708B;
        font-size: 0.93rem;
        font-weight: 700;
    }

    /* 섹션 */
    .section-title {
        color: #202A3D;
        font-size: 1.2rem;
        font-weight: 900;
        margin-bottom: 8px;
    }

    .section-description {
        color: #71809A;
        font-size: 0.93rem;
        margin-bottom: 28px;
    }

    /* 항목 카드 */
    .competency-card {
        background: white;
        border: 1px solid #DFE5EF;
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 22px;
        box-shadow: 0 8px 22px rgba(30, 41, 59, 0.08);
    }

    .card-info {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .letter-box {
        min-width: 52px;
        height: 52px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.05rem;
        font-weight: 900;
    }

    .competency-title {
        color: #273044;
        font-size: 1.05rem;
        font-weight: 900;
        margin-bottom: 6px;
    }

    .competency-desc {
        color: #748099;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    /* Streamlit 버튼 */
    .stButton > button {
        border-radius: 15px;
        min-height: 56px;
        font-size: 1rem;
        font-weight: 800;
        transition: all 0.2s ease;
        border: 1px solid #DDE3ED;
        background: #F9FAFC;
        color: #4B5568;
    }

    .stButton > button:hover {
        border-color: #4F67E8;
        color: #4F67E8;
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: #4F67E8;
        color: white;
        border-color: #4F67E8;
        box-shadow: 0 8px 18px rgba(79, 103, 232, 0.22);
    }

    /* 제출 버튼 */
    .submit-area {
        margin-top: 12px;
    }

    /* 결과 */
    .result-box {
        background: white;
        border: 1px solid #DFE5EF;
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 20px;
        box-shadow: 0 8px 22px rgba(30, 41, 59, 0.08);
    }

    .result-main {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 900;
        color: #4F67E8;
        margin-bottom: 8px;
    }

    .result-label {
        text-align: center;
        color: #6B778D;
        margin-bottom: 24px;
    }

    .result-row {
        display: flex;
        justify-content: space-between;
        padding: 14px 0;
        border-bottom: 1px solid #EEF1F6;
        color: #30394C;
        font-weight: 700;
    }

    .result-row:last-child {
        border-bottom: none;
    }

    .stars {
        color: #F5A524;
        letter-spacing: 2px;
    }


    .constellation-wrap {
        background: #080B16;
        border: 1px solid #1D2436;
        border-radius: 22px;
        padding: 18px 18px 22px 18px;
        margin-top: 24px;
        box-shadow: 0 14px 34px rgba(8, 11, 22, 0.22);
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

    .result-heading {
        text-align: center;
        color: white;
        font-size: 1.25rem;
        font-weight: 900;
        margin-top: 6px;
        margin-bottom: 2px;
    }

    .result-subheading {
        text-align: center;
        color: #A8B0C3;
        font-size: 0.87rem;
        margin-bottom: 2px;
    }

    /* 모바일 */
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

        .competency-card {
            padding: 20px;
        }

        .status-card {
            padding: 13px 14px;
        }

        .step-dot {
            width: 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 상단 제목
# =========================================================
st.markdown(
    """
    <div class="top-icon-wrap">
        <div class="top-icon">▣</div>
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
# 상단 탭
# =========================================================
st.markdown('<div class="tab-shell">', unsafe_allow_html=True)

tab_col1, tab_col2 = st.columns(2)

with tab_col1:
    if st.button(
        "▥  역량 점수 평가",
        use_container_width=True,
        type="primary" if st.session_state.active_tab == "score" else "secondary",
    ):
        st.session_state.active_tab = "score"
        st.rerun()

with tab_col2:
    if st.button(
        "✎  한 줄 회고",
        use_container_width=True,
        type="primary" if st.session_state.active_tab == "reflection" else "secondary",
    ):
        st.session_state.active_tab = "reflection"
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 진행 상태
# =========================================================
answered_count = len(st.session_state.scores)
reflection_count = sum(
    1
    for key, value in st.session_state.items()
    if key.startswith("reflection_") and str(value).strip()
)

dots_html = ""
for index in range(6):
    active_class = "active" if index < answered_count else ""
    dots_html += f'<span class="step-dot {active_class}"></span>'

st.markdown(
    f"""
    <div class="status-card">
        <div class="status-left">
            {dots_html}
            <span style="margin-left: 4px;">역량 {answered_count}/6</span>
        </div>
        <div class="status-right">
            회고 {reflection_count}/6
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 역량 점수 탭
# =========================================================
if st.session_state.active_tab == "score":

    st.markdown(
        """
        <div class="section-title">역량 점수 평가</div>
        <div class="section-description">
            각 역량 항목에 대해 1~5점을 선택해주세요.
            (1: 미흡 ~ 5: 최우수)
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, item in enumerate(competencies):

        st.markdown('<div class="competency-card">', unsafe_allow_html=True)

        info_col, score_col = st.columns([1.35, 1])

        with info_col:
            st.markdown(
                f"""
                <div class="card-info">
                    <div class="letter-box" style="background:{item['color']};">
                        {item['code']}
                    </div>
                    <div>
                        <div class="competency-title">{item['title']}</div>
                        <div class="competency-desc">{item['description']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with score_col:
            score_columns = st.columns(6)

            for score in range(1, 6):
                with score_columns[score - 1]:
                    selected = st.session_state.scores.get(item["code"]) == score

                    if st.button(
                        str(score),
                        key=f"{item['code']}_{score}",
                        use_container_width=True,
                        type="primary" if selected else "secondary",
                    ):
                        st.session_state.scores[item["code"]] = score
                        st.session_state.submitted = False
                        st.rerun()

            with score_columns[5]:
                current_value = st.session_state.scores.get(item["code"], "-")
                st.markdown(
                    f"""
                    <div style="
                        height:56px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        color:#8994A8;
                        font-weight:800;
                    ">
                        {current_value}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="submit-area">', unsafe_allow_html=True)

    if st.button(
        "결과 보기",
        use_container_width=True,
        type="primary",
    ):
        if len(st.session_state.scores) < 6:
            st.warning("6개 역량의 점수를 모두 선택해 주세요.")
        else:
            st.session_state.submitted = True

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.submitted:
        average = sum(st.session_state.scores.values()) / 6

        # 최고·최저 점수와 동점 역량 찾기
        max_score = max(st.session_state.scores.values())
        min_score = min(st.session_state.scores.values())

        strength_items = [
            item for item in competencies
            if st.session_state.scores[item["code"]] == max_score
        ]

        growth_items = [
            item for item in competencies
            if st.session_state.scores[item["code"]] == min_score
        ]

        strength_text = ", ".join(
            f"{item['title']} ({max_score:.1f}점)"
            for item in strength_items
        )

        growth_text = ", ".join(
            f"{item['title']} ({min_score:.1f}점)"
            for item in growth_items
        )

        # 별자리형 레이더 차트 데이터
        category_codes = [item["code"] for item in competencies]
        score_values = [
            st.session_state.scores[item["code"]]
            for item in competencies
        ]

        # 도형을 닫기 위해 첫 값을 마지막에 다시 추가
        closed_categories = category_codes + [category_codes[0]]
        closed_scores = score_values + [score_values[0]]

        marker_symbols = []

        for item in competencies:
            score = st.session_state.scores[item["code"]]

            if score == max_score:
                marker_symbols.append("star")
            else:
                marker_symbols.append("circle")

        marker_symbols.append(marker_symbols[0])

        fig = go.Figure()

        # 바깥 기준선
        fig.add_trace(
            go.Scatterpolar(
                r=[5] * 7,
                theta=closed_categories,
                mode="lines",
                line=dict(
                    color="rgba(255,255,255,0.22)",
                    width=1,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # 점수 별자리
        fig.add_trace(
            go.Scatterpolar(
                r=closed_scores,
                theta=closed_categories,
                mode="lines+markers",
                fill="toself",
                fillcolor="rgba(91, 176, 255, 0.22)",
                line=dict(
                    color="#69B8FF",
                    width=3,
                ),
                marker=dict(
                    size=[
                        14 if score == max_score else 8
                        for score in closed_scores
                    ],
                    color=[
                        "#FFD166" if score == max_score else "#69B8FF"
                        for score in closed_scores
                    ],
                    symbol=marker_symbols,
                    line=dict(
                        color="#D8EEFF",
                        width=1,
                    ),
                ),
                text=[
                    f"{item['code']} · {item['title']}: "
                    f"{st.session_state.scores[item['code']]}점"
                    for item in competencies
                ] + [
                    f"{competencies[0]['code']} · "
                    f"{competencies[0]['title']}: "
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
            font=dict(
                color="#F8FAFC",
                size=14,
            ),
            polar=dict(
                bgcolor="#080B16",
                radialaxis=dict(
                    visible=True,
                    range=[0, 5.2],
                    tickmode="array",
                    tickvals=[0, 1, 2, 3, 4, 5],
                    ticktext=["0", "1", "2", "3", "4", "5"],
                    tickfont=dict(
                        color="rgba(255,255,255,0.55)",
                        size=10,
                    ),
                    gridcolor="rgba(255,255,255,0.10)",
                    linecolor="rgba(255,255,255,0.16)",
                    angle=90,
                ),
                angularaxis=dict(
                    tickfont=dict(
                        color="#FFFFFF",
                        size=14,
                    ),
                    gridcolor="rgba(255,255,255,0.13)",
                    linecolor="rgba(255,255,255,0.18)",
                    rotation=90,
                    direction="clockwise",
                ),
            ),
        )

        st.markdown(
            f"""
            <div class="constellation-wrap">
                <div class="result-heading">나의 역량 별자리</div>
                <div class="result-subheading">
                    전체 평균 {average:.1f}점 · 5점 만점
                </div>
            """,
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

        st.markdown(
            f"""
                <div class="analysis-card">
                    <div>
                        🥇 <span class="analysis-strength">강점:</span>
                        {strength_text}
                    </div>
                    <div>
                        🎯 <span class="analysis-growth">보완:</span>
                        {growth_text}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 세부 점수
        with st.expander("역량별 세부 점수 보기"):
            for item in competencies:
                score = st.session_state.scores[item["code"]]
                stars = "★" * score + "☆" * (5 - score)

                st.markdown(
                    f"""
                    <div class="result-row">
                        <span>{item['code']}. {item['title']}</span>
                        <span class="stars">{stars} · {score}점</span>
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
        <div class="section-title">한 줄 회고</div>
        <div class="section-description">
            각 역량과 관련하여 연수 과정에서 배운 점이나 느낀 점을
            한 문장으로 작성해 주세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for item in competencies:

        st.markdown('<div class="competency-card">', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="card-info" style="margin-bottom:16px;">
                <div class="letter-box" style="background:{item['color']};">
                    {item['code']}
                </div>
                <div>
                    <div class="competency-title">{item['title']}</div>
                    <div class="competency-desc">{item['description']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.text_input(
            f"{item['title']} 회고",
            placeholder="이번 과정에서 배운 점을 한 줄로 작성해 주세요.",
            key=f"reflection_{item['code']}",
            label_visibility="collapsed",
        )

        st.markdown("</div>", unsafe_allow_html=True)

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
