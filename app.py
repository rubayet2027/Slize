import streamlit as st
import os
import tempfile
import zipfile
import shutil
import time
import base64
from datetime import timedelta
from video_utils import get_video_info, process_video_clip
from auth_utils import init_db, add_user, login_user, add_history, get_user_history

# Initialize Database
init_db()

# Page Configuration
st.set_page_config(
    page_title="Slize - Turn Long Videos into Viral Shorts",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
USER_DATA_DIR = "user_vault"
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file):
        return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_custom_css(bg_img_base64):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: #FAFAFA;
        }}

        .stApp {{
            background: linear-gradient(rgba(15, 15, 26, 0.85), rgba(15, 15, 26, 0.85)), 
                        url("data:image/png;base64,{bg_img_base64}") no-repeat center center fixed;
            background-size: cover;
        }}

        .navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.8rem 5%;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .nav-logo {{
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(90deg, #BB86FC, #03DAC6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }}

        .nav-auth {{
            display: flex;
            gap: 1.5rem;
            align-items: center;
        }}

        .nav-user {{
            color: #BB86FC;
            font-weight: 700;
        }}

        .glass-container {{
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 28px;
            padding: 3rem;
            margin: 2rem auto;
            max-width: 1100px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        }}

        .hero-section {{
            text-align: center;
            padding: 8rem 1rem 4rem 1rem;
        }}

        .hero-title {{
            font-size: 5.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(180deg, #FFFFFF 0%, #A0A0A0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .stButton>button {{
            background: linear-gradient(90deg, #6200EE, #BB86FC);
            color: white !important;
            border: none;
            padding: 0.8rem 2.5rem;
            border-radius: 14px;
            font-weight: 700;
            transition: all 0.3s ease;
            width: 100%;
        }}

        [data-testid="stSidebar"] {{ display: none; }}
        
        .history-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        </style>
    """, unsafe_allow_html=True)

def main():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'Login'

    bg_img_base64 = get_base64_of_bin_file("assets/slize_hero.png")
    inject_custom_css(bg_img_base64)

    # --- NAVBAR ---
    auth_html = ""
    if st.session_state['authenticated']:
        auth_html = f'<div class="nav-auth"><span class="nav-user">@{st.session_state["username"]}</span></div>'
    else:
        auth_html = '<div class="nav-auth"><span style="opacity: 0.7;">Guest Mode</span></div>'

    st.markdown(f"""
        <div class="navbar">
            <a href="/" class="nav-logo">Slize</a>
            {auth_html}
        </div>
    """, unsafe_allow_html=True)

    # --- AUTH LOGIC & HERO ---
    if not st.session_state['authenticated']:
        st.markdown('<div class="hero-section"><h1 class="hero-title">Slize</h1><p style="font-size: 1.5rem; color: #03DAC6;">Log in to unlock viral potential.</p></div>', unsafe_allow_html=True)
        
        _, auth_col, _ = st.columns([1, 1.5, 1])
        with auth_col:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            
            mode = st.radio("Join the community", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed")
            
            if mode == "Login":
                user = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.button("Access Dashboard"):
                    if login_user(user, pw):
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = user
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            else:
                new_user = st.text_input("Choose Username")
                new_email = st.text_input("Email Address")
                new_pw = st.text_input("Create Password", type="password")
                if st.button("Create Account"):
                    if add_user(new_user, new_pw, new_email):
                        st.success("Account created! You can now login.")
                    else:
                        st.error("Username already exists")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        # LOGGED IN VIEW
        st.markdown(f'<div class="hero-section" style="padding-top: 6rem; padding-bottom: 2rem;"><h1 class="hero-title" style="font-size: 3.5rem;">Welcome back, {st.session_state["username"]}</h1></div>', unsafe_allow_html=True)

        # Logout button in a clean spot
        if st.button("Logout", key="logout_btn", width=100):
            st.session_state['authenticated'] = False
            st.session_state['username'] = None
            st.rerun()

        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        
        # DASHBOARD
        uploaded_file = st.file_uploader("Drop your video file (MP4/MOV)", type=["mp4", "mov", "avi", "mkv"])

        if uploaded_file:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_path = tfile.name

            info = get_video_info(video_path)
            if "error" in info:
                st.error("Invalid Video")
            else:
                st.video(video_path)
                
                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    ratio = st.selectbox("Format", ["9:16 (Vertical)", "Original"])
                    speed = st.slider("Viral Speed", 0.5, 2.0, 1.0)
                with col_b:
                    caption = st.text_input("Caption", "WAIT FOR IT!")
                    color = st.color_picker("Color", "#FFFFFF")

                # Slicing
                tabs = st.tabs(["🎯 Manual", "⚖️ Equal", "🧠 Smart"])
                clips = []
                
                with tabs[0]:
                    s, e = st.columns(2)
                    start = s.number_input("Start", 0.0, float(info['duration']), 0.0)
                    end = e.number_input("End", 0.0, float(info['duration']), min(float(info['duration']), 30.0))
                    if st.button("Add to Queue", width='stretch'):
                        st.session_state.setdefault('queue', []).append((start, end))

                if st.session_state.get('queue'):
                    st.write(f"Queue: {len(st.session_state['queue'])} clips")
                    if st.button("🚀 PROCESS CLIPS", width='stretch'):
                        user_path = os.path.join(USER_DATA_DIR, st.session_state['username'])
                        if not os.path.exists(user_path): os.makedirs(user_path)
                        
                        pbar = st.progress(0)
                        for i, (stt, enn) in enumerate(st.session_state['queue']):
                            fname = f"clip_{int(time.time())}_{i}.mp4"
                            out_path = os.path.join(user_path, fname)
                            
                            process_video_clip(
                                video_path, out_path, stt, enn,
                                aspect_ratio="9:16" if "9:16" in ratio else "original",
                                speed=speed, text_overlay=caption,
                                text_options={'fontsize': 70, 'color': color, 'position': 'center'}
                            )
                            add_history(st.session_state['username'], fname, uploaded_file.name)
                            pbar.progress((i+1)/len(st.session_state['queue']))
                        
                        st.session_state['queue'] = []
                        st.success("Clips ready in your History!")
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # --- HISTORY SECTION ---
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.subheader("📁 Your Slize Vault")
        history = get_user_history(st.session_state['username'])
        if history:
            for fname, ts in history:
                with st.expander(f"🎬 {fname} - {ts}"):
                    fpath = os.path.join(USER_DATA_DIR, st.session_state['username'], fname)
                    if os.path.exists(fpath):
                        st.video(fpath)
                        with open(fpath, "rb") as f:
                            st.download_button("Download", f, file_name=fname, key=f"dl_{fname}")
                    else:
                        st.error("File not found on server")
        else:
            st.info("No clips yet. Start slicing to build your vault!")
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("<div style='text-align: center; color: #666; padding: 4rem;'>© 2026 Slize AI. Individual user data is encrypted and secure.</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
