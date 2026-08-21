import random
import datetime
import requests
import concurrent.futures
import pandas as pd
import streamlit as st

# ==========================================
# 🎨 로또 번호별 색상 설정 
# ==========================================
def get_lotto_style(num):
    if num <= 10: return "background-color: #fbc400; color: #111;"
    elif num <= 20: return "background-color: #69c8f2; color: #111;"
    elif num <= 30: return "background-color: #ff7272; color: white;"
    elif num <= 40: return "background-color: #aaaaaa; color: white;"
    else: return "background-color: #b0d840; color: #111;"

# ==========================================
# 📡 1년치 데이터 수집 및 예외 처리(Fallback) 방어 로직
# ==========================================
def fetch_draw(draw_no):
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = requests.get(url, timeout=3).json()
        if res.get("returnValue") == "success":
            return [res[f"drwtNo{i}"] for i in range(1, 7)]
    except:
        return []
    return []

@st.cache_data(ttl=86400)
def analyze_recent_1_year():
    first_draw = datetime.date(2002, 12, 7)
    latest_draw_no = ((datetime.date.today() - first_draw).days // 7) + 1
    frequencies = {i: 0 for i in range(1, 46)}
    draws_to_fetch = [latest_draw_no - i for i in range(52)]
    
    # 동행복권 서버에 52번 질문 던지기
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_draw, draws_to_fetch)
        
    for nums in results:
        for n in nums:
            frequencies[n] += 1
            
    # 🚨 [플랜 B 방어 로직] 만약 서버가 차단해서 긁어온 데이터가 '0'이라면?
    if sum(frequencies.values()) == 0:
        # 서비스가 멈추지 않게 1년치(52주) 그럴싸한 가상 데이터를 무작위로 생성해 줍니다!
        for _ in range(52):
            mock_nums = random.sample(range(1, 46), 6)
            for n in mock_nums:
                frequencies[n] += 1
        return frequencies, True # 가상 데이터임을 표시
        
    return frequencies, False

# ==========================================
# 🧠 가중치 기반 추첨 알고리즘
# ==========================================
def generate_weighted_numbers(freq_dict):
    numbers = list(range(1, 46))
    weights = [freq_dict[n] + 1 for n in numbers] 
    
    picked = []
    for _ in range(6):
        choice = random.choices(numbers, weights=weights, k=1)[0]
        picked.append(choice)
        idx = numbers.index(choice)
        numbers.pop(idx)
        weights.pop(idx)
        
    return sorted(picked)

# ==========================================
# 🎲 웹 앱 화면 구성
# ==========================================
st.set_page_config(page_title="빅데이터 로또 분석기", page_icon="📊", layout="centered")

st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>📊 빅데이터 로또 추첨기</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #666; margin-bottom: 20px;'>최근 1년치 당첨 패턴을 분석하여 확률을 높여보세요!</div>", unsafe_allow_html=True)
st.divider()

# 💡 분석 스위치
use_ai = st.toggle("🤖 최근 1년(52주) 당첨 패턴 분석 및 확률 가중치 반영하기")

freq_data = None
if use_ai:
    with st.spinner("최근 52주 당첨 데이터를 수집/분석 중입니다... 🚀"):
        freq_data, is_mock = analyze_recent_1_year()
    
    # 플랜 B(가상 데이터)가 발동되었을 때 화면에 살짝 안내문 띄우기
    if is_mock:
        st.warning("⚠️ 현재 동행복권 서버 접속이 지연되어, 임시 분석(Mock) 데이터로 시뮬레이션 합니다.")
    else:
        st.success("✅ 최근 1년 실제 데이터 분석 완료!")
        
    # 막대그래프 시각화
    freq_df = pd.DataFrame(list(freq_data.items()), columns=["번호", "출현 횟수"]).set_index("번호")
    top10 = freq_df.sort_values(by="출현 횟수", ascending=False).head(10)
    
    st.markdown("### 🏆 최근 1년 가장 많이 나온 번호 Top 10")
    st.bar_chart(top10, height=250)

st.subheader("💰 구매 금액 설정")
amount = st.number_input("자동 추첨을 원하는 금액 (1게임 = 1,000원)", min_value=1000, max_value=50000, value=5000, step=1000)
game_count = amount // 1000

button_label = f"🎯 {amount:,}원어치 빅데이터 추천 뽑기!" if use_ai else f"🎲 {amount:,}원어치 100% 무작위 뽑기!"
button_type = "primary" if use_ai else "secondary"

if st.button(button_label, type=button_type, use_container_width=True):
    st.write("") 
    
    html_content = "<div style='background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>"
    copy_text_lines = [f"[📊 빅데이터 반영 {game_count}게임 추첨 결과]" if use_ai else f"[🎲 무작위 {game_count}게임 추첨 결과]"]
    
    for i in range(game_count):
        row_label = chr(65 + i) if i < 26 else str(i + 1)
        
        if use_ai and freq_data:
            nums = generate_weighted_numbers(freq_data)
        else:
            nums = sorted(random.sample(range(1, 46), 6))
        
        num_str = ", ".join([f"{n:02d}" for n in nums])
        copy_text_lines.append(f"{row_label}: {num_str}")
        
        html_content += "<div style='display: flex; align-items: center; margin-bottom: 12px; font-family: sans-serif;'>"
        html_content += f"<div style='width: 30px; font-size: 1.1rem; font-weight: bold; color: #666;'>{row_label}</div>"
        
        for n in nums:
            style = get_lotto_style(n)
            html_content += f"<div style='{style}; border: 1px solid rgba(0,0,0,0.1); width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; margin-right: 8px; border-radius: 5px; font-size: 1.2rem; font-weight: bold;'>{n:02d}</div>"
        
        html_content += "</div>"
        
    html_content += "</div>"
    st.markdown(html_content, unsafe_allow_html=True)
    st.balloons()
    
    st.write("")
    st.info("아래 박스 우측 상단 📄 아이콘을 누르면 번호가 전체 복사됩니다.")
    st.code("\n".join(copy_text_lines), language="text")

