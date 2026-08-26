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
# 📡 로또 1년치 데이터 수집 (방어 로직 포함)
# ==========================================
def fetch_draw(draw_no):
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = requests.get(url, timeout=3).json()
        if res.get("returnValue") == "success": return [res[f"drwtNo{i}"] for i in range(1, 7)]
    except: return []
    return []

@st.cache_data(ttl=86400)
def analyze_recent_1_year():
    first_draw = datetime.date(2002, 12, 7)
    latest_draw_no = ((datetime.date.today() - first_draw).days // 7) + 1
    frequencies = {i: 0 for i in range(1, 46)}
    draws_to_fetch = [latest_draw_no - i for i in range(52)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_draw, draws_to_fetch)
        
    for nums in results:
        for n in nums: frequencies[n] += 1
            
    if sum(frequencies.values()) == 0:
        for _ in range(52):
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

# 왼쪽 메뉴바(사이드바) 생성
with st.sidebar:
    st.title("💸 종합 복권 플랫폼")
    menu = st.radio("메뉴를 선택하세요", ["🎱 로또 6/45", "🎫 연금복권 720+", "🗺️ 전국 로또 명당 지도", "💾 내 추첨 기록 (마이페이지)"])

# ------------------------------------------
# 🎱 메뉴 1: 로또 6/45
# ------------------------------------------
if menu == "🎱 로또 6/45":
    st.markdown("<h2 style='text-align: center;'>🎱 로또 6/45 추첨기</h2>", unsafe_allow_html=True)
    use_ai = st.toggle("🤖 1년(52주) 당첨 패턴 분석 및 확률 가중치 반영")
    
    freq_data = None
    if use_ai:
        with st.spinner("빅데이터 분석 중..."):
            freq_data, is_mock = analyze_recent_1_year()
        if is_mock: st.warning("⚠️ 트래픽 과부하로 가상 시뮬레이션 데이터를 활용합니다.")
        else: st.success("✅ 최근 1년 실제 당첨 데이터 분석 완료!")
            
    amount = st.number_input("구매 금액 (1게임=1,000원)", min_value=1000, max_value=50000, value=5000, step=1000, key="lotto_amt")
    
    if st.button(f"🎯 {amount:,}원어치 뽑기!", type="primary", use_container_width=True):
        st.write("")
        game_count = amount // 1000
        html_content = "<div style='background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd;'>"
        
        saved_nums = [] # DB 저장용 리스트
        
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
        
        # 임시 세션 기록에 저장 (마이페이지용)
        if "history" not in st.session_state: st.session_state["history"] = []
        st.session_state["history"].append({"type": "로또 6/45", "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "nums": saved_nums})

# ------------------------------------------
# 🎫 메뉴 2: 연금복권 720+
# ------------------------------------------
elif menu == "🎫 연금복권 720+":
    st.markdown("<h2 style='text-align: center; color: #2b6cb0;'>🎫 연금복권 720+ 추첨기</h2>", unsafe_allow_html=True)
    st.info("연금복권은 1조~5조 중 하나, 그리고 0~9까지의 숫자 6개로 이루어집니다.")
    
    amount = st.number_input("구매 금액 (1게임=1,000원)", min_value=1000, max_value=50000, value=5000, step=1000, key="pen_amt")
    
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
# 🗺️ 메뉴 3: 전국 로또 명당 지도
# ------------------------------------------
elif menu == "🗺️ 전국 로또 명당 지도":
    st.markdown("<h2 style='text-align: center;'>🗺️ 전국 1등 배출 명당 지도</h2>", unsafe_allow_html=True)
    st.write("내 주변에서 1등이 가장 많이 나온 명당의 위치를 확인해 보세요!")
    
    # 대한민국 전국 1등 최다 배출점 가라 데이터 (실제 좌표)
    spot_data = pd.DataFrame({
        "명당 이름": ["서울 노원 스파", "부산 부일카서비스", "대구 일등복권", "용인 로또휴게소", "종로 제이복권방", "수원 웅진"],
        "lat": [37.6551, 35.1432, 35.8450, 37.2662, 37.5701, 37.2635],
        "lon": [127.0601, 129.0089, 128.5360, 127.1009, 126.9830, 127.0286],
        "1등 배출": ["45번", "39번", "30번", "22번", "18번", "15번"]
    })
    
    # 지도에 좌표 찍기
    st.map(spot_data, zoom=6, use_container_width=True)
    
    # 표로 자세히 보여주기
    st.markdown("### 🏆 최다 배출점 리스트")
    st.dataframe(spot_data[["명당 이름", "1등 배출"]], use_container_width=True)

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
