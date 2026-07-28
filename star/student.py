import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
from html import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="연수과정 돌아보기",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# 역량 데이터
# =========================================================
COMPETENCIES = [
    {
        "code": "A",
        "icon": "①",
        "title": "본질 이해",
        "subtitle": "AI 시대 교육 방향·역할 매트릭스",
        "description": "도구가 아닌 교육의 본질과 교사의 역할을 이해하는 역량",
        "prompt": "AI 시대 교육의 본질과 내 역할 변화에 대해 한 줄로 남겨주세요.",
        "color": "#4F67E8",
    },
    {
        "code": "B",
        "icon": "②③",
        "title": "가치관·윤리",
        "subtitle": "가치관 선언문·윤리 체크리스트",
        "description": "나만의 교육 가치관과 윤리적 기준을 세우는 역량",
        "prompt": "나만의 교육 가치관과 윤리적 기준에 대한 한 줄 회고를 적어주세요.",
        "color": "#5BA4E6",
    },
    {
        "code": "C",
        "icon": "④⑤",
        "title": "데이터·설계",
        "subtitle": "데이터 해석·수업설계 뼈대",
        "description": "데이터를 해석하고 수업 설계 뼈대를 세우는 역량",
        "prompt": "데이터를 해석하고 수업 설계를 구성하며 배운 점을 적어주세요.",
        "color": "#62B8A9",
    },
    {
        "code": "D",
        "icon": "⑥⑦",
        "title": "도구·평가",
        "subtitle": "도구 맥락 활용·과정중심평가 설계",
        "description": "도구를 맥락에 맞게 활용하고 과정중심평가를 설계하는 역량",
        "prompt": "도구 활용과 과정중심평가 설계에서 느낀 점을 적어주세요.",
        "color": "#6861EF",
    },
    {
        "code": "E",
        "icon": "⑧⑨⑩",
        "title": "집합 실행",
        "subtitle": "팀 설계·마이크로티칭 실행",
        "description": "팀을 설계하고 마이크로티칭을 실행하는 역량",
        "prompt": "팀 설계와 마이크로티칭 실행 과정에서 깨달은 점을 한 줄로 적어주세요.",
        "color": "#8558F4",
    },
    {
        "code": "F",
        "icon": "⑪⑫",
        "title": "분석·환류",
        "subtitle": "학습데이터 분석·환류 설계",
        "description": "학습 데이터를 분석하고 환류를 설계하는 역량",
        "prompt": "학습 데이터 분석과 환류 설계의 의미를 한 줄 회고로 작성해주세요.",
        "color": "#4B9C8F",
    },
]

# =========================================================
# 세션 상태
# =========================================================
defaults = {
    "page": "score",
    "scores": {},
    "name": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# 유틸리티
# =========================================================
def score_count():
    return len(st.session_state.scores)


def reflection_count():
    return sum(
        1
        for item in COMPETENCIES
        if st.session_state.get(f"reflection_{item['code']}", "").strip()
    )


def all_complete():
    return score_count() == 6 and reflection_count() == 6


def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()



def reset_all():
    """모든 입력값을 초기화하고 첫 화면으로 이동합니다."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.session_state.page = "score"
    st.session_state.scores = {}
    st.session_state.name = ""


def get_korean_font_path(bold=False):
    """Streamlit Cloud와 일반 Linux 환경에서 사용할 한글 폰트를 찾습니다."""
    candidates = (
        [
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
    )

    for path in candidates:
        try:
            with open(path, "rb"):
                return path
        except OSError:
            continue

    return None


def build_report_pdf(avg_score, total_score, strength, growth, today, trainee_name):
    """최종 리포트를 PDF 파일로 생성합니다."""
    buffer = BytesIO()

    regular_path = get_korean_font_path(False)
    bold_path = get_korean_font_path(True)

    if regular_path and bold_path:
        try:
            pdfmetrics.registerFont(TTFont("Korean", regular_path))
            pdfmetrics.registerFont(TTFont("KoreanBold", bold_path))
            regular_font = "Korean"
            bold_font = "KoreanBold"
        except Exception:
            regular_font = "Helvetica"
            bold_font = "Helvetica-Bold"
    else:
        regular_font = "Helvetica"
        bold_font = "Helvetica-Bold"

    page_width, page_height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # 배경
    pdf.setFillColor(HexColor("#F6F8FC"))
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # 메인 카드
    margin = 28
    card_x = margin
    card_y = 34
    card_w = page_width - margin * 2
    card_h = page_height - 68

    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.roundRect(card_x, card_y, card_w, card_h, 18, fill=1, stroke=0)

    # 제목
    y = page_height - 72
    pdf.setFillColor(HexColor("#172033"))
    pdf.setFont(bold_font, 16)
    pdf.drawString(54, y, "역량 진단 및 한 줄 회고 리포트")

    pdf.setFillColor(HexColor("#8390A6"))
    pdf.setFont(regular_font, 9)
    pdf.drawString(54, y - 18, f"{today} · {trainee_name}")

    # 구분선
    pdf.setStrokeColor(HexColor("#E7ECF3"))
    pdf.line(54, y - 38, page_width - 54, y - 38)

    # 요약 지표
    metric_y = y - 92
    metric_width = 118
    gap = 8
    metrics = [
        ("평균 점수", f"{avg_score:.1f} / 5"),
        ("총점", f"{total_score} / 30"),
        ("역량 평가", f"{score_count()} / 6 완료"),
        ("한 줄 회고", f"{reflection_count()} / 6 완료"),
    ]

    for idx, (label, value) in enumerate(metrics):
        x = 54 + idx * (metric_width + gap)

        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setStrokeColor(HexColor("#E5EAF2"))
        pdf.roundRect(x, metric_y, metric_width, 62, 12, fill=1, stroke=1)

        pdf.setFillColor(HexColor("#71809A"))
        pdf.setFont(regular_font, 8)
        pdf.drawString(x + 12, metric_y + 42, label)

        pdf.setFillColor(HexColor("#172033"))
        pdf.setFont(bold_font, 14)
        pdf.drawString(x + 12, metric_y + 17, value)

    # 강점/보완
    box_y = metric_y - 104
    pdf.setFillColor(HexColor("#EEF5FF"))
    pdf.roundRect(54, box_y, 236, 76, 12, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#4F67E8"))
    pdf.setFont(bold_font, 9)
    pdf.drawString(68, box_y + 54, "강점 역량")
    pdf.setFillColor(HexColor("#172033"))
    pdf.setFont(bold_font, 13)
    pdf.drawString(68, box_y + 31, f"{strength['code']}  {strength['title']}")
    pdf.setFont(regular_font, 9)
    pdf.setFillColor(HexColor("#71809A"))
    pdf.drawString(68, box_y + 14, f"{max(st.session_state.scores.values())}점 · 최고 점수")

    pdf.setFillColor(HexColor("#FFF8E9"))
    pdf.roundRect(305, box_y, 236, 76, 12, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#D88A00"))
    pdf.setFont(bold_font, 9)
    pdf.drawString(319, box_y + 54, "보완 역량")
    pdf.setFillColor(HexColor("#172033"))
    pdf.setFont(bold_font, 13)
    pdf.drawString(319, box_y + 31, f"{growth['code']}  {growth['title']}")
    pdf.setFont(regular_font, 9)
    pdf.setFillColor(HexColor("#71809A"))
    pdf.drawString(319, box_y + 14, f"{min(st.session_state.scores.values())}점 · 보완 필요")

    # 항목별 점수 및 회고
    y = box_y - 32
    pdf.setFillColor(HexColor("#172033"))
    pdf.setFont(bold_font, 11)
    pdf.drawString(54, y, "항목별 점수 및 한 줄 회고")

    y -= 24

    for item in COMPETENCIES:
        score = st.session_state.scores[item["code"]]
        reflection = st.session_state.get(
            f"reflection_{item['code']}",
            ""
        ).strip() or "작성된 회고가 없습니다."

        if y < 100:
            pdf.showPage()
            pdf.setFillColor(HexColor("#F6F8FC"))
            pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)
            y = page_height - 60

        pdf.setFillColor(HexColor("#F8FAFD"))
        pdf.roundRect(54, y - 54, page_width - 108, 62, 10, fill=1, stroke=0)

        pdf.setFillColor(HexColor(item["color"]))
        pdf.roundRect(66, y - 42, 32, 32, 8, fill=1, stroke=0)

        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setFont(bold_font, 11)
        pdf.drawCentredString(82, y - 31, item["code"])

        pdf.setFillColor(HexColor("#172033"))
        pdf.setFont(bold_font, 10)
        pdf.drawString(110, y - 18, f"{item['title']} · {score}점")

        pdf.setFillColor(HexColor("#66728A"))
        pdf.setFont(regular_font, 8)

        # 간단 줄바꿈
        max_chars = 46
        lines = [
            reflection[i:i + max_chars]
            for i in range(0, len(reflection), max_chars)
        ][:2]

        for line_idx, line in enumerate(lines):
            pdf.drawString(110, y - 36 - line_idx * 12, line)

        y -= 72

    pdf.setFillColor(HexColor("#9AA6BA"))
    pdf.setFont(regular_font, 8)
    pdf.drawCentredString(
        page_width / 2,
        48,
        "본 리포트는 연수생 본인의 자기 진단 및 회고를 위해 작성되었습니다."
    )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def build_report_image(avg_score, total_score, strength, growth, today, trainee_name):
    """최종 리포트 요약 이미지를 PNG로 생성합니다."""
    width, height = 1500, 1050
    image = Image.new("RGB", (width, height), "#F6F8FC")
    draw = ImageDraw.Draw(image)

    regular_path = get_korean_font_path(False)
    bold_path = get_korean_font_path(True)

    regular = ImageFont.truetype(regular_path, 30) if regular_path else ImageFont.load_default()
    small = ImageFont.truetype(regular_path, 23) if regular_path else ImageFont.load_default()
    bold = ImageFont.truetype(bold_path, 38) if bold_path else ImageFont.load_default()
    big = ImageFont.truetype(bold_path, 54) if bold_path else ImageFont.load_default()

    # 메인 카드
    draw.rounded_rectangle(
        (38, 38, width - 38, height - 38),
        radius=36,
        fill="#FFFFFF",
        outline="#E1E7F0",
        width=2,
    )

    draw.text((82, 86), "역량 진단 및 한 줄 회고 리포트", fill="#172033", font=bold)
    draw.text((82, 145), f"{today} · {trainee_name}", fill="#8390A6", font=small)

    # 지표 카드
    metrics = [
        ("평균 점수", f"{avg_score:.1f} / 5"),
        ("총점", f"{total_score} / 30"),
        ("역량 평가", f"{score_count()} / 6 완료"),
        ("한 줄 회고", f"{reflection_count()} / 6 완료"),
    ]

    card_w = 315
    for idx, (label, value) in enumerate(metrics):
        x1 = 82 + idx * 342
        draw.rounded_rectangle(
            (x1, 220, x1 + card_w, 350),
            radius=24,
            fill="#FFFFFF",
            outline="#E6EBF3",
            width=2,
        )
        draw.text((x1 + 24, 245), label, fill="#71809A", font=small)
        draw.text((x1 + 24, 290), value, fill="#172033", font=big)

    # 강점/보완
    draw.rounded_rectangle((82, 395, 700, 535), radius=24, fill="#EEF5FF")
    draw.text((112, 423), "강점 역량", fill="#4F67E8", font=small)
    draw.text((112, 470), f"{strength['code']}  {strength['title']}", fill="#172033", font=bold)

    draw.rounded_rectangle((730, 395, 1348, 535), radius=24, fill="#FFF8E9")
    draw.text((760, 423), "보완 역량", fill="#D88A00", font=small)
    draw.text((760, 470), f"{growth['code']}  {growth['title']}", fill="#172033", font=bold)

    # 점수 목록
    draw.text((82, 590), "항목별 점수", fill="#172033", font=bold)

    y = 650
    for item in COMPETENCIES:
        score = st.session_state.scores[item["code"]]

        draw.text((94, y), item["title"], fill="#42506A", font=regular)
        draw.rounded_rectangle((330, y + 8, 1050, y + 30), radius=11, fill="#EDF1F7")
        draw.rounded_rectangle(
            (330, y + 8, 330 + int(720 * score / 5), y + 30),
            radius=11,
            fill=item["color"],
        )
        draw.text((1090, y - 2), str(score), fill="#172033", font=bold)
        y += 56

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output.getvalue()


def build_radar_chart():
    labels = [item["title"] for item in COMPETENCIES]
    values = [st.session_state.scores.get(item["code"], 0) for item in COMPETENCIES]

    closed_labels = labels + [labels[0]]
    closed_values = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=closed_values,
            theta=closed_labels,
            fill="toself",
            fillcolor="rgba(79,103,232,0.16)",
            line=dict(color="#4F67E8", width=3),
            marker=dict(
                size=8,
                color="#4F67E8",
                line=dict(color="#FFFFFF", width=1),
            ),
            hovertemplate="%{theta}: %{r}점<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        height=470,
        margin=dict(l=70, r=70, t=50, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#273044"),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                tickfont=dict(color="#9AA6BA", size=10),
                gridcolor="#E5EAF2",
                linecolor="#E5EAF2",
            ),
            angularaxis=dict(
                tickfont=dict(color="#273044", size=13),
                gridcolor="#E5EAF2",
                linecolor="#E5EAF2",
            ),
        ),
    )
    return fig


# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --bg: #F6F8FC;
        --card: #FFFFFF;
        --border: #DFE5EF;
        --text: #202A3D;
        --sub: #748099;
        --primary: #4F67E8;
    }

    .stApp {
        background: var(--bg);
    }

    .block-container {
        max-width: 1080px;
        padding-top: 24px;
        padding-bottom: 70px;
    }

    header, footer, #MainMenu {
        visibility: hidden;
    }

    .top-title {
        text-align: center;
        font-size: 2.25rem;
        font-weight: 900;
        color: #172033;
        letter-spacing: -0.04em;
        margin-top: 8px;
        margin-bottom: 10px;
    }

    .top-desc {
        max-width: 680px;
        margin: 0 auto 30px auto;
        text-align: center;
        color: #6E7B92;
        line-height: 1.75;
        font-size: 1rem;
    }

    .top-icon {
        width: 58px;
        height: 58px;
        margin: 0 auto 18px;
        border-radius: 16px;
        background: var(--primary);
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 29px;
        box-shadow: 0 10px 22px rgba(79,103,232,0.22);
    }

    .tab-shell {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 8px;
        box-shadow: 0 8px 20px rgba(30,41,59,0.08);
        margin-bottom: 28px;
    }

    .status-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 14px 18px;
        box-shadow: 0 7px 18px rgba(30,41,59,0.07);
        margin-bottom: 30px;
    }

    .status-left {
        display: flex;
        gap: 7px;
        align-items: center;
        font-size: 0.9rem;
        font-weight: 700;
        color: #61708A;
    }

    .status-right {
        border-left: 1px solid #E5EAF2;
        padding-left: 18px;
        font-size: 0.9rem;
        font-weight: 700;
        color: #61708A;
    }

    .step-dot {
        width: 27px;
        height: 9px;
        border-radius: 999px;
        background: #E4E9F2;
        display: inline-block;
    }

    .step-dot.active {
        background: var(--primary);
    }

    .section-title {
        color: var(--text);
        font-size: 1.25rem;
        font-weight: 900;
        margin-bottom: 8px;
    }

    .section-desc {
        color: #71809A;
        font-size: 0.94rem;
        margin-bottom: 24px;
    }

    .stButton > button {
        border-radius: 14px;
        min-height: 52px;
        font-size: 0.96rem;
        font-weight: 800;
        border: 1px solid #DDE3ED;
        background: #FFFFFF;
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
        color: white;
        border-color: var(--primary);
        box-shadow: 0 8px 18px rgba(79,103,232,0.20);
    }

    .stButton > button:disabled {
        background: #E9EDF5 !important;
        border-color: #E9EDF5 !important;
        color: #A8B2C4 !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF;
        border: 1px solid var(--border) !important;
        border-radius: 20px !important;
        box-shadow: 0 9px 24px rgba(30,41,59,0.08);
        margin-bottom: 22px;
        overflow: hidden;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 24px 26px 20px !important;
    }

    .score-info,
    .reflection-header {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .badge {
        width: 54px;
        height: 54px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-size: 0.96rem;
        font-weight: 900;
        flex-shrink: 0;
    }

    .item-title {
        color: #273044;
        font-size: 1.05rem;
        font-weight: 900;
        margin-bottom: 4px;
    }

    .item-sub {
        color: #748099;
        font-size: 0.86rem;
        line-height: 1.45;
    }

    div[data-testid="stTextArea"] textarea {
        min-height: 80px !important;
        height: 80px !important;
        border-radius: 15px !important;
        border: 1px solid #DCE3ED !important;
        background: #F8FAFD !important;
        color: #273044 !important;
        padding: 16px 18px !important;
        resize: none !important;
        box-shadow: none !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(79,103,232,0.10) !important;
    }

    div[data-testid="stTextArea"] textarea::placeholder {
        color: #A3AEC0 !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextArea"] small {
        display: none !important;
    }

    .char-count {
        text-align: right;
        color: #9AA6BA;
        font-size: 0.86rem;
        font-weight: 700;
        margin-top: 5px;
    }


    .dashboard-toolbar {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 18px;
        margin: 6px 0 28px;
    }

    .dashboard-title {
        color: #172033;
        font-size: 1.65rem;
        font-weight: 900;
        letter-spacing: -0.035em;
        margin-bottom: 8px;
    }

    .dashboard-subtitle {
        color: #6F7C93;
        font-size: 0.92rem;
    }

    .toolbar-hint {
        color: #8D99AC;
        font-size: 0.76rem;
        text-align: right;
        margin-top: 5px;
    }

    @media print {
        .dashboard-toolbar,
        div[data-testid="stButton"],
        div[data-testid="stDownloadButton"],
        div[data-testid="stPopover"] {
            display: none !important;
        }

        .stApp {
            background: #FFFFFF !important;
        }

        .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }

        .report-shell {
            box-shadow: none !important;
            border: none !important;
        }
    }

    .report-shell {
        background: #FFFFFF;
        border: 1px solid #E1E7F0;
        border-radius: 28px;
        box-shadow: 0 14px 36px rgba(30,41,59,0.10);
        padding: 32px;
        margin-top: 8px;
    }

    .report-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 20px;
        border-bottom: 1px solid #E8EDF4;
        margin-bottom: 26px;
    }

    .report-title {
        font-size: 1.15rem;
        font-weight: 900;
        color: #172033;
        margin-bottom: 5px;
    }

    .report-date {
        color: #8A96AA;
        font-size: 0.82rem;
    }

    .report-avatar {
        width: 56px;
        height: 56px;
        border-radius: 18px;
        background: #EEF3FF;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--primary);
        font-size: 1.35rem;
        font-weight: 900;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E6EBF3;
        border-radius: 17px;
        padding: 18px 16px;
        box-shadow: 0 7px 16px rgba(30,41,59,0.07);
        min-height: 88px;
    }

    .metric-label {
        color: #71809A;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .metric-value {
        color: #172033;
        font-size: 1.65rem;
        font-weight: 900;
    }

    .metric-unit {
        color: #9AA6BA;
        font-size: 0.8rem;
        margin-left: 3px;
    }

    .panel {
        background: #FFFFFF;
        border: 1px solid #E6EBF3;
        border-radius: 18px;
        padding: 20px;
        height: 100%;
    }

    .panel-title {
        color: #273044;
        font-size: 0.92rem;
        font-weight: 900;
        margin-bottom: 12px;
    }

    .strength-card,
    .growth-card {
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .strength-card {
        background: #EEF5FF;
    }

    .growth-card {
        background: #FFF8E9;
    }

    .small-label {
        font-size: 0.8rem;
        font-weight: 900;
        margin-bottom: 10px;
    }

    .strength-card .small-label {
        color: #4F67E8;
    }

    .growth-card .small-label {
        color: #D88A00;
    }

    .score-row {
        display: grid;
        grid-template-columns: 92px 1fr 24px;
        align-items: center;
        gap: 10px;
        margin: 10px 0;
        font-size: 0.82rem;
        color: #42506A;
    }

    .score-bar {
        height: 9px;
        background: #EDF1F7;
        border-radius: 999px;
        overflow: hidden;
    }

    .score-fill {
        height: 100%;
        border-radius: 999px;
        background: var(--primary);
    }

    .reflection-grid-title {
        border-left: 4px solid var(--primary);
        padding-left: 10px;
        color: #273044;
        font-size: 1rem;
        font-weight: 900;
        margin: 32px 0 18px;
    }

    .reflection-report-card {
        background: #FFFFFF;
        border: 1px solid #E1E7F0;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
        min-height: 150px;
        position: relative;
        box-shadow: 0 5px 14px rgba(30,41,59,0.05);
        overflow: hidden;
    }

    .reflection-report-card::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 5px;
        background: var(--accent);
    }

    .reflection-report-head {
        display: flex;
        gap: 11px;
        align-items: center;
        margin-bottom: 12px;
    }

    .mini-badge {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.8rem;
        font-weight: 900;
        background: var(--accent);
    }

    .reflection-text {
        background: #F8FAFD;
        border-radius: 12px;
        padding: 14px;
        color: #536179;
        font-size: 0.88rem;
        min-height: 55px;
        line-height: 1.55;
    }

    .report-footer {
        text-align: center;
        color: #9AA6BA;
        font-size: 0.78rem;
        padding-top: 24px;
        margin-top: 24px;
        border-top: 1px solid #E8EDF4;
    }

    @media (max-width: 760px) {
        .block-container {
            padding: 16px 12px 50px;
        }

        .top-title {
            font-size: 1.8rem;
        }

        .step-dot {
            width: 17px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 20px 17px 16px !important;
        }

    
    .dashboard-toolbar {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 18px;
        margin: 6px 0 28px;
    }

    .dashboard-title {
        color: #172033;
        font-size: 1.65rem;
        font-weight: 900;
        letter-spacing: -0.035em;
        margin-bottom: 8px;
    }

    .dashboard-subtitle {
        color: #6F7C93;
        font-size: 0.92rem;
    }

    .toolbar-hint {
        color: #8D99AC;
        font-size: 0.76rem;
        text-align: right;
        margin-top: 5px;
    }

    @media print {
        .dashboard-toolbar,
        div[data-testid="stButton"],
        div[data-testid="stDownloadButton"],
        div[data-testid="stPopover"] {
            display: none !important;
        }

        .stApp {
            background: #FFFFFF !important;
        }

        .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }

        .report-shell {
            box-shadow: none !important;
            border: none !important;
        }
    }

    .report-shell {
            padding: 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 공통 상단
# =========================================================
if st.session_state.page != "report":
    st.markdown(
        """
        <div class="top-icon">✓</div>
        <div class="top-title">연수과정 돌아보기</div>
        <div class="top-desc">
            이번 연수를 지나오며 내가 느낀 성장의 깊이를 점수로 표현해보고,
            과정별 배움을 한 줄 회고로 남겨보세요.
            모든 작성이 끝나면 나만의 회고 대시보드와 카드가 완성됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="tab-shell">', unsafe_allow_html=True)
    tab1, tab2 = st.columns(2)

    with tab1:
        if st.button(
            "▥  역량 점수 평가",
            use_container_width=True,
            type="primary" if st.session_state.page == "score" else "secondary",
        ):
            go_to("score")

    with tab2:
        if st.button(
            "✎  한 줄 회고",
            use_container_width=True,
            type="primary" if st.session_state.page == "reflection" else "secondary",
        ):
            go_to("reflection")

    st.markdown("</div>", unsafe_allow_html=True)

    current_count = score_count() if st.session_state.page == "score" else reflection_count()
    current_label = "역량" if st.session_state.page == "score" else "회고"
    other_count = reflection_count() if st.session_state.page == "score" else score_count()
    other_label = "회고" if st.session_state.page == "score" else "역량"

    dots = "".join(
        f'<span class="step-dot {"active" if i < current_count else ""}"></span>'
        for i in range(6)
    )

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-left">
                {dots}
                <span style="margin-left:4px;">{current_label} {current_count}/6</span>
            </div>
            <div class="status-right">{other_label} {other_count}/6</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# 1. 점수 평가
# =========================================================
if st.session_state.page == "score":
    st.markdown(
        """
        <div class="section-title">역량 점수 평가</div>
        <div class="section-desc">
            각 역량 항목에 대해 1~5점을 선택해주세요. (1: 미흡 ~ 5: 최우수)
        </div>
        """,
        unsafe_allow_html=True,
    )

    for item in COMPETENCIES:
        with st.container(border=True):
            left, right = st.columns([1.3, 1])

            with left:
                st.markdown(
                    f"""
                    <div class="score-info">
                        <div class="badge" style="background:{item['color']};">
                            {item['code']}
                        </div>
                        <div>
                            <div class="item-title">{item['title']}</div>
                            <div class="item-sub">{item['description']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with right:
                score_cols = st.columns(6)
                for score in range(1, 6):
                    with score_cols[score - 1]:
                        selected = st.session_state.scores.get(item["code"]) == score
                        if st.button(
                            str(score),
                            key=f"{item['code']}_{score}",
                            use_container_width=True,
                            type="primary" if selected else "secondary",
                        ):
                            st.session_state.scores[item["code"]] = score
                            st.rerun()

                with score_cols[5]:
                    current = st.session_state.scores.get(item["code"], "-")
                    st.markdown(
                        f"""
                        <div style="
                            height:52px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            color:#8994A8;
                            font-weight:800;
                        ">{current}</div>
                        """,
                        unsafe_allow_html=True,
                    )

    _, nav_col = st.columns([3, 1])
    with nav_col:
        if st.button(
            "회고 작성으로 이동  →",
            use_container_width=True,
            disabled=score_count() < 6,
        ):
            go_to("reflection")

# =========================================================
# 2. 한 줄 회고
# =========================================================
elif st.session_state.page == "reflection":
    st.markdown(
        """
        <div class="section-title">과정별 한 줄 회고</div>
        <div class="section-desc">
            각 과정의 핵심 배움을 확인하고, 한 줄로 회고를 작성해주세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for item in COMPETENCIES:
        key = f"reflection_{item['code']}"

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="reflection-header">
                    <div class="badge" style="background:{item['color']};">
                        {item['icon']}
                    </div>
                    <div>
                        <div class="item-title">{item['title']}</div>
                        <div class="item-sub">{item['subtitle']}</div>
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
                height=80,
                key=key,
                label_visibility="collapsed",
            )

            st.markdown(
                f'<div class="char-count">{len(value)} / 120</div>',
                unsafe_allow_html=True,
            )

    back_col, _, final_col = st.columns([1.2, 2, 2.1])

    with back_col:
        if st.button("점수 평가로 이동", use_container_width=True):
            go_to("score")

    with final_col:
        if st.button(
            "최종 대시보드 및 회고 카드 확인하기  →",
            use_container_width=True,
            type="primary",
            disabled=not all_complete(),
        ):
            go_to("report")

# =========================================================
# 3. 최종 리포트
# =========================================================
elif st.session_state.page == "report":
    scores = [st.session_state.scores[item["code"]] for item in COMPETENCIES]
    avg_score = sum(scores) / 6
    total_score = sum(scores)

    max_score = max(scores)
    min_score = min(scores)

    strength_items = [
        item for item in COMPETENCIES
        if st.session_state.scores[item["code"]] == max_score
    ]
    growth_items = [
        item for item in COMPETENCIES
        if st.session_state.scores[item["code"]] == min_score
    ]

    strength = strength_items[0]
    growth = growth_items[0]

    today = datetime.now().strftime("%Y년 %m월 %d일")
    trainee_name = st.session_state.name.strip() or "연수생"

    pdf_bytes = build_report_pdf(
        avg_score,
        total_score,
        strength,
        growth,
        today,
        trainee_name,
    )

    image_bytes = build_report_image(
        avg_score,
        total_score,
        strength,
        growth,
        today,
        trainee_name,
    )

    title_col, action_col = st.columns([1.55, 1])

    with title_col:
        st.markdown(
            """
            <div class="dashboard-toolbar">
                <div>
                    <div class="dashboard-title">역량 진단 대시보드</div>
                    <div class="dashboard-subtitle">
                        입력하신 점수와 회고가 한눈에 정리되었습니다.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with action_col:
        save_col, print_col, reset_col = st.columns([1.45, 0.8, 1])

        with save_col:
            with st.popover("⇩  이미지/PDF 저장", use_container_width=True):
                st.download_button(
                    "PDF 리포트 다운로드",
                    data=pdf_bytes,
                    file_name="역량진단_회고리포트.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

                st.download_button(
                    "PNG 요약 이미지 다운로드",
                    data=image_bytes,
                    file_name="역량진단_대시보드.png",
                    mime="image/png",
                    use_container_width=True,
                )

        with print_col:
            if st.button("▣  인쇄", use_container_width=True):
                components.html(
                    """
                    <script>
                    window.parent.print();
                    </script>
                    """,
                    height=0,
                )

        with reset_col:
            if st.button("↻  다시 작성", use_container_width=True):
                reset_all()
                st.rerun()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="report-header">
            <div>
                <div class="report-title">역량 진단 및 한 줄 회고 리포트</div>
                <div class="report-date">{today} · {trainee_name}</div>
            </div>
            <div class="report-avatar">R</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    metrics = [
        ("평균 점수", f"{avg_score:.1f}", "/ 5"),
        ("총점", str(total_score), "/ 30"),
        ("역량 평가", str(score_count()), "/ 6 완료"),
        ("한 줄 회고", str(reflection_count()), "/ 6 완료"),
    ]

    for col, (label, value, unit) in zip(metric_cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <span class="metric-value">{value}</span>
                    <span class="metric-unit">{unit}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    chart_col, side_col = st.columns([1.35, 0.85])

    with chart_col:
        st.markdown('<div class="panel"><div class="panel-title">역량 방사형 차트</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_radar_chart(),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with side_col:
        st.markdown(
            f"""
            <div class="strength-card">
                <div class="small-label">강점 역량</div>
                <div class="reflection-report-head">
                    <div class="badge" style="background:{strength['color']};">
                        {strength['code']}
                    </div>
                    <div>
                        <div class="item-title">{strength['title']}</div>
                        <div class="item-sub">{max_score}점 · 최고 점수</div>
                    </div>
                </div>
            </div>

            <div class="growth-card">
                <div class="small-label">보완 역량</div>
                <div class="reflection-report-head">
                    <div class="badge" style="background:{growth['color']};">
                        {growth['code']}
                    </div>
                    <div>
                        <div class="item-title">{growth['title']}</div>
                        <div class="item-sub">{min_score}점 · 보완 필요</div>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title">항목별 점수</div>
            """,
            unsafe_allow_html=True,
        )

        for item in COMPETENCIES:
            score = st.session_state.scores[item["code"]]
            width = score * 20

            st.markdown(
                f"""
                <div class="score-row">
                    <span>{item['title']}</span>
                    <div class="score-bar">
                        <div class="score-fill" style="width:{width}%;"></div>
                    </div>
                    <strong>{score}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="reflection-grid-title">한 줄 회고 카드 <span style="font-size:0.8rem;color:#9AA6BA;font-weight:600;">6개 과정</span></div>',
        unsafe_allow_html=True,
    )

    for row_start in range(0, 6, 2):
        cols = st.columns(2)

        for col, item in zip(cols, COMPETENCIES[row_start:row_start + 2]):
            reflection = st.session_state.get(
                f"reflection_{item['code']}",
                ""
            ).strip() or "작성된 회고가 없습니다."

            with col:
                st.markdown(
                    f"""
                    <div class="reflection-report-card" style="--accent:{item['color']};">
                        <div class="reflection-report-head">
                            <div class="mini-badge">{item['icon']}</div>
                            <div>
                                <div class="item-title">{item['title']}</div>
                                <div class="item-sub">{item['subtitle']}</div>
                            </div>
                        </div>
                        <div class="reflection-text">{reflection}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        """
        <div class="report-footer">
            본 리포트는 연수생 본인의 자기 진단 및 회고를 위해 작성되었습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
