import streamlit as st
from google import genai
import os
import glob
from PIL import Image
# 引入 time 用於計時效能
import time
# 引入 uuid 用於產生唯一 Session ID
import uuid
# 引入 timedelta 用來做時間加減
from datetime import datetime, date, timedelta
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 頁面設定與 CSS
# ==========================================
st.set_page_config(page_title="中正企研小幫手", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #eff6ff; }
    h1, h2, h3, h4, h5, h6, p, li, span, div.stMarkdown, div.stMetricLabel { color: #0d0d0d !important; }
    [data-testid="stMetricValue"] { color: #1e3a8a !important; font-weight: bold; }
    a { color: #1e3a8a !important; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div { color: #374151 !important; }
    .main-header { font-size: 1.8rem; font-weight: 700; color: #1e3a8a !important; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #6b7280 !important; margin-bottom: 2rem; }
    .stChatMessage { background-color: transparent; }
    .sidebar-title { font-size: 1.1rem; font-weight: bold; color: #1e3a8a !important; margin-bottom: 15px; margin-top: 10px; }
    .schedule-item { margin-bottom: 12px; font-size: 0.95rem; color: #374151 !important; line-height: 1.4; }
    .footer-text { font-size: 0.8rem; color: #9ca3af !important; text-align: center; margin-top: 20px; }
    a img { border: none; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. 初始化與 API 設定
# ==========================================
# A. Gemini API
if "client" not in st.session_state:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
            st.session_state.client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            st.warning("⚠️ 尚未設定 GEMINI_API_KEY")
            st.stop()
    except Exception as e:
        st.error(f"API 初始化失敗: {e}")
        st.stop()

if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.client.chats.create(model="gemini-2.0-flash-exp")

# B. Google Sheets 連線初始化
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Google Sheets 連線失敗，請檢查 secrets 設定: {e}")
    conn = None

# 初始化歷史訊息
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "你好！我是中正大學企業管理研究所（MBA）的 AI 小幫手。關於課程特色、師資或報考資訊，歡迎隨時問我！"
    })

# 🔥 初始化 Session ID (用於履歷數據分析：使用者黏著度)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ==========================================
# 3. 每日限制與日期
# ==========================================
if "daily_count" not in st.session_state:
    st.session_state.daily_count = 0
if "last_visit_date" not in st.session_state:
    st.session_state.last_visit_date = str(date.today())

current_date = str(date.today())
if st.session_state.last_visit_date != current_date:
    st.session_state.daily_count = 0
    st.session_state.last_visit_date = current_date

MAX_QUESTIONS = 5

# ==========================================
# 4. 讀取知識庫
# ==========================================
KNOWLEDGE_BASE_TEXT = ""
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
knowledge_files = glob.glob(os.path.join(BASE_DIR, "*.TXT"))

if knowledge_files:
    for file_path in knowledge_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                KNOWLEDGE_BASE_TEXT += f.read() + "\n\n"
        except Exception:
            pass

# ==========================================
# 5. 側邊欄 (純資訊，無登入框)
# ==========================================
with st.sidebar:
    if os.path.exists("ccu_logo.png"):
        st.image("ccu_logo.png", width=200)
    else:
        st.markdown("### 🎓 中正企研小幫手")

    st.write(" ")
    col_fb, col_ig, col_empty = st.columns([1, 1, 3])
    with col_fb:
        st.markdown(
            "[![FB](https://img.icons8.com/color/48/facebook-new.png)](https://www.facebook.com/joinccumba/?locale=zh_TW)")
    with col_ig:
        st.markdown("[![IG](https://img.icons8.com/color/48/instagram-new.png)](https://www.instagram.com/ccu_mba/)")

    st.markdown("---")

    st.markdown('<div class="sidebar-title">📌 2025 企管所考試入學重要資訊</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="schedule-item">⏰ <b>一、報名</b><br>114/12/2 09:00 — 12/15 17:00</div>
    <div class="schedule-item">🎫 <b>二、筆試准考證下載</b><br>115/2/2 — 2/11</div>
    <div class="schedule-item">✍️ <b>三、考試時間</b><br>115/2/11</div>
    <div class="schedule-item">📢 <b>四、放榜日期</b><br>115/3/20</div>
    <div class="schedule-item">🌐 <b>五、網路報到意願登記</b><br>115/3/26 09:00 — 3/30 17:00</div>
    <div class="schedule-item">🧾 <b>六、正式報到</b><br>115/4/15 – 4/16</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.caption(f"📅 今日額度: {st.session_state.daily_count}/{MAX_QUESTIONS}")


# ==========================================
# 6. 主畫面
# ==========================================

st.markdown('<div class="main-header">中正企研小幫手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">隨時為您回答問題</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    avatar = "🤖" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

user_input = None
if st.session_state.daily_count < MAX_QUESTIONS:
    user_input = st.chat_input("請輸入關於中正企研所的問題...")
else:
    st.info("🔔 今日提問額度已達上限，歡迎明天再來！")

if user_input:
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    full_prompt = f"""
    角色設定： 你是國立中正大學企業管理研究所（MBA）的專屬 AI 小幫手。 
    你的任務是僅回答關於「中正企研所」的課程、師資、考試、報名等資訊。 

    重要規則： 
    1. 若使用者詢問「金融科技所」、「FinTech」或其他系所，請禮貌回答：「抱歉，我目前僅負責企研所（MBA）的相關諮詢，無法回答其他系所的問題。」 
    2. 嚴格依據以下知識庫回答，若無資料請建議聯繫系辦。 
    3. 語氣親切、專業且具鼓勵性。 
    4. 嚴格依據【知識庫】回答問題。 
    5. 如果問題涉及本系，但知識庫中沒有答案：「這部分資訊我目前手邊沒有確切資料，建議您直接聯繫系辦確認。」 
    6. 如果問題與中正大學企管所無關：「抱歉，我不適合回答這個問題。」 
    7. 條理分明，複雜資訊請使用條列式呈現。 
    8. 不回答私人問題或閒聊。

        知識庫內容：
        {KNOWLEDGE_BASE_TEXT}

        使用者問題：{user_input}
    """

    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("請稍後..."):
                # A. 開始計時 (用於履歷數據分析：系統延遲 Latency)
                start_time = time.time()

                # B. 呼叫 AI
                response = st.session_state.chat_session.send_message(full_prompt)
                ai_reply = response.text
                st.markdown(ai_reply)

                # C. 結束計時
                end_time = time.time()
                duration = round(end_time - start_time, 2)

        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        st.session_state.daily_count += 1

        # 🔥 核心：寫入 Google Sheets (背景執行 - 含完整量化指標)
        if conn:
            try:
                # 1. 讀取現有資料
                existing_data = conn.read(worksheet="Sheet1", ttl=0)

                # 2. 準備新的一筆資料 (含 Session_ID 與 效能數據)
                new_entry = pd.DataFrame([{
                    "Session_ID": st.session_state.session_id,  # 識別單次對話 (重要！)
                    "時間": (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
                    "使用者問題": user_input,
                    "AI 回答": ai_reply,
                    "回應秒數": duration,  # 系統效能指標
                    "問題字數": len(user_input),  # Input Token 成本估算
                    "回答字數": len(ai_reply)  # Output Token 成本估算
                }])

                # 3. 合併
                if existing_data.empty:
                    updated_data = new_entry
                else:
                    updated_data = pd.concat([existing_data, new_entry], ignore_index=True)

                # 4. 更新回 Google Sheets
                conn.update(worksheet="Sheet1", data=updated_data)

            except Exception as db_e:
                print(f"資料庫寫入失敗: {db_e}")

        st.rerun()

    except Exception as e:
        st.error(f"發生錯誤: {e}")




