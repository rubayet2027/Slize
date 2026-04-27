import streamlit as st
import os
import tempfile
import zipfile
import shutil
import time
import base64
from datetime import datetime
from supabase import create_client, Client
from video_utils import get_video_info, process_video_clip

# --- APP CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Slize", page_icon="✂️")

# --- SUPABASE CONNECTION ---
@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        return None

supabase = get_supabase()

if supabase is None:
    st.error("⚠️ Supabase Configuration Missing")
    st.info("Please go to **App Settings > Secrets** on Streamlit Cloud and add your `[supabase]` section.")
    st.stop()

# --- CUSTOM CSS (NEON ANIMATIONS) ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Orbitron:wght@400;900&family=Inter:wght@400;700&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #050505; color: #ffffff; }
        
        .stApp {
            background: radial-gradient(circle at 50% -20%, #1a1a2e 0%, #050505 80%);
        }

        /* Neon Animations */
        @keyframes flicker { 0%, 100% { opacity: 1; text-shadow: 0 0 10px #ec4899; } 50% { opacity: 0.8; text-shadow: 0 0 5px #ec4899; } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        .neon-logo {
            font-family: 'Bangers', cursive; font-size: 7rem; text-align: center;
            color: #ffffff; animation: flicker 3s infinite; letter-spacing: 5px;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 245, 255, 0.1); border-radius: 24px;
            padding: 2.5rem; animation: fadeInUp 0.6s ease-out;
        }

        .stButton>button {
            background: linear-gradient(45deg, #6200EE, #ec4899); color: white !important;
            border: none; border-radius: 12px; padding: 0.8rem 2rem; font-weight: 800;
            transition: all 0.3s; width: 100%;
        }
        .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 20px #ec4899; }

        .nav-logo { font-family: 'Bangers', cursive; color: #ec4899; font-size: 2rem; margin-bottom: 20px; }

        /* Sidebar Styling */
        [data-testid="stSidebar"] { background-color: rgba(0,0,0,0.5); border-right: 1px solid rgba(255,255,255,0.05); }
        </style>
    """, unsafe_allow_html=True)

# --- DB HELPERS ---
def sync_user_to_db(user):
    """Sync Google user info to Supabase users table."""
    if not user: return
    try:
        data = {
            "id": user.email,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.picture,
            "last_login": datetime.now().isoformat()
        }
        supabase.table("users").upsert(data).execute()
    except Exception as e:
        # Log error but don't crash the app
        print(f"DB Sync Error: {e}")

def save_short_to_history(email, clip_name, original_name):
    """Save generation record to Supabase."""
    try:
        data = {
            "user_id": email,
            "clip_name": clip_name,
            "original_video": original_name,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("user_shorts").insert(data).execute()
    except Exception as e:
        st.error(f"History Save Error: {e}")
        print(f"History Error: {e}")

# --- PAGE FUNCTIONS ---

def login_page():
    inject_custom_css()
    st.markdown('<div style="height: 15vh;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-logo">SLIZE</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #00f5ff; font-size: 1.2rem; letter-spacing: 2px;">VIRAL CONTENT IN SECONDS 🔥</p>', unsafe_allow_html=True)
    
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; margin-bottom: 2rem;'>CREATOR ACCESS</h3>", unsafe_allow_html=True)
        if st.button("CONTINUE WITH GOOGLE"):
            st.login("google")
        st.markdown("<p style='text-align: center; opacity: 0.5; font-size: 0.8rem; margin-top: 1.5rem;'>Secure • Private • Powerful</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def home_page():
    inject_custom_css()
    user = st.user
    
    # Sync in background, don't block UI
    if 'synced' not in st.session_state:
        sync_user_to_db(user)
        st.session_state.synced = True
    
    # Sidebar Profile
    with st.sidebar:
        st.markdown('<div class="nav-logo">SLIZE</div>', unsafe_allow_html=True)
        if user.picture:
            st.image(user.picture, width=80)
        st.write(f"Logged in as **{user.name}**")
        if st.button("LOGOUT"):
            st.logout()
        st.markdown("---")

    # Content
    st.markdown(f'<h1 style="font-family: Bangers; font-size: 3.5rem; color: #ec4899;">STUDIO</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("DROP VIDEO FILE", type=["mp4", "mov", "avi"])
    
    if uploaded_file:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name
        
        info = get_video_info(video_path)
        st.video(video_path)
        
        st.markdown("### ⚡ ENGINE SETTINGS")
        c1, c2, c3 = st.columns(3)
        with c1: ratio = st.selectbox("FORMAT", ["9:16 VERTICAL", "ORIGINAL"])
        with c2: speed = st.slider("SPEED RAMP", 0.5, 2.0, 1.1)
        with c3: caption = st.text_input("CAPTION", "WAIT FOR IT!")

        if 'q' not in st.session_state: st.session_state.q = []
        
        st.markdown("---")
        ca, cb = st.columns(2)
        start = ca.number_input("START (S)", 0.0, float(info['duration']), 0.0)
        end = cb.number_input("END (S)", 0.0, float(info['duration']), min(float(info['duration']), 30.0))
        if st.button("ADD TO PIPELINE"):
            st.session_state.q.append((start, end))
            st.toast("Added!")

        if st.session_state.q:
            st.write(f"Queue: {len(st.session_state.q)} clips")
            if st.button("🚀 GENERATE VIRAL SHORTS"):
                user_dir = os.path.join("user_vault", user.email)
                if not os.path.exists(user_dir): os.makedirs(user_dir)
                
                pbar = st.progress(0)
                for i, (s, e) in enumerate(st.session_state.q):
                    fname = f"short_{int(time.time())}_{i}.mp4"
                    out = os.path.join(user_dir, fname)
                    process_video_clip(video_path, out, s, e, aspect_ratio="9:16" if "9:16" in ratio else "original", speed=speed, text_overlay=caption)
                    save_short_to_history(user.email, fname, uploaded_file.name)
                    pbar.progress((i+1)/len(st.session_state.q))
                
                st.balloons()
                st.session_state.q = []
                st.success("VAULT UPDATED!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def history_page():
    inject_custom_css()
    user = st.user
    
    # Sidebar Profile
    with st.sidebar:
        st.markdown('<div class="nav-logo">SLIZE</div>', unsafe_allow_html=True)
        if user.picture:
            st.image(user.picture, width=80)
        st.write(f"Logged in as **{user.name}**")
        if st.button("LOGOUT"):
            st.logout()
        st.markdown("---")

    st.markdown('<h1 style="font-family: Bangers; font-size: 3.5rem; color: #ec4899;">MY VAULT</h1>', unsafe_allow_html=True)
    
    # Fetch from Supabase
    try:
        res = supabase.table("user_shorts").select("*").eq("user_id", user.email).order("created_at", desc=True).execute()
        shorts = res.data
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        shorts = []
    
    if shorts:
        hcols = st.columns(3)
        for i, item in enumerate(shorts):
            with hcols[i % 3]:
                st.markdown('<div class="glass-card" style="padding: 1rem; margin-bottom: 1.5rem;">', unsafe_allow_html=True)
                st.write(f"📅 {item['created_at'][:10]}")
                fpath = os.path.join("user_vault", user.email, item['clip_name'])
                if os.path.exists(fpath):
                    st.video(fpath)
                    with open(fpath, "rb") as f:
                        st.download_button("DOWNLOAD", f, file_name=item['clip_name'], key=f"dl_{i}")
                else:
                    st.error("File missing locally")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Your vault is empty. Start slicing!")

# --- ROUTING LOGIC ---

# 1. Define Pages
login_pg = st.Page(login_page, title="Login", icon="🔐")
home_pg = st.Page(home_page, title="Studio", icon="✂️", default=True)
history_pg = st.Page(history_page, title="Vault", icon="📁")

# 2. Build Navigation based on Auth State
if not st.user.is_logged_in:
    pg = st.navigation([login_pg], position="hidden")
else:
    pg = st.navigation({
        "Creation": [home_pg],
        "Archive": [history_pg]
    })

# 3. Run App
if __name__ == "__main__":
    pg.run()
