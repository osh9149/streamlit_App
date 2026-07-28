import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="온라인 설문",
    page_icon="⭐",
    layout="centered",
)

SPREADSHEET_ID = "1oITSnXoXMDP8Dbs_L5ZLvwRbhYB6qm2fruyjES3jDfM"
QUESTION_SHEET_GID = 655139617
RESPONSE_SHEET_NAME = "응답"
QUESTION_RANGE = "C1:H1"

SCORE_LABELS = {
    1: "⭐",
    2: "⭐⭐",
    3: "⭐⭐⭐",
    4: "⭐⭐⭐⭐",
    5: "⭐⭐⭐⭐⭐",
}

# =========================================================
# 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    .main-title {
        text-align: center;
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .result-card {
        padding: 1rem 1.2rem;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        background: #fafafa;
        margin-bottom: 0.8rem;
    }
    .star-result {
        font-size: 1.45rem;
        letter-spacing: 0.08rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">⭐ 온라인 설문</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">각 문항을 읽고 1점부터 5점까지 선택해 주세요.</div>',
    unsafe_allow_html=True,
)

# =========================================================
# 구글시트 연결
# =========================================================
@st.cache_resource
def connect_google_sheet():
    """Streamlit Secrets의 서비스 계정 정보로 구글시트에 연결합니다."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    service_account_info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=scopes,
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(SPREADSHEET_ID)


def get_worksheet_by_gid(spreadsheet, gid):
    """gid 값으로 설문 문항이 들어 있는 워크시트를 찾습니다."""
    for worksheet in spreadsheet.worksheets():
        if worksheet.id == gid:
            return worksheet
    raise ValueError(f"gid={gid}인 시트를 찾을 수 없습니다.")


@st.cache_data(ttl=60)
def load_questions():
    """설문 시트의 C1:H1에서 문항 6개를 읽습니다."""
    spreadsheet = connect_google_sheet()
    question_sheet = get_worksheet_by_gid(spreadsheet, QUESTION_SHEET_GID)
    values = question_sheet.get(QUESTION_RANGE)

    if not values:
        return []

    questions = [str(value).strip() for value in values[0] if str(value).strip()]
    return questions


def get_or_create_response_sheet(questions):
    """같은 스프레드시트 안에 '응답' 시트를 만들거나 불러옵니다."""
    spreadsheet = connect_google_sheet()

    try:
        response_sheet = spreadsheet.worksheet(RESPONSE_SHEET_NAME)
    except gspread.WorksheetNotFound:
        response_sheet = spreadsheet.add_worksheet(
            title=RESPONSE_SHEET_NAME,
            rows=1000,
            cols=max(10, len(questions) + 2),
        )

    expected_headers = ["제출일시", "이름"] + questions
    current_headers = response_sheet.row_values(1)

    # 응답 시트가 비어 있으면 제목 행을 자동 작성합니다.
    if not current_headers:
        response_sheet.append_row(expected_headers, value_input_option="USER_ENTERED")
        response_sheet.freeze(rows=1)

    return response_sheet


def save_response(name, questions, scores):
    """이름과 점수를 구글시트의 다음 빈 행에 저장합니다."""
    response_sheet = get_or_create_response_sheet(questions)
    submitted_at = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    row = [submitted_at, name] + [scores[q] for q in questions]
    response_sheet.append_row(row, value_input_option="USER_ENTERED")


@st.cache_data(ttl=10)
def load_responses(questions):
    """저장된 전체 응답을 데이터프레임으로 불러옵니다."""
    response_sheet = get_or_create_response_sheet(questions)
    records = response_sheet.get_all_records()

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def score_to_stars(score):
    """평균 점수를 별 모양으로 변환합니다."""
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "☆☆☆☆☆"

    filled = max(0, min(5, int(round(score))))
    return "★" * filled + "☆" * (5 - filled)


# =========================================================
# 설문 문항 표시
# =========================================================
try:
    questions = load_questions()
except Exception as error:
    st.error("구글시트에 연결하지 못했습니다.")
    st.code(str(error))
    st.info(
        "Streamlit Secrets 설정과 서비스 계정 이메일의 구글시트 편집 권한을 확인해 주세요."
    )
    st.stop()

if not questions:
    st.warning("구글시트의 C1:H1 범위에서 설문 문항을 찾지 못했습니다.")
    st.stop()

with st.form("survey_form", clear_on_submit=True):
    name = st.text_input(
        "이름",
        placeholder="이름을 입력하세요.",
        max_chars=30,
    )

    scores = {}

    for index, question in enumerate(questions, start=1):
        st.markdown(f"#### {index}. {question}")
        scores[question] = st.radio(
            label=f"{index}번 문항 점수",
            options=[1, 2, 3, 4, 5],
            format_func=lambda value: SCORE_LABELS[value],
            horizontal=True,
            index=None,
            key=f"question_{index}",
            label_visibility="collapsed",
        )
        st.divider()

    submitted = st.form_submit_button(
        "📨 제출하기",
        use_container_width=True,
        type="primary",
    )

if submitted:
    missing_questions = [
        str(index)
        for index, question in enumerate(questions, start=1)
        if scores[question] is None
    ]

    if not name.strip():
        st.error("이름을 입력해 주세요.")
    elif missing_questions:
        st.error(f"{', '.join(missing_questions)}번 문항의 점수를 선택해 주세요.")
    else:
        try:
            save_response(name.strip(), questions, scores)
            load_responses.clear()
            st.success("설문 응답이 구글시트에 저장되었습니다.")
            st.balloons()
        except Exception as error:
            st.error("응답을 저장하지 못했습니다.")
            st.code(str(error))

# =========================================================
# 결과 보기
# =========================================================
st.markdown("---")

if st.button("📊 결과 보기", use_container_width=True):
    try:
        responses = load_responses(questions)

        if responses.empty:
            st.info("아직 제출된 설문 응답이 없습니다.")
        else:
            st.subheader("설문 결과")
            st.caption(f"총 응답자 수: {len(responses)}명")

            available_questions = [
                question for question in questions
                if question in responses.columns
            ]

            for index, question in enumerate(available_questions, start=1):
                numeric_scores = pd.to_numeric(
                    responses[question],
                    errors="coerce",
                ).dropna()

                if numeric_scores.empty:
                    average_score = 0
                else:
                    average_score = numeric_scores.mean()

                stars = score_to_stars(average_score)

                st.markdown(
                    f"""
                    <div class="result-card">
                        <strong>{index}. {question}</strong><br>
                        <span class="star-result">{stars}</span>
                        &nbsp; <strong>{average_score:.1f}점</strong> / 5점
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            overall_values = responses[available_questions].apply(
                pd.to_numeric,
                errors="coerce",
            )
            overall_average = overall_values.stack().mean()

            if pd.notna(overall_average):
                st.metric(
                    "전체 문항 평균",
                    f"{overall_average:.2f}점",
                    score_to_stars(overall_average),
                )

    except Exception as error:
        st.error("결과를 불러오지 못했습니다.")
        st.code(str(error))
