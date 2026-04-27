from __future__ import annotations

import base64
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import moviepy.video.fx as vfx
import streamlit as st
from moviepy import CompositeVideoClip, TextClip, VideoFileClip
from supabase import ClientOptions, create_client
from supabase_auth._sync.storage import SyncSupportedStorage


APP_TITLE = "Slize"
APP_ICON = "✂️"
DEFAULT_REDIRECT_URI = "http://localhost:8501"
USER_VAULT_DIR = Path("user_vault")


class SessionStateStorage(SyncSupportedStorage):
    def __init__(self, namespace: str) -> None:
        self.namespace = namespace

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def get_item(self, key: str) -> Optional[str]:
        return st.session_state.get(self._key(key))

    def set_item(self, key: str, value: str) -> None:
        st.session_state[self._key(key)] = value

    def remove_item(self, key: str) -> None:
        st.session_state.pop(self._key(key), None)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_binary_base64(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def get_redirect_uri() -> str:
    auth_section = st.secrets.get("auth", {}) if hasattr(st, "secrets") else {}
    return auth_section.get("redirect_uri", DEFAULT_REDIRECT_URI)


def get_supabase_client() -> Any:
    supabase_config = st.secrets.get("supabase", {})
    url = supabase_config.get("url")
    key = supabase_config.get("key")

    if not url or not key:
        return None

    if "_slize_browser_id" not in st.session_state:
        st.session_state["_slize_browser_id"] = uuid.uuid4().hex

    storage = SessionStateStorage(f"slize-auth-{st.session_state['_slize_browser_id']}")
    options = ClientOptions(
        storage=storage,
        persist_session=True,
        auto_refresh_token=True,
        flow_type="pkce",
    )
    return create_client(url, key, options)


def get_current_user(supabase: Any) -> Any:
    session = supabase.auth.get_session()
    if not session:
        return None

    user_response = supabase.auth.get_user()
    if user_response and user_response.user:
        return user_response.user
    return getattr(session, "user", None)


def normalize_name(user: Any) -> str:
    metadata = getattr(user, "user_metadata", {}) or {}
    return (
        getattr(user, "name", None)
        or metadata.get("full_name")
        or metadata.get("name")
        or (getattr(user, "email", None) or "Creator").split("@")[0]
    )


def sync_user_to_db(supabase: Any, user: Any) -> None:
    if not user:
        return

    metadata = getattr(user, "user_metadata", {}) or {}
    payload = {
        "id": user.id,
        "email": user.email,
        "name": normalize_name(user),
        "avatar_url": metadata.get("avatar_url") or metadata.get("picture"),
        "last_login": now_iso(),
    }

    try:
        supabase.table("users").upsert(payload, on_conflict="id").execute()
    except Exception as exc:
        st.sidebar.warning(f"User sync skipped: {exc}")


def save_short_to_history(
    supabase: Any,
    user: Any,
    source_name: str,
    clip_name: str,
    output_path: str,
    start_time: float,
    end_time: float,
    aspect_ratio: str,
    speed: float,
    caption: str,
) -> None:
    payload = {
        "user_id": user.id,
        "email": user.email,
        "clip_name": clip_name,
        "original_video": source_name,
        "output_path": output_path,
        "start_time": start_time,
        "end_time": end_time,
        "aspect_ratio": aspect_ratio,
        "speed": speed,
        "caption": caption,
        "created_at": now_iso(),
    }

    try:
        supabase.table("user_shorts").insert(payload).execute()
    except Exception as exc:
        st.sidebar.warning(f"History save skipped: {exc}")


def get_video_info(file_path: str) -> dict[str, Any]:
    clip = None
    try:
        clip = VideoFileClip(file_path)
        return {
            "duration": float(clip.duration or 0),
            "size": clip.size,
            "fps": float(clip.fps or 30),
            "aspect_ratio": clip.size[0] / clip.size[1] if clip.size[1] else 0,
        }
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        if clip is not None:
            clip.close()


def process_video_clip(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    aspect_ratio: str = "9:16",
    speed: float = 1.0,
    text_overlay: Optional[str] = None,
    text_options: Optional[dict[str, Any]] = None,
    fade_duration: float = 0.5,
) -> str:
    clip = None
    overlay = None
    final_clip = None
    try:
        clip = VideoFileClip(input_path).subclipped(start_time, end_time)

        if speed != 1.0:
            clip = clip.with_effects([vfx.MultiplySpeed(speed)])

        if aspect_ratio == "9:16":
            target_ratio = 9 / 16
            width, height = clip.size
            current_ratio = width / height if height else target_ratio

            if current_ratio > target_ratio:
                new_width = height * target_ratio
                clip = clip.with_effects([vfx.Crop(x_center=width / 2, width=new_width)])
            elif current_ratio < target_ratio:
                new_height = width / target_ratio
                clip = clip.with_effects([vfx.Crop(y_center=height / 2, height=new_height)])

            if clip.h < 1920:
                clip = clip.resized(height=1920)
            else:
                clip = clip.resized(width=1080)

            clip = clip.resized(new_size=(1080, 1920))

        if fade_duration > 0:
            clip = clip.with_effects([vfx.FadeIn(fade_duration), vfx.FadeOut(fade_duration)])

        if text_overlay:
            options = text_options or {}
            try:
                overlay = TextClip(
                    text=text_overlay,
                    font_size=options.get("fontsize", 72),
                    color=options.get("color", "white"),
                    font=options.get("font", "Arial-Bold"),
                    method="caption",
                    size=(int(clip.w * 0.82), None),
                )

                position = options.get("position", "center")
                if position == "top":
                    overlay = overlay.with_position(("center", 180))
                elif position == "bottom":
                    overlay = overlay.with_position(("center", clip.h - 280))
                else:
                    overlay = overlay.with_position("center")

                overlay = overlay.with_duration(clip.duration)
                final_clip = CompositeVideoClip([clip, overlay])
            except Exception as exc:
                st.warning(f"Caption overlay skipped: {exc}")

        export_clip = final_clip or clip
        export_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=export_clip.fps or 30,
            threads=4,
            logger=None,
        )
        return output_path
    finally:
        if overlay is not None:
            overlay.close()
        if final_clip is not None:
            final_clip.close()
        if clip is not None:
            clip.close()


def css() -> None:
    background = read_binary_base64("assets/slize_hero.png")
    background_image = (
        f'url("data:image/png;base64,{background}")' if background else ""
    )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;700;900&display=swap');

        :root {{
            --bg-0: #050816;
            --bg-1: #0b1020;
            --surface: rgba(10, 15, 30, 0.72);
            --surface-strong: rgba(8, 12, 24, 0.92);
            --line: rgba(255, 255, 255, 0.09);
            --text: #f5f7ff;
            --muted: rgba(245, 247, 255, 0.72);
            --pink: #ff4fd8;
            --cyan: #41d9ff;
            --violet: #7c5cff;
            --gold: #ffb347;
        }}

        html, body, .stApp {{
            background:
                radial-gradient(circle at top left, rgba(255, 79, 216, 0.16), transparent 30%),
                radial-gradient(circle at top right, rgba(65, 217, 255, 0.12), transparent 24%),
                radial-gradient(circle at bottom right, rgba(124, 92, 255, 0.16), transparent 28%),
                linear-gradient(135deg, var(--bg-0) 0%, var(--bg-1) 100%);
            color: var(--text);
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            {f"background-image: linear-gradient(rgba(4, 8, 20, 0.88), rgba(4, 8, 20, 0.96)), {background_image};" if background_image else ""}
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 0.02em;
        }}

        .slize-shell {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 1rem 0 2rem;
        }}

        .slize-hero {{
            position: relative;
            overflow: hidden;
            padding: 2rem;
            border: 1px solid var(--line);
            border-radius: 28px;
            background: linear-gradient(180deg, rgba(18, 22, 40, 0.88), rgba(9, 11, 22, 0.96));
            box-shadow: 0 28px 90px rgba(0, 0, 0, 0.45);
        }}

        .slize-hero::before,
        .slize-hero::after {{
            content: "";
            position: absolute;
            width: 280px;
            height: 280px;
            border-radius: 999px;
            filter: blur(40px);
            opacity: 0.32;
            pointer-events: none;
        }}

        .slize-hero::before {{
            top: -120px;
            right: -40px;
            background: radial-gradient(circle, rgba(255, 79, 216, 0.95), transparent 66%);
        }}

        .slize-hero::after {{
            bottom: -130px;
            left: -40px;
            background: radial-gradient(circle, rgba(65, 217, 255, 0.95), transparent 66%);
        }}

        .slize-brand {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: clamp(2.6rem, 8vw, 5.5rem);
            line-height: 0.95;
            margin: 0;
            text-transform: uppercase;
            text-shadow: 0 0 24px rgba(255, 79, 216, 0.55), 0 0 44px rgba(65, 217, 255, 0.25);
            animation: pulseGlow 3.8s ease-in-out infinite;
        }}

        .slize-tagline {{
            margin-top: 0.75rem;
            color: var(--muted);
            max-width: 58ch;
            font-size: 1rem;
            line-height: 1.6;
        }}

        .slize-pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1.25rem;
        }}

        .slize-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.04);
            color: var(--text);
            font-size: 0.84rem;
        }}

        .slize-card,
        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: linear-gradient(180deg, rgba(14, 18, 34, 0.86), rgba(8, 10, 18, 0.98)) !important;
            border-radius: 24px !important;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.3) !important;
        }}

        .slize-card {{
            padding: 1.25rem 1.35rem;
        }}

        .slize-cta, .stButton > button, .stDownloadButton > button {{
            border-radius: 16px !important;
            border: 0 !important;
            background: linear-gradient(135deg, var(--violet), var(--pink)) !important;
            color: white !important;
            font-weight: 800 !important;
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08), 0 18px 36px rgba(255, 79, 216, 0.2) !important;
            transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease !important;
            text-decoration: none !important;
        }}

        .slize-cta:hover, .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-1px) scale(1.01);
            filter: brightness(1.06);
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.09), 0 24px 50px rgba(255, 79, 216, 0.3) !important;
        }}

        .slize-cta {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            min-height: 3.5rem;
            padding: 0.95rem 1.25rem;
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            border: 1px dashed rgba(65, 217, 255, 0.45) !important;
            background: linear-gradient(180deg, rgba(65, 217, 255, 0.05), rgba(255, 255, 255, 0.03)) !important;
            border-radius: 22px !important;
            transition: border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease;
        }}

        [data-testid="stFileUploaderDropzone"]:hover {{
            border-color: rgba(255, 79, 216, 0.75) !important;
            transform: translateY(-1px);
            box-shadow: 0 0 0 1px rgba(255, 79, 216, 0.1), 0 20px 50px rgba(65, 217, 255, 0.14);
        }}

        [data-testid="stSidebar"] {{
            background: rgba(4, 6, 14, 0.76);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }}

        .slize-avatar {{
            width: 84px;
            height: 84px;
            border-radius: 22px;
            object-fit: cover;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 18px 30px rgba(0, 0, 0, 0.35);
            margin-bottom: 0.8rem;
        }}

        .slize-section-title {{
            margin: 0 0 1rem;
            font-size: 1rem;
            color: rgba(245, 247, 255, 0.86);
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }}

        .slize-muted {{
            color: var(--muted);
        }}

        .slize-login-grid {{
            display: grid;
            grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.9fr);
            gap: 1.5rem;
            align-items: center;
        }}

        .slize-login-panel {{
            padding: 1.3rem;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}

        .slize-login-panel h2 {{
            margin-top: 0;
        }}

        .slize-visual {{
            min-height: 460px;
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background:
                radial-gradient(circle at 20% 20%, rgba(255, 79, 216, 0.34), transparent 28%),
                radial-gradient(circle at 80% 20%, rgba(65, 217, 255, 0.24), transparent 24%),
                radial-gradient(circle at 50% 75%, rgba(124, 92, 255, 0.22), transparent 30%),
                linear-gradient(160deg, rgba(12, 16, 30, 0.9), rgba(4, 6, 14, 0.96));
            position: relative;
            overflow: hidden;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03), 0 22px 60px rgba(0, 0, 0, 0.28);
        }}

        .slize-visual::before {{
            content: "";
            position: absolute;
            inset: 18px;
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: inset 0 0 35px rgba(255, 255, 255, 0.03);
        }}

        .slize-visual-chip {{
            position: absolute;
            inset: auto auto 28px 28px;
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.55rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            color: white;
            font-size: 0.86rem;
            backdrop-filter: blur(12px);
        }}

        @keyframes pulseGlow {{
            0%, 100% {{ filter: drop-shadow(0 0 0 rgba(255, 79, 216, 0)); }}
            50% {{ filter: drop-shadow(0 0 26px rgba(255, 79, 216, 0.48)); }}
        }}

        @media (max-width: 900px) {{
            .slize-login-grid {{
                grid-template-columns: 1fr;
            }}

            .slize-visual {{
                min-height: 280px;
            }}

            .slize-shell {{
                padding-inline: 0.2rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def query_param(name: str) -> Optional[str]:
    try:
        value = st.query_params.get(name)
    except Exception:
        return None

    if value is None:
        return None
    if isinstance(value, list):
        return value[0] if value else None
    return str(value)


def handle_supabase_callback(supabase: Any) -> None:
    auth_code = query_param("code")
    if not auth_code:
        return

    processed_code = st.session_state.get("_processed_auth_code")
    if processed_code == auth_code:
        return

    try:
        supabase.auth.exchange_code_for_session(
            {
                "auth_code": auth_code,
                "redirect_to": get_redirect_uri(),
            }
        )
        st.session_state["_processed_auth_code"] = auth_code
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()
    except Exception as exc:
        st.session_state["auth_error"] = str(exc)


def require_supabase() -> Any:
    supabase = get_supabase_client()
    if supabase is None:
        st.error("Supabase configuration is missing.")
        st.info("Add `supabase.url` and `supabase.key` to `.streamlit/secrets.toml`.")
        st.stop()
    return supabase


def sidebar_user_panel(supabase: Any, user: Any) -> None:
    with st.sidebar:
        st.markdown("<p class='slize-section-title'>Workspace</p>", unsafe_allow_html=True)
        metadata = getattr(user, "user_metadata", {}) or {}
        avatar_url = metadata.get("avatar_url") or metadata.get("picture")

        if avatar_url:
            st.image(avatar_url, width=96)
        else:
            st.markdown(
                "<div style='width:96px;height:96px;border-radius:24px;background:linear-gradient(135deg,#7c5cff,#ff4fd8);display:flex;align-items:center;justify-content:center;font-family:Orbitron;font-weight:900;font-size:2rem;'>S</div>",
                unsafe_allow_html=True,
            )

        st.markdown(f"**{normalize_name(user)}**")
        st.caption(user.email)
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            try:
                supabase.auth.sign_out()
            finally:
                st.session_state.pop("clip_queue", None)
                st.session_state.pop("_processed_auth_code", None)
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.rerun()


def login_page(supabase: Any) -> None:
    redirect_uri = get_redirect_uri()
    auth_result = supabase.auth.sign_in_with_oauth(
        {
            "provider": "google",
            "options": {
                "redirect_to": redirect_uri,
            },
        }
    )

    hero = """
    <div class="slize-hero">
        <div class="slize-login-grid">
            <div>
                <p class="slize-section-title">Supabase Google Auth</p>
                <h1 class="slize-brand">Slize</h1>
                <p class="slize-tagline">
                    Turn long-form videos into premium shorts with a neon workflow that stays fast on mobile,
                    stable on reruns, and clean after Google sign-in.
                </p>
                <div class="slize-pill-row">
                    <span class="slize-pill">Google OAuth</span>
                    <span class="slize-pill">Supabase session sync</span>
                    <span class="slize-pill">Vertical shorts</span>
                    <span class="slize-pill">History vault</span>
                </div>
                <div class="slize-login-panel" style="margin-top:1.4rem;">
                    <h2>Creator Access</h2>
                    <p class="slize-muted" style="margin-bottom:1.2rem;">
                        Sign in with Google to unlock the slicer, save generated clips, and load your vault from Supabase.
                    </p>
                </div>
                <div style="margin-top:1rem; max-width: 28rem;">
                    <a class="slize-cta" href="{auth_url}" target="_self" rel="noreferrer noopener">Continue with Google</a>
                </div>
                <p class="slize-muted" style="margin-top:0.9rem; font-size:0.9rem;">
                    On success, Supabase returns to this app with a code. The app exchanges it immediately and reruns once.
                </p>
            </div>
            <div class="slize-visual">
                <div class="slize-visual-chip">Neon routing ready</div>
            </div>
        </div>
    </div>
    """.format(auth_url=auth_result.url)

    st.markdown(hero, unsafe_allow_html=True)

    if error := st.session_state.pop("auth_error", None):
        st.error(error)


def ensure_user_record(supabase: Any, user: Any) -> None:
    synced_key = f"_user_synced_{user.id}"
    if st.session_state.get(synced_key):
        return

    sync_user_to_db(supabase, user)
    st.session_state[synced_key] = True


def clear_user_sync_flags() -> None:
    for key in list(st.session_state.keys()):
        key_name = str(key)
        if key_name.startswith("_user_synced_"):
            st.session_state.pop(key_name, None)


def slicer_page(supabase: Any, user: Any) -> None:
    ensure_user_record(supabase, user)
    sidebar_user_panel(supabase, user)

    st.markdown(
        """
        <div class="slize-shell">
            <div class="slize-hero" style="margin-bottom:1.25rem;">
                <p class="slize-section-title">Main Studio</p>
                <h1 class="slize-brand" style="font-size:clamp(2.2rem, 7vw, 4.8rem);">Slize Studio</h1>
                <p class="slize-tagline">
                    Upload a source video, tune the range and style, then generate polished shorts with a smooth neon UI.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "clip_queue" not in st.session_state:
        st.session_state["clip_queue"] = []

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Drop a video here",
            type=["mp4", "mov", "avi", "mkv"],
            help="Upload a source video to slice into short-form clips.",
        )

        if not uploaded_file:
            st.info("Upload a video to start slicing.")
            return

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix or ".mp4")
        try:
            temp_file.write(uploaded_file.read())
            temp_file.close()
            input_path = temp_file.name

            info = get_video_info(input_path)
            if "error" in info:
                st.error(info["error"])
                return

            st.video(input_path)

            st.markdown("### Slice controls")
            left, middle, right = st.columns([1.1, 1, 1])
            with left:
                aspect = st.selectbox("Aspect ratio", ["9:16", "Original"], index=0)
            with middle:
                speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.05)
            with right:
                caption = st.text_input("Caption", value="WAIT FOR IT!")

            left_range, right_range = st.columns(2)
            max_duration = float(info["duration"])
            default_end = min(max_duration, 30.0)
            with left_range:
                start = st.number_input("Start (s)", min_value=0.0, max_value=max_duration, value=0.0, step=0.1)
            with right_range:
                end = st.number_input(
                    "End (s)",
                    min_value=0.1,
                    max_value=max_duration,
                    value=default_end,
                    step=0.1,
                )

            if end <= start:
                st.warning("End time must be greater than start time.")

            queue_controls = st.columns([1, 1])
            if queue_controls[0].button("Add to queue", use_container_width=True, disabled=end <= start):
                st.session_state["clip_queue"].append(
                    {
                        "start": float(start),
                        "end": float(end),
                        "aspect": aspect,
                        "speed": float(speed),
                        "caption": caption,
                    }
                )
                st.toast("Added to queue")

            if queue_controls[1].button("Clear queue", use_container_width=True):
                st.session_state["clip_queue"] = []
                st.rerun()

            if st.session_state["clip_queue"]:
                st.write(f"Queued clips: **{len(st.session_state['clip_queue'])}**")
                for index, item in enumerate(st.session_state["clip_queue"], start=1):
                    st.caption(
                        f"{index}. {item['start']:.1f}s → {item['end']:.1f}s | {item['aspect']} | {item['speed']:.2f}x"
                    )

                if st.button("Generate shorts", use_container_width=True):
                    output_dir = USER_VAULT_DIR / user.id
                    output_dir.mkdir(parents=True, exist_ok=True)

                    progress = st.progress(0)
                    status = st.empty()

                    try:
                        for index, item in enumerate(st.session_state["clip_queue"], start=1):
                            output_name = f"short_{int(time.time())}_{index}.mp4"
                            output_path = str(output_dir / output_name)
                            status.write(f"Generating clip {index}/{len(st.session_state['clip_queue'])}...")
                            process_video_clip(
                                input_path=input_path,
                                output_path=output_path,
                                start_time=item["start"],
                                end_time=item["end"],
                                aspect_ratio="9:16" if item["aspect"] == "9:16" else "original",
                                speed=item["speed"],
                                text_overlay=item["caption"],
                                text_options={
                                    "fontsize": 72,
                                    "color": "white",
                                    "font": "Arial-Bold",
                                    "position": "center",
                                },
                                fade_duration=0.5,
                            )
                            save_short_to_history(
                                supabase=supabase,
                                user=user,
                                source_name=uploaded_file.name,
                                clip_name=output_name,
                                output_path=output_path,
                                start_time=item["start"],
                                end_time=item["end"],
                                aspect_ratio=item["aspect"],
                                speed=item["speed"],
                                caption=item["caption"],
                            )
                            progress.progress(index / len(st.session_state["clip_queue"]))

                        status.success("Shorts generated successfully.")
                        st.balloons()
                        st.session_state["clip_queue"] = []
                        st.rerun()
                    except Exception as exc:
                        status.error(str(exc))
                    finally:
                        progress.empty()
        finally:
            if temp_file is not None:
                try:
                    temp_file.close()
                except Exception:
                    pass


def history_page(supabase: Any, user: Any) -> None:
    ensure_user_record(supabase, user)
    sidebar_user_panel(supabase, user)

    st.markdown(
        """
        <div class="slize-shell">
            <div class="slize-hero" style="margin-bottom:1.25rem;">
                <p class="slize-section-title">My Shorts</p>
                <h1 class="slize-brand" style="font-size:clamp(2.2rem, 7vw, 4.8rem);">Vault</h1>
                <p class="slize-tagline">Browse the clips saved to Supabase and preview local files when they exist on disk.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        response = (
            supabase.table("user_shorts")
            .select("*")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = response.data or []
    except Exception as exc:
        st.error(f"Unable to load history: {exc}")
        rows = []

    if not rows:
        st.info("No shorts yet. Generate your first clip from Slize.")
        return

    cols = st.columns(2)
    for index, row in enumerate(rows):
        with cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{row.get('clip_name', 'Untitled')}**")
                st.caption(row.get("created_at", ""))
                st.write(
                    f"{row.get('start_time', 0):.1f}s → {row.get('end_time', 0):.1f}s • {row.get('aspect_ratio', 'n/a')} • {row.get('speed', 1.0)}x"
                )

                local_file = row.get("output_path") or str(USER_VAULT_DIR / user.id / row.get("clip_name", ""))
                if local_file and os.path.exists(local_file):
                    st.video(local_file)
                    with open(local_file, "rb") as file:
                        st.download_button(
                            "Download clip",
                            file,
                            file_name=row.get("clip_name", "slize-short.mp4"),
                            use_container_width=True,
                            key=f"download-{row.get('id', index)}",
                        )
                else:
                    st.info("The local render file is not available in this runtime.")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
    css()

    supabase = require_supabase()
    handle_supabase_callback(supabase)

    current_user = get_current_user(supabase)

    if current_user:
        ensure_user_record(supabase, current_user)
        pages = {
            "Studio": [
                st.Page(lambda: slicer_page(supabase, current_user), title="Slize", icon="✂️", default=True),
                st.Page(lambda: history_page(supabase, current_user), title="My Shorts", icon="📁"),
            ]
        }
        nav = st.navigation(pages, position="sidebar")
    else:
        nav = st.navigation(
            [st.Page(lambda: login_page(supabase), title="Login", icon="🔐", default=True)],
            position="hidden",
        )

    nav.run()


if __name__ == "__main__":
    main()
