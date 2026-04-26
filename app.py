import streamlit as st
import os
import tempfile
import zipfile
import shutil
from datetime import timedelta
from video_utils import get_video_info, process_video_clip

# Page Configuration
st.set_page_config(
    page_title="VideoSlicer - Free Video to Shorts Maker",
    page_icon="🎬",
    layout="centered"
)

# Custom CSS for modern look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
    }
    .stDownloadButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #2e7d32;
        color: white;
        font-weight: bold;
    }
    .video-info-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #262730;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("🎬 VideoSlicer")
    st.subheader("Turn long videos into viral Shorts, Reels & TikToks")

    with st.expander("ℹ️ How it works"):
        st.write("""
        1. **Upload**: Drop your MP4, MOV, or AVI file.
        2. **Configure**: Choose your slicing mode (Manual, Equal Parts, or Smart).
        3. **Customize**: Set aspect ratio (9:16 for Shorts), add text overlays, or speed up the clip.
        4. **Generate**: We'll process your clips and provide download links.
        """)

    # Sidebar Settings
    st.sidebar.header("⚙️ Global Settings")
    aspect_ratio = st.sidebar.selectbox("Aspect Ratio", ["9:16 (Vertical)", "Original"], index=0)
    speed_factor = st.sidebar.slider("Speed Factor", 0.5, 2.0, 1.0, 0.1)
    
    st.sidebar.markdown("---")
    st.sidebar.header("🎨 Text Overlay")
    text_overlay = st.sidebar.text_input("Caption Text", placeholder="e.g. WAIT FOR IT!")
    text_color = st.sidebar.color_picker("Text Color", "#FFFFFF")
    text_size = st.sidebar.slider("Font Size", 20, 150, 70)
    text_pos = st.sidebar.selectbox("Position", ["top", "center", "bottom"], index=1)

    # File Uploader
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        # Create a temporary file to save the upload
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name

        # Get Video Metadata
        with st.spinner("Analyzing video..."):
            info = get_video_info(video_path)

        if "error" in info:
            st.error(f"Error reading video: {info['error']}")
        else:
            # Display Video Info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Duration", f"{info['duration']:.2f}s")
            with col2:
                st.metric("Resolution", f"{info['size'][0]}x{info['size'][1]}")
            with col3:
                st.metric("FPS", f"{info['fps']:.2f}")

            st.video(video_path)

            st.markdown("---")
            st.header("✂️ Slicing Options")
            
            tab1, tab2, tab3 = st.tabs(["Manual Mode", "Equal Parts", "Smart Shorts"])
            
            clips_to_process = []

            with tab1:
                st.write("Extract a specific segment from the video.")
                col_start, col_end = st.columns(2)
                start_s = col_start.number_input("Start Time (seconds)", 0.0, float(info['duration']), 0.0)
                end_s = col_end.number_input("End Time (seconds)", 0.0, float(info['duration']), min(float(info['duration']), 30.0))
                
                if st.button("Add Manual Clip"):
                    clips_to_process.append((start_s, end_s))
                    st.success(f"Added clip: {start_s}s - {end_s}s")

            with tab2:
                st.write("Split the video into multiple equal parts.")
                split_mode = st.radio("Split by:", ["Number of clips", "Duration per clip"])
                if split_mode == "Number of clips":
                    num_clips = st.number_input("How many clips?", 2, 20, 3)
                    if st.button("Generate Equal Ranges"):
                        duration = info['duration']
                        clip_len = duration / num_clips
                        for i in range(num_clips):
                            clips_to_process.append((i * clip_len, (i + 1) * clip_len))
                else:
                    clip_dur = st.number_input("Clip duration (seconds)", 5.0, float(info['duration']), 30.0)
                    if st.button("Generate Duration Ranges"):
                        duration = info['duration']
                        current = 0
                        while current + clip_dur <= duration:
                            clips_to_process.append((current, current + clip_dur))
                            current += clip_dur

            with tab3:
                st.write("Input multiple custom ranges (start-end).")
                ranges_text = st.text_area("Enter ranges (e.g. 10-20, 45-60)", help="Format: start-end, comma separated")
                if st.button("Parse Smart Ranges"):
                    try:
                        for r in ranges_text.split(','):
                            s, e = map(float, r.strip().split('-'))
                            clips_to_process.append((s, e))
                        st.success(f"Parsed {len(clips_to_process)} clips")
                    except:
                        st.error("Invalid format. Use start-end, start-end (e.g. 10-20, 40-50)")

            st.markdown("---")
            
            # Show list of clips to be processed
            if clips_to_process:
                st.subheader(f"📋 Clips to Generate ({len(clips_to_process)})")
                for i, (s, e) in enumerate(clips_to_process):
                    st.text(f"Clip {i+1}: {s:.2f}s to {e:.2f}s (Duration: {e-s:.2f}s)")

                if st.button("🚀 PROCESS AND GENERATE SHORTS"):
                    output_dir = tempfile.mkdtemp()
                    generated_files = []
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, (start, end) in enumerate(clips_to_process):
                        status_text.text(f"Processing Clip {i+1}/{len(clips_to_process)}...")
                        output_filename = f"short_clip_{i+1}.mp4"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        try:
                            # Run MoviePy processing
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
                            st.error(f"Error processing Clip {i+1}: {e}")
                        
                        progress_bar.progress((i + 1) / len(clips_to_process))
                    
                    status_text.text("✅ All clips processed!")
                    
                    # Display Results
                    st.header("🎁 Your Generated Shorts")
                    
                    zip_path = os.path.join(output_dir, "all_shorts.zip")
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for file in generated_files:
                            # Display individual preview and download
                            with st.container():
                                col_v, col_d = st.columns([2, 1])
                                with col_v:
                                    st.video(file)
                                with col_d:
                                    st.markdown(f"**Clip {os.path.basename(file)}**")
                                    with open(file, "rb") as f:
                                        st.download_button(
                                            label=f"Download Clip",
                                            data=f,
                                            file_name=os.path.basename(file),
                                            mime="video/mp4",
                                            key=f"dl_{file}"
                                        )
                            zipf.write(file, os.path.basename(file))
                    
                    st.markdown("---")
                    # Bulk download
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="📦 Download All Clips (ZIP)",
                            data=f,
                            file_name="videoslicer_shorts.zip",
                            mime="application/zip"
                        )

            elif uploaded_file:
                st.info("Add clips using the modes above to start processing.")

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center'>
            <p>Made with ❤️ for Content Creators</p>
            <small>Note: Processing large videos may take some time depending on your server resources.</small>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
