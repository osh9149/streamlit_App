import base64
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
import pandas as pd
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="디벗 보관함 비밀번호 관리",
    page_icon="🔐",
    layout="centered",
)

SHEET_COLUMNS = [
    "저장일시",
    "학년",
    "반",
    "암호화된_비밀번호",
    "수정일시",
]


# ---------------------------------------------------------
# 화면 디자인
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        color: #173B57;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #5D6D7E;
        margin-bottom: 1.2rem;
    }
    .guide-box {
        background: #F4F8FB;
        border: 1px solid #D6E4EE;
        border-radius: 14px;
        padding: 18px;
        margin: 10px 0 18px 0;
    }
    .warning-box {
        background: #FFF8E7;
        border-left: 5px solid #F0B429;
        border-radius: 8px;
        padding: 12px 14px;
        margin: 10px 0;
    }
    div.stButton > button, div.stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 보안 및 Google Sheets 연결 함수
# ---------------------------------------------------------
def get_secret(name: str):
    """필수 Secret 값을 읽고, 없으면 사용자에게 설정 방법을 안내합니다."""
    try:
        return st.secrets[name]
    except KeyError:
        st.error(f"Streamlit Secrets에 `{name}` 값이 없습니다.")
        st.stop()


def get_fernet() -> Fernet:
    """비밀번호 암호화·복호화에 사용할 Fernet 객체를 만듭니다."""
    encryption_key = get_secret("ENCRYPTION_KEY")
    try:
        return Fernet(str(encryption_key).encode("utf-8"))
    except Exception:
        st.error("ENCRYPTION_KEY 형식이 올바르지 않습니다. Fernet 키를 다시 생성해 주세요.")
        st.stop()


@st.cache_resource
def connect_worksheet():
    """서비스 계정으로 Google Sheets에 연결합니다."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    try:
        service_account_info = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes,
        )
        client = gspread.authorize(credentials)

        spreadsheet_id = str(get_secret("SPREADSHEET_ID"))
        worksheet_name = str(st.secrets.get("WORKSHEET_NAME", "비밀번호관리"))
        spreadsheet = client.open_by_key(spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=300,
                cols=len(SHEET_COLUMNS),
            )
            worksheet.append_row(SHEET_COLUMNS)

        # 빈 시트이거나 헤더가 없을 때 헤더를 생성합니다.
        first_row = worksheet.row_values(1)
        if first_row != SHEET_COLUMNS:
            worksheet.update("A1:E1", [SHEET_COLUMNS])

        return worksheet
    except Exception as error:
        st.error("Google Sheets 연결에 실패했습니다.")
        st.code(str(error))
        st.info("서비스 계정 이메일에 해당 Google 스프레드시트의 편집 권한을 부여했는지 확인하세요.")
        st.stop()


def encrypt_password(password: str) -> str:
    """4자리 비밀번호를 암호화하여 저장용 문자열로 바꿉니다."""
    return get_fernet().encrypt(password.encode("utf-8")).decode("utf-8")


def decrypt_password(encrypted_password: str) -> str:
    """관리자 화면에서 암호화된 비밀번호를 복호화합니다."""
    try:
        return get_fernet().decrypt(encrypted_password.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, AttributeError):
        return "복호화 오류"


def admin_password_matches(input_password: str) -> bool:
    """관리자 비밀번호를 안전하게 비교합니다."""
    saved_password = str(get_secret("ADMIN_PASSWORD"))
    input_hash = hashlib.sha256(input_password.encode("utf-8")).digest()
    saved_hash = hashlib.sha256(saved_password.encode("utf-8")).digest()
    return input_hash == saved_hash


def load_records() -> pd.DataFrame:
    """Google Sheets의 전체 저장 기록을 데이터프레임으로 읽습니다."""
    worksheet = connect_worksheet()
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=SHEET_COLUMNS)

    df = pd.DataFrame(records)
    for column in SHEET_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[SHEET_COLUMNS]


def save_or_update_record(grade: int, class_no: int, new_password: str) -> str:
    """같은 학년·반이 있으면 수정하고, 없으면 새 행을 추가합니다."""
    worksheet = connect_worksheet()
    encrypted = encrypt_password(new_password)
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    all_values = worksheet.get_all_values()
    target_row = None

    # 2행부터 학년·반이 같은 기록을 찾습니다.
    for row_number, row in enumerate(all_values[1:], start=2):
        row_grade = str(row[1]).strip() if len(row) > 1 else ""
        row_class = str(row[2]).strip() if len(row) > 2 else ""
        if row_grade == str(grade) and row_class == str(class_no):
            target_row = row_number
            break

    if target_row:
        original_created_at = worksheet.cell(target_row, 1).value or now
        worksheet.update(
            f"A{target_row}:E{target_row}",
            [[original_created_at, grade, class_no, encrypted, now]],
        )
        return "updated"

    worksheet.append_row([now, grade, class_no, encrypted, now])
    return "created"


def delete_record(sheet_row_number: int) -> None:
    """관리자가 선택한 행을 삭제합니다."""
    connect_worksheet().delete_rows(sheet_row_number)


# ---------------------------------------------------------
# 공통 제목과 안내문
# ---------------------------------------------------------
st.markdown('<div class="main-title">🔐 디벗 보관함 비밀번호 관리</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">도어락 비밀번호 변경 방법을 확인하고, 변경한 비밀번호를 안전하게 등록하세요.</div>',
    unsafe_allow_html=True,
)

student_tab, admin_tab = st.tabs(["📝 비밀번호 등록", "🛡️ 관리자 조회"])


# ---------------------------------------------------------
# 학생·담임 입력 화면
# ---------------------------------------------------------
with student_tab:
    st.markdown(
        """
        <div class="guide-box">
        <b>📌 디지털 도어락 비밀번호 변경 순서</b><br><br>
        ① 초기화 번호 <b>8810</b> 입력 → <b>OK</b><br>
        ② 기존 비밀번호 <b>1111</b> 입력 → <b>C</b><br>
        ③ 새 비밀번호 <b>4자리</b> 입력 → <b>OK</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="warning-box">
        새 비밀번호는 기억하기 쉬운 4자리 숫자로 설정하고, 변경 후 잠금·해제가 정상적으로 되는지 반드시 확인하세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("password_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("학년", options=[1, 2, 3], index=None, placeholder="학년 선택")
        with col2:
            class_no = st.selectbox("반", options=list(range(1, 13)), index=None, placeholder="반 선택")

        new_password = st.text_input(
            "변경한 비밀번호",
            type="password",
            max_chars=4,
            placeholder="숫자 4자리",
            help="Google Sheets에는 원문이 아닌 암호화된 값으로 저장됩니다.",
        )
        confirm_password = st.text_input(
            "비밀번호 확인",
            type="password",
            max_chars=4,
            placeholder="같은 비밀번호를 다시 입력",
        )
        agree = st.checkbox("비밀번호 변경 후 잠금·해제를 확인했습니다.")
        submitted = st.form_submit_button("🔒 변경 비밀번호 저장", type="primary")

    if submitted:
        if grade is None or class_no is None:
            st.warning("학년과 반을 모두 선택하세요.")
        elif not (new_password.isdigit() and len(new_password) == 4):
            st.warning("비밀번호는 숫자 4자리로 입력하세요.")
        elif new_password != confirm_password:
            st.warning("두 비밀번호가 일치하지 않습니다.")
        elif not agree:
            st.warning("잠금·해제 확인 항목에 체크하세요.")
        else:
            result = save_or_update_record(grade, class_no, new_password)
            if result == "updated":
                st.success(f"{grade}학년 {class_no}반의 비밀번호가 새 값으로 수정되었습니다.")
            else:
                st.success(f"{grade}학년 {class_no}반의 비밀번호가 저장되었습니다.")
            st.balloons()

    st.caption("변경 중 오류가 발생하면 연구정보부(3567)로 문의하세요.")


# ---------------------------------------------------------
# 관리자 조회 화면
# ---------------------------------------------------------
with admin_tab:
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.subheader("관리자 로그인")
        admin_input = st.text_input("관리자 비밀번호", type="password", key="admin_login_password")
        if st.button("관리자 로그인", type="primary"):
            if admin_password_matches(admin_input):
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("관리자 비밀번호가 올바르지 않습니다.")
    else:
        top_col1, top_col2 = st.columns([3, 1])
        with top_col1:
            st.success("관리자 권한으로 로그인했습니다.")
        with top_col2:
            if st.button("로그아웃"):
                st.session_state.admin_authenticated = False
                st.rerun()

        df = load_records()

        if df.empty:
            st.info("아직 저장된 비밀번호가 없습니다.")
        else:
            # 원본 시트 행 번호를 삭제 기능에 사용합니다. 헤더가 1행이므로 +2입니다.
            df = df.reset_index(drop=True)
            df["시트행번호"] = df.index + 2
            df["학년"] = pd.to_numeric(df["학년"], errors="coerce").fillna(0).astype(int)
            df["반"] = pd.to_numeric(df["반"], errors="coerce").fillna(0).astype(int)
            df["변경 비밀번호"] = df["암호화된_비밀번호"].apply(decrypt_password)

            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                grade_filter = st.selectbox("학년 필터", ["전체", 1, 2, 3])
            with filter_col2:
                class_filter = st.selectbox("반 필터", ["전체"] + list(range(1, 13)))

            filtered_df = df.copy()
            if grade_filter != "전체":
                filtered_df = filtered_df[filtered_df["학년"] == grade_filter]
            if class_filter != "전체":
                filtered_df = filtered_df[filtered_df["반"] == class_filter]

            filtered_df = filtered_df.sort_values(["학년", "반"]).reset_index(drop=True)

            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric("전체 등록 반", len(df))
            metric_col2.metric("현재 조회 결과", len(filtered_df))

            display_df = filtered_df[["학년", "반", "변경 비밀번호", "수정일시"]].copy()
            display_df.index = display_df.index + 1
            st.dataframe(display_df, use_container_width=True)

            # 다운로드 파일에는 복호화된 비밀번호가 포함되므로 관리자만 사용할 수 있습니다.
            csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 조회 결과 CSV 다운로드",
                data=csv_data,
                file_name=f"디벗_보관함_비밀번호_{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

            with st.expander("🗑️ 잘못 저장된 기록 삭제"):
                delete_options = {
                    f"{row['학년']}학년 {row['반']}반 · 수정 {row['수정일시']}": int(row["시트행번호"])
                    for _, row in filtered_df.iterrows()
                }
                if delete_options:
                    selected_label = st.selectbox("삭제할 기록", list(delete_options.keys()))
                    confirm_delete = st.checkbox("선택한 기록을 삭제하겠습니다.")
                    if st.button("선택 기록 삭제"):
                        if not confirm_delete:
                            st.warning("삭제 확인 항목에 체크하세요.")
                        else:
                            delete_record(delete_options[selected_label])
                            st.success("기록을 삭제했습니다.")
                            st.cache_resource.clear()
                            st.rerun()

        st.markdown("---")
        st.caption("보안을 위해 관리자 화면 사용 후 반드시 로그아웃하고, CSV 파일은 제한된 장소에 보관하세요.")
