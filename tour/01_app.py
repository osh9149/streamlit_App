import streamlit as st
import random
import time

# --- 페이지 설정 ---
st.set_page_config(
    page_title="🎁 랜덤 국내여행 뽑기",
    page_icon="✈️",
    layout="centered"
)

# --- 국내 여행지 데이터베이스 ---
TRAVEL_DATA = [
    {
        "name": "강릉",
        "region": "강원",
        "theme": "해변/힐링",
        "spots": ["안목해변 커피거리", "경포호수", "하슬라아트월드"],
        "food": ["초당순두부", "장칼국수", "강릉 샌드"],
        "desc": "푸른 동해바다와 향긋한 커피 향이 가득한 힐링 도시!"
    },
    {
        "name": "속초",
        "region": "강원",
        "theme": "자연/식도락",
        "spots": ["설악산 국립공원", "속초관광수산시장", "외옹치 바다향기로"],
        "food": ["속초 닭강정", "오징어순대", "아바이순대"],
        "desc": "산과 바다, 그리고 먹거리가 완벽한 삼박자를 이루는 곳!"
    },
    {
        "name": "경주",
        "region": "경상",
        "theme": "역사/문화",
        "spots": ["황리단길", "동궁과 월지", "첨성대"],
        "food": ["십원빵", "경주 쌈밥", "황남빵"],
        "desc": "낮에는 고즈넉한 사적지, 밤에는 야경이 아름다운 감성 도시!"
    },
    {
        "name": "여수",
        "region": "전라",
        "theme": "해변/야경",
        "spots": ["돌산대교 야경", "오동도", "향일암"],
        "food": ["돌산갓김치", "여수 삼합", "게장백반"],
        "desc": "여수 밤바다 노래가 절로 나오는 감성 넘치는 항구 도시!"
    },
    {
        "name": "전주",
        "region": "전라",
        "theme": "식도락/문화",
        "spots": ["전주 한옥마을", "경기전", "덕진공원"],
        "food": ["전주 비빔밥", "콩나물국밥", "초코파이"],
        "desc": "한복 입고 거니는 한옥마을과 입이 즐거운 미식의 수도!"
    },
    {
        "name": "제주 서귀포",
        "region": "제주",
        "theme": "자연/힐링",
        "spots": ["성산일출봉", "쇠소깍", "천지연폭포"],
        "food": ["흑돼지 구이", "고기국수", "한라봉 디저트"],
        "desc": "에메랄드빛 바다와 천혜의 자연이 반겨주는 대표 휴양지!"
    },
    {
        "name": "단양",
        "region": "충청",
        "theme": "액티비티/자연",
        "spots": ["만천하스카이워크", "도담삼봉", "패러글라이딩 정상"],
        "food": ["마늘 떡갈비", "쏘가리 매운탕", "마늘 순대"],
        "desc": "짜릿한 액티비티와 남한강의 비경을 둘 다 즐기는 곳!"
    },
    {
        "name": "남해",
        "region": "경상",
        "theme": "해변/힐링",
        "spots": ["독일마을", "보리암", "다랭이마을"],
        "food": ["멸치쌈밥", "유자 에이드", "독일식 수제맥주"],
        "desc": "이국적인 풍경과 드넓은 바다가 선사하는 느긋한 휴식!"
    },
    {
        "name": "포항",
        "region": "경상",
        "theme": "해변/사진",
        "spots": ["호미곶 해맞이광장", "환호공원 스페이스워크", "영일대 해수욕장"],
        "food": ["포항 물회", "구룡포 과메기", "대게"],
        "desc": "바다 위를 걷는 스페이스워크와 시원한 물회가 기다리는 곳!"
    },
    {
        "name": "안동",
        "region": "경상",
        "theme": "역사/식도락",
        "spots": ["하회마을", "월영교", "병산서원"],
        "food": ["안동찜닭", "간고등어구이", "안동소주"],
        "desc": "전통의 숨결이 느껴지는 마을과 고소한 찜닭이 맞이하는 곳!"
    }
]

# --- 세션 상태 초기화 ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- 헤더 ---
st.title("🎁 랜덤 국내여행 뽑기")
st.caption("어디로 떠날지 고민될 땐? 버튼 하나로 여행지를 결정해보세요!")

st.markdown("---")

# --- 사이드바 필터 ---
st.sidebar.header("🎯 여행 조건 설정")

regions = ["전체"] + sorted(list(set(item["region"] for item in TRAVEL_DATA)))
selected_region = st.sidebar.selectbox("선호 지역", regions)

themes = ["전체"] + sorted(list(set(item["theme"] for item in TRAVEL_DATA)))
selected_theme = st.sidebar.selectbox("여행 테마", themes)

# --- 필터링 로직 ---
filtered_data = TRAVEL_DATA

if selected_region != "전체":
    filtered_data = [item for item in filtered_data if item["region"] == selected_region]

if selected_theme != "전체":
    filtered_data = [item for item in filtered_data if item["theme"] == selected_theme]

st.sidebar.info(f"현재 조건에 맞는 여행지: **{len(filtered_data)}곳**")

# --- 뽑기 실행 영역 ---
st.subheader("🎲 행운의 주사위를 던져보세요")

if not filtered_data:
    st.warning("선택하신 조건에 맞는 여행지가 없습니다. 필터를 변경해주세요!")
else:
    if st.button("🚀 여행지 뽑기!", use_container_width=True, type="primary"):
        # 슬롯머신 랜더링 효과
        slot_placeholder = st.empty()
        
        for _ in range(12):
            temp_pick = random.choice(filtered_data)
            slot_placeholder.markdown(
                f"<h2 style='text-align: center; color: #888888;'>✨ {temp_pick['name']} (으)로 떠나는 중...</h2>", 
                unsafe_allow_html=True
            )
            time.sleep(0.12)
            
        # 최종 결정
        final_pick = random.choice(filtered_data)
        slot_placeholder.empty()
        
        st.balloons()
        
        # 기록 저장
        st.session_state.history.append(final_pick['name'])
        
        # 결과 출력 카드
        st.success(f"🎉 축하합니다! 이번 여행지는 **[{final_pick['name']}]** 입니다!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="지역", value=final_pick["region"])
        with col2:
            st.metric(label="테마", value=final_pick["theme"])
            
        st.markdown(f"> *\"{final_pick['desc']}\"*")
        
        st.markdown("### 📍 추천 명소")
        for spot in final_pick["spots"]:
            st.markdown(f"- {spot}")
            
        st.markdown("### 🍽️ 대표 먹거리")
        for food in final_pick["food"]:
            st.markdown(f"- {food}")
            
        # 네이버 지도 / 구글 지도 검색 링크 제공
        search_query = f"{final_pick['name']} 여행"
        map_url = f"https://map.naver.com/v5/search/{search_query}"
        st.markdown(f"👉 [네이버 지도로 **{final_pick['name']}** 검색하기]({map_url})")

st.markdown("---")

# --- 최근 뽑기 기록 ---
if st.session_state.history:
    with st.expander("📜 이번 세션의 뽑기 히스토리 보기"):
        for idx, item_name in enumerate(reversed(st.session_state.history), 1):
            st.write(f"**{idx}회차:** {item_name}")
