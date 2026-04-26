import streamlit as st
import os
import tempfile
import zipfile
import shutil
import time
import base64
from datetime import timedelta
from video_utils import get_video_info, process_video_clip
from auth_utils import init_db, add_history, get_user_history

# Initialize History Database
init_db()

# Page Configuration
st.set_page_config(
    page_title="Slize - Viral Shorts in Seconds",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
USER_DATA_DIR = "user_vault"
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file): return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- ADVANCED NEON ANIMATED CSS ---
def inject_neon_css(bg_img_base64):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@400;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            background-color: #050505;
            color: #ffffff;
        }}

        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.95)), 
                        url("data:image/png;base64,{bg_img_base64}") no-repeat center center fixed;
            background-size: cover;
        }}

        @keyframes flicker {{ 0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {{ opacity: 1; text-shadow: 0 0 10px #ec4899; }} 20%, 22%, 24%, 55% {{ opacity: 0.5; text-shadow: none; }} }}
        @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        .neon-logo {{
            font-family: 'Orbitron', sans-serif;
            font-size: 6rem;
            font-weight: 900;
            text-align: center;
            color: #ffffff;
            animation: flicker 3s infinite alternate;
            letter-spacing: 15px;
            margin-top: 2rem;
        }}

        .tagline {{
            text-align: center; font-size: 1.5rem; color: #00f5ff; margin-bottom: 2rem; font-weight: 700; animation: fadeInUp 1s ease-out; letter-spacing: 2px;
        }}

        .login-card {{
            background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(0, 245, 255, 0.3); border-radius: 30px; padding: 4rem; text-align: center; backdrop-filter: blur(25px); max-width: 600px; margin: 0 auto; animation: fadeInUp 0.8s ease-out; box-shadow: 0 0 40px rgba(0, 245, 255, 0.1);
        }}

        .stButton>button {{
            background: linear-gradient(45deg, #6200EE, #ec4899); color: white !important; border: none; padding: 1.2rem 3rem; border-radius: 15px; font-weight: 900; transition: all 0.3s ease; width: 100%; text-transform: uppercase; letter-spacing: 1px;
        }}

        .stButton>button:hover {{ transform: scale(1.05); box-shadow: 0 0 30px #ec4899; }}

        .navbar {{
            display: flex; justify-content: space-between; align-items: center; padding: 1rem 5%; background: rgba(0, 0, 0, 0.85); border-bottom: 2px solid #ec4899; backdrop-filter: blur(20px); position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
        }}

        .nav-logo-text {{ font-family: 'Orbitron', sans-serif; color: #ec4899; font-weight: 900; font-size: 2rem; letter-spacing: 2px; }}

        [data-testid="stSidebar"] {{ display: none; }}
        [data-testid="stSidebarNav"] {{ display: none; }}
        </style>
    """, unsafe_allow_html=True)

def main():
    bg_img = get_base64_of_bin_file("assets/slize_hero.png")
    inject_neon_css(bg_img)

    # --- ROBUST AUTH CHECK ---
    if "auth" not in st.secrets:
        st.error("⚠️ Authentication Configuration Missing")
        st.info("Please add `[auth]` and `[auth.google]` to your Streamlit Secrets.")
        st.stop()

    is_logged_in = False
    try:
        is_logged_in = st.user.get("is_logged_in", False)
    except Exception:
        if hasattr(st.user, "is_logged_in"):
            is_logged_in = st.user.is_logged_in

    if not is_logged_in:
        # FULL SCREEN LOGIN
        st.markdown('<div style="height: 15vh;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="neon-logo">SLIZE</div>', unsafe_allow_html=True)
        st.markdown('<div class="tagline">SLICE LONG VIDEOS INTO VIRAL SHORTS IN SECONDS 🔥</div>', unsafe_allow_html=True)
        
        _, mid, _ = st.columns([1, 1.5, 1])
        with mid:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("<h3 style='color: #ffffff; margin-bottom: 2rem; font-family: Orbitron;'>ACCESS CREATOR ENGINE</h3>", unsafe_allow_html=True)
            if st.button("CONTINUE WITH GOOGLE"):
                try:
                    st.login("google")
                except Exception as e:
                    st.error(f"Authentication Error: {str(e)}")
                    st.warning("Ensure your Redirect URI in Google Console matches your Streamlit Secrets.")
            st.markdown("<p style='margin-top: 2rem; opacity: 0.6; font-size: 0.9rem;'>Free • No Watermark • Secure with Google</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # --- LOGGED IN DASHBOARD ---
    user = st.user
    
    # Navbar
    st.markdown(f"""
        <div class="navbar">
            <div class="nav-logo-text">SLIZE</div>
            <div style="display: flex; align-items: center; gap: 20px;">
                <span style="color: #00f5ff; font-weight: 800; font-family: Orbitron; font-size: 0.9rem;">{user.get("name", "CREATOR").upper()}</span>
                <img src="{user.get("picture", "")}" style="width: 40px; border-radius: 50%; border: 2px solid #00f5ff;">
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height: 120px;"></div>', unsafe_allow_html=True)
    
    # Dashboard Container
    st.markdown('<div style="background: rgba(255,255,255,0.03); padding: 3rem; border-radius: 30px; border: 1px solid rgba(0,245,255,0.1); backdrop-filter: blur(10px);">', unsafe_allow_html=True)
    
    col_out, _ = st.columns([1, 6])
    if col_out.button("LOGOUT [EXIT]"):
        st.logout()

    uploaded_file = st.file_uploader("DROP YOUR MASTERPIECE HERE", type=["mp4", "mov", "avi"])
    
    if uploaded_file:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name
        
        info = get_video_info(video_path)
        st.video(video_path)
        
        st.markdown("### ⚡ VIRAL ENGINE")
        col1, col2, col3 = st.columns(3)
        with col1: ratio = st.selectbox("FORMAT", ["9:16 VERTICAL", "ORIGINAL"])
        with col2: speed = st.slider("SPEED RAMP", 0.5, 2.0, 1.1)
        with col3: caption = st.text_input("CAPTIONS", "WAIT FOR IT!")

        if 'q' not in st.session_state: st.session_state.q = []
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        stt = c1.number_input("START (S)", 0.0, float(info['duration']), 0.0)
        enn = c2.number_input("END (S)", 0.0, float(info['duration']), min(float(info['duration']), 30.0))
        if st.button("ADD TO QUEUE"):
            st.session_state.q.append((stt, enn))
            st.toast("Clip Added!")

        if st.session_state.q:
            st.markdown(f"**QUEUE: {len(st.session_state.q)} CLIPS READY**")
            if st.button("🚀 GENERATE VIRAL SHORTS"):
                email = user.get("email", "unknown")
                user_dir = os.path.join(USER_DATA_DIR, email)
                if not os.path.exists(user_dir): os.makedirs(user_dir)
                
                pbar = st.progress(0)
                for i, (s, e) in enumerate(st.session_state.q):
                    fname = f"clip_{int(time.time())}_{i}.mp4"
                    out = os.path.join(user_dir, fname)
                    process_video_clip(video_path, out, s, e, aspect_ratio="9:16", speed=speed, text_overlay=caption)
                    add_history(email, fname, uploaded_file.name)
                    pbar.progress((i+1)/len(st.session_state.q))
                
                st.balloons()
                st.session_state.q = []
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # --- VAULT (HISTORY) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 30px; border: 1px solid #ec4899; backdrop-filter: blur(10px);">', unsafe_allow_html=True)
    email = user.get("email", "unknown")
    st.markdown(f"### 📁 {user.get('name', 'CREATOR').upper()}'S VAULT")
    history = get_user_history(email)
    if history:
        hcols = st.columns(3)
        for i, (fname, ts) in enumerate(history):
            with hcols[i % 3]:
                fpath = os.path.join(USER_DATA_DIR, email, fname)
                if os.path.exists(fpath):
                    st.video(fpath)
                    with open(fpath, "rb") as f: st.download_button("DOWNLOAD", f, file_name=fname, key=f"v_{i}")
    else:
        st.info("Your vault is empty. Start slicing to build your viral library!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; color: #444; padding: 4rem; font-family: Orbitron; font-size: 0.8rem; letter-spacing: 2px;'>SLIZE.AI // THE CREATOR'S EDGE</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
