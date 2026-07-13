import streamlit as st
from datetime import date

# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="별빛 궁합 테스트",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# 디자인(CSS)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 15%, rgba(157, 107, 255, 0.22), transparent 28%),
            radial-gradient(circle at 85% 10%, rgba(255, 105, 180, 0.18), transparent 25%),
            linear-gradient(145deg, #090b22 0%, #171238 48%, #27144b 100%);
        color: #ffffff;
    }

    .block-container {
        max-width: 1120px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .hero {
        text-align: center;
        padding: 2.2rem 1rem 1.2rem;
    }

    .hero-title {
        font-size: clamp(2.4rem, 6vw, 4.4rem);
        font-weight: 800;
        line-height: 1.1;
        background: linear-gradient(90deg, #fff, #d9c4ff, #ffb9df);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.7rem;
    }

    .hero-subtitle {
        color: #d8d2f3;
        font-size: 1.05rem;
        line-height: 1.8;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.09);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 24px;
        padding: 1.5rem;
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        margin-bottom: 1rem;
    }

    .zodiac-card {
        text-align: center;
        background: linear-gradient(
            145deg,
            rgba(255,255,255,0.15),
            rgba(255,255,255,0.06)
        );
        border: 1px solid rgba(255,255,255,0.22);
        border-radius: 26px;
        padding: 2rem 1.3rem;
        min-height: 330px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.25);
    }

    .zodiac-symbol {
        font-size: 5.2rem;
        line-height: 1.1;
        filter: drop-shadow(0 0 18px rgba(220, 195, 255, 0.55));
    }

    .zodiac-name {
        font-size: 2rem;
        font-weight: 800;
        margin-top: 0.5rem;
    }

    .zodiac-period {
        color: #cabff2;
        font-size: 0.95rem;
        margin-top: 0.3rem;
    }

    .keyword {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.15);
        padding: 0.35rem 0.72rem;
        border-radius: 999px;
        margin: 0.2rem;
        color: #f4efff;
        font-size: 0.9rem;
    }

    .section-title {
        font-size: 1.45rem;
        font-weight: 800;
        margin: 0.3rem 0 1rem;
    }

    .compat-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 1.2rem;
        height: 100%;
    }

    .compat-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }

    .compat-sign {
        font-size: 1.35rem;
        font-weight: 800;
        color: #f6ddff;
    }

    .score-wrap {
        text-align: center;
        padding: 1rem 0 0.4rem;
    }

    .score {
        font-size: clamp(3rem, 7vw, 5rem);
        font-weight: 800;
        line-height: 1;
        background: linear-gradient(90deg, #ffe08a, #ff9fd5, #c8adff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .score-label {
        color: #d7cef1;
        margin-top: 0.5rem;
    }

    .friend-result {
        border-radius: 24px;
        padding: 1.5rem;
        background: linear-gradient(
            135deg,
            rgba(255, 178, 221, 0.14),
            rgba(174, 143, 255, 0.14)
        );
        border: 1px solid rgba(255,255,255,0.2);
    }

    .small-note {
        color: #bdb4d9;
        font-size: 0.84rem;
        line-height: 1.6;
        text-align: center;
        margin-top: 2rem;
    }

    div[data-testid="stDateInput"] > div {
        background: rgba(255,255,255,0.06);
        border-radius: 14px;
    }

    div.stButton > button {
        width: 100%;
        border: 0;
        border-radius: 14px;
        min-height: 3.2rem;
        font-weight: 800;
        font-size: 1.02rem;
        color: #25143f;
        background: linear-gradient(90deg, #e4d1ff, #ffbddd);
        box-shadow: 0 8px 24px rgba(218, 168, 255, 0.25);
        transition: 0.2s ease;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        color: #25143f;
        border: 0;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.14);
        padding: 1rem;
        border-radius: 18px;
    }

    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
    }

    hr {
        border-color: rgba(255,255,255,0.14);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 별자리 정보
# ---------------------------------------------------------
ZODIACS = {
    "염소자리": {
        "symbol": "♑",
        "period": "12월 22일 ~ 1월 19일",
        "element": "흙",
        "keywords": ["책임감", "성실함", "현실적"],
        "description": "목표를 향해 꾸준히 나아가며 믿음직한 모습을 보여주는 타입이에요.",
        "best": ["황소자리", "처녀자리", "전갈자리"],
        "difficult": ["양자리", "천칭자리"],
    },
    "물병자리": {
        "symbol": "♒",
        "period": "1월 20일 ~ 2월 18일",
        "element": "공기",
        "keywords": ["독창적", "자유로움", "호기심"],
        "description": "새로운 생각과 개성을 중요하게 여기며 자유로운 관계를 좋아해요.",
        "best": ["쌍둥이자리", "천칭자리", "사수자리"],
        "difficult": ["황소자리", "전갈자리"],
    },
    "물고기자리": {
        "symbol": "♓",
        "period": "2월 19일 ~ 3월 20일",
        "element": "물",
        "keywords": ["공감력", "감성적", "상상력"],
        "description": "감정이 풍부하고 상대의 마음을 섬세하게 이해하는 따뜻한 타입이에요.",
        "best": ["게자리", "전갈자리", "황소자리"],
        "difficult": ["쌍둥이자리", "사수자리"],
    },
    "양자리": {
        "symbol": "♈",
        "period": "3월 21일 ~ 4월 19일",
        "element": "불",
        "keywords": ["열정적", "솔직함", "도전적"],
        "description": "에너지가 넘치고 마음먹은 일은 빠르게 실행하는 적극적인 타입이에요.",
        "best": ["사자자리", "사수자리", "쌍둥이자리"],
        "difficult": ["게자리", "염소자리"],
    },
    "황소자리": {
        "symbol": "♉",
        "period": "4월 20일 ~ 5월 20일",
        "element": "흙",
        "keywords": ["안정감", "인내심", "신뢰"],
        "description": "편안하고 안정적인 관계를 선호하며 한번 맺은 인연을 소중히 여겨요.",
        "best": ["처녀자리", "염소자리", "물고기자리"],
        "difficult": ["사자자리", "물병자리"],
    },
    "쌍둥이자리": {
        "symbol": "♊",
        "period": "5월 21일 ~ 6월 21일",
        "element": "공기",
        "keywords": ["재치", "소통", "다재다능"],
        "description": "대화와 새로운 경험을 즐기며 주변에 활기를 불어넣는 타입이에요.",
        "best": ["천칭자리", "물병자리", "양자리"],
        "difficult": ["처녀자리", "물고기자리"],
    },
    "게자리": {
        "symbol": "♋",
        "period": "6월 22일 ~ 7월 22일",
        "element": "물",
        "keywords": ["다정함", "보호본능", "섬세함"],
        "description": "가까운 사람을 세심하게 챙기며 정서적인 안정과 신뢰를 중요하게 생각해요.",
        "best": ["전갈자리", "물고기자리", "처녀자리"],
        "difficult": ["양자리", "천칭자리"],
    },
    "사자자리": {
        "symbol": "♌",
        "period": "7월 23일 ~ 8월 22일",
        "element": "불",
        "keywords": ["자신감", "리더십", "따뜻함"],
        "description": "밝고 당당하며 소중한 사람에게 아낌없이 애정을 표현하는 타입이에요.",
        "best": ["양자리", "사수자리", "천칭자리"],
        "difficult": ["황소자리", "전갈자리"],
    },
    "처녀자리": {
        "symbol": "♍",
        "period": "8월 23일 ~ 9월 22일",
        "element": "흙",
        "keywords": ["꼼꼼함", "배려", "분석적"],
        "description": "세심한 관찰력과 현실적인 조언으로 상대에게 든든한 힘이 되어줘요.",
        "best": ["황소자리", "염소자리", "게자리"],
        "difficult": ["쌍둥이자리", "사수자리"],
    },
    "천칭자리": {
        "symbol": "♎",
        "period": "9월 23일 ~ 10월 22일",
        "element": "공기",
        "keywords": ["균형감", "사교적", "센스"],
        "description": "조화로운 관계와 즐거운 대화를 좋아하며 갈등을 부드럽게 조율해요.",
        "best": ["쌍둥이자리", "물병자리", "사자자리"],
        "difficult": ["게자리", "염소자리"],
    },
    "전갈자리": {
        "symbol": "♏",
        "period": "10월 23일 ~ 11월 22일",
        "element": "물",
        "keywords": ["집중력", "진정성", "직관력"],
        "description": "겉으로는 차분하지만 깊은 신뢰와 진솔한 관계를 중요하게 생각해요.",
        "best": ["게자리", "물고기자리", "염소자리"],
        "difficult": ["사자자리", "물병자리"],
    },
    "사수자리": {
        "symbol": "♐",
        "period": "11월 23일 ~ 12월 21일",
        "element": "불",
        "keywords": ["긍정적", "모험심", "솔직함"],
        "description": "새로운 경험과 자유를 즐기며 함께 성장할 수 있는 관계를 좋아해요.",
        "best": ["양자리", "사자자리", "물병자리"],
        "difficult": ["처녀자리", "물고기자리"],
    },
}

ELEMENT_RELATION = {
    frozenset(["불", "공기"]): 88,
    frozenset(["흙", "물"]): 88,
    frozenset(["불", "흙"]): 66,
    frozenset(["불", "물"]): 58,
    frozenset(["공기", "흙"]): 61,
    frozenset(["공기", "물"]): 64,
}

PAIR_MESSAGES = {
    ("불", "불"): ("에너지 넘치는 친구", "함께 도전하면 즐거움이 커져요.", "서로 주도권을 잡으려 할 수 있어요."),
    ("흙", "흙"): ("든든하고 안정적인 친구", "신뢰를 천천히 단단하게 쌓을 수 있어요.", "변화를 너무 조심스러워할 수 있어요."),
    ("공기", "공기"): ("대화가 잘 통하는 친구", "아이디어와 관심사를 자유롭게 나눌 수 있어요.", "감정을 말로만 해결하려 할 수 있어요."),
    ("물", "물"): ("마음을 잘 알아주는 친구", "공감과 정서적 유대가 깊어질 수 있어요.", "서로의 감정에 지나치게 영향을 받을 수 있어요."),
    ("공기", "불"): ("서로에게 활력을 주는 친구", "아이디어와 추진력이 만나 재미있는 일이 많아요.", "흥분했을 때 말이 앞설 수 있어요."),
    ("물", "흙"): ("편안하고 믿음직한 친구", "안정감과 배려가 자연스럽게 어우러져요.", "속마음을 표현하는 속도가 다를 수 있어요."),
    ("불", "흙"): ("서로 다른 장점을 가진 친구", "실행력과 현실감이 만나 좋은 결과를 낼 수 있어요.", "속도와 계획 방식의 차이를 존중해야 해요."),
    ("불", "물"): ("감성과 열정이 만나는 친구", "서로에게 새로운 시각을 줄 수 있어요.", "직설적인 말이 상대에게 상처가 될 수 있어요."),
    ("공기", "흙"): ("생각과 실행을 연결하는 친구", "아이디어를 현실적인 계획으로 발전시킬 수 있어요.", "자유로움과 안정감 사이의 조율이 필요해요."),
    ("공기", "물"): ("대화로 서로를 알아가는 친구", "이성과 감성을 균형 있게 배울 수 있어요.", "감정을 표현하는 방식이 다를 수 있어요."),
}


def get_zodiac(birth_date: date) -> str:
    """월과 일을 기준으로 서양 별자리를 반환합니다."""
    month = birth_date.month
    day = birth_date.day

    if (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "염소자리"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "물병자리"
    if (month == 2 and day >= 19) or (month == 3 and day <= 20):
        return "물고기자리"
    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return "양자리"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "황소자리"
    if (month == 5 and day >= 21) or (month == 6 and day <= 21):
        return "쌍둥이자리"
    if (month == 6 and day >= 22) or (month == 7 and day <= 22):
        return "게자리"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "사자자리"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "처녀자리"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return "천칭자리"
    if (month == 10 and day >= 23) or (month == 11 and day <= 22):
        return "전갈자리"
    return "사수자리"


def compatibility_score(sign1: str, sign2: str) -> int:
    """별자리 추천 관계와 원소 조합을 바탕으로 0~100점 점수를 계산합니다."""
    if sign1 == sign2:
        return 91

    info1 = ZODIACS[sign1]
    info2 = ZODIACS[sign2]

    # 서로 추천 목록에 들어 있으면 최고 궁합
    if sign2 in info1["best"] and sign1 in info2["best"]:
        return 94

    # 한쪽 추천 목록에만 들어 있으면 좋은 궁합
    if sign2 in info1["best"] or sign1 in info2["best"]:
        return 88

    # 서로 어려운 관계로 분류되면 낮은 점수
    if sign2 in info1["difficult"] and sign1 in info2["difficult"]:
        return 48

    # 한쪽만 어려운 관계이면 조율이 필요한 관계
    if sign2 in info1["difficult"] or sign1 in info2["difficult"]:
        return 57

    e1, e2 = info1["element"], info2["element"]

    if e1 == e2:
        return 82

    return ELEMENT_RELATION.get(frozenset([e1, e2]), 70)


def score_grade(score: int) -> tuple[str, str]:
    if score >= 90:
        return "환상의 단짝", "서로의 장점을 자연스럽게 끌어내는 매우 좋은 관계예요."
    if score >= 80:
        return "찰떡 친구", "대화와 활동에서 즐거움을 쉽게 찾을 수 있는 관계예요."
    if score >= 70:
        return "좋은 친구", "서로의 차이를 이해하면 오래 이어질 수 있는 관계예요."
    if score >= 60:
        return "성장형 친구", "다른 점이 많지만 서로에게 새로운 배움을 줄 수 있어요."
    return "노력이 필요한 친구", "표현 방식의 차이를 이해하고 천천히 맞춰가는 것이 중요해요."


def element_message(element1: str, element2: str) -> tuple[str, str, str]:
    key = tuple(sorted([element1, element2]))
    return PAIR_MESSAGES.get(
        key,
        ("서로를 알아가는 친구", "차이를 존중하면 좋은 관계가 될 수 있어요.", "상대의 표현 방식을 먼저 이해해 보세요."),
    )


def render_zodiac_card(name: str, sign: str):
    info = ZODIACS[sign]
    keywords = "".join(
        f'<span class="keyword">#{keyword}</span>' for keyword in info["keywords"]
    )
    st.markdown(
        f"""
        <div class="zodiac-card">
            <div style="color:#d6c8f7; font-weight:600;">{name}의 별자리</div>
            <div class="zodiac-symbol">{info["symbol"]}</div>
            <div class="zodiac-name">{sign}</div>
            <div class="zodiac-period">{info["period"]} · {info["element"]} 원소</div>
            <div style="margin-top:1rem;">{keywords}</div>
            <div style="color:#e6e0f6; line-height:1.7; margin-top:1rem;">
                {info["description"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# 화면 구성
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div style="font-size:2rem;">🌙 ✨ 🔮</div>
        <div class="hero-title">별빛 궁합 테스트</div>
        <div class="hero-subtitle">
            생년월일로 나의 별자리를 확인하고<br>
            나와 잘 맞는 별자리와 친구 궁합을 알아보세요.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🌟 나의 정보 입력</div>', unsafe_allow_html=True)

    input_col1, input_col2 = st.columns([1, 1])
    with input_col1:
        my_name = st.text_input(
            "내 이름 또는 별명",
            value="나",
            max_chars=20,
            placeholder="예: 별빛이",
        )
    with input_col2:
        my_birth = st.date_input(
            "내 생년월일",
            value=date(2000, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="YYYY/MM/DD",
        )

    show_friend = st.toggle("친구와의 궁합도 확인하기", value=True)

    friend_name = "친구"
    friend_birth = date(2000, 7, 1)

    if show_friend:
        friend_col1, friend_col2 = st.columns([1, 1])
        with friend_col1:
            friend_name = st.text_input(
                "친구 이름 또는 별명",
                value="친구",
                max_chars=20,
                placeholder="예: 달빛이",
            )
        with friend_col2:
            friend_birth = st.date_input(
                "친구 생년월일",
                value=date(2000, 7, 1),
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                format="YYYY/MM/DD",
                key="friend_birth",
            )

    analyze = st.button("✨ 별자리와 궁합 알아보기", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if analyze:
    safe_my_name = my_name.strip() or "나"
    safe_friend_name = friend_name.strip() or "친구"

    my_sign = get_zodiac(my_birth)
    my_info = ZODIACS[my_sign]

    st.markdown("---")
    st.markdown(
        '<div class="section-title">🌌 나의 별자리 결과</div>',
        unsafe_allow_html=True,
    )

    result_col1, result_col2 = st.columns([0.9, 1.1], gap="large")

    with result_col1:
        render_zodiac_card(safe_my_name, my_sign)

    with result_col2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">💞 잘 맞는 별자리</div>
                <div class="compat-sign">
                    {" · ".join(my_info["best"])}
                </div>
                <p style="color:#ddd5ef; line-height:1.75;">
                    {my_info["element"]} 원소인 {my_sign}의 안정적인 성향과 자연스럽게
                    어우러지거나, 서로에게 좋은 자극을 주는 별자리예요.
                </p>
            </div>

            <div class="glass-card">
                <div class="section-title">⚡ 조율이 필요한 별자리</div>
                <div class="compat-sign">
                    {" · ".join(my_info["difficult"])}
                </div>
                <p style="color:#ddd5ef; line-height:1.75;">
                    서로의 속도나 감정 표현 방식이 다를 수 있어요.
                    하지만 대화를 충분히 나누면 오히려 서로에게 새로운 시각을 줄 수 있습니다.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="small-note">
            별자리 궁합은 재미를 위한 콘텐츠입니다. 실제 관계는 성격, 대화, 배려와 경험에 따라 달라질 수 있어요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if show_friend:
        friend_sign = get_zodiac(friend_birth)
        friend_info = ZODIACS[friend_sign]
        score = compatibility_score(my_sign, friend_sign)
        grade, grade_description = score_grade(score)
        relation_title, strength, caution = element_message(
            my_info["element"], friend_info["element"]
        )

        st.markdown("---")
        st.markdown(
            '<div class="section-title">🫶 친구와의 별자리 궁합</div>',
            unsafe_allow_html=True,
        )

        friend_col1, friend_col2, friend_col3 = st.columns([1, 0.8, 1], gap="large")

        with friend_col1:
            render_zodiac_card(safe_my_name, my_sign)

        with friend_col2:
            st.markdown(
                f"""
                <div class="score-wrap">
                    <div style="font-size:2rem;">💫</div>
                    <div class="score">{score}</div>
                    <div class="score-label">궁합 점수 / 100</div>
                    <div style="font-size:1.25rem; font-weight:800; margin-top:1rem;">
                        {grade}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(score)

        with friend_col3:
            render_zodiac_card(safe_friend_name, friend_sign)

        st.markdown(
            f"""
            <div class="friend-result">
                <div style="font-size:1.5rem; font-weight:800; margin-bottom:0.7rem;">
                    {my_info["symbol"]} {safe_my_name} × {friend_info["symbol"]} {safe_friend_name}
                </div>
                <div style="font-size:1.15rem; font-weight:700; color:#f6d9ff;">
                    {relation_title}
                </div>
                <p style="color:#e8e1f5; line-height:1.75;">{grade_description}</p>
                <div style="margin-top:1rem;">
                    <b>✨ 관계의 강점</b><br>
                    <span style="color:#dcd4ee;">{strength}</span>
                </div>
                <div style="margin-top:0.8rem;">
                    <b>🌙 주의할 점</b><br>
                    <span style="color:#dcd4ee;">{caution}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("나의 별자리", f"{my_info['symbol']} {my_sign}")
        with metric_col2:
            st.metric("친구 별자리", f"{friend_info['symbol']} {friend_sign}")
        with metric_col3:
            st.metric("궁합 등급", grade)

with st.expander("별자리 날짜 기준 보기"):
    for sign, info in ZODIACS.items():
        st.write(f"{info['symbol']} **{sign}** — {info['period']}")

st.markdown(
    """
    <div class="small-note">
        Made with Streamlit · 별자리 해석은 오락 및 친교 활동용입니다.
    </div>
    """,
    unsafe_allow_html=True,
)
