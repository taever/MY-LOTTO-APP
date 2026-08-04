import random
import streamlit as st

# ==========================================
# 🎨 로또 번호별 색상 설정 
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
# 🎲 화면 구성 및 추첨 로직
# ==========================================
# 브라우저 탭 설정
st.set_page_config(page_title="행운의 로또 번호 생성기", page_icon="🍀")

# 메인 타이틀
st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>이번 주 1등은 바로 나! 💸</h1>", unsafe_allow_html=True)

# 빨간색 큼지막한 버튼 생성
if st.button("🎯 5천원어치 자동 번호 뽑기", type="primary", use_container_width=True):
    st.write("") # 버튼과 결과창 사이 간격 띄우기
    
    # 📝 결과를 감싸는 하얀색 테두리 박스
    html_content = """
    <div style='background-color: #ffffff; padding: 30px; border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
    """
    
    # A, B, C, D, E 5번 반복
    rows = ['A', 'B', 'C', 'D', 'E']
    for row_label in rows:
        nums = sorted(random.sample(range(1, 46), 6))
        
        html_content += "<div style='display: flex; align-items: center; margin-bottom: 12px; font-family: sans-serif;'>"
        
        # A, B, C 알파벳
        html_content += f"<div style='width: 40px; font-size: 1.2rem; font-weight: bold; color: #666;'>{row_label}</div>"
        
        # 뽑힌 숫자 6개
        for n in nums:
            style = get_lotto_style(n)
            html_content += f"<div style='{style}; width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; margin-right: 10px; border-radius: 5px; font-size: 1.2rem; font-weight: bold;'>{n:02d}</div>"
        
        html_content += "</div>"
        
    html_content += "</div>"
    
    # 조립한 HTML 화면에 그리기
    st.markdown(html_content, unsafe_allow_html=True)
    st.balloons() # 🎉 추첨 완료 풍선!
