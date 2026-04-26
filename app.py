import streamlit as st
import os
import tempfile
import zipfile
import shutil
import time
import base64
from datetime import timedelta
from video_utils import get_video_info, process_video_clip

# Page Configuration
st.set_page_config(
    page_title="Slize - Turn Long Videos into Viral Shorts",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def main():
    # Load background image
    bg_img_path = "assets/slize_hero.png"
    bg_img_base64 = ""
    if os.path.exists(bg_img_path):
        bg_img_base64 = get_base64_of_bin_file(bg_img_path)

    # --- CUSTOM CSS ---
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: #FAFAFA;
        }}

        /* Full Background Image with Overlay */
        .stApp {{
            background: linear-gradient(rgba(15, 15, 26, 0.7), rgba(15, 15, 26, 0.7)), 
                        url("data:image/png;base64,{bg_img_base64}") no-repeat center center fixed;
            background-size: cover;
        }}

        /* Navbar */
        .navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 5%;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .nav-logo {{
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(90deg, #BB86FC, #03DAC6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .nav-links {{
            display: flex;
            gap: 2rem;
        }}

        .nav-link {{
            color: #FAFAFA;
            text-decoration: none;
            font-weight: 600;
            opacity: 0.8;
        }}

        .nav-link:hover {{
            opacity: 1;
            color: #BB86FC;
        }}

        /* Glassmorphism Container */
        .glass-container {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 3rem;
            margin: 2rem auto;
            max-width: 1200px;
        }}

        /* Hero Text */
        .hero-section {{
            text-align: center;
            padding: 6rem 1rem;
        }}

        .hero-title {{
            font-size: 5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            text-shadow: 0 10px 30px rgba(0,0,0,0.5);
            background: linear-gradient(90deg, #FFFFFF, #B0B0B0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .hero-subtitle {{
            font-size: 1.8rem;
            color: #03DAC6;
            font-weight: 600;
            margin-bottom: 2rem;
            text-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}

        /* Buttons */
        .stButton>button {{
            background: linear-gradient(90deg, #6200EE, #BB86FC);
            color: white !important;
            border: none;
            padding: 0.8rem 2.5rem;
            border-radius: 14px;
            font-weight: 700;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(98, 0, 238, 0.4);
            width: 100%;
        }}

        .stButton>button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(98, 0, 238, 0.6);
        }}

        /* Hide Sidebar */
        [data-testid="stSidebar"] {{
            display: none;
        }}
        [data-testid="stSidebarNav"] {{
            display: none;
        }}
        
        /* Mobile */
        @media (max-width: 768px) {{
            .hero-title {{ font-size: 3rem; }}
            .hero-subtitle {{ font-size: 1.2rem; }}
            .glass-container {{ padding: 1.5rem; }}
        }}
        </style>
    """, unsafe_allow_html=True)

    # --- NAVBAR ---
    st.markdown("""
        <div class="navbar">
            <div class="nav-logo">Slize</div>
            <div class="nav-links">
                <a href="#" class="nav-link">Home</a>
                <a href="#" class="nav-link">Features</a>
                <a href="#" class="nav-link">Pricing</a>
                <a href="#" class="nav-link">Contact</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- HERO SECTION ---
    st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">Slize</h1>
            <p class="hero-subtitle">Viral Content in One Click.</p>
            <p style="color: #FAFAFA; opacity: 0.8; max-width: 700px; margin: 0 auto; font-size: 1.1rem;">
                Transform your horizontal videos into high-engagement vertical Shorts, Reels, and TikToks. 
                Powered by state-of-the-art video processing.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- MAIN CONTENT (GLASS CONTAINER) ---
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    # Uploader
    uploaded_file = st.file_uploader("Upload your video and go viral", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        # Create a temporary file
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name

        with st.spinner("Analyzing..."):
            info = get_video_info(video_path)

        if "error" in info:
            st.error(f"Error: {info['error']}")
        else:
            st.video(video_path)
            
            st.markdown("---")
            st.subheader("⚙️ Video Optimization")
            
            # Options moved from sidebar to main area
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                aspect_ratio = st.selectbox("Format", ["9:16 (Vertical)", "Original"], index=0)
                speed_factor = st.slider("Viral Speed", 0.5, 2.0, 1.0, 0.1)
            with col_opt2:
                text_overlay = st.text_input("Header Caption", placeholder="WAIT FOR IT!")
                text_color = st.color_picker("Text Color", "#FFFFFF")
            
            col_opt3, col_opt4 = st.columns(2)
            with col_opt3:
                text_size = st.slider("Font Size", 20, 150, 70)
            with col_opt4:
                text_pos = st.selectbox("Caption Position", ["top", "center", "bottom"], index=1)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Slicing Engine
            st.subheader("✂️ Slicing Engine")
            tab1, tab2, tab3 = st.tabs(["🎯 Manual", "⚖️ Equal", "🧠 Smart"])
            
            if 'clips' not in st.session_state:
                st.session_state['clips'] = []

            with tab1:
                c1, c2 = st.columns(2)
                start_s = c1.number_input("Start (s)", 0.0, float(info['duration']), 0.0)
                end_s = c2.number_input("End (s)", 0.0, float(info['duration']), min(float(info['duration']), 30.0))
                if st.button("Add Clip", key="manual_add", width='stretch'):
                    st.session_state['clips'].append((start_s, end_s))
                    st.toast("Added!")

            with tab2:
                num_clips = st.number_input("Parts", 2, 20, 3)
                if st.button("Divide Video", key="equal_add", width='stretch'):
                    st.session_state['clips'] = [(i * (info['duration']/num_clips), (i+1) * (info['duration']/num_clips)) for i in range(num_clips)]
                    st.toast("Divided!")

            with tab3:
                ranges_text = st.text_area("Ranges (e.g. 10-20, 30-40)")
                if st.button("Apply Smart Ranges", key="smart_add", width='stretch'):
                    try:
                        st.session_state['clips'] = []
                        for r in ranges_text.split(','):
                            s, e = map(float, r.strip().split('-'))
                            st.session_state['clips'].append((s, e))
                        st.success("Ranges Loaded")
                    except:
                        st.error("Invalid format")

            # Queue & Processing
            if st.session_state['clips']:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"**Queue: {len(st.session_state['clips'])} Clips Ready**")
                
                if st.button("🚀 GENERATE VIRAL CONTENT", key="main_process", width='stretch'):
                    output_dir = tempfile.mkdtemp()
                    generated_files = []
                    p_bar = st.progress(0)
                    
                    for i, (start, end) in enumerate(st.session_state['clips']):
                        output_filename = f"Slize_{i+1}.mp4"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        process_video_clip(
                            video_path, output_path, start, end,
                            aspect_ratio="9:16" if "9:16" in aspect_ratio else "original",
                            speed=speed_factor, text_overlay=text_overlay if text_overlay else None,
                            text_options={'fontsize': text_size, 'color': text_color, 'position': text_pos}
                        )
                        generated_files.append(output_path)
                        p_bar.progress((i + 1) / len(st.session_state['clips']))
                    
                    st.balloons()
                    
                    # Results
                    st.markdown("### 🎁 Results")
                    cols = st.columns(3)
                    zip_path = os.path.join(output_dir, "Slize_Bundle.zip")
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for idx, file in enumerate(generated_files):
                            with cols[idx % 3]:
                                st.video(file)
                                with open(file, "rb") as f:
                                    st.download_button("Download", f, file_name=os.path.basename(file), key=f"dl_{idx}")
                                zipf.write(file, os.path.basename(file))
                    
                    with open(zip_path, "rb") as f:
                        st.download_button("📦 Download All (ZIP)", f, file_name="Slize_Bundle.zip", width='stretch')

    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 3rem;'>
            <p>Made with ❤️ by Slize team</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
