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
    st.info("Please add your [supabase] section to Secrets.")
    st.stop()

# --- IMAGE LOADING ---
def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file): return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- CUSTOM CSS (NEON ANIMATIONS) ---
def inject_custom_css():
    bg_img = get_base64_of_bin_file("assets/slize_hero.png")
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Orbitron:wght@400;900&family=Inter:wght@400;700&display=swap');

        html, body, [class*="css"], h1, h2, h3, h4, h5, h6, p, span, button, label, .stMarkdown, .stText, .stButton, input, select, textarea {{ 
            font-family: 'Bangers', cursive !important; 
            color: #ffffff; 
            letter-spacing: 1px; 
        }}
        
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.9)), 
                        url("data:image/png;base64,{bg_img}") no-repeat center center fixed;
            background-size: cover;
        }}

        /* Neon Animations */
        @keyframes flicker {{ 0%, 100% {{ opacity: 1; text-shadow: 0 0 10px #ec4899; }} 50% {{ opacity: 0.8; text-shadow: 0 0 5px #ec4899; }} }}
        @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        .neon-logo {{
            font-family: 'Bangers', cursive; font-size: 7rem; text-align: center;
            color: #ffffff; animation: flicker 3s infinite; letter-spacing: 5px;
            margin-top: 2rem;
        }}

        /* Container Styling */
        [data-testid="stVerticalBlockBorderWrapper"] > div:has(div[data-testid="stVerticalBlock"]) {{
            background: rgba(255, 255, 255, 0.04) !important;
            backdrop-filter: blur(60px) !important;
            border: 1px solid rgba(0, 245, 255, 0.2) !important;
            border-radius: 40px !important;
            padding: 3rem !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.6) !important;
        }}

        .stButton>button {{
            background: linear-gradient(45deg, #6200EE, #ec4899); color: white !important;
            border: none; border-radius: 15px; padding: 1rem 2rem; font-weight: 800;
            transition: all 0.3s; width: 100%; text-transform: uppercase;
        }}
        .stButton>button:hover {{ transform: scale(1.02); box-shadow: 0 0 30px #ec4899; }}

        .nav-logo {{ font-family: 'Bangers', cursive; color: #ec4899; font-size: 2.5rem; margin-bottom: 20px; text-align: center; }}
        
        /* Center text */
        .centered-text {{ text-align: center; }}
        </style>
    """, unsafe_allow_html=True)

# --- DB HELPERS ---
def sync_user_to_db(user):
    if not user: return
    try:
        data = {"id": user.email, "email": user.email, "name": user.name, "avatar_url": user.picture, "last_login": datetime.now().isoformat()}
        supabase.table("users").upsert(data).execute()
    except Exception as e:
        print(f"DB Sync Error: {e}")

def save_short_to_history(email, clip_name, original_name):
    try:
        data = {"user_id": email, "clip_name": clip_name, "original_video": original_name, "created_at": datetime.now().isoformat()}
        supabase.table("user_shorts").insert(data).execute()
    except Exception as e:
        st.error(f"History Save Error: {e}")

# --- PAGE FUNCTIONS ---

def login_page():
    inject_custom_css()
    st.markdown('<div style="height: 10vh;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-logo">SLIZE</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #00f5ff; font-size: 1.5rem; font-weight: 700; letter-spacing: 2px;">SLICE VIDEOS INTO VIRAL SHORTS 🔥</p>', unsafe_allow_html=True)
    
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; font-family: Orbitron; font-size: 1.8rem; letter-spacing: 2px;'>CREATOR ACCESS</h2>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Dual Buttons: Login and Sign Up
            l_col, r_col = st.columns(2)
            with l_col:
                if st.button("🔐 LOGIN"):
                    st.login("google")
            with r_col:
                if st.button("🚀 SIGN UP"):
                    st.login("google")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; opacity: 0.6; font-size: 0.9rem; margin-top: 1rem;'>Free • No Watermark • Secure with Google</p>", unsafe_allow_html=True)

def home_page():
    inject_custom_css()
    user = st.user
    if 'synced' not in st.session_state:
        sync_user_to_db(user)
        st.session_state.synced = True
    
    with st.sidebar:
        st.markdown('<div class="nav-logo">SLIZE</div>', unsafe_allow_html=True)
        if user.picture: st.image(user.picture, width=100)
        st.write(f"Hello, **{user.name}**")
        if st.button("LOGOUT"): st.logout()
        st.markdown("---")

    st.markdown(f'<h1 style="font-family: Bangers; font-size: 4rem; color: #ec4899; text-shadow: 0 0 10px #ec4899;">STUDIO</h1>', unsafe_allow_html=True)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("DROP YOUR MASTERPIECE HERE", type=["mp4", "mov", "avi"])
        
        if uploaded_file:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_path = tfile.name
            
            info = get_video_info(video_path)
            st.video(video_path)
            
            st.markdown("### ⚡ VIRAL ENGINE")
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
                st.toast("Added to Queue!")

            if st.session_state.q:
                st.write(f"**QUEUE: {len(st.session_state.q)} CLIPS READY**")
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

def history_page():
    inject_custom_css()
    user = st.user
    with st.sidebar:
        st.markdown('<div class="nav-logo">SLIZE</div>', unsafe_allow_html=True)
        if user.picture: st.image(user.picture, width=100)
        st.write(f"Logged in as **{user.name}**")
        if st.button("LOGOUT"): st.logout()
        st.markdown("---")

    st.markdown('<h1 style="font-family: Bangers; font-size: 4rem; color: #ec4899; text-shadow: 0 0 10px #ec4899;">MY VAULT</h1>', unsafe_allow_html=True)
    
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
                with st.container(border=True):
                    st.write(f"📅 {item['created_at'][:10]}")
                    fpath = os.path.join("user_vault", user.email, item['clip_name'])
                    if os.path.exists(fpath):
                        st.video(fpath)
                        with open(fpath, "rb") as f:
                            st.download_button("DOWNLOAD", f, file_name=item['clip_name'], key=f"dl_{i}")
                    else:
                        st.error("File missing locally")
    else:
        st.info("Your vault is empty. Start slicing!")

# --- ROUTING LOGIC ---
login_pg = st.Page(login_page, title="Login", icon="🔐")
home_pg = st.Page(home_page, title="Studio", icon="✂️", default=True)
history_pg = st.Page(history_page, title="Vault", icon="📁")

if not st.user.is_logged_in:
    pg = st.navigation([login_pg], position="hidden")
else:
    pg = st.navigation({"Creation": [home_pg], "Archive": [history_pg]})

if __name__ == "__main__":
    pg.run()
