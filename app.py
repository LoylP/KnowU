import streamlit as st
import asyncio
import pandas as pd
import csv
from datetime import datetime
from agents_setup import async_chat

USER_DB = "in4.csv"
CHAT_HISTORY_FILE = "history_chat.csv"
MAX_HISTORY = 50

# ---------- Session States ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "history" not in st.session_state:
    st.session_state.history = []
if "visible_count" not in st.session_state:
    st.session_state.visible_count = 5  # Số tin nhắn hiển thị ban đầu

VISIBLE_MESSAGES = st.session_state.visible_count

# ---------- Utility ----------
def verify_user(username, password):
    users = pd.read_csv(USER_DB)
    user_row = users[users["username"] == username]
    if user_row.empty:
        return None
    if password == str(user_row.iloc[0]["password"]):
        return user_row.iloc[0].to_dict()
    return None

def save_chat_history(username, role, message):
    try:
        df = pd.read_csv(CHAT_HISTORY_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["username", "timestamp", "role", "message"])
    new_row = pd.DataFrame([[username, datetime.now().isoformat(), role, message]],
                           columns=["username", "timestamp", "role", "message"])
    df = pd.concat([df, new_row], ignore_index=True)
    df = df[df["username"] == username].tail(MAX_HISTORY)
    df.to_csv(CHAT_HISTORY_FILE, index=False, encoding="utf-8")

def load_user_history(username):
    try:
        df = pd.read_csv(CHAT_HISTORY_FILE)
        user_history = df[df["username"] == username].tail(MAX_HISTORY)
        return [{"role": r["role"], "content": r["message"]} for _, r in user_history.iterrows()]
    except FileNotFoundError:
        return []

# ---------- UI Config ----------
st.set_page_config(page_title="KnowU", page_icon="🤖", layout="centered")

# ---------- Login ----------
if not st.session_state.user:
    st.title("🔐 KnowU - Đăng nhập")
    with st.form("login_form"):
        username = st.text_input("👤 Tên người dùng")
        password = st.text_input("🔒 Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")
    if submitted:
        user = verify_user(username, password)
        if user:
            st.session_state.user = user
            st.session_state.history = load_user_history(username)
            st.success(f"Chào {user['fullname']} 👋")
            st.rerun()
        else:
            st.error("Tên đăng nhập hoặc mật khẩu sai.")
    st.stop()

user = st.session_state.user

# ---------- UI CSS ----------
st.markdown("""
    <style>
    .chat-container {
        height: 420px;
        overflow-y: scroll;
        padding: 1rem;
        border-radius: 12px;
        background-color: #f4f4f4;
        margin-bottom: 0.5rem;
    }
    .bubble-user, .bubble-ai {
        padding: 10px;
        border-radius: 12px;
        margin: 10px 0;
        width: fit-content;
        max-width: 90%;
        display: flex;
        gap: 10px;
        align-items: flex-start;
    }
    .bubble-user {
        background-color: #E1E8ED;
        margin-left: auto;
        justify-content: flex-end;
    }
    .bubble-ai {
        background-color: #D2DCE1;
        margin-right: auto;
        border: 1px solid #ccc;
    }
    .chat-title {
        text-align: center;
        font-size: 26px;
        font-weight: 600;
        margin: 0.5rem 0 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Chat Header ----------
st.markdown("<div class='chat-title'>💬 KnowU Assistant</div>", unsafe_allow_html=True)

# ---------- Nút Load More ----------
if st.session_state.history and len(st.session_state.history) > VISIBLE_MESSAGES:
    if st.button("🔄 Load thêm tin nhắn"):
        st.session_state.visible_count += 5
        st.rerun()

# ---------- Chat Display ----------
if st.session_state.history:
    for msg in st.session_state.history[-VISIBLE_MESSAGES:]:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class='bubble-user'>
                <div>{msg['content']}</div>
                <img src='https://img.icons8.com/color/36/user-male-circle--v1.png'/>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='bubble-ai'>
                <img src='https://img.icons8.com/fluency/36/bot.png'/>
                <div><b>AI:</b> {msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("👋 Xin chào! Bạn hãy nhập câu hỏi bên dưới để bắt đầu trò chuyện với KnowU.")

# ---------- Input Form ----------
with st.form("chat_input", clear_on_submit=True):
    col1, col2 = st.columns([8, 2])
    with col1:
        user_input = st.text_input("💬 Nhập câu hỏi của bạn", label_visibility="collapsed")
    with col2:
        submitted = st.form_submit_button("Gửi")

if submitted and user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    save_chat_history(user["username"], "user", user_input)

    with st.spinner("🤖 Đang phản hồi..."):
        result = asyncio.run(async_chat(user_input, user_info=user))

    st.session_state.history.append({"role": "assistant", "content": result})
    save_chat_history(user["username"], "assistant", result)
    st.rerun()
