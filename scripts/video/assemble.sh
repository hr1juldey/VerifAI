#!/bin/bash
# VerifAI Demo Video — Assembly Script (v3)
# Merges PNG frame segments with narration audio into final MP4
# Run: bash scripts/video/assemble.sh

set -e

BASE="/home/riju279/Documents/Code/Jepa/VerifAI/scripts/video"
FRAMES="$BASE/segments/frames"
AUDIO="$BASE/segments/audio"
TMP="$BASE/tmp"
OUTPUT="$BASE/output"

mkdir -p "$TMP" "$OUTPUT"

echo "=== VerifAI Video Assembly (v3) ==="

# Step 1: Encode PNG frames → MP4 per segment
echo "[1/4] Encoding PNG frames → MP4..."
for seg in seg1_hero seg2_obstacle seg3_outcome seg4_insight seg5_demo seg6_close; do
    frames_dir="$FRAMES/$seg"
    out="$TMP/${seg}.mp4"
    
    if [ -d "$frames_dir" ] && [ "$(ls -1 $frames_dir/*.png 2>/dev/null | wc -l)" -gt 0 ]; then
        frame_count=$(ls -1 $frames_dir/*.png 2>/dev/null | wc -l)
        echo "  $seg: $frame_count frames → MP4"
        ffmpeg -y -framerate 30 -i "$frames_dir/frame_%06d.png" \
            -c:v libx264 -pix_fmt yuv420p -profile:v high -crf 18 -preset medium \
            -movflags +faststart "$out" 2>/dev/null
    else
        echo "  $seg: NO FRAMES — generating placeholder"
        dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$AUDIO/${seg}.wav")
        ffmpeg -y -f lavfi -i "color=c=#0a0a0f:s=1920x1080:d=${dur}:r=30" \
            -c:v libx264 -pix_fmt yuv420p -profile:v high -crf 18 -preset fast \
            "$out" 2>/dev/null
    fi
    
    echo "file '$out'" >> "$TMP/video_concat.txt"
done

# Step 2: Concatenate all video segments
echo "[2/4] Concatenating video segments..."
ffmpeg -y -f concat -safe 0 -i "$TMP/video_concat.txt" \
    -c:v libx264 -pix_fmt yuv420p -profile:v high -crf 18 -preset medium -r 30 \
    "$TMP/full_video.mp4" 2>/dev/null
vid_dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$TMP/full_video.mp4")
echo "  Full video: ${vid_dur}s"

# Step 3: Use narration_full.wav as audio track
echo "[3/4] Preparing audio..."
ffmpeg -y -i "$AUDIO/narration_full.wav" \
    -c:a aac -b:a 192k -ar 44100 -ac 2 \
    "$TMP/full_audio.m4a" 2>/dev/null
aud_dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$TMP/full_audio.m4a")
echo "  Full audio: ${aud_dur}s"

# Step 4: Merge video + audio
echo "[4/4] Merging video + audio..."
ffmpeg -y \
    -i "$TMP/full_video.mp4" \
    -i "$TMP/full_audio.m4a" \
    -c:v copy -c:a aac -b:a 192k \
    -shortest \
    -movflags +faststart \
    "$OUTPUT/verifai-demo-final.mp4" 2>/dev/null

final_dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT/verifai-demo-final.mp4")
final_size=$(du -h "$OUTPUT/verifai-demo-final.mp4" | cut -f1)

echo ""
echo "=== DONE ==="
echo "Output: $OUTPUT/verifai-demo-final.mp4"
echo "Duration: ${final_dur}s"
echo "Size: ${final_size}"
