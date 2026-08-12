import io
import re
from pathlib import Path

import pandas as pd
import pdfplumber
import streamlit as st

st.set_page_config(
    page_title="교사 시간표 · 공강 비교",
    page_icon="🗓️",
    layout="wide",
)

DAYS = ["월", "화", "수", "목", "금"]
PERIODS = [str(i) for i in range(1, 8)]

# GitHub 저장소에 이 PDF를 app.py와 같은 폴더에 올려 두면
# 앱 최초 실행 시 자동으로 이 파일을 읽습니다.
DEFAULT_PDF_FILENAME = "2026-2학기 교사별 시간표 (임시).pdf"
APP_DIR = Path(__file__).resolve().parent
DEFAULT_PDF_PATH = APP_DIR / DEFAULT_PDF_FILENAME
APP_VERSION = "2026-08-13 PDF-UPLOAD-V2"


def _word_center(word):
    return (word["x0"] + word["x1"]) / 2, (word["top"] + word["bottom"]) / 2


def _parse_teacher_page(page, page_no):
    """교사 1명 = PDF 1페이지 구조의 시간표를 분석한다."""
    text = page.extract_text() or ""

    # 예: 1. 강민영(106) - 15시간 :
    title_match = re.search(
        r"(?m)^\s*(\d+)\.\s*(.+?)\s*-\s*(\d+)시간\s*:", text
    )
    if not title_match:
        raise ValueError(f"{page_no}페이지에서 교사명/수업시간을 찾지 못했습니다.")

    teacher_no = int(title_match.group(1))
    raw_name = title_match.group(2).strip()
    hours_declared = int(title_match.group(3))

    room_match = re.match(r"(.+?)\(([^()]*)\)\s*$", raw_name)
    if room_match:
        teacher_name = room_match.group(1).strip()
        homeroom = room_match.group(2).strip()
    else:
        teacher_name = raw_name
        homeroom = ""

    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)

    # 표 머리글의 실제 좌표를 이용해 월~금 열을 자동으로 찾는다.
    header_candidates = [w for w in words if w["text"] == "교시"]
    if not header_candidates:
        raise ValueError(f"{page_no}페이지에서 시간표 머리글을 찾지 못했습니다.")

    header_word = header_candidates[0]
    _, header_y = _word_center(header_word)

    header_x = {}
    for label in ["교시"] + DAYS:
        candidates = []
        for w in words:
            _, cy = _word_center(w)
            if w["text"] == label and abs(cy - header_y) < 5:
                candidates.append(w)
        if not candidates:
            raise ValueError(f"{page_no}페이지에서 '{label}' 열을 찾지 못했습니다.")
        header_x[label], _ = _word_center(candidates[0])

    centers_x = [header_x["교시"]] + [header_x[d] for d in DAYS]
    x_bounds = [centers_x[0] - (centers_x[1] - centers_x[0]) / 2]
    x_bounds += [(a + b) / 2 for a, b in zip(centers_x, centers_x[1:])]
    x_bounds.append(centers_x[-1] + (centers_x[-1] - centers_x[-2]) / 2)

    # 1~7교시 숫자의 실제 좌표를 이용해 행 경계를 자동으로 찾는다.
    period_centers_y = {}
    period_left, period_right = x_bounds[0], x_bounds[1]
    for period in range(1, 8):
        candidates = []
        for w in words:
            cx, cy = _word_center(w)
            if (
                w["text"] == str(period)
                and period_left <= cx < period_right
                and cy > header_y
            ):
                candidates.append((cy, w))
        if not candidates:
            raise ValueError(f"{page_no}페이지에서 {period}교시 행을 찾지 못했습니다.")
        period_centers_y[period] = min(candidates, key=lambda item: item[0])[0]

    centers_y = [period_centers_y[p] for p in range(1, 8)]
    y_bounds = [centers_y[0] - (centers_y[1] - centers_y[0]) / 2]
    y_bounds += [(a + b) / 2 for a, b in zip(centers_y, centers_y[1:])]
    y_bounds.append(centers_y[-1] + (centers_y[-1] - centers_y[-2]) / 2)

    schedule = {day: {period: "" for period in PERIODS} for day in DAYS}

    # 각 셀 안에 들어 있는 글자를 좌표 기준으로 모은다.
    for day_index, day in enumerate(DAYS):
        x0, x1 = x_bounds[day_index + 1], x_bounds[day_index + 2]

        for period_index, period in enumerate(PERIODS):
            y0, y1 = y_bounds[period_index], y_bounds[period_index + 1]
            cell_words = []

            for w in words:
                cx, cy = _word_center(w)
                if x0 <= cx < x1 and y0 <= cy < y1:
                    cell_words.append(w)

            if cell_words:
                cell_words.sort(key=lambda w: (w["top"], w["x0"]))

                # 같은 줄의 단어끼리 묶고, 원래 PDF처럼 줄바꿈 형태를 유지한다.
                lines = []
                for w in cell_words:
                    if not lines or abs(w["top"] - lines[-1][0]) > 1.5:
                        lines.append([w["top"], [w]])
                    else:
                        lines[-1][1].append(w)

                schedule[day][period] = "\n".join(
                    " ".join(word["text"] for word in line_words)
                    for _, line_words in lines
                )

    extracted_hours = sum(
        bool(schedule[day][period]) for day in DAYS for period in PERIODS
    )

    return {
        "no": teacher_no,
        "name": teacher_name,
        "homeroom": homeroom,
        "hours_declared": hours_declared,
        "hours_extracted": extracted_hours,
        "schedule": schedule,
    }


@st.cache_data(show_spinner=False)
def parse_timetable_pdf(pdf_bytes):
    """PDF 전체를 읽어 {교사명: 시간표정보} 형식으로 반환한다."""
    teachers = {}
    warnings = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            try:
                info = _parse_teacher_page(page, page_no)
                teachers[info["name"]] = info

                if info["hours_declared"] != info["hours_extracted"]:
                    warnings.append(
                        f"{page_no}페이지 {info['name']}: "
                        f"표기 {info['hours_declared']}시간 / 추출 {info['hours_extracted']}시간"
                    )
            except Exception as exc:
                warnings.append(f"{page_no}페이지 분석 실패: {exc}")

    if not teachers:
        raise ValueError("PDF에서 교사 시간표를 한 건도 읽지 못했습니다.")

    return teachers, warnings


def load_default_pdf():
    # 1) 지정한 기본 파일명을 우선 사용
    if DEFAULT_PDF_PATH.exists():
        return DEFAULT_PDF_PATH.read_bytes(), DEFAULT_PDF_PATH.name

    # 2) 파일명이 조금 달라도 app.py와 같은 폴더의 첫 PDF를 자동 사용
    pdf_files = sorted(APP_DIR.glob("*.pdf"))
    if pdf_files:
        return pdf_files[0].read_bytes(), pdf_files[0].name

    return None, None


def schedule_df(info):
    rows = []
    for period in PERIODS:
        row = {"교시": f"{period}교시"}
        for day in DAYS:
            row[day] = info["schedule"][day][period] or "공강"
        rows.append(row)
    return pd.DataFrame(rows).set_index("교시")


def free_slots(info):
    return {
        (day, period)
        for day in DAYS
        for period in PERIODS
        if not info["schedule"][day][period]
    }


def compact_cell(text):
    if not text:
        return ""
    return " / ".join(part.strip() for part in text.splitlines() if part.strip())


def render_schedule_table(info):
    df = schedule_df(info).map(compact_cell)

    def style_free(value):
        if value == "공강":
            return "background-color: #eaf7ee; color: #166534; font-weight: 700;"
        return ""

    st.dataframe(
        df.style.map(style_free),
        use_container_width=True,
        height=325,
    )


def common_free_df(common):
    rows = []
    for period in PERIODS:
        row = {"교시": f"{period}교시"}
        for day in DAYS:
            row[day] = "●" if (day, period) in common else ""
        rows.append(row)
    return pd.DataFrame(rows).set_index("교시")


def day_summary(common):
    result = []
    for day in DAYS:
        periods = [int(p) for p in PERIODS if (day, p) in common]
        if periods:
            result.append(f"**{day}요일**: " + ", ".join(f"{p}교시" for p in periods))
        else:
            result.append(f"**{day}요일**: 공통 공강 없음")
    return "  \n".join(result)


st.title("🗓️ 교사 시간표 · 공강 비교")
st.caption("PDF를 자동 분석하여 교사별 시간표와 선택 교사의 공통 공강을 보여줍니다.")
st.caption(f"앱 버전: {APP_VERSION}")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem; padding-bottom: 3rem;}
    div[data-testid="stMetric"] {background: #f8fafc; border: 1px solid #e5e7eb; padding: 12px; border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# PDF 선택: 업로드 파일 우선, 없으면 GitHub 저장소의 기본 PDF
# -------------------------
with st.sidebar:
    st.header("📄 시간표 PDF")
    uploaded_pdf = st.file_uploader(
        "새 시간표 PDF 업로드",
        type=["pdf"],
        help="업로드한 PDF가 있으면 GitHub의 기본 PDF 대신 이 파일을 사용합니다.",
    )

    if uploaded_pdf is not None:
        pdf_bytes = uploaded_pdf.getvalue()
        pdf_name = uploaded_pdf.name
        source_label = "업로드한 PDF"
    else:
        pdf_bytes, pdf_name = load_default_pdf()
        source_label = "GitHub 저장소 기본 PDF"

    if pdf_bytes is None:
        st.error(
            f"기본 PDF를 찾지 못했습니다. GitHub 저장소에서 app.py와 같은 위치에 "
            f"'{DEFAULT_PDF_FILENAME}' 파일을 올리거나, 위에서 PDF를 업로드해 주세요."
        )
        st.stop()

    st.success(f"사용 중: {source_label}")
    st.caption(pdf_name)

with st.spinner("시간표 PDF를 분석하고 있습니다..."):
    try:
        data, parse_warnings = parse_timetable_pdf(pdf_bytes)
    except Exception as exc:
        st.error(f"PDF 분석 중 오류가 발생했습니다: {exc}")
        st.stop()

teachers = sorted(data.keys(), key=lambda name: data[name]["no"])

st.info(f"📄 **{pdf_name}** · 교사 **{len(teachers)}명** 시간표를 불러왔습니다.")

if parse_warnings:
    with st.expander(f"⚠️ PDF 분석 확인사항 {len(parse_warnings)}건"):
        for warning in parse_warnings:
            st.write("-", warning)

selected = st.multiselect(
    "교사 선택",
    options=teachers,
    placeholder="교사를 1명 이상 선택하세요. 2명 이상 선택하면 공통 공강을 비교합니다.",
)

if not selected:
    st.info("위의 선택 상자에서 교사를 선택해 주세요.")
    st.stop()

metric_cols = st.columns(min(len(selected), 4))
for i, name in enumerate(selected[:4]):
    info = data[name]
    metric_cols[i].metric(name, f"수업 {info['hours_declared']}시간")
if len(selected) > 4:
    st.caption(f"외 {len(selected) - 4}명 선택됨")

if len(selected) >= 2:
    st.divider()
    st.subheader("🤝 선택 교사의 공통 공강")

    common = set.intersection(*(free_slots(data[name]) for name in selected))
    c1, c2 = st.columns([1, 2])

    with c1:
        st.metric("공통 공강", f"주 {len(common)}교시")
        st.markdown(day_summary(common))

    with c2:
        grid = common_free_df(common)

        def style_common(value):
            if value == "●":
                return "background-color: #dcfce7; color: #15803d; font-weight: 900; text-align: center;"
            return "background-color: #f8fafc; color: #cbd5e1;"

        st.dataframe(
            grid.style.map(style_common),
            use_container_width=True,
            height=325,
        )

    if common:
        export_rows = [
            {"요일": day, "교시": int(period), "선택교사": ", ".join(selected)}
            for day in DAYS
            for period in PERIODS
            if (day, period) in common
        ]
        csv = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "공통 공강 CSV 다운로드",
            data=csv,
            file_name="공통공강.csv",
            mime="text/csv",
        )
    else:
        st.warning("선택한 교사 모두가 동시에 공강인 시간이 없습니다.")

st.divider()
st.subheader("👩‍🏫 교사별 시간표")

for name in selected:
    info = data[name]
    homeroom = f" · 표시 교실/담임 {info['homeroom']}" if info.get("homeroom") else ""

    with st.expander(
        f"{name} - 주 {info['hours_declared']}시간{homeroom}",
        expanded=(len(selected) <= 2),
    ):
        render_schedule_table(info)

        free = sorted(
            free_slots(info),
            key=lambda item: (DAYS.index(item[0]), int(item[1])),
        )
        by_day = []
        for day in DAYS:
            periods = [p for d, p in free if d == day]
            by_day.append(
                f"**{day}** "
                + (", ".join(f"{p}교시" for p in periods) if periods else "없음")
            )
        st.markdown("공강: " + "  |  ".join(by_day))

st.caption(
    "※ 공강은 PDF 시간표에서 수업이 배정되지 않은 교시를 뜻합니다. "
    "회의·업무·보강 등 별도 일정은 반영되지 않습니다."
)
