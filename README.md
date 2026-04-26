# VideoSlicer - Free Video to Shorts Maker

VideoSlicer is a production-ready Streamlit application designed to help content creators quickly turn long-form videos into viral vertical Shorts, Reels, and TikToks.

## Features
- **Upload**: Support for MP4, MOV, AVI, and MKV.
- **Modes**:
  - **Manual**: Extract specific segments.
  - **Equal Parts**: Automatically split into $N$ clips.
  - **Smart Shorts**: Batch process multiple custom ranges.
- **Transformations**:
  - Auto-crop to **9:16 Vertical** (Centered).
  - Center-aligned **Text Overlays**.
  - **Speed control** (0.5x to 2.0x).
  - Smooth **Fade in/out**.
- **Download**: Individual clip previews and bulk ZIP download.

## Local Installation

1. **Prerequisites**:
   - Python 3.8+
   - [FFmpeg](https://ffmpeg.org/download.html) installed and added to your system PATH.

2. **Clone and Install**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run**:
   ```bash
   streamlit run app.py
   ```

## Deployment on Streamlit Community Cloud

This app is optimized for Streamlit Cloud.
1. Push your code to a GitHub repository.
2. Connect the repository to Streamlit Cloud.
3. **Important**: Ensure `packages.txt` is present in the root (it contains `ffmpeg`), which Streamlit uses to install the necessary system dependencies.
4. Set `.streamlit/config.toml` to increase `maxUploadSize` if you plan to upload videos larger than 200MB.

## Technical Notes
- Uses **MoviePy** for all video manipulation.
- Temporary files are handled using `tempfile` and cleaned up by the OS/Streamlit session.
- For high-resolution exports (1080x1920), processing time depends on CPU power.
