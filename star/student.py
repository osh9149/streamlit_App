import streamlit as st

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="디지털 교육 역량 설문",
    page_icon="⭐",
    layout="centered"
)

# =========================================================
# 설문 문항
# 나중에 구글시트 C1:H1의 내용으로 자동 교체할 부분
# =========================================================
questions = [
    "교육 이해 역량",
    "윤리적 실천 역량",
    "수업·학습자 분석 역량",
    "수업 설계 역량",
    "수업 실행 역량",
    "수업 평가 역량"
]

# 점수별 별 표시
score_labels = {
    1: "⭐ 1점",
    2: "⭐⭐ 2점",
    3: "⭐⭐⭐ 3점",
    4: "⭐⭐⭐⭐ 4점",
    5: "⭐⭐⭐⭐⭐ 5점"
}

# =========================================================
# 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .survey-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.4rem;
    }

    .survey-description {
        text-align: center;
        color: #666666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    .question-box {
        padding: 18px 20px;
        margin-top: 15px;
        margin-bottom: 8px;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        background-color: #fafafa;
        font-size: 1.08rem;
        font-weight: 700;
    }

    div[data-testid="stRadio"] {
        padding-left: 10px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 설문 제목
# =========================================================
st.markdown(
    '<div class="survey-title">⭐ 디지털 교육 역량 자가 진단</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="survey-description">
        각 문항을 읽고 자신의 수준에 가장 가까운 점수를 선택해 주세요.
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 설문 입력 폼
# =========================================================
with st.form("survey_form"):

    name = st.text_input(
        "이름",
        placeholder="이름을 입력하세요.",
        max_chars=30
    )

    st.divider()

    answers = {}

    for index, question in enumerate(questions, start=1):

        st.markdown(
            f"""
            <div class="question-box">
                {index}. {question}
            </div>
            """,
            unsafe_allow_html=True
        )

        answers[question] = st.radio(
            label=f"{index}번 문항 점수",
            options=[1, 2, 3, 4, 5],
            format_func=lambda score: score_labels[score],
            horizontal=True,
            index=None,
            key=f"question_{index}",
            label_visibility="collapsed"
        )

    st.divider()

    submitted = st.form_submit_button(
        "📨 설문 제출",
        type="primary",
        use_container_width=True
    )

# =========================================================
# 제출 결과 확인
# 아직 구글시트에는 저장하지 않고 화면에서만 확인
# =========================================================
if submitted:

    if not name.strip():
        st.error("이름을 입력해 주세요.")

    elif any(score is None for score in answers.values()):
        st.error("모든 문항의 점수를 선택해 주세요.")

    else:
        st.success(f"{name}님의 설문이 정상적으로 제출되었습니다.")

        st.subheader("나의 설문 결과")

        total_score = 0

        for index, question in enumerate(questions, start=1):
            score = answers[question]
            total_score += score

            st.write(
                f"**{index}. {question}**  \n"
                f"{'★' * score}{'☆' * (5 - score)} · {score}점"
            )

        average_score = total_score / len(questions)

        st.metric(
            label="전체 평균",
            value=f"{average_score:.1f}점",
            delta=f"{'★' * round(average_score)}{'☆' * (5 - round(average_score))}"
        )
