#!/usr/bin/env python3
"""
Video Slicer - Automatically splits a long video into clips using FFmpeg.
"""

import argparse
import subprocess
import os
import sys
import glob

def check_dependencies():
    """Check if ffmpeg and ffprobe are installed and accessible in the system PATH."""
    for tool in ["ffmpeg", "ffprobe"]:
        try:
            subprocess.run([tool, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"Error: '{tool}' is not installed or not found in system PATH.")
            print("Please install FFmpeg from https://ffmpeg.org/download.html")
            sys.exit(1)

def split_video(input_file, mode="fast", duration=30):
    """Split the video into segments using ffmpeg."""
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    check_dependencies()

    # Prepare output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    input_base = os.path.splitext(os.path.basename(input_file))[0]
    
    # Output pattern for the generated segments
    output_pattern = os.path.join(output_dir, f"{input_base}_clip_%03d.mp4")

    # Base FFmpeg command using the segment muxer
    cmd = [
        "ffmpeg", 
        "-hide_banner",
        "-i", input_file,
        "-f", "segment", 
        "-segment_time", str(duration), 
        "-reset_timestamps", "1",
        "-y" # Overwrite output files without asking
    ]

    if mode == "fast":
        # Fast mode: copy streams directly (no re-encoding)
        # Note: Splits occur at the nearest keyframe, so durations may not be exactly accurate.
        cmd.extend(["-c", "copy"])
    elif mode == "precise":
        # Precise mode: re-encode streams to split exactly at the specified duration
        cmd.extend([
            "-c:v", "libx264", 
            "-crf", "23",           # Constant Rate Factor for balanced quality/size
            "-preset", "fast",      # Faster encoding speed
            "-c:a", "aac",          # AAC audio encoding
            "-force_key_frames", f"expr:gte(t,n_forced*{duration})"
        ])
    
    cmd.append(output_pattern)

    print(f"--- Video Slicer ---")
    print(f"Input File: {os.path.abspath(input_file)}")
    print(f"Mode: {mode.capitalize()}")
    print(f"Clip Duration: {duration} seconds")
    print(f"Output Directory: {output_dir}")
    print("--------------------")
    print("Running FFmpeg... Please wait.\n")

    try:
        # Run ffmpeg command. 
        # Standard error is not redirected so that FFmpeg's native progress output is visible.
        subprocess.run(cmd, check=True)
        
        # Count and summarize created files
        created_clips = sorted(glob.glob(os.path.join(output_dir, f"{input_base}_clip_*.mp4")))
        
        print("\n" + "="*30)
        print(" SUMMARY")
        print("="*30)
        print(f"Success! Video was split into {len(created_clips)} clips.")
        print(f"Clips are located in: {output_dir}\n")
        
        for clip in created_clips:
            print(f" - {os.path.basename(clip)}")
            
    except subprocess.CalledProcessError:
        print("\nError: FFmpeg encountered an issue while processing the video.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Automatically split a long video into smaller consecutive clips using FFmpeg.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input", 
        help="Path to the input video file (e.g., input/video.mp4)"
    )
    parser.add_argument(
        "--mode", 
        choices=["fast", "precise"], 
        default="fast", 
        help="fast: No re-encoding. Splits on nearest keyframes (fastest, clip durations may vary).\n"
             "precise: Re-encodes video to ensure exact clip duration (slower, but accurate)."
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=30, 
        help="Duration of each clip in seconds (default: 30)"
    )
    
    args = parser.parse_args()
    split_video(args.input, args.mode, args.duration)

if __name__ == "__main__":
    main()
