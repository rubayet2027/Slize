import streamlit as st
import os
import tempfile
import zipfile
import shutil
import time
from datetime import timedelta
from video_utils import get_video_info, process_video_clip

# Page Configuration
st.set_page_config(
    page_title="Slize - Turn Long Videos into Viral Shorts",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
def local_css(mode="Dark"):
    if mode == "Dark":
        bg_color = "#0F0F1A"
        text_color = "#FAFAFA"
        card_bg = "rgba(30, 30, 46, 0.6)"
        hero_bg = "rgba(255, 255, 255, 0.03)"
        border_color = "rgba(255, 255, 255, 0.1)"
        gradient = "radial-gradient(circle at 50% -20%, #2A1B3D 0%, #0F0F1A 60%)"
        sub_text = "#B0B0B0"
    else:
        bg_color = "#F0F2F6"
        text_color = "#1F1F1F"
        card_bg = "rgba(255, 255, 255, 0.9)"
        hero_bg = "rgba(0, 0, 0, 0.02)"
        border_color = "rgba(0, 0, 0, 0.1)"
        gradient = "radial-gradient(circle at 50% -20%, #E0E7FF 0%, #F0F2F6 60%)"
        sub_text = "#4B5563"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            background-color: {bg_color};
            color: {text_color};
        }}

        .stApp {{
            background: {gradient};
        }}

        /* Hero Section */
        .hero-container {{
            padding: 4rem 2rem;
            text-align: center;
            background: {hero_bg};
            border-radius: 20px;
            margin-bottom: 3rem;
            border: 1px solid {border_color};
            backdrop-filter: blur(10px);
        }}

        .hero-title {{
            font-size: 4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #BB86FC, #03DAC6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }}

        .hero-subtitle {{
            font-size: 1.5rem;
            color: {sub_text};
            margin-bottom: 2rem;
        }}

        /* Buttons */
        .stButton>button {{
            background: linear-gradient(90deg, #6200EE, #BB86FC);
            color: white !important;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 12px;
            font-weight: 700;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(98, 0, 238, 0.3);
        }}

        .stButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(98, 0, 238, 0.5);
            background: linear-gradient(90deg, #BB86FC, #6200EE);
        }}

        /* Cards */
        .card {{
            background: {card_bg};
            padding: 2rem;
            border-radius: 16px;
            border: 1px solid {border_color};
            transition: transform 0.3s ease;
            color: {text_color};
        }}

        .card:hover {{
            border-color: #BB86FC;
        }}

        /* Badges */
        .badge {{
            background: #03DAC6;
            color: #0F0F1A;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 800;
            vertical-align: middle;
            margin-left: 10px;
        }}

        /* Result Item */
        .result-card {{
            background: {card_bg};
            border-radius: 12px;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid {border_color};
        }}

        /* Hide Streamlit Branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Custom Uploader Styling */
        .stFileUploader {{
            border: 2px dashed rgba(187, 134, 252, 0.3);
            border-radius: 15px;
            padding: 20px;
            background: rgba(187, 134, 252, 0.02);
        /* Mobile Responsiveness */
        @media (max-width: 768px) {{
            .hero-title {{
                font-size: 2.5rem !important;
            }}
            .hero-subtitle {{
                font-size: 1.1rem !important;
            }}
            .hero-container {{
                padding: 2rem 1rem !important;
            }}
            .card {{
                padding: 1.5rem !important;
                margin-bottom: 1rem !important;
            }}
        }}
        </style>
    """, unsafe_allow_html=True)

def main():
    # --- MODE TOGGLE ---
    theme_mode = st.sidebar.radio("Appearance", ["Dark", "Light"], horizontal=True)
    local_css(theme_mode)
    # --- HERO SECTION ---
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">Slize</h1>
            <p class="hero-subtitle">Turn Long Videos into Viral Shorts, Reels & TikToks in Seconds</p>
            <p style="color: #03DAC6; font-weight: bold;">⚡ Free • No Watermark • High Performance</p>
        </div>
    """, unsafe_allow_html=True)

    # Hero Image
    if os.path.exists("assets/slize_hero.png"):
        st.image("assets/slize_hero.png", width='stretch')
    else:
        st.image("https://picsum.photos/id/1015/1200/600", width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)

    # --- HOW IT WORKS ---
    st.markdown("### 🚀 How it Works")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="card">
                <h4>1. Upload 📤</h4>
                <p>Drop your long video (MP4/MOV). We support files up to 1GB.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="card">
                <h4>2. Slice ✂️</h4>
                <p>Choose Manual, Equal, or Smart mode. Auto-crop to 9:16 Vertical.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
            <div class="card">
                <h4>3. Go Viral 📈</h4>
                <p>Download your optimized clips and share directly to TikTok & Reels.</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.1)'><br>", unsafe_allow_html=True)

    # --- SIDEBAR SETTINGS ---
    st.sidebar.markdown("<h2 style='color: #BB86FC;'>🎨 Short Settings</h2>", unsafe_allow_html=True)
    aspect_ratio = st.sidebar.selectbox("Export Format", ["9:16 (Vertical)", "Original"], index=0)
    speed_factor = st.sidebar.slider("Viral Speed (1.1x - 1.2x recommended)", 0.5, 2.0, 1.0, 0.1)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='color: #03DAC6;'>🏷️ Caption Styling</h3>", unsafe_allow_html=True)
    text_overlay = st.sidebar.text_input("Header Text", placeholder="WAIT FOR IT!")
    text_color = st.sidebar.color_picker("Text Color", "#FFFFFF")
    text_size = st.sidebar.slider("Text Size", 20, 150, 70)
    text_pos = st.sidebar.selectbox("Caption Position", ["top", "center", "bottom"], index=1)

    # --- MAIN CONTENT ---
    # Centered Uploader
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        uploaded_file = st.file_uploader("Ready to go viral?", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        # Create a temporary file
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name

        # Video Info Card
        with st.spinner("Analyzing your video..."):
            info = get_video_info(video_path)

        if "error" in info:
            st.error(f"Error reading video: {info['error']}")
        else:
            # Stats & Preview
            st.markdown("<br>", unsafe_allow_html=True)
            col_info, col_prev = st.columns([1, 2])
            
            with col_info:
                st.markdown(f"""
                    <div class="card" style="margin-bottom: 20px;">
                        <h4>Video Stats</h4>
                        <p>⏱️ Duration: <b>{info['duration']:.2f}s</b></p>
                        <p>📐 Resolution: <b>{info['size'][0]}x{info['size'][1]}</b></p>
                        <p>🎞️ FPS: <b>{info['fps']:.2f}</b></p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.info("💡 Tip: 15-60s is ideal for Shorts/Reels algorithm.")
                
            with col_prev:
                st.video(video_path)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- SLICING ENGINE ---
            st.markdown("### ✂️ Slicing Engine")
            tab1, tab2, tab3 = st.tabs(["🎯 Manual Slice", "⚖️ Equal Parts", "🧠 Smart Shorts"])
            
            clips_to_process = []

            with tab1:
                st.write("Extract a specific high-engagement moment.")
                c1, c2 = st.columns(2)
                start_s = c1.number_input("Start (sec)", 0.0, float(info['duration']), 0.0)
                end_s = c2.number_input("End (sec)", 0.0, float(info['duration']), min(float(info['duration']), 30.0))
                if st.button("Add Manual Clip", width='stretch'):
                    st.session_state.setdefault('clips', []).append((start_s, end_s))
                    st.toast("Clip Added!", icon="✅")

            with tab2:
                st.write("Divide your video into perfectly sized chunks.")
                split_mode = st.radio("Divide by:", ["Number of clips", "Duration per clip"], horizontal=True)
                if split_mode == "Number of clips":
                    num_clips = st.number_input("Number of parts", 2, 50, 3)
                    if st.button("Generate Ranges", width='stretch'):
                        duration = info['duration']
                        clip_len = duration / num_clips
                        st.session_state['clips'] = [(i * clip_len, (i + 1) * clip_len) for i in range(num_clips)]
                else:
                    clip_dur = st.number_input("Duration (seconds)", 5.0, float(info['duration']), 30.0)
                    if st.button("Generate Ranges ", width='stretch'):
                        duration = info['duration']
                        st.session_state['clips'] = []
                        current = 0
                        while current + clip_dur <= duration:
                            st.session_state['clips'].append((current, current + clip_dur))
                            current += clip_dur

            with tab3:
                st.markdown("Enter multiple timestamps <span class='badge'>AI-OPTIMIZED READY</span>", unsafe_allow_html=True)
                ranges_text = st.text_area("Format: start-end, start-end (e.g. 10-25, 40-70)")
                if st.button("Apply Smart Ranges", width='stretch'):
                    try:
                        st.session_state['clips'] = []
                        for r in ranges_text.split(','):
                            s, e = map(float, r.strip().split('-'))
                            st.session_state['clips'].append((s, e))
                        st.success(f"Successfully loaded {len(st.session_state['clips'])} ranges")
                    except:
                        st.error("Format error: use 10-20, 30-40")

            # --- PROCESSING AREA ---
            if 'clips' in st.session_state and st.session_state['clips']:
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader(f"📋 Clip Queue ({len(st.session_state['clips'])})")
                
                with st.expander("Review Queue"):
                    for i, (s, e) in enumerate(st.session_state['clips']):
                        st.text(f"Short {i+1}: {s:.1f}s → {e:.1f}s ({e-s:.1f}s)")
                
                if st.button("🚀 GENERATE VIRAL SHORTS", width='stretch'):
                    output_dir = tempfile.mkdtemp()
                    generated_files = []
                    
                    p_bar = st.progress(0)
                    p_status = st.empty()
                    
                    start_proc_time = time.time()
                    
                    for i, (start, end) in enumerate(st.session_state['clips']):
                        p_status.markdown(f"**Processing Short {i+1}/{len(st.session_state['clips'])}...**")
                        output_filename = f"Slize_{i+1}.mp4"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        try:
                            process_video_clip(
                                video_path,
                                output_path,
                                start,
                                end,
                                aspect_ratio="9:16" if "9:16" in aspect_ratio else "original",
                                speed=speed_factor,
                                text_overlay=text_overlay if text_overlay else None,
                                text_options={
                                    'fontsize': text_size,
                                    'color': text_color,
                                    'position': text_pos
                                }
                            )
                            generated_files.append(output_path)
                        except Exception as e:
                            st.error(f"Error on Short {i+1}: {e}")
                        
                        p_bar.progress((i + 1) / len(st.session_state['clips']))
                    
                    end_proc_time = time.time()
                    st.balloons()
                    p_status.success(f"🔥 Successfully generated {len(generated_files)} Shorts in {end_proc_time - start_proc_time:.1f}s!")
                    
                    # --- RESULTS GRID ---
                    st.markdown("### 🎁 Your Viral Content")
                    
                    cols = st.columns(3)
                    zip_path = os.path.join(output_dir, "Slize_Bundle.zip")
                    
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for idx, file in enumerate(generated_files):
                            with cols[idx % 3]:
                                st.markdown(f"""
                                    <div class="result-card">
                                        <p style="color: #BB86FC; font-weight: bold; margin-bottom: 5px;">🔥 Ready for TikTok/Reels</p>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.video(file)
                                with open(file, "rb") as f:
                                    st.download_button(
                                        label="Download MP4",
                                        data=f,
                                        file_name=os.path.basename(file),
                                        mime="video/mp4",
                                        key=f"res_{idx}"
                                    )
                                zipf.write(file, os.path.basename(file))
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="📦 DOWNLOAD ALL AS ZIP",
                            data=f,
                            file_name="Slize_Bundle.zip",
                            mime="application/zip",
                            width='stretch'
                        )

    # --- FOOTER ---
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 2rem; border-top: 1px solid rgba(255,255,255,0.05)'>
            <p>Built with ❤️ by <b>Slize</b> for the next generation of creators.</p>
            <p style='font-size: 0.8rem;'>Optimized for Streamlit Cloud • Powered by MoviePy 2.x</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
