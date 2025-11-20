import streamlit as st
from google import genai
import os
import glob
from PIL import Image

# ==========================
# 1. 初始化
# ==========================
# 建立 GenAI client
if "client" not in st.session_state:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")  # <- 從 Streamlit Secrets 讀取
    if not GEMINI_API_KEY:
        st.error("找不到 GEMINI_API_KEY，請確認 Streamlit Secrets 是否正確設置")
        st.stop()
    st.session_state.client = genai.Client(api_key=GEMINI_API_KEY)

# 建立聊天 session
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.client.chats.create(model="gemini-2.0-flash")
    st.session_state.history = []

# ==========================
# 2. 讀取知識庫 txt 檔案（根目錄）
# ==========================
KNOWLEDGE_BASE_TEXT = ""
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 直接抓專案根目錄下所有 txt
knowledge_files = glob.glob(os.path.join(BASE_DIR, "*.txt"))

if not knowledge_files:
    st.error("專案目錄中找不到任何 .txt 檔案，請確認檔案是否正確上傳")
    st.stop()

for file_path in knowledge_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            KNOWLEDGE_BASE_TEXT += f.read() + "\n\n"
    except Exception as e:
        st.warning(f"讀取 {file_path} 發生錯誤：{e}")

# ==========================
# 3. 系統指令 (含知識庫)
# ==========================
SYSTEM_INSTRUCTION = f"""
角色設定：
你是國立中正大學（CCU）企管所與金融科技研究所的專屬 AI 招生顧問。
你的名字叫「中正小幫手」，語氣專業、親切、且充滿鼓勵性。

主要任務：
回答關於「企管所 MBA」與「FinTech 碩士學位學程」的所有相關問題，包括課程、師資、未來出路、報名資格、書審重點、口試形式，以及兩所科系的差異分析。

知識庫：
以下是你必須依據的知識庫資料（嚴格依照這份文件回答問題）：
---
{KNOWLEDGE_BASE_TEXT}
---

回答規則：
1. 嚴格依據【知識庫】回答問題。
2. 如果問題涉及本系，但知識庫中沒有答案：
   「這部分資訊我目前手邊沒有確切資料，建議您直接聯繫系辦確認。」
3. 如果問題與中正大學企管所或 FinTech 無關：
   「抱歉，我不適合回答這個問題。」
4. 條理分明，複雜資訊請使用條列式呈現。
5. 不回答私人問題或閒聊。
6. 當問題不明確時，要說請問是在說企研所還是金科所呢?
"""

# ==========================
# 4. UI - 藍色主題 + 校徽 + 標題
# ==========================
st.set_page_config(page_title="中正小幫手", layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: #0a2342;  /* 深藍背景 */
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color:#f5f5f5;  /* 輸入框白底 */
        color:#000000;
    }
    .stButton>button {
        background-color:#0d6efd;  /* 按鈕亮藍 */
        color:white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 校徽 + 標題
col1, col2 = st.columns([1, 8])
with col1:
    try:
        logo = Image.open("ccu_logo.png")
        st.image(logo, width=800)
    except:
        st.write("")
with col2:
    st.markdown('<h1 style="color:#000000; margin:0;"> 中正小幫手(企研所+金科所)</h1>', unsafe_allow_html=True)

# ==========================
# 對話氣泡函式
# ==========================
def display_message(role, text):
    safe_text = text.replace("<", "&lt;").replace(">", "&gt;")
    if role == "user":
        st.markdown(
            f'<div style="text-align:left; background-color:#d9d9d9; padding:12px; border-radius:12px; margin:8px 0; max-width:70%; color:#000000; word-wrap: break-word;">👤 你：{safe_text}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="text-align:left; background-color:#cce5ff; padding:12px; border-radius:12px; margin:8px 0; max-width:70%; color:#000000; word-wrap: break-word;">🤖 中正小幫手：{safe_text}</div>',
            unsafe_allow_html=True
        )

# 顯示歷史訊息
for role, text in st.session_state.history:
    display_message(role, text)

# ==========================
# 使用者輸入與即時回應
# ==========================
def send_message():
    user_input = st.session_state.user_input.strip()
    if not user_input:
        return

    if "system_sent" not in st.session_state:
        try:
            st.session_state.chat_session.send_message(f"system: {SYSTEM_INSTRUCTION}")
            st.session_state.system_sent = True
        except Exception as e:
            st.error(f"初始化 SYSTEM 指令錯誤：{e}")

    st.session_state.history.append(("user", user_input))

    try:
        response = st.session_state.chat_session.send_message(user_input)
        ai_text = "\n".join([part.text for part in response.parts])
        st.session_state.history.append(("ai", ai_text))
    except Exception as e:
        st.error(f"API 呼叫錯誤：{e}")

    st.session_state.user_input = ""

st.text_area("輸入問題...", key="user_input", height=50)
st.button("送出", on_click=send_message)

# ==========================
# 清除對話按鈕
# ==========================
if st.button("清除對話"):
    st.session_state.history = []
