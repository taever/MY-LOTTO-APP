import random
import time
import datetime
import os
import requests
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
# 📡 당첨번호 조회 (당첨 확인 기능에서 사용)
#
# v0.6까지 있던 "최근 N주 당첨 패턴 분석/가중치 추첨" 기능은 걷어냈다.
# 동행복권 서버가 해외(클라우드) IP를 차단해서, 배포 환경에서는 항상
# Mock(가상) 데이터로만 동작해 실제로는 의미가 없었기 때문이다.
# 회차 하나를 조회하는 이 함수 자체도 배포 환경에서는 막힐 수 있는데,
# '당첨 확인' 기능에서는 실패 시 화면에 바로 안내 문구를 띄우고 끝내면
# 되므로(별도 Mock 로직 불필요) 그대로 남겨둔다.
# ==========================================
FIRST_DRAW_DATE = datetime.date(2002, 12, 7)


def latest_draw_no():
    return ((datetime.date.today() - FIRST_DRAW_DATE).days // 7) + 1


def fetch_draw_raw(draw_no):
    """해당 회차의 원본 응답을 그대로 돌려준다 (당첨 확인 기능에서 보너스볼까지 써야 해서)."""
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = requests.get(url, timeout=3).json()
        if res.get("returnValue") == "success":
            return res
    except Exception:
        return None
    return None



# ==========================================
# 🎡 연금복권 720+ 추첨 (조 + 6자리)
# ==========================================
def generate_pension_number():
    jo = random.randint(1, 5)
    digits = f"{random.randint(0, 999999):06d}"
    return jo, digits


# ==========================================
# 🏆 당첨 등수 판정 (로또 6/45)
# ==========================================
def judge_rank(my_numbers, win_numbers, bonus):
    match = len(set(my_numbers) & set(win_numbers))
    bonus_hit = bonus in my_numbers
    if match == 6:
        return 1, "1등 🎉🎉🎉"
    if match == 5 and bonus_hit:
        return 2, "2등 🎉🎉"
    if match == 5:
        return 3, "3등 🎉"
    if match == 4:
        return 4, "4등"
    if match == 3:
        return 5, "5등"
    return 0, "낙첨"


# ==========================================
# 🗺️ 명당 지도 데이터
#
# 출처: 공공데이터포털 "기획예산처_온라인복권 1등 당첨 판매점 현황 정보"
#   https://www.data.go.kr/data/15059963/fileData.do
#   (무료·로그인 불필요, CSV, 상호/지역(시군구, 축약형 표기: '서울 강남구')/
#    1등 자동 당첨 건수. 인코딩은 CP949)
#
# 이 데이터셋은 좌표가 없다. v0.5에서는 40여 개 지역만 손으로 좌표를 넣어뒀는데
# 실제 데이터는 177개 세부 지역(구·군 단위)까지 나뉘어 있어 감당이 안 됐다.
# v0.6부터는 Nominatim(OpenStreetMap, API 키 불필요)으로 지역명을
# 실시간 지오코딩해서 좌표를 자동으로 채운다. 결과는 30일 캐시.
# ==========================================
STORE_CSV_PATH = "lotto_stores.csv"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


@st.cache_data(ttl=86400)
def load_store_data():
    """공식 CSV(CP949)를 읽는다. 없으면 예시 데이터로 대체(Fallback)한다."""
    if os.path.exists(STORE_CSV_PATH):
        df = None
        for enc in ("cp949", "utf-8-sig", "utf-8"):
            try:
                df = pd.read_csv(STORE_CSV_PATH, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            return _sample_store_df(), True

        df.columns = [c.strip() for c in df.columns]
        rename_map = {}
        for c in df.columns:
            if "상호" in c: rename_map[c] = "상호"
            elif "지역" in c: rename_map[c] = "지역"
            elif "건수" in c: rename_map[c] = "건수"
        df = df.rename(columns=rename_map)
        if not {"상호", "지역", "건수"}.issubset(df.columns):
            return _sample_store_df(), True
        df["건수"] = pd.to_numeric(df["건수"], errors="coerce").fillna(0).astype(int)
        return df[["상호", "지역", "건수"]], False
    else:
        return _sample_store_df(), True


def _sample_store_df():
    sample = [
        ("복권명당 강남점", "서울 강남구", 4),
        ("행운복권방", "서울 강남구", 2),
        ("로또명당 수원점", "경기 수원시 팔달구", 3),
        ("복권천국 해운대점", "부산 해운대구", 3),
        ("연금복권 전주점", "전북 전주시 덕진구", 2),
    ]
    return pd.DataFrame(sample, columns=["상호", "지역", "건수"])


@st.cache_data(ttl=60 * 60 * 24 * 30)  # 좌표는 안 바뀌니 30일 캐시
def geocode_region(region_name):
    """'지역명'을 위도/경도로 변환한다 (Nominatim, API 키 불필요). 실패하면 None."""
    try:
        params = {"q": f"대한민국 {region_name}", "format": "json", "limit": 1}
        headers = {"User-Agent": "lotto-analysis-app/1.0 (school assignment)"}
        res = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=5).json()
        if res:
            return float(res[0]["lat"]), float(res[0]["lon"])
    except Exception:
        pass
    return None


def geocode_regions_with_progress(region_list):
    """여러 지역을 지오코딩한다. Nominatim 정책상 초당 1건으로 속도를 제한한다.
    (캐시된 지역은 API를 다시 안 부르므로, 두 번째 조회부터는 즉시 끝난다)
    """
    coords = {}
    progress = st.progress(0.0, text="지역 좌표 확인 중...")
    for i, r in enumerate(region_list):
        c = geocode_region(r)
        if c:
            coords[r] = c
        progress.progress((i + 1) / max(len(region_list), 1), text=f"지역 좌표 확인 중... ({i+1}/{len(region_list)})")
        time.sleep(1.05)  # Nominatim 정책: 초당 1건 이하
    progress.empty()
    return coords


# ==========================================
# 🎲 화면 구성
# ==========================================
st.set_page_config(page_title="빅데이터 로또 분석기", page_icon="📊", layout="centered")

st.sidebar.title("📊 빅데이터 복권 분석기")
menu = st.sidebar.radio(
    "메뉴",
    ["🎲 로또 6/45 추첨기", "🎡 연금복권 720+ 추첨기", "✅ 당첨 확인", "🗺️ 명당 지도", "📜 내 추첨 기록"],
)

if "history" not in st.session_state:
    st.session_state.history = []  # [{시각, 종류, 결과}, ...] 세션 동안만 유지


def add_history(kind, text):
    st.session_state.history.append({
        "시각": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "종류": kind,
        "결과": text,
    })


# ------------------------------------------------------------------
# 페이지 1) 로또 6/45 추첨기
# ------------------------------------------------------------------
if menu == "🎲 로또 6/45 추첨기":
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>📊 로또 자동 추첨기</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #666; margin-bottom: 20px;'>완전 무작위로 번호를 뽑아드립니다</div>", unsafe_allow_html=True)
    st.divider()
    # v0.6까지 있던 "최근 N주 당첨 패턴 분석" 가중치 기능은 제거했다.
    # 동행복권 서버가 해외(클라우드) IP를 차단해서, 배포 환경에서는 항상
    # Mock(가상) 데이터로만 동작해 실제로는 의미가 없었다 — 3차수 보고서에서
    # 이미 확인된 한계다. 진짜로 풀려면 한국 소재 서버를 거치는 중계(프록시)가
    # 필요한데 별도 인프라 비용이 들어가서, 이번 차수에서는 기능 자체를 걷어내고
    # 순수 무작위 추첨만 남겨 사용자에게 실제로 동작하지 않는 기능을 보여주지
    # 않기로 했다.

    st.subheader("💰 구매 금액 설정")
    amount = st.number_input("자동 추첨을 원하는 금액 (1게임 = 1,000원)", min_value=1000, max_value=50000, value=5000, step=1000)
    game_count = amount // 1000

    if st.button(f"🎲 {amount:,}원어치 무작위 뽑기!", type="primary", use_container_width=True):
        st.write("")

        html_content = "<div style='background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>"
        copy_text_lines = [f"[🎲 무작위 {game_count}게임 추첨 결과]"]
        drawn_games = []

        for i in range(game_count):
            row_label = chr(65 + i) if i < 26 else str(i + 1)

            nums = sorted(random.sample(range(1, 46), 6))
            drawn_games.append(nums)

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

        # CSV 다운로드
        export_df = pd.DataFrame(
            [{"게임": chr(65 + i) if i < 26 else str(i + 1), "번호": ", ".join(f"{n:02d}" for n in g)}
             for i, g in enumerate(drawn_games)]
        )
        st.download_button(
            "⬇️ 뽑은 번호 CSV로 저장",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"로또번호_{datetime.date.today()}.csv",
            mime="text/csv",
        )

        add_history("로또 6/45", " / ".join(copy_text_lines[1:]))


# ------------------------------------------------------------------
# 페이지 2) 연금복권 720+ 추첨기
# ------------------------------------------------------------------
elif menu == "🎡 연금복권 720+ 추첨기":
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>🎡 연금복권 720+ 추첨기</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #666; margin-bottom: 20px;'>조(1~5) + 6자리 번호를 무작위로 뽑아드립니다</div>", unsafe_allow_html=True)
    st.divider()

    count = st.slider("몇 장 뽑을까요?", min_value=1, max_value=5, value=1)

    if st.button("🎡 연금복권 번호 뽑기", type="primary", use_container_width=True):
        lines = ["[🎡 연금복권 720+ 추첨 결과]"]
        for i in range(count):
            jo, digits = generate_pension_number()
            label = chr(65 + i)
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;font-family:sans-serif;'>"
                f"<div style='width:26px;font-weight:bold;color:#666;'>{label}</div>"
                f"<div style='background:#122D43;color:white;padding:8px 14px;border-radius:6px;font-weight:bold;'>{jo}조</div>"
                f"<div style='background:#eee;padding:8px 14px;border-radius:6px;font-size:1.2rem;font-weight:bold;letter-spacing:2px;'>{digits}</div>"
                f"</div>", unsafe_allow_html=True)
            lines.append(f"{label}: {jo}조 {digits}")

        st.code("\n".join(lines), language="text")
        add_history("연금복권 720+", " / ".join(lines[1:]))


# ------------------------------------------------------------------
# 페이지 3) 당첨 확인 (신규) — 실제 회차 결과와 내 번호를 대조
# ------------------------------------------------------------------
elif menu == "✅ 당첨 확인":
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>✅ 로또 당첨 확인</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #666; margin-bottom: 20px;'>회차를 고르고 내 번호를 넣으면 실제 결과와 바로 대조합니다</div>", unsafe_allow_html=True)
    st.divider()

    latest_no = latest_draw_no()
    draw_no = st.number_input("확인할 회차", min_value=1, max_value=latest_no, value=latest_no, step=1)

    my_numbers = st.multiselect("내가 산 번호 6개를 선택하세요", options=list(range(1, 46)), max_selections=6)

    if st.button("결과 확인", type="primary", use_container_width=True):
        if len(my_numbers) != 6:
            st.warning("번호를 정확히 6개 선택해주세요.")
        else:
            with st.spinner("당첨 결과를 조회하는 중..."):
                res = fetch_draw_raw(draw_no)
            if not res:
                st.error("해당 회차 결과를 불러오지 못했습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요.")
            else:
                win_numbers = [res[f"drwtNo{i}"] for i in range(1, 7)]
                bonus = res["bnusNo"]
                rank, label = judge_rank(my_numbers, win_numbers, bonus)

                win_str = ", ".join(f"{n:02d}" for n in win_numbers)
                st.write(f"**{draw_no}회 당첨번호**: {win_str}  (보너스 {bonus:02d})")
                st.write(f"**내 번호**: {', '.join(f'{n:02d}' for n in sorted(my_numbers))}")

                if rank == 1:
                    st.success(f"🎉 {label}")
                elif rank in (2, 3):
                    st.success(label)
                elif rank in (4, 5):
                    st.info(label)
                else:
                    st.write(label)

                add_history("당첨 확인", f"{draw_no}회 / 내번호 {sorted(my_numbers)} / 결과: {label}")


# ------------------------------------------------------------------
# 페이지 4) 명당 지도
# ------------------------------------------------------------------
elif menu == "🗺️ 명당 지도":
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>🗺️ 로또 1등 명당 지도</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align: center; color: #666; margin-bottom: 20px;'>"
        "공공데이터포털 '온라인복권 1등 당첨 판매점 현황 정보' 기반</div>",
        unsafe_allow_html=True)
    st.divider()

    df, is_sample = load_store_data()
    if is_sample:
        st.warning(
            "⚠️ 공식 데이터 파일(lotto_stores.csv)을 찾지 못해 예시 데이터로 보여드립니다.\n\n"
            "https://www.data.go.kr/data/15059963/fileData.do 에서 CSV를 내려받아 "
            "앱 폴더에 'lotto_stores.csv' 로 넣으면 실제 데이터로 바뀝니다."
        )
    else:
        st.success(f"✅ 공식 데이터 {len(df):,}건 로딩 완료")

    # 전국 Top 10 (필터와 무관하게 항상 보여준다)
    st.markdown("### 🏆 전국 1등 배출 Top 10 판매점")
    national_top = (
        df.groupby(["상호", "지역"], as_index=False)["건수"].sum()
        .sort_values("건수", ascending=False).head(10)
    )
    st.bar_chart(national_top.set_index("상호")["건수"])

    st.divider()

    sido_list = sorted({r.split(" ")[0] for r in df["지역"]})
    sido = st.selectbox("시/도 선택", ["전체"] + sido_list)

    filtered = df if sido == "전체" else df[df["지역"].str.startswith(sido)]

    sigungu_list = sorted(filtered["지역"].unique())
    sigungu = st.selectbox("시/군/구 선택", ["전체"] + sigungu_list)
    if sigungu != "전체":
        filtered = filtered[filtered["지역"] == sigungu]

    ranked = (
        filtered.groupby(["상호", "지역"], as_index=False)["건수"]
        .sum()
        .sort_values("건수", ascending=False)
        .reset_index(drop=True)
    )
    ranked.index = ranked.index + 1

    st.markdown(f"### 📋 {sido if sido != '전체' else '전국'} 1등 배출 랭킹")
    st.dataframe(ranked, use_container_width=True)

    # 지도 표시 — 필터링된(=화면에 보이는) 지역만 지오코딩해서 찍는다.
    unique_regions = sorted(ranked["지역"].unique())
    if unique_regions:
        if len(unique_regions) > 30 and sido == "전체":
            st.info("전체 지역은 좌표 확인에 시간이 걸릴 수 있어, 시/도를 하나 골라서 보시길 권장합니다.")
        coords = geocode_regions_with_progress(unique_regions)
        map_rows = [{"lat": lat, "lon": lon} for lat, lon in coords.values()]
        if map_rows:
            st.markdown("### 📍 지역별 위치")
            st.map(pd.DataFrame(map_rows))
        missed = set(unique_regions) - set(coords.keys())
        if missed:
            st.caption(f"좌표를 찾지 못한 지역 {len(missed)}곳은 지도에서 제외됐습니다 (표에는 포함).")


# ------------------------------------------------------------------
# 페이지 5) 내 추첨 기록 (세션 기반, 새로고침하면 초기화됨)
# ------------------------------------------------------------------
elif menu == "📜 내 추첨 기록":
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>📜 내 추첨 기록</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align: center; color: #666; margin-bottom: 20px;'>"
        "이번 브라우저 세션에서 뽑은 번호만 모아봅니다 (새로고침하면 사라집니다)</div>",
        unsafe_allow_html=True)
    st.divider()

    if not st.session_state.history:
        st.info("아직 뽑은 기록이 없습니다. 로또 6/45 또는 연금복권 탭에서 먼저 번호를 뽑아보세요!")
    else:
        for item in reversed(st.session_state.history):
            st.markdown(f"**{item['시각']}** · {item['종류']}")
            st.code(item["결과"], language="text")

        hist_df = pd.DataFrame(st.session_state.history)
        st.download_button(
            "⬇️ 전체 기록 CSV로 저장",
            data=hist_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"내추첨기록_{datetime.date.today()}.csv",
            mime="text/csv",
        )

        if st.button("🗑️ 기록 전체 지우기"):
            st.session_state.history = []
            st.rerun()
