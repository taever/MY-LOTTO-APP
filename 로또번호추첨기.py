import random
import datetime
import requests
import concurrent.futures
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# ==========================================
# 🔑 DB 연동 (수파베이스)
# ==========================================
SUPABASE_URL = "https://pytxrcczpbcnhtwbgkvn.supabase.co/rest/v1/" 
SUPABASE_KEY = "sb_publishable_bkMhLIhY1CO7HWZbutc_2A_FxzBBHgw"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    supabase = None

# ==========================================
# 🎨 색상 및 디자인
# ==========================================
def get_lotto_style(num):
    if num <= 10: return "background-color: #fbc400; color: #111;"
    elif num <= 20: return "background-color: #69c8f2; color: #111;"
    elif num <= 30: return "background-color: #ff7272; color: white;"
    elif num <= 40: return "background-color: #aaaaaa; color: white;"
    else: return "background-color: #b0d840; color: #111;"

# ==========================================
# 📡 로또 3개월(12주) 데이터 수집
# ==========================================
def fetch_draw(draw_no):
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = requests.get(url, timeout=3).json()
        if res.get("returnValue") == "success": return [res[f"drwtNo{i}"] for i in range(1, 7)]
    except: return []
    return []

@st.cache_data(ttl=86400)
def analyze_recent_3_months(): 
    first_draw = datetime.date(2002, 12, 7)
    latest_draw_no = ((datetime.date.today() - first_draw).days // 7) + 1
    frequencies = {i: 0 for i in range(1, 46)}
    
    draws_to_fetch = [latest_draw_no - i for i in range(12)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = executor.map(fetch_draw, draws_to_fetch)
        
    for nums in results:
        for n in nums: frequencies[n] += 1
            
    if sum(frequencies.values()) == 0:
        for _ in range(12):
            for n in random.sample(range(1, 46), 6): frequencies[n] += 1
        return frequencies, True
    return frequencies, False

def generate_weighted_numbers(freq_dict):
    numbers = list(range(1, 46))
    weights = [freq_dict[n] + 1 for n in numbers] 
    picked = []
    for _ in range(6):
        choice = random.choices(numbers, weights=weights, k=1)[0]
        picked.append(choice)
        idx = numbers.index(choice)
        numbers.pop(idx); weights.pop(idx)
    return sorted(picked)

# ==========================================
# 🎲 앱 화면 및 사이드바 메뉴 구성
# ==========================================
st.set_page_config(page_title="종합 복권 명당 플랫폼", page_icon="💸", layout="centered")

with st.sidebar:
    st.title("💸 종합 복권 플랫폼")
    menu = st.radio("메뉴를 선택하세요", ["🎱 로또 6/45", "🎫 연금복권 720+", "🗺️ 우리 동네 명당 찾기", "💾 내 추첨 기록 (마이페이지)"])

# ------------------------------------------
# 🎱 메뉴 1: 로또 6/45
# ------------------------------------------
if menu == "🎱 로또 6/45":
    st.markdown("<h2 style='text-align: center;'>🎱 로또 6/45 추첨기</h2>", unsafe_allow_html=True)
    use_ai = st.toggle("🤖 최근 3개월(12주) 당첨 패턴 분석 및 확률 가중치 반영")
    
    freq_data = None
    if use_ai:
        with st.spinner("최근 3개월 빅데이터 분석 중..."):
            freq_data, is_mock = analyze_recent_3_months()
        if is_mock: st.warning("⚠️ 트래픽 과부하로 가상 시뮬레이션 데이터를 활용합니다.")
        else: st.success("✅ 최근 3개월 실제 당첨 데이터 분석 완료!")
            
    amount = st.number_input("구매 금액 (1게임=1,000원)", min_value=1000, max_value=50000, value=5000, step=1000)
    
    if st.button(f"🎯 {amount:,}원어치 뽑기!", type="primary", use_container_width=True):
        st.write("")
        game_count = amount // 1000
        html_content = "<div style='background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd;'>"
        saved_nums = []
        
        for i in range(game_count):
            row_label = chr(65 + i) if i < 26 else str(i + 1)
            nums = generate_weighted_numbers(freq_data) if (use_ai and freq_data) else sorted(random.sample(range(1, 46), 6))
            saved_nums.append(f"{row_label}: {nums}")
            
            html_content += f"<div style='display: flex; align-items: center; margin-bottom: 12px; font-family: sans-serif;'>"
            html_content += f"<div style='width: 30px; font-weight: bold; color: #666;'>{row_label}</div>"
            for n in nums:
                style = get_lotto_style(n)
                html_content += f"<div style='{style}; width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; margin-right: 8px; border-radius: 5px; font-weight: bold;'>{n:02d}</div>"
            html_content += "</div>"
        
        html_content += "</div>"
        st.markdown(html_content, unsafe_allow_html=True)
        st.balloons()
        
        if "history" not in st.session_state: st.session_state["history"] = []
        st.session_state["history"].append({"type": "로또 6/45", "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "nums": saved_nums})

# ------------------------------------------
# 🎫 메뉴 2: 연금복권 720+
# ------------------------------------------
elif menu == "🎫 연금복권 720+":
    st.markdown("<h2 style='text-align: center; color: #2b6cb0;'>🎫 연금복권 720+ 추첨기</h2>", unsafe_allow_html=True)
    amount = st.number_input("구매 금액 (1게임=1,000원)", min_value=1000, max_value=50000, value=5000, step=1000)
    
    if st.button(f"🎯 {amount:,}원어치 연금복권 뽑기!", type="primary", use_container_width=True):
        st.write("")
        game_count = amount // 1000
        html_content = "<div style='background-color: #f7fafc; padding: 20px; border-radius: 10px; border: 1px solid #cbd5e0;'>"
        saved_nums = []
        
        for i in range(game_count):
            group = random.randint(1, 5)
            nums = [random.randint(0, 9) for _ in range(6)]
            num_str = "".join(map(str, nums))
            saved_nums.append(f"{group}조 {num_str}")
            
            html_content += f"<div style='display: flex; align-items: center; margin-bottom: 15px; font-family: sans-serif; font-size: 1.5rem; font-weight: bold;'>"
            html_content += f"<div style='background-color: #4299e1; color: white; padding: 5px 15px; border-radius: 5px; margin-right: 15px;'>{group}조</div>"
            for idx, n in enumerate(nums):
                color = "#e53e3e" if idx < 3 else "#3182ce"
                html_content += f"<span style='color: {color}; margin-right: 5px;'>{n}</span>"
            html_content += "</div>"
            
        html_content += "</div>"
        st.markdown(html_content, unsafe_allow_html=True)
        st.snow()
        
        if "history" not in st.session_state: st.session_state["history"] = []
        st.session_state["history"].append({"type": "연금복권", "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "nums": saved_nums})

# ------------------------------------------
# 🗺️ 메뉴 3: [찐최종] 전국 우리 동네 명당 찾기
# ------------------------------------------
elif menu == "🗺️ 우리 동네 명당 찾기":
    st.markdown("<h2 style='text-align: center;'>🗺️ 전국 동네별 명당 찾기</h2>", unsafe_allow_html=True)
    st.write("📍 내 동네를 선택하면 주변의 1등 배출점들을 순위별로 찾아줍니다!")
    
    # 대한민국 전국 17개 시/도 및 시/군/구 DB (MVP)
    regions = {
        "서울특별시": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
        "부산광역시": ["강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구", "북구", "사상구", "사하구", "서구", "수영구", "연제구", "영도구", "중구", "해운대구"],
        "대구광역시": ["남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구", "군위군"],
        "인천광역시": ["강화군", "계양구", "미추홀구", "남동구", "동구", "부평구", "서구", "연수구", "옹진군", "중구"],
        "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
        "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
        "울산광역시": ["남구", "동구", "북구", "울주군", "중구"],
        "세종특별자치시": ["세종특별자치시"],
        "경기도": ["가평군", "고양시", "과천시", "광명시", "광주시", "구리시", "군포시", "김포시", "남양주시", "동두천시", "부천시", "성남시", "수원시", "시흥시", "안산시", "안성시", "안양시", "양주시", "양평군", "여주시", "연천군", "오산시", "용인시", "의왕시", "의정부시", "이천시", "파주시", "평택시", "포천시", "하남시", "화성시"],
        "강원특별자치도": ["강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군", "영월군", "원주시", "인제군", "정선군", "철원군", "춘천시", "태백시", "평창군", "홍천군", "화천군", "횡성군"],
        "충청북도": ["괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시", "증평군", "진천군", "청주시", "충주시"],
        "충청남도": ["계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군", "서산시", "서천군", "아산시", "예산군", "천안시", "청양군", "태안군", "홍성군"],
        "전북특별자치도": ["고창군", "군산시", "김제시", "남원시", "무주군", "부안군", "순창군", "완주군", "익산시", "임실군", "장수군", "전주시", "정읍시", "진안군"],
        "전라남도": ["강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시", "담양군", "목포시", "무안군", "보성군", "순천시", "신안군", "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군", "진도군", "함평군", "해남군", "화순군"],
        "경상북도": ["경산시", "경주시", "고령군", "구미시", "김천시", "문경시", "봉화군", "상주시", "성주군", "안동시", "영덕군", "영양군", "영주시", "영천시", "예천군", "울릉군", "울진군", "의성군", "청도군", "청송군", "칠곡군", "포항시"],
        "경상남도": ["거제시", "거창군", "고성군", "김해시", "남해군", "밀양시", "사천시", "산청군", "양산시", "의령군", "진주시", "창녕군", "창원시", "통영시", "하동군", "함안군", "함양군", "합천군"],
        "제주특별자치도": ["서귀포시", "제주시"]
    }
    
    # 도별 중심 좌표
    region_cords = {
        "서울특별시": (37.5665, 126.9780), "부산광역시": (35.1795, 129.0756), "대구광역시": (35.8714, 128.6014),
        "인천광역시": (37.4562, 126.7052), "광주광역시": (35.1595, 126.8526), "대전광역시": (36.3504, 127.3845),
        "울산광역시": (35.5383, 129.3113), "세종특별자치시": (36.4800, 127.2890), "경기도": (37.2749, 127.0093),
        "강원특별자치도": (37.8813, 127.7297), "충청북도": (36.6358, 127.4913), "충청남도": (36.6588, 126.6728),
        "전북특별자치도": (35.8242, 127.1479), "전라남도": (34.8160, 126.4629), "경상북도": (36.5760, 128.5055),
        "경상남도": (35.2382, 128.6923), "제주특별자치도": (33.4890, 126.4983)
    }

    # 1. 2단계 드롭다운 UI 만들기
    col1, col2 = st.columns(2)
    with col1:
        sido = st.selectbox("시/도 선택", list(regions.keys()))
    with col2:
        sigungu = st.selectbox("시/군/구 선택", regions[sido])
        
    base_lat, base_lon = region_cords[sido]
    selected_region = f"{sido} {sigungu}"
    
    # 2. 명당 데이터 시뮬레이션
    shop_count = random.randint(5, 12)
    shops, lats, lons, wins = [], [], [], []
    shop_names = ["대박 복권방", "황금 두꺼비", "스파 복권", "로또 명당", "일등 복권방", "천하제일 명당", "인생역전 로또", "행운의 집", "돈벼락 복권"]
    
    for i in range(shop_count):
        lat_offset = random.uniform(-0.03, 0.03) 
        lon_offset = random.uniform(-0.03, 0.03)
        
        shops.append(f"{selected_region} {random.choice(shop_names)} {i+1}호점")
        lats.append(base_lat + lat_offset)
        lons.append(base_lon + lon_offset)
        # 문자가 아닌 '순수 숫자'로 저장해야 순서대로 정렬됩니다!
        wins.append(random.randint(1, 25)) 
        
    map_data = pd.DataFrame({
        "명당 이름": shops,
        "lat": lats,
        "lon": lons,
        "1등 배출 횟수": wins
    })
    
    # 3. 지도 출력
    st.map(map_data, zoom=11, use_container_width=True)
    
    # 4. 랭킹 정렬 및 표 출력 (해결 완료!)
    # 숫자 기준으로 내림차순 정렬 후, 인덱스(순위)를 다시 맞춥니다.
    sorted_map = map_data.sort_values(by="1등 배출 횟수", ascending=False).reset_index(drop=True)
    
    # 화면에 보여주기 직전에 숫자에 '번'이라는 글자를 붙여줍니다.
    sorted_map['1등 배출 횟수'] = sorted_map['1등 배출 횟수'].astype(str) + "번"
    
    # 0, 1, 2... 대신 1위, 2위, 3위... 로 인덱스(순위) 이름 변경
    sorted_map.index = [f"{i+1}위" for i in range(len(sorted_map))]
    
    st.markdown(f"### 🏆 {selected_region} 주변 최다 배출점 랭킹")
    # 지도 위도/경도 데이터는 숨기고 이름과 횟수만 표로 보여줍니다.
    st.dataframe(sorted_map[["명당 이름", "1등 배출 횟수"]], use_container_width=True)

# ------------------------------------------
# 💾 메뉴 4: 마이페이지 (기록)
# ------------------------------------------
elif menu == "💾 내 추첨 기록 (마이페이지)":
    st.markdown("<h2 style='text-align: center;'>💾 나의 추첨 기록</h2>", unsafe_allow_html=True)
    st.info("이번 주에 내가 뽑은 번호들을 모아볼 수 있습니다. (DB 연동 시 영구 저장됨)")
    
    if "history" in st.session_state and st.session_state["history"]:
        for record in reversed(st.session_state["history"]):
            with st.expander(f"🕒 {record['time']} - {record['type']} 추첨 내역"):
                for line in record["nums"]:
                    st.write(line)
    else:
        st.warning("아직 추첨한 기록이 없습니다. 먼저 번호를 뽑아보세요!")
