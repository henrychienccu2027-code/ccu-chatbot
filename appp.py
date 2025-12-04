import streamlit as st
from google import genai
import os
import glob
from PIL import Image
from datetime import date

# ==========================================
# 1. 頁面設定與 CSS (UI 美化)
# ==========================================
st.set_page_config(page_title="中正企研小幫手", layout="wide", page_icon="🎓")

# CSS 樣式
st.markdown(
    """
    <style>
    /* 全域背景色：淡藍色 */
    .stApp {
        background-color: #eff6ff; 
    }

    /* 側邊欄樣式優化 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    /* 調整 Header 標題 */
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3a8a; /* 深藍色 */
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }

    /* 聊天氣泡優化 */
    .stChatMessage {
        background-color: transparent;
    }

    /* 側邊欄標題樣式 */
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1e3a8a;
        margin-bottom: 15px;
        margin-top: 10px;
    }

    /* 側邊欄日程表樣式 (解決擠在一起的問題) */
    .schedule-item {
        margin-bottom: 12px; /* 每一項之間的距離 */
        font-size: 0.95rem;
        color: #374151;
        line-height: 1.4;
    }
    .schedule-icon {
        margin-right: 5px;
    }

    /* 版權宣告樣式 */
    .footer-text {
        font-size: 0.8rem;
        color: #9ca3af; /* 淺灰色 */
        text-align: center;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. 初始化與 API 設定
# ==========================================
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

# 初始化聊天 Session
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.client.chats.create(model="gemini-2.0-flash")

# 初始化歷史訊息
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 預設歡迎訊息 (專注於企研所)
    st.session_state.messages.append({
        "role": "assistant",
        "content": "你好！我是中正大學企業管理研究所（MBA）的 AI 小幫手。關於課程特色、師資或報考資訊，歡迎隨時問我！"
    })

# ==========================================
# 3. 每日限制功能 (Rate Limiting)
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
# 5. 側邊欄 (修正版)
# ==========================================
with st.sidebar:
    if os.path.exists("ccu_logo.png"):
        st.image("ccu_logo.png", width=200)
    else:
        st.markdown("###  中正企研小幫手")

    # ----- 社群 ICON 區塊 -----
    st.write(" ")  # 加一點間距
    col_fb, col_ig, col_empty = st.columns([1, 1, 3])

    with col_fb:
        # Facebook 圖示
        st.markdown(
            "[![FB](https://img.icons8.com/color/48/facebook-new.png)](https://www.facebook.com/joinccumba/?locale=zh_TW)")

    with col_ig:
        # Instagram 圖示
        st.markdown("[![IG](https://img.icons8.com/color/48/instagram-new.png)](https://www.instagram.com/ccu_mba/)")

    st.markdown("---")

    # 📌 2025 企管所考試入學重要資訊 (使用 HTML Div 確保排版不跑掉)
    st.markdown('<div class="sidebar-title">📌 2025 企管所考試入學重要資訊</div>', unsafe_allow_html=True)

    # 這裡改成用 div class="schedule-item" 來包每一行，確保它們之間有間距且不會擠在一起
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

    # 版權宣告 (Footer)
    st.markdown(
        """
        <div class="footer-text">
            CCUMBA Chatbot 
            created by 2025招說會團隊
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# 6. 主畫面 (Main Chat Area)
# ==========================================

# 標題區
st.markdown('<div class="main-header">中正企研小幫手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">隨時為您回答問題</div>', unsafe_allow_html=True)

# 顯示歷史訊息
for message in st.session_state.messages:
    avatar = "🤖" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ==========================================
# 7. 輸入處理與 AI 回答
# ==========================================

# 底部輸入框
user_input = None

if st.session_state.daily_count < MAX_QUESTIONS:
    user_input = st.chat_input("請輸入關於中正企研所的問題...")
else:
    st.info("🔔 今日提問額度已達上限，歡迎明天再來！")

if user_input:
    # 1. 顯示使用者輸入
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. 準備 System Prompt (鎖定企研所範圍)
    full_prompt = f"""
角色設定：
    你是國立中正大學企業管理研究所（MBA）的專屬 AI 小幫手。
    你的任務是僅回答關於「中正企研所」的課程、師資、考試、報名等資訊。

    重要規則：
    1. 若使用者詢問「金融科技所」、「FinTech」或其他系所，請禮貌回答：「抱歉，我目前僅負責企研所（MBA）的相關諮詢，無法回答其他系所的問題。」
    2. 嚴格依據以下資料庫回答，若無資料請建議聯繫系辦。
    3. 語氣親切、專業且具鼓勵性。
    4. 嚴格依據【資料庫】回答問題。
    5. 如果問題涉及本系，但資料庫中沒有答案：
       「這部分資訊我目前手邊沒有確切資料，建議您直接聯繫系辦確認。」
    6. 如果問題與中正大學企管所無關：
       「抱歉，我不適合回答這個問題。」
    7. 條理分明，複雜資訊請使用條列式呈現。
    8. 不回答私人問題或閒聊。
    
        知識庫內容：
    {KNOWLEDGE_BASE_TEXT}

    使用者問題：{user_input}
    """

    # 3. 呼叫 AI
    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("請稍後..."):
                response = st.session_state.chat_session.send_message(full_prompt)
                ai_reply = response.text
                st.markdown(ai_reply)

        # 4. 儲存回應
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

        # 5. 扣除額度
        st.session_state.daily_count += 1

        # 強制刷新以更新側邊欄額度 (可選)
        st.rerun()

    except Exception as e:
        st.error(f"發生錯誤: {e}")
