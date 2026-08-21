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
# 📡 [핵심 기술 1] 최근 1년(52주) 데이터 고속 수집
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

@st.cache_data(ttl=86400) # 서버 과부하를 막기 위해 분석 결과는 하루(86400초)에 한 번만 갱신!
def analyze_recent_1_year():
    # 현재 회차 계산
    first_draw = datetime.date(2002, 12, 7)
    latest_draw_no = ((datetime.date.today() - first_draw).days // 7) + 1

    frequencies = {i: 0 for i in range(1, 46)}
    draws_to_fetch = [latest_draw_no - i for i in range(52)] # 최근 52주
    
    # 52번을 한 번에 다발로 쏴서 1초 만에 긁어오기 (멀티스레딩)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_draw, draws_to_fetch)
        
    for nums in results:
        for n in nums:
            frequencies[n] += 1
    return frequencies

# ==========================================
# 🧠 [핵심 기술 2] 확률 가중치 기반 추첨 알고리즘
# ==========================================
def generate_weighted_numbers(freq_dict):
    numbers = list(range(1, 46))
    # 많이 나온 번호일수록 뽑힐 확률(가중치)을 높여줍니다. (기본 기회 +1 보장)
    weights = [freq_dict[n] + 1 for n in numbers] 
    
    picked = []
    for _ in range(6):
        choice = random.choices(numbers, weights=weights, k=1)[0]
        picked.append(choice)
        
        # 한 번 뽑힌 번호는 다시 안 뽑히게 목록에서 제거
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

# 💡 [UI 개선] 데이터 분석 토글(스위치)
use_ai = st.toggle("🤖 최근 1년(52주) 당첨 패턴 분석 및 확률 가중치 반영하기")

freq_data = None
if use_ai:
    with st.spinner("초고속 멀티스레딩으로 최근 52주 당첨 데이터를 수집/분석 중입니다... 🚀"):
        freq_data = analyze_recent_1_year()
    
    # 📊 [핵심 기술 3] 스트림릿 내장 차트를 이용한 데이터 시각화
    freq_df = pd.DataFrame(list(freq_data.items()), columns=["번호", "출현 횟수"]).set_index("번호")
    top10 = freq_df.sort_values(by="출현 횟수", ascending=False).head(10)
    
    st.success("✅ 최근 1년 데이터 분석 완료! 가장 많이 나온 번호 Top 10을 확인하세요.")
    st.bar_chart(top10, height=200)

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
        
        # 사용자가 스위치를 켰으면 가중치 기반 알고리즘 적용, 안 켰으면 그냥 무작위
        if use_ai and freq_data:
            nums = generate_weighted_numbers(freq_data)
        else:
            nums = sorted(random.sample(range(1, 46), 6))
        
        # 복사용 텍스트 조립
        num_str = ", ".join([f"{n:02d}" for n in nums])
        copy_text_lines.append(f"{row_label}: {num_str}")
        
        # 화면에 그려질 HTML 조립
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
    st.info("아래 박스 우측 상단 아이콘을 누르면 번호가 복사됩니다.")
    st.code("\n".join(copy_text_lines), language="text")
