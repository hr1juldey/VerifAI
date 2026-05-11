"""
VerifAI Demo Video — PNG Frame Recorder
Records each segment as a sequence of PNG screenshots (lossless),
then encodes to high-quality MP4 via FFmpeg.

No CSS/theme changes. The site stays as-is.
Run: python3.10 scripts/video/record_frames.py [seg_name ...]
"""

import os
import sys
import subprocess
import shutil

BASE_URL = "http://localhost:3000"
FIXTURES = "/home/riju279/Documents/Code/Jepa/VerifAI/frontend/public/fixtures"
BASE_DIR = "/home/riju279/Documents/Code/Jepa/VerifAI/scripts/video"
FRAMES_DIR = os.path.join(BASE_DIR, "segments/frames")
AUDIO_DIR = os.path.join(BASE_DIR, "segments/audio")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(FRAMES_DIR, exist_ok=True)

VIEWPORT = {"width": 1920, "height": 1080}
FPS = 30

SEGMENT_DURATIONS = {
    "seg1_hero": 25.6,
    "seg2_obstacle": 61.7,
    "seg3_outcome": 34.0,
    "seg4_insight": 45.2,
    "seg5_demo": 21.4,
    "seg6_close": 10.8,
}


def smooth_scroll(page, target_y, duration_ms=1500):
    page.evaluate(f"window.scrollTo({{ top: {target_y}, behavior: 'smooth' }})")
    page.wait_for_timeout(duration_ms)


def record_segment(segment_name):
    """Record one segment as PNG frames in a subprocess."""
    target_dur = SEGMENT_DURATIONS.get(segment_name, 30)
    print(f"\n[{segment_name}] Recording ({target_dur}s target)...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_script = os.path.join(FRAMES_DIR, f"_tmp_{segment_name}.py")
    with open(tmp_script, "w") as f:
        f.write(f"""
import os, sys
sys.path.insert(0, r'{script_dir}')
from record_frames_lib import record_one_segment
record_one_segment('{segment_name}')
""")

    result = subprocess.run(
        ["python3.10", tmp_script],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        print(f"[{segment_name}] FAILED:")
        print(result.stderr[-500:])
        return False

    print(result.stdout.strip().split('\n')[-1])
    return True


def encode_segment(segment_name):
    """Encode PNG frames → MP4 for one segment."""
    frames_path = os.path.join(FRAMES_DIR, segment_name)
    output_path = os.path.join(FRAMES_DIR, f"{segment_name}.mp4")

    if not os.path.exists(frames_path) or not os.listdir(frames_path):
        print(f"[{segment_name}] No frames found, skipping encode")
        return False

    frame_count = len([f for f in os.listdir(frames_path) if f.endswith('.png')])
    print(f"[{segment_name}] Encoding {frame_count} frames → MP4...", end=" ", flush=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_path, "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-crf", "18",
        "-preset", "medium",
        "-movflags", "+faststart",
        output_path
    ], capture_output=True, timeout=120)

    size = os.path.getsize(output_path)
    print(f"{size:,} bytes")
    return True


if __name__ == "__main__":
    segments = sys.argv[1:] if len(sys.argv) > 1 else list(SEGMENT_DURATIONS.keys())

    print(f"Recording {len(segments)} segment(s)...")

    # Phase 1: Record all segments as PNG frames
    for seg in segments:
        record_segment(seg)

    # Phase 2: Encode to MP4
    print("\n=== Encoding ===")
    for seg in segments:
        encode_segment(seg)

    # Phase 3: Concatenate with audio
    print("\n=== Assembling ===")

    # Build video concat list
    video_list = os.path.join(FRAMES_DIR, "video_concat.txt")
    with open(video_list, "w") as f:
        for seg in segments:
            mp4_path = os.path.join(FRAMES_DIR, f"{seg}.mp4")
            if os.path.exists(mp4_path):
                f.write(f"file '{mp4_path}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", video_list,
        "-c", "copy",
        os.path.join(BASE_DIR, "tmp", "full_video_lossless.mp4")
    ], capture_output=True, timeout=60)

    # Build audio — use narration_full.wav directly
    narration_wav = os.path.join(AUDIO_DIR, "narration_full.wav")
    full_audio = os.path.join(BASE_DIR, "tmp", "full_audio.m4a")

    subprocess.run([
        "ffmpeg", "-y",
        "-i", narration_wav,
        "-c:a", "aac", "-b:a", "192k",
        "-ar", "44100", "-ac", "2",
        full_audio
    ], capture_output=True, timeout=60)

    # Merge video + audio
    final_output = os.path.join(OUTPUT_DIR, "verifai-demo-final.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", os.path.join(BASE_DIR, "tmp", "full_video_lossless.mp4"),
        "-i", os.path.join(BASE_DIR, "tmp", "full_audio.m4a"),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        final_output
    ], capture_output=True, timeout=60)

    size = os.path.getsize(final_output)
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", final_output],
        capture_output=True, text=True
    )
    dur = probe.stdout.strip()
    print(f"\n=== DONE ===")
    print(f"Output: {final_output}")
    print(f"Duration: {dur}s | Size: {size/1024/1024:.1f}MB")
