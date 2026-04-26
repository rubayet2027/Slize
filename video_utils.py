import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx as vfx


def get_video_info(file_path):
    """Extract metadata from a video file."""
    try:
        clip = VideoFileClip(file_path)
        info = {
            "duration": clip.duration,
            "size": clip.size,
            "fps": clip.fps,
            "aspect_ratio": clip.size[0] / clip.size[1]
        }
        clip.close()
        return info
    except Exception as e:
        return {"error": str(e)}

def process_video_clip(
    input_path, 
    output_path, 
    start_time, 
    end_time, 
    aspect_ratio="9:16", 
    speed=1.0, 
    text_overlay=None,
    text_options=None,
    fade_duration=0.5
):
    """
    Cuts and transforms a video clip.
    """
    # Load clip
    clip = VideoFileClip(input_path).subclipped(start_time, end_time)
    
    # Apply speed
    if speed != 1.0:
        clip = clip.with_effects([vfx.MultiplySpeed(speed)])
    
    # Handle Aspect Ratio (Crop to Vertical if needed)
    if aspect_ratio == "9:16":
        target_ratio = 9/16
        w, h = clip.size
        current_ratio = w / h
        
        if current_ratio > target_ratio:
            # Video is wider than 9:16 - Crop sides
            new_w = h * target_ratio
            clip = vfx.crop(clip, x_center=w/2, width=new_w)
        elif current_ratio < target_ratio:
            # Video is taller than 9:16 - Crop top/bottom
            new_h = w / target_ratio
            clip = vfx.crop(clip, y_center=h/2, height=new_h)
        
        # Resize to standard Short resolution
        clip = clip.resized(height=1920) if clip.h < 1920 else clip.resized(width=1080)
        # Ensure it fits 1080x1920 exactly
        clip = clip.resized(new_size=(1080, 1920))

    # Apply Fades
    if fade_duration > 0:
        clip = clip.with_effects([vfx.FadeIn(fade_duration), vfx.FadeOut(fade_duration)])

    # Apply Text Overlay
    if text_overlay and text_options:
        try:
            txt_clip = TextClip(
                text=text_overlay, 
                font_size=text_options.get('fontsize', 70), 
                color=text_options.get('color', 'white'),
                font=text_options.get('font', 'Arial-Bold'),
                method='caption',
                size=(clip.w * 0.8, None)
            )
            
            # Position
            pos = text_options.get('position', 'center')
            if pos == 'top':
                txt_clip = txt_clip.with_position(('center', 200))
            elif pos == 'bottom':
                txt_clip = txt_clip.with_position(('center', clip.h - 300))
            else:
                txt_clip = txt_clip.with_position('center')
                
            txt_clip = txt_clip.with_duration(clip.duration)
            clip = CompositeVideoClip([clip, txt_clip])
        except Exception as e:
            print(f"Warning: Text overlay failed: {e}")

    # Write output
    clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac", 
        fps=clip.fps or 30,
        threads=4,
        logger=None # Disable verbose output for cleaner logs
    )
    
    clip.close()
    return output_path
