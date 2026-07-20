import random
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="대한민국 인구 놀이터",
    page_icon="🎡",
    layout="wide",
)

DEFAULT_CSV = "202606_202606_연령별인구현황_월간(5).csv"


# =========================================================
# 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #fffdf7 0%, #f4f9ff 100%);
    }

    .main-title {
        padding: 1.2rem 1.4rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #ffe7a8, #ffd1dc, #cdefff);
        margin-bottom: 1rem;
        box-shadow: 0 8px 22px rgba(80, 90, 120, 0.12);
    }

    .main-title h1 {
        margin: 0;
        font-size: 2.3rem;
    }

    .main-title p {
        margin: 0.4rem 0 0 0;
        font-size: 1.05rem;
    }

    .fun-card {
        padding: 1.1rem;
        border-radius: 20px;
        background: white;
        border: 1px solid #edf0f5;
        box-shadow: 0 6px 16px rgba(60, 70, 100, 0.08);
        margin-bottom: 0.8rem;
    }

    .rank-first {
        padding: 1rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #fff5bd, #ffe5a4);
        border: 2px solid #f5c85b;
        text-align: center;
        margin-bottom: 1rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid #eef0f4;
        padding: 0.8rem;
        border-radius: 18px;
        box-shadow: 0 5px 14px rgba(70, 80, 110, 0.07);
    }

    div.stButton > button {
        border-radius: 14px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 데이터 처리 함수
# =========================================================
def read_population_csv(file_source):
    """행정안전부 인구 CSV를 여러 인코딩으로 읽는다."""
    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]

    for encoding in encodings:
        try:
            if hasattr(file_source, "seek"):
                file_source.seek(0)

            return pd.read_csv(
                file_source,
                encoding=encoding,
                dtype=str,
                low_memory=False,
            )
        except (UnicodeDecodeError, LookupError):
            continue

    raise ValueError(
        "CSV 파일의 인코딩을 확인할 수 없습니다. "
        "cp949 또는 UTF-8 형식의 파일을 사용해 주세요."
    )


def clean_number(series):
    """쉼표와 공백이 포함된 인구수를 숫자로 변환한다."""
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("-", "0", regex=False),
        errors="coerce",
    ).fillna(0)


def extract_admin_info(value):
    """
    예:
    서울특별시 종로구 (1111000000)
    → 지역명: 서울특별시 종로구
    → 행정구역코드: 1111000000
    """
    text = str(value).strip()
    match = re.search(r"\((\d{10})\)\s*$", text)

    code = match.group(1) if match else ""
    name = re.sub(r"\s*\(\d{10}\)\s*$", "", text).strip()
    name = re.sub(r"\s+", " ", name)

    return name, code


def find_column(columns, suffix):
    """열 이름 끝부분을 기준으로 필요한 열을 찾는다."""
    matches = [column for column in columns if str(column).endswith(suffix)]
    return matches[0] if matches else None


def find_age_column(columns, gender, age):
    """
    gender: 계, 남, 여
    age: 0~99 또는 100
    """
    age_text = "100세 이상" if age == 100 else f"{age}세"
    pattern = re.compile(rf"^\d{{4}}년\d{{2}}월_{gender}_{re.escape(age_text)}$")
    matches = [column for column in columns if pattern.match(str(column))]
    return matches[0] if matches else None


@st.cache_data(show_spinner=False)
def prepare_population_data(raw_df):
    """업로드된 행정안전부 연령별 인구 CSV를 앱 분석용 데이터로 변환한다."""
    df = raw_df.copy()
    df.columns = [str(column).strip() for column in df.columns]

    if "행정구역" not in df.columns:
        raise ValueError("CSV 파일에 '행정구역' 열이 없습니다.")

    parsed = df["행정구역"].apply(extract_admin_info)
    df["지역명"] = parsed.str[0]
    df["행정구역코드"] = parsed.str[1]

    # 10자리 코드의 끝자리로 행정계층 구분
    # 시도: 1100000000, 시군구: 1111000000, 읍면동: 1111051500
    df["지역단계"] = np.select(
        [
            df["행정구역코드"].str.endswith("00000000"),
            df["행정구역코드"].str.endswith("00000"),
        ],
        ["시도", "시군구"],
        default="읍면동",
    )

    # 해당 파일은 2026년06월처럼 기준월이 열 이름에 들어 있다.
    month_match = re.search(r"(\d{4}년\d{2}월)", " ".join(df.columns))
    base_month = month_match.group(1) if month_match else "기준월 미상"

    total_col = find_column(df.columns, "_계_총인구수")
    male_col = find_column(df.columns, "_남_총인구수")
    female_col = find_column(df.columns, "_여_총인구수")

    if not all([total_col, male_col, female_col]):
        raise ValueError(
            "'계_총인구수', '남_총인구수', '여_총인구수' 열을 찾지 못했습니다."
        )

    result = pd.DataFrame(
        {
            "지역명": df["지역명"],
            "행정구역코드": df["행정구역코드"],
            "지역단계": df["지역단계"],
            "기준월": base_month,
            "총인구수": clean_number(df[total_col]),
            "남자인구수": clean_number(df[male_col]),
            "여자인구수": clean_number(df[female_col]),
        }
    )

    # 0~14세, 15~64세, 65세 이상 인구 합산
    age_values = {}

    for gender in ["계", "남", "여"]:
        gender_age_columns = []

        for age in range(101):
            column = find_age_column(df.columns, gender, age)
            if column:
                values = clean_number(df[column])
            else:
                values = pd.Series(0, index=df.index, dtype=float)

            age_values[(gender, age)] = values
            gender_age_columns.append(values)

        # 필요 시 전체 연령 합계를 재검증할 수 있는 값
        age_values[(gender, "합계")] = sum(gender_age_columns)

    result["유소년인구"] = sum(age_values[("계", age)] for age in range(0, 15))
    result["생산가능인구"] = sum(age_values[("계", age)] for age in range(15, 65))
    result["고령인구"] = sum(age_values[("계", age)] for age in range(65, 101))

    # 인구 피라미드용 연령 데이터도 보존
    age_rows = []
    for idx in df.index:
        for age in range(101):
            age_rows.append(
                {
                    "행정구역코드": result.loc[idx, "행정구역코드"],
                    "지역명": result.loc[idx, "지역명"],
                    "연령": age,
                    "연령표시": "100세 이상" if age == 100 else f"{age}세",
                    "남자": int(age_values[("남", age)].loc[idx]),
                    "여자": int(age_values[("여", age)].loc[idx]),
                }
            )

    age_df = pd.DataFrame(age_rows)

    # 비율 계산
    denominator = result["총인구수"].replace(0, np.nan)
    result["남자비율"] = result["남자인구수"] / denominator * 100
    result["여자비율"] = result["여자인구수"] / denominator * 100
    result["유소년비율"] = result["유소년인구"] / denominator * 100
    result["생산가능비율"] = result["생산가능인구"] / denominator * 100
    result["고령인구비율"] = result["고령인구"] / denominator * 100

    ratio_columns = [
        "남자비율",
        "여자비율",
        "유소년비율",
        "생산가능비율",
        "고령인구비율",
    ]
    result[ratio_columns] = result[ratio_columns].fillna(0)

    # 시도와 시군구 이름 분리
    sido_rows = result[result["지역단계"] == "시도"].copy()
    sido_names = sorted(sido_rows["지역명"].unique())

    def get_sido_name(region_name):
        matched = [
            sido
            for sido in sido_names
            if region_name == sido or region_name.startswith(sido + " ")
        ]
        return max(matched, key=len) if matched else region_name.split()[0]

    result["시도"] = result["지역명"].apply(get_sido_name)
    result["시군구"] = result.apply(
        lambda row: (
            row["지역명"].replace(row["시도"], "", 1).strip()
            if row["지역단계"] == "시군구"
            else row["지역명"]
        ),
        axis=1,
    )

    result = result[result["총인구수"] > 0].reset_index(drop=True)
    return result, age_df


def format_population(value):
    return f"{int(value):,}명"


def safe_minmax(series, reverse=False):
    """0~100 사이로 정규화한다."""
    series = pd.to_numeric(series, errors="coerce").fillna(0)
    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        score = pd.Series(50.0, index=series.index)
    else:
        score = (series - minimum) / (maximum - minimum) * 100

    return 100 - score if reverse else score


def population_nickname(row, population_data):
    youth_q75 = population_data["유소년비율"].quantile(0.75)
    working_q75 = population_data["생산가능비율"].quantile(0.75)
    elderly_q75 = population_data["고령인구비율"].quantile(0.75)
    population_q75 = population_data["총인구수"].quantile(0.75)
    population_q25 = population_data["총인구수"].quantile(0.25)

    if row["유소년비율"] >= youth_q75:
        return "🌱 새싹 도시"
    if row["생산가능비율"] >= working_q75:
        return "⚡ 활력 도시"
    if row["고령인구비율"] >= elderly_q75:
        return "🌳 여유로운 도시"
    if row["총인구수"] >= population_q75:
        return "🏙️ 북적북적 대도시"
    if row["총인구수"] <= population_q25:
        return "🏡 아기자기한 지역"
    return "🎨 균형 잡힌 도시"


def describe_region(row, population_data):
    youth_avg = population_data["유소년비율"].mean()
    elderly_avg = population_data["고령인구비율"].mean()
    working_avg = population_data["생산가능비율"].mean()

    descriptions = []

    if row["유소년비율"] >= youth_avg:
        descriptions.append("유소년 인구 비율이 시군구 평균보다 높습니다.")
    else:
        descriptions.append("유소년 인구 비율이 시군구 평균보다 낮습니다.")

    if row["고령인구비율"] >= elderly_avg:
        descriptions.append("고령인구 비율이 높아 고령화 특성이 나타납니다.")
    else:
        descriptions.append("고령인구 비율이 시군구 평균보다 낮습니다.")

    if row["생산가능비율"] >= working_avg:
        descriptions.append("생산가능인구 비율이 비교적 높은 지역입니다.")

    return " ".join(descriptions)


def get_region_row(data, region_name):
    selected = data[data["지역명"] == region_name]
    return selected.iloc[0] if not selected.empty else None


def region_selector(data, label, key):
    sido_list = sorted(data["시도"].dropna().unique())
    sido = st.selectbox(f"{label} 시도", sido_list, key=f"{key}_sido")

    region_list = sorted(
        data.loc[data["시도"] == sido, "지역명"].dropna().unique()
    )
    region = st.selectbox(f"{label} 시군구", region_list, key=f"{key}_region")
    return region


def make_quiz_question(population_data):
    """현재 데이터에서 무작위 퀴즈 한 문제를 생성한다."""
    quiz_types = [
        "총인구",
        "고령인구비율",
        "유소년비율",
        "남자인구",
        "두지역",
    ]
    quiz_type = random.choice(quiz_types)

    sample_size = 2 if quiz_type == "두지역" else 4
    sample = population_data.sample(
        n=min(sample_size, len(population_data)),
        replace=False,
    ).copy()

    if quiz_type == "총인구":
        answer_row = sample.loc[sample["총인구수"].idxmax()]
        question = "다음 중 총인구가 가장 많은 지역은 어디일까요?"
        explanation = (
            f"{answer_row['지역명']}의 총인구는 "
            f"{format_population(answer_row['총인구수'])}입니다."
        )

    elif quiz_type == "고령인구비율":
        answer_row = sample.loc[sample["고령인구비율"].idxmax()]
        question = "다음 중 65세 이상 인구 비율이 가장 높은 지역은 어디일까요?"
        explanation = (
            f"{answer_row['지역명']}의 고령인구 비율은 "
            f"{answer_row['고령인구비율']:.1f}%입니다."
        )

    elif quiz_type == "유소년비율":
        answer_row = sample.loc[sample["유소년비율"].idxmax()]
        question = "다음 중 0~14세 인구 비율이 가장 높은 지역은 어디일까요?"
        explanation = (
            f"{answer_row['지역명']}의 유소년 인구 비율은 "
            f"{answer_row['유소년비율']:.1f}%입니다."
        )

    elif quiz_type == "남자인구":
        answer_row = sample.loc[sample["남자인구수"].idxmax()]
        question = "다음 중 남자인구수가 가장 많은 지역은 어디일까요?"
        explanation = (
            f"{answer_row['지역명']}의 남자인구는 "
            f"{format_population(answer_row['남자인구수'])}입니다."
        )

    else:
        answer_row = sample.loc[sample["총인구수"].idxmax()]
        question = "두 지역 중 총인구가 더 많은 곳은 어디일까요?"
        explanation = (
            f"{answer_row['지역명']}의 총인구가 "
            f"{format_population(answer_row['총인구수'])}으로 더 많습니다."
        )

    options = sample["지역명"].tolist()
    random.shuffle(options)

    return {
        "question": question,
        "options": options,
        "answer": answer_row["지역명"],
        "explanation": explanation,
    }


# =========================================================
# 파일 불러오기
# =========================================================
st.markdown(
    """
    <div class="main-title">
        <h1>🎡 대한민국 인구 놀이터</h1>
        <p>인구 데이터를 보고, 비교하고, 맞혀보는 체험형 데이터 놀이터</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 데이터 파일 불러오기
# =========================================================
default_path = Path(DEFAULT_CSV)

try:
    # GitHub 저장소에 기본 CSV가 있으면 자동 사용
    if default_path.exists():
        raw_data = read_population_csv(default_path)
        source_name = DEFAULT_CSV

        with st.sidebar:
            st.header("📂 데이터 설정")
            st.success("✅ GitHub의 기본 데이터를 사용합니다.")
            st.caption(DEFAULT_CSV)

    # 기본 CSV가 없을 때만 업로드 기능 표시
    else:
        with st.sidebar:
            st.header("📂 데이터 설정")
            st.warning("GitHub 저장소에서 기본 CSV를 찾지 못했습니다.")

            uploaded_file = st.file_uploader(
                "행정안전부 연령별 인구 CSV",
                type=["csv"],
                help="연령별 인구현황 월간 CSV 파일을 업로드해 주세요.",
            )

        if uploaded_file is None:
            st.info(
                f"GitHub 저장소에 `{DEFAULT_CSV}` 파일을 올리거나 "
                "사이드바에서 CSV 파일을 업로드해 주세요."
            )
            st.stop()

        raw_data = read_population_csv(uploaded_file)
        source_name = uploaded_file.name

    # 데이터 전처리
    population_all, age_detail = prepare_population_data(raw_data)

except Exception as error:
    st.error(f"데이터를 불러오는 중 문제가 발생했습니다: {error}")
    st.stop()


# 앱의 비교·추천·퀴즈에는 시군구 행만 사용
population = population_all[population_all["지역단계"] == "시군구"].copy()

if population.empty:
    st.error("분석할 시군구 데이터가 없습니다.")
    st.stop()

base_month = population["기준월"].iloc[0]

with st.sidebar:
    st.success(f"불러온 파일: {source_name}")
    st.caption(f"기준월: {base_month}")
    st.caption(f"시군구 수: {len(population):,}개")

    menu = st.radio(
        "🎠 놀이터 메뉴",
        [
            "🔎 인구 한눈에 보기",
            "⚔️ 지역 인구 배틀",
            "🎯 나에게 맞는 지역 찾기",
            "🎲 랜덤 지역 탐험",
            "🧠 인구 퀴즈",
            "🏆 인구 랭킹",
        ],
    )


# =========================================================
# 1. 인구 한눈에 보기
# =========================================================
if menu == "🔎 인구 한눈에 보기":
    st.subheader("🔎 우리 지역 인구 한눈에 보기")

    selected_region = region_selector(population, "선택", "overview")
    row = get_region_row(population, selected_region)

    if row is not None:
        st.markdown(
            f"""
            <div class="fun-card">
                <h3>{population_nickname(row, population)} · {row['지역명']}</h3>
                <p>{describe_region(row, population)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_columns = st.columns(6)
        metric_columns[0].metric("👥 총인구", format_population(row["총인구수"]))
        metric_columns[1].metric("👨 남자", format_population(row["남자인구수"]))
        metric_columns[2].metric("👩 여자", format_population(row["여자인구수"]))
        metric_columns[3].metric("🌱 유소년", f"{row['유소년비율']:.1f}%")
        metric_columns[4].metric("⚡ 생산가능", f"{row['생산가능비율']:.1f}%")
        metric_columns[5].metric("🌳 고령인구", f"{row['고령인구비율']:.1f}%")

        left, right = st.columns(2)

        gender_df = pd.DataFrame(
            {
                "구분": ["남자", "여자"],
                "인구": [row["남자인구수"], row["여자인구수"]],
            }
        )
        gender_chart = px.pie(
            gender_df,
            names="구분",
            values="인구",
            hole=0.58,
            title="남녀 인구 비율",
        )
        left.plotly_chart(gender_chart, use_container_width=True)

        age_group_df = pd.DataFrame(
            {
                "연령구분": ["0~14세", "15~64세", "65세 이상"],
                "인구": [
                    row["유소년인구"],
                    row["생산가능인구"],
                    row["고령인구"],
                ],
            }
        )
        age_group_chart = px.bar(
            age_group_df,
            x="연령구분",
            y="인구",
            text_auto=",",
            title="연령 3계층 인구",
        )
        right.plotly_chart(age_group_chart, use_container_width=True)

        # 5세 단위 인구 피라미드
        region_age = age_detail[
            age_detail["행정구역코드"] == row["행정구역코드"]
        ].copy()

        region_age["연령대"] = region_age["연령"].apply(
            lambda age: "100세 이상"
            if age == 100
            else f"{(age // 5) * 5}~{(age // 5) * 5 + 4}세"
        )

        pyramid = (
            region_age.groupby("연령대", as_index=False)[["남자", "여자"]]
            .sum()
        )

        age_order = [
            f"{start}~{start + 4}세" for start in range(0, 100, 5)
        ] + ["100세 이상"]
        pyramid["연령대"] = pd.Categorical(
            pyramid["연령대"],
            categories=age_order,
            ordered=True,
        )
        pyramid = pyramid.sort_values("연령대")
        pyramid["남자표시"] = -pyramid["남자"]

        figure = go.Figure()
        figure.add_bar(
            y=pyramid["연령대"],
            x=pyramid["남자표시"],
            name="남자",
            orientation="h",
            customdata=pyramid["남자"],
            hovertemplate="남자 %{customdata:,}명<extra></extra>",
        )
        figure.add_bar(
            y=pyramid["연령대"],
            x=pyramid["여자"],
            name="여자",
            orientation="h",
            hovertemplate="여자 %{x:,}명<extra></extra>",
        )
        figure.update_layout(
            title="5세 단위 인구 피라미드",
            barmode="relative",
            height=700,
            xaxis_title="인구수",
            yaxis_title="",
        )
        st.plotly_chart(figure, use_container_width=True)


# =========================================================
# 2. 지역 인구 배틀
# =========================================================
elif menu == "⚔️ 지역 인구 배틀":
    st.subheader("⚔️ 지역 인구 배틀")
    st.write("서로 다른 두 지역을 선택해 인구 특성을 비교해 보세요.")

    col_a, col_b = st.columns(2)

    with col_a:
        region_a = region_selector(population, "A 지역", "battle_a")

    with col_b:
        region_b = region_selector(population, "B 지역", "battle_b")

    if region_a == region_b:
        st.warning("서로 다른 두 지역을 선택해 주세요.")
    else:
        row_a = get_region_row(population, region_a)
        row_b = get_region_row(population, region_b)

        st.markdown(f"### 🟥 {region_a}  VS  🟦 {region_b}")

        comparison = pd.DataFrame(
            {
                "항목": [
                    "총인구(십만 명)",
                    "유소년 비율",
                    "생산가능인구 비율",
                    "고령인구 비율",
                    "여성 비율",
                ],
                region_a: [
                    row_a["총인구수"] / 100000,
                    row_a["유소년비율"],
                    row_a["생산가능비율"],
                    row_a["고령인구비율"],
                    row_a["여자비율"],
                ],
                region_b: [
                    row_b["총인구수"] / 100000,
                    row_b["유소년비율"],
                    row_b["생산가능비율"],
                    row_b["고령인구비율"],
                    row_b["여자비율"],
                ],
            }
        )

        long_comparison = comparison.melt(
            id_vars="항목",
            var_name="지역",
            value_name="값",
        )
        battle_chart = px.bar(
            long_comparison,
            x="항목",
            y="값",
            color="지역",
            barmode="group",
            text_auto=".1f",
            title="지역별 주요 지표 비교",
        )
        st.plotly_chart(battle_chart, use_container_width=True)

        score_a = 0
        score_b = 0
        reasons_a = []
        reasons_b = []

        scoring_items = [
            ("총인구수", "총인구"),
            ("유소년비율", "유소년 비율"),
            ("생산가능비율", "생산가능인구 비율"),
        ]

        for column, label in scoring_items:
            if row_a[column] > row_b[column]:
                score_a += 1
                reasons_a.append(label)
            elif row_b[column] > row_a[column]:
                score_b += 1
                reasons_b.append(label)

        result_cols = st.columns(3)
        result_cols[0].metric(region_a, f"{score_a}점")
        result_cols[1].markdown("## ⚔️")
        result_cols[2].metric(region_b, f"{score_b}점")

        if score_a > score_b:
            st.success(f"🏆 이번 인구 배틀의 승자는 **{region_a}**입니다!")
        elif score_b > score_a:
            st.success(f"🏆 이번 인구 배틀의 승자는 **{region_b}**입니다!")
        else:
            st.info("🤝 두 지역의 결과는 무승부입니다!")

        st.write(
            f"- **{region_a}** 강점: "
            f"{', '.join(reasons_a) if reasons_a else '비슷한 수준'}"
        )
        st.write(
            f"- **{region_b}** 강점: "
            f"{', '.join(reasons_b) if reasons_b else '비슷한 수준'}"
        )
        st.caption(
            "고령인구 비율은 높고 낮음을 승패 점수에 반영하지 않고 "
            "지역의 인구 특성으로만 비교했습니다."
        )


# =========================================================
# 3. 나에게 맞는 지역 찾기
# =========================================================
elif menu == "🎯 나에게 맞는 지역 찾기":
    st.subheader("🎯 나에게 맞는 지역 찾기")
    st.write("원하는 조건의 중요도를 선택하면 인구 데이터로 지역을 추천합니다.")

    selected_sido = st.selectbox(
        "검색 범위",
        ["전국"] + sorted(population["시도"].unique().tolist()),
    )

    recommend_data = (
        population.copy()
        if selected_sido == "전국"
        else population[population["시도"] == selected_sido].copy()
    )

    c1, c2 = st.columns(2)

    with c1:
        youth_weight = st.slider("🌱 아이가 많은 지역", 0, 5, 3)
        working_weight = st.slider("⚡ 생산가능인구 비율이 높은 지역", 0, 5, 3)
        low_elderly_weight = st.slider("🧒 고령인구 비율이 낮은 지역", 0, 5, 2)

    with c2:
        big_population_weight = st.slider("🏙️ 전체 인구가 많은 지역", 0, 5, 1)
        moderate_population_weight = st.slider(
            "🏡 사람이 너무 많지 않은 지역",
            0,
            5,
            1,
        )

    total_weight = (
        youth_weight
        + working_weight
        + low_elderly_weight
        + big_population_weight
        + moderate_population_weight
    )

    if total_weight == 0:
        st.warning("하나 이상의 조건에 중요도를 지정해 주세요.")
    else:
        recommend_data["아이점수"] = safe_minmax(recommend_data["유소년비율"])
        recommend_data["활력점수"] = safe_minmax(recommend_data["생산가능비율"])
        recommend_data["낮은고령점수"] = safe_minmax(
            recommend_data["고령인구비율"],
            reverse=True,
        )
        recommend_data["대도시점수"] = safe_minmax(recommend_data["총인구수"])

        median_population = recommend_data["총인구수"].median()
        max_distance = (
            recommend_data["총인구수"] - median_population
        ).abs().max()

        if max_distance == 0:
            recommend_data["적정규모점수"] = 100
        else:
            recommend_data["적정규모점수"] = (
                100
                - (
                    (recommend_data["총인구수"] - median_population).abs()
                    / max_distance
                    * 100
                )
            )

        recommend_data["추천점수"] = (
            recommend_data["아이점수"] * youth_weight
            + recommend_data["활력점수"] * working_weight
            + recommend_data["낮은고령점수"] * low_elderly_weight
            + recommend_data["대도시점수"] * big_population_weight
            + recommend_data["적정규모점수"] * moderate_population_weight
        ) / total_weight

        top5 = recommend_data.nlargest(5, "추천점수").copy()

        chart = px.bar(
            top5.sort_values("추천점수"),
            x="추천점수",
            y="지역명",
            orientation="h",
            text="추천점수",
            title="나와 잘 맞는 지역 TOP 5",
        )
        chart.update_traces(texttemplate="%{text:.1f}점")
        st.plotly_chart(chart, use_container_width=True)

        for rank, (_, item) in enumerate(top5.iterrows(), start=1):
            reasons = []
            if youth_weight > 0 and item["아이점수"] >= 60:
                reasons.append("유소년 비율이 높습니다.")
            if working_weight > 0 and item["활력점수"] >= 60:
                reasons.append("생산가능인구 비율이 높습니다.")
            if low_elderly_weight > 0 and item["낮은고령점수"] >= 60:
                reasons.append("고령인구 비율이 비교적 낮습니다.")
            if big_population_weight > 0 and item["대도시점수"] >= 60:
                reasons.append("전체 인구가 많은 편입니다.")
            if moderate_population_weight > 0 and item["적정규모점수"] >= 60:
                reasons.append("인구 규모가 중간 수준에 가깝습니다.")

            st.markdown(
                f"""
                <div class="fun-card">
                    <h3>{rank}위 · {item['지역명']}</h3>
                    <p><b>선택 조건 일치 점수: {item['추천점수']:.1f}점</b></p>
                    <p>{' '.join(reasons) if reasons else '선택한 조건을 종합해 추천된 지역입니다.'}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.info(
            "이 추천은 인구 데이터 학습을 위한 체험 결과이며, "
            "실제 거주지나 부동산 선택 기준으로 사용하기에는 충분하지 않습니다."
        )


# =========================================================
# 4. 랜덤 지역 탐험
# =========================================================
elif menu == "🎲 랜덤 지역 탐험":
    st.subheader("🎲 랜덤 지역 탐험")
    st.write("버튼을 눌러 대한민국의 새로운 지역을 발견해 보세요.")

    if "random_region_code" not in st.session_state:
        st.session_state.random_region_code = None

    if st.button("🎲 오늘의 지역 뽑기", use_container_width=True):
        st.session_state.random_region_code = population.sample(1)[
            "행정구역코드"
        ].iloc[0]

    if st.session_state.random_region_code:
        selected = population[
            population["행정구역코드"]
            == st.session_state.random_region_code
        ]

        if not selected.empty:
            row = selected.iloc[0]

            st.markdown(
                f"""
                <div class="fun-card" style="text-align:center;">
                    <h2>{population_nickname(row, population)}</h2>
                    <h1>{row['지역명']}</h1>
                    <p>{describe_region(row, population)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            cols = st.columns(5)
            cols[0].metric("👥 총인구", format_population(row["총인구수"]))
            cols[1].metric("👨 남자", f"{row['남자비율']:.1f}%")
            cols[2].metric("👩 여자", f"{row['여자비율']:.1f}%")
            cols[3].metric("🌱 유소년", f"{row['유소년비율']:.1f}%")
            cols[4].metric("🌳 고령인구", f"{row['고령인구비율']:.1f}%")
    else:
        st.info("위 버튼을 누르면 무작위 지역이 나타납니다.")


# =========================================================
# 5. 인구 퀴즈
# =========================================================
elif menu == "🧠 인구 퀴즈":
    st.subheader("🧠 대한민국 인구 퀴즈")

    if "quiz_number" not in st.session_state:
        st.session_state.quiz_number = 1
        st.session_state.quiz_score = 0
        st.session_state.quiz_question = make_quiz_question(population)
        st.session_state.quiz_answered = False
        st.session_state.quiz_selected = None
        st.session_state.quiz_finished = False

    if not st.session_state.quiz_finished:
        st.progress((st.session_state.quiz_number - 1) / 5)
        st.write(
            f"### 문제 {st.session_state.quiz_number} / 5 "
            f"· 현재 점수 {st.session_state.quiz_score}점"
        )

        quiz = st.session_state.quiz_question
        st.markdown(f"### {quiz['question']}")

        selected_answer = st.radio(
            "정답을 선택하세요.",
            quiz["options"],
            key=f"quiz_radio_{st.session_state.quiz_number}",
            disabled=st.session_state.quiz_answered,
        )

        if not st.session_state.quiz_answered:
            if st.button("✅ 정답 확인", use_container_width=True):
                st.session_state.quiz_selected = selected_answer
                st.session_state.quiz_answered = True

                if selected_answer == quiz["answer"]:
                    st.session_state.quiz_score += 1

                st.rerun()

        else:
            if st.session_state.quiz_selected == quiz["answer"]:
                st.success("정답입니다! 🎉")
            else:
                st.error(f"아쉽습니다. 정답은 **{quiz['answer']}**입니다.")

            st.info(quiz["explanation"])

            button_text = (
                "🏁 결과 보기"
                if st.session_state.quiz_number == 5
                else "➡️ 다음 문제"
            )

            if st.button(button_text, use_container_width=True):
                if st.session_state.quiz_number == 5:
                    st.session_state.quiz_finished = True
                else:
                    st.session_state.quiz_number += 1
                    st.session_state.quiz_question = make_quiz_question(population)
                    st.session_state.quiz_answered = False
                    st.session_state.quiz_selected = None

                st.rerun()

    else:
        score = st.session_state.quiz_score

        if score == 5:
            title = "🏆 대한민국 인구 박사"
        elif score == 4:
            title = "🥇 인구 분석가"
        elif score >= 2:
            title = "🥈 인구 탐험가"
        else:
            title = "🌱 인구 데이터 새싹"

        st.balloons()
        st.markdown(
            f"""
            <div class="fun-card" style="text-align:center;">
                <h1>{title}</h1>
                <h2>최종 점수: {score} / 5점</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔄 다시 도전하기", use_container_width=True):
            for key in [
                "quiz_number",
                "quiz_score",
                "quiz_question",
                "quiz_answered",
                "quiz_selected",
                "quiz_finished",
            ]:
                st.session_state.pop(key, None)

            st.rerun()


# =========================================================
# 6. 인구 랭킹
# =========================================================
elif menu == "🏆 인구 랭킹":
    st.subheader("🏆 대한민국 인구 랭킹")

    ranking_type = st.selectbox(
        "랭킹 기준",
        [
            "총인구가 많은 지역",
            "총인구가 적은 지역",
            "유소년 비율이 높은 지역",
            "고령인구 비율이 높은 지역",
            "생산가능인구 비율이 높은 지역",
        ],
    )

    selected_sido = st.selectbox(
        "지역 범위",
        ["전국"] + sorted(population["시도"].unique().tolist()),
        key="ranking_sido",
    )

    ranking_data = (
        population.copy()
        if selected_sido == "전국"
        else population[population["시도"] == selected_sido].copy()
    )

    ranking_config = {
        "총인구가 많은 지역": ("총인구수", False, "명"),
        "총인구가 적은 지역": ("총인구수", True, "명"),
        "유소년 비율이 높은 지역": ("유소년비율", False, "%"),
        "고령인구 비율이 높은 지역": ("고령인구비율", False, "%"),
        "생산가능인구 비율이 높은 지역": ("생산가능비율", False, "%"),
    }

    column, ascending, unit = ranking_config[ranking_type]

    ranking = ranking_data.sort_values(
        column,
        ascending=ascending,
    ).head(10).copy()
    ranking["순위"] = range(1, len(ranking) + 1)

    first = ranking.iloc[0]
    first_value = (
        f"{int(first[column]):,}{unit}"
        if unit == "명"
        else f"{first[column]:.1f}{unit}"
    )

    st.markdown(
        f"""
        <div class="rank-first">
            <h2>🥇 1위 · {first['지역명']}</h2>
            <h3>{first_value}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_data = ranking.sort_values(column)
    chart = px.bar(
        chart_data,
        x=column,
        y="지역명",
        orientation="h",
        text=column,
        title=f"{ranking_type} TOP 10",
    )

    if unit == "명":
        chart.update_traces(texttemplate="%{text:,.0f}명")
    else:
        chart.update_traces(texttemplate="%{text:.1f}%")

    average_value = ranking_data[column].mean()
    chart.add_vline(
        x=average_value,
        line_dash="dash",
        annotation_text=f"평균 {average_value:,.1f}",
    )
    st.plotly_chart(chart, use_container_width=True)

    table = ranking[["순위", "지역명", column]].copy()
    if unit == "명":
        table[column] = table[column].apply(lambda value: f"{int(value):,}명")
    else:
        table[column] = table[column].apply(lambda value: f"{value:.1f}%")

    st.dataframe(table, use_container_width=True, hide_index=True)


# =========================================================
# 하단 안내
# =========================================================
st.divider()
st.caption(
    f"자료 기준: {base_month} 행정안전부 주민등록 연령별 인구현황 · "
    "이 앱은 데이터 분석 교육용 예시입니다."
)
