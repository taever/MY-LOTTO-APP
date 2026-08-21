import random
import datetime
import requests
import streamlit as st

# ==========================================
# 🎨 로또 번호별 색상 설정 (기존 둥근 네모 UI 유지)
# ==========================================
def get_lotto_style(num):
    if num <= 10:
        return "background-color: #fbc400; color: #111;" # 1~10: 노랑
    elif num <= 20:
        return "background-color: #69c8f2; color: #111;" # 11~20: 파랑
    elif num <= 30:
        return "background-color: #ff7272; color: white;" # 21~30: 빨강
    elif num <= 40:
        return "background-color: #aaaaaa; color: white;" # 31~40: 회색
    else:
        return "background-color: #b0d840; color: #111;" # 41~45: 초록

# ==========================================
# 📡 [과제 3] 최신 로또 당첨 번호 API 불러오기
# ==========================================
@st.cache_data(ttl=3600) # 서버 과부하 방지를 위해 1시간 동안만 저장해두고 씁니다.
def get_latest_lotto():
    # 로또 1회차 날짜를 기준으로 이번 주가 몇 회차인지 계산
    first_draw_date = datetime.date(2002, 12, 7)
    today = datetime.date.today()
    days_passed = (today - first_draw_date).days
    draw_no = (days_passed // 7) + 1
    
    # 동행복권 API 찔러보기
    for _ in range(3): 
        try:
            url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
            res = requests.get(url, timeout=5).json()
            if res.get("returnValue") == "success":
                winning_nums = [res[f"drwtNo{i}"] for i in range(1, 7)]
                bonus_num = res["bnusNo"]
                return draw_no, winning_nums, bonus_num, res["drwNoDate"]
        except Exception:
            pass
        # 토요일 추첨 전이면 이전 회차를 찾아봅니다.
        draw_no -= 1
    return None, [], None, ""

# ==========================================
# 🎲 화면 구성 및 추첨/채점 로직
# ==========================================
st.set_page_config(page_title="행운의 로또 번호 생성기", page_icon="🍀", layout="centered")

st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>이번 주 1등은 바로 나! 💸</h1>", unsafe_allow_html=True)

# 1. 최신 당첨 번호 화면에 띄우기
draw_no, win_nums, bonus_num, draw_date = get_latest_lotto()

if draw_no:
    st.markdown(f"<div style='text-align: center; color: #666; margin-bottom: 20px;'>👑 <b>제 {draw_no}회</b> 실제 당첨 번호 ({draw_date})</div>", unsafe_allow_html=True)
    
    win_html = "<div style='display: flex; justify-content: center; align-items: center; margin-bottom: 30px; font-family: sans-serif;'>"
    for n in win_nums:
        style = get_lotto_style(n)
        win_html += f"<div style='{style}; width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; margin-right: 10px; border-radius: 5px; font-size: 1.2rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>{n:02d}</div>"
    
    win_html += "<div style='font-size: 1.5rem; margin-right: 10px; color: #666;'>+</div>"
    bonus_style = get_lotto_style(bonus_num)
    win_html += f"<div style='{bonus_style}; width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; border-radius: 5px; font-size: 1.2rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>{bonus_num:02d}</div>"
    win_html += "</div>"
    st.markdown(win_html, unsafe_allow_html=True)

st.divider()

# 2. [과제 1] 구매 금액 입력 기능 추가
st.subheader("💰 구매 금액 설정")
amount = st.number_input("자동 추첨을 원하는 금액을 입력하세요 (1게임 = 1,000원)", min_value=1000, max_value=50000, value=5000, step=1000)
game_count = amount // 1000

if st.button(f"🎯 {amount:,}원어치 자동 번호 뽑기! ({game_count}게임)", type="primary", use_container_width=True):
    st.write("") 
    
    html_content = "<div style='background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>"
    copy_text_lines = [f"[🍀 로또 자동 {game_count}게임 추첨 결과]"]
    
    for i in range(game_count):
        row_label = chr(65 + i) if i < 26 else str(i + 1)
        nums = sorted(random.sample(range(1, 46), 6))
        
        # 3. [과제 3 연결] 채점 로직
        match_count = len(set(nums) & set(win_nums))
        has_bonus = bonus_num in nums
        
        if match_count == 6:
            rank = "🎉 1등!"
            rank_color = "#e53e3e"
        elif match_count == 5 and has_bonus:
            rank = "🎊 2등!"
            rank_color = "#dd6b20"
        elif match_count == 5:
            rank = "✨ 3등"
            rank_color = "#d69e2e"
        elif match_count == 4:
            rank = "👍 4등"
            rank_color = "#3182ce"
        elif match_count == 3:
            rank = "😊 5등"
            rank_color = "#38a169"
        else:
            rank = "낙첨"
            rank_color = "#a0aec0"
        
        # 복사용 텍스트 조립
        num_str = ", ".join([f"{n:02d}" for n in nums])
        copy_text_lines.append(f"{row_label}: {num_str} ({rank})")
        
        html_content += "<div style='display: flex; align-items: center; margin-bottom: 12px; font-family: sans-serif;'>"
        html_content += f"<div style='width: 30px; font-size: 1.1rem; font-weight: bold; color: #666;'>{row_label}</div>"
        
        for n in nums:
            style = get_lotto_style(n)
            # 당첨 번호와 일치하면 빨간색 굵은 테두리로 눈에 띄게 강조!
            border = "border: 3px solid #ff0000; box-sizing: border-box;" if n in win_nums else "border: 1px solid transparent; box-sizing: border-box;"
            html_content += f"<div style='{style}; {border} width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; margin-right: 8px; border-radius: 5px; font-size: 1.2rem; font-weight: bold;'>{n:02d}</div>"
        
        # 우측에 채점 결과 (1등~낙첨) 표시
        html_content += f"<div style='margin-left: auto; font-size: 1rem; font-weight: bold; color: {rank_color};'>{rank}</div>"
        html_content += "</div>"
        
    html_content += "</div>"
    st.markdown(html_content, unsafe_allow_html=True)
    st.balloons()
    
    st.write("")
    
    # 4. [과제 2] 전체 복사 기능 구현
    st.subheader("📋 전체 번호 복사하기")
    st.info("아래 박스 오른쪽 위 코너에 있는 📄 모양 아이콘을 누르면 전체 번호가 한 번에 복사됩니다!")
    st.code("\n".join(copy_text_lines), language="text")
