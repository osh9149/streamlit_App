import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="교사 시간표 · 공강 비교",
    page_icon="🗓️",
    layout="wide",
)

DAYS = ["월", "화", "수", "목", "금"]
PERIODS = [str(i) for i in range(1, 8)]
DATA_PATH = Path(__file__).with_name("teacher_timetable.json")


@st.cache_data
def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


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
    # PDF에서 추출된 여러 줄을 화면에서는 한 줄에 가깝게 표시
    return " / ".join(part.strip() for part in text.splitlines() if part.strip())


def render_schedule_table(info):
    df = schedule_df(info).map(compact_cell)

    def style_free(v):
        if v == "공강":
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
        ps = [int(p) for p in PERIODS if (day, p) in common]
        if ps:
            result.append(f"**{day}요일**: " + ", ".join(f"{p}교시" for p in ps))
        else:
            result.append(f"**{day}요일**: 공통 공강 없음")
    return "  \n".join(result)


data = load_data()
teachers = sorted(data.keys(), key=lambda n: data[n]["no"])

st.title("🗓️ 교사 시간표 · 공강 비교")
st.caption("2026학년도 2학기 교사별 시간표(임시) 기준")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem; padding-bottom: 3rem;}
    div[data-testid="stMetric"] {background: #f8fafc; border: 1px solid #e5e7eb; padding: 12px; border-radius: 12px;}
    .teacher-card {padding: 0.85rem 1rem; border: 1px solid #e5e7eb; border-radius: 12px; margin-bottom: .5rem; background: white;}
    </style>
    """,
    unsafe_allow_html=True,
)

selected = st.multiselect(
    "교사 선택",
    options=teachers,
    placeholder="교사를 1명 이상 선택하세요. 2명 이상 선택하면 공통 공강을 비교합니다.",
)

if not selected:
    st.info("위의 선택 상자에서 교사를 선택해 주세요.")
    st.stop()

# 요약 지표
metric_cols = st.columns(min(len(selected), 4))
for i, name in enumerate(selected[:4]):
    info = data[name]
    metric_cols[i].metric(name, f"수업 {info['hours_declared']}시간")
if len(selected) > 4:
    st.caption(f"외 {len(selected)-4}명 선택됨")

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

        def style_common(v):
            if v == "●":
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
    with st.expander(f"{name} - 주 {info['hours_declared']}시간{homeroom}", expanded=(len(selected) <= 2)):
        render_schedule_table(info)

        free = sorted(
            free_slots(info),
            key=lambda x: (DAYS.index(x[0]), int(x[1])),
        )
        by_day = []
        for day in DAYS:
            ps = [p for d, p in free if d == day]
            by_day.append(f"**{day}** " + (", ".join(f"{p}교시" for p in ps) if ps else "없음"))
        st.markdown("공강: " + "  |  ".join(by_day))

st.caption("※ '공강'은 첨부된 수업 시간표에서 수업이 배정되지 않은 교시를 뜻합니다. 회의·업무·보강 등 별도 일정은 반영되지 않습니다.")
