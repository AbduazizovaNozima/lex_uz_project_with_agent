import streamlit as st
import requests
from datetime import datetime
import time

# ==============================================================================
# PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Lex.uz AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CUSTOM CSS - Yanada chiroyli dizayn
# ==============================================================================
st.markdown("""
<style>
    /* Global styling */
    .main {
        background-color: #0e1117;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d29 0%, #0e1117 100%);
        border-right: 1px solid #2d3748;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    /* User message */
    [data-testid="stChatMessageContent"] {
        background-color: #1e2936;
    }

    /* Image styling within chat */
    [data-testid="stChatMessageContent"] img {
        max-width: 300px !important;
        width: auto !important;
        height: auto !important;
        border-radius: 8px;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 158, 255, 0.3);
    }
    
    /* Primary button */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #4a9eff 0%, #2d5aa6 100%);
    }
    
    /* Chat input */
    .stChatInput {
        border-radius: 12px;
    }
    
    /* Session item */
    .session-item {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background-color: #1e2936;
        border-left: 3px solid transparent;
        transition: all 0.2s ease;
    }
    
    .session-item:hover {
        background-color: #2d3748;
        border-left-color: #4a9eff;
    }
    
    .session-active {
        background-color: #2d5aa6;
        border-left-color: #4a9eff;
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(135deg, #4a9eff 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: #2d3748;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stInfo {
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# API CONFIGURATION
# ==============================================================================
API_BASE_URL = "http://127.0.0.1:8000"

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "sessions" not in st.session_state:
    st.session_state.sessions = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "refresh_trigger" not in st.session_state:
    st.session_state.refresh_trigger = 0

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def create_new_session():
    """Yangi session (ticket) yaratish"""
    try:
        response = requests.post(f"{API_BASE_URL}/sessions/new", timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.current_session_id = data["session_id"]
            st.session_state.messages = []
            st.session_state.refresh_trigger += 1
            return True
    except Exception as e:
        st.error(f"❌ Xato: {e}")
    return False


def load_sessions():
    """Barcha sessionlarni yuklash"""
    try:
        response = requests.get(f"{API_BASE_URL}/sessions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.sessions = data.get("sessions", [])
    except Exception as e:
        st.error(f"❌ Sessionlarni yuklashda xato: {e}")


def load_session_history(session_id):
    """Session tarixini yuklash"""
    try:
        response = requests.get(f"{API_BASE_URL}/sessions/{session_id}/history", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("messages", [])
    except Exception as e:
        st.error(f"❌ Tarixni yuklashda xato: {e}")
    return []


def switch_session(session_id):
    """Boshqa sessionga o'tish"""
    st.session_state.current_session_id = session_id
    # Load session history
    messages = load_session_history(session_id)
    st.session_state.messages = messages
    st.rerun()


def delete_session(session_id):
    """Sessionni o'chirish"""
    try:
        response = requests.delete(f"{API_BASE_URL}/sessions/{session_id}", timeout=5)
        if response.status_code == 200:
            if st.session_state.current_session_id == session_id:
                st.session_state.current_session_id = None
                st.session_state.messages = []
            st.session_state.refresh_trigger += 1
            return True
    except Exception as e:
        st.error(f"❌ O'chirishda xato: {e}")
    return False


def send_message(question, session_id):
    """Xabar yuborish"""
    try:
        payload = {
            "question": question,
            "session_id": session_id
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=60  # 60 soniya timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Server xatosi: {response.status_code}")
    except requests.exceptions.Timeout:
        st.error("⏱️ Javob olish juda uzoq davom etdi. Iltimos, qaytadan urinib ko'ring.")
    except Exception as e:
        st.error(f"❌ Xato: {e}")
    return None


def format_timestamp(iso_timestamp):
    """Timestamp'ni formatlash"""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return iso_timestamp


# ==============================================================================
# SIDEBAR - TICKET MANAGEMENT
# ==============================================================================
with st.sidebar:
    st.title("💬 Chatlar")
    
    # Yangi chat yaratish tugmasi
    if st.button("➕ Yangi Chat", use_container_width=True, type="primary"):
        # Agar hozirgi chatda xabarlar bo'lsa, yangi chat yaratamiz
        if st.session_state.messages:
            if create_new_session():
                st.rerun()
        else:
            # Agar xabarlar bo'lmasa, shunchaki ogohlantiramiz
            st.toast("⚠️ Siz allaqachon yangi chatdasiz!")
    
    st.divider()
    
    # Sessionlarni yuklash
    load_sessions()
    
    # Sessionlar ro'yxatini tayyorlash
    sessions_to_display = st.session_state.sessions.copy()
    
    # Agar hozirgi session ro'yxatda bo'lmasa (yangi bo'lsa), uni qo'shish
    if st.session_state.current_session_id:
        current_in_list = any(s["session_id"] == st.session_state.current_session_id for s in sessions_to_display)
        if not current_in_list:
            sessions_to_display.insert(0, {
                "session_id": st.session_state.current_session_id,
                "title": "Mavjud Chat",
                "message_count": 0,
                "last_active": datetime.now().isoformat()
            })
    
    # Sessionlar ro'yxati
    if sessions_to_display:
        st.subheader("📋 Mavjud Chatlar")
        
        for session in sessions_to_display:
            session_id = session["session_id"]
            
            # Title'ni olish
            title = session.get("title", "Yangi Chat")
            # Agar title bo'sh bo'lsa
            if not title:
                title = "Yangi Chat"
            
            message_count = session.get("message_count", 0)
            last_active = format_timestamp(session.get("last_active", ""))
            
            # Faol session belgisi
            is_active = session_id == st.session_state.current_session_id
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                button_label = f"{'✓ ' if is_active else ''}{title[:30]}..."
                if st.button(
                    button_label,
                    key=f"session_{session_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    switch_session(session_id)
            
            with col2:
                if st.button("🗑️", key=f"delete_{session_id}"):
                    if delete_session(session_id):
                        st.rerun()
            
            # Session ma'lumotlari
            st.caption(f"💬 {message_count} xabar • ⏰ {last_active}")
            st.divider()
    else:
        st.info("📭 Hali chatlar yo'q. Yangi chat yarating!")
    
    # Statistika
    st.divider()
    st.metric("Jami chatlar", len(sessions_to_display))

# ==============================================================================
# MAIN CHAT AREA
# ==============================================================================
st.title("⚖️ Lex.uz AI Assistant")
st.caption("O'zbekiston qonunchilik bo'yicha professional yordamchi")

# Agar session yo'q bo'lsa
if not st.session_state.current_session_id:
    # Welcome message
    st.markdown("""
    ### 👋 Xush kelibsiz!
    
    Men sizga quyidagi mavzularda yordam bera olaman:
    - 📚 O'zbekiston qonunlari va kodekslari
    - ⚖️ Huquqiy maslahatlar
    - 📋 Lex.uz saytidan foydalanish
    - 💼 Mehnat, fuqarolik, jinoyat huquqi
    
    Boshlash uchun pastdagi maydonga savolingizni yozing!
    """)

# Chat tarixini ko'rsatish
for msg in st.session_state.messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    
    with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
        # Agar user bo'lsa, shunchaki chiqaramiz
        if role == "user":
            st.markdown(content)
        else:
            # Matnni chiqarish (endi regex bilan tozalash shart emas, chunki api.py da tozalangan bo'lishi mumkin)
            # Lekin ehtiyot shart, agar eski xabarlar bo'lsa, regex qoldiramiz
            
            # 1. Rasm yo'lini olish (yangi usul)
            image_path = msg.get("image_path")
            
            # Agar yangi usulda rasm bo'lmasa, eski usulni (regex) tekshiramiz (eski xabarlar uchun)
            if not image_path:
                import re
                md_image_match = re.search(r'!\[.*?\]\((.*?)\)', content)
                legacy_image_match = re.search(r'📷 Rasm: (.+)', content)
                
                if md_image_match:
                    image_path = md_image_match.group(1).strip()
                    content = content.replace(md_image_match.group(0), "")
                elif legacy_image_match:
                    image_path = legacy_image_match.group(1).strip()
                    content = content.replace(legacy_image_match.group(0), "")
            
            # Matnni chiqarish
            st.markdown(content)
            
            # Rasmni chiqarish
            if image_path:
                if "sandbox:" in image_path:
                    image_path = image_path.replace("sandbox:", "")
                
                try:
                    st.image(image_path, caption="Yo'riqnoma")
                except Exception as e:
                    pass

# Chat input
if prompt := st.chat_input("💭 Savolingizni yozing..."):
    # Agar session yo'q bo'lsa, avtomatik yaratamiz
    if not st.session_state.current_session_id:
        create_new_session()
    
    # Foydalanuvchi xabarini qo'shish
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Foydalanuvchi xabarini ko'rsatish
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # Bot javobini olish
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🤔 O'ylamoqda..."):
            response_data = send_message(prompt, st.session_state.current_session_id)
            
            if response_data:
                answer = response_data.get("response", "Javob olishda xato")
                image_path = response_data.get("image_path")
                if image_path and "sandbox:" in image_path:
                    image_path = image_path.replace("sandbox:", "")
                
                st.markdown(answer)
                
                # Rasm ko'rsatish
                if image_path:
                    try:
                        st.image(image_path, caption="Yo'riqnoma")
                    except Exception as e:
                        st.caption(f"⚠️ Rasmni yuklab bo'lmadi: {image_path}")
                
                # Tarixga qo'shish
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })
                
                # Session'ni yangilash
                st.session_state.refresh_trigger += 1
                st.rerun()
            else:
                st.error("❌ Javob olishda xato yuz berdi. Iltimos, qaytadan urinib ko'ring.")
