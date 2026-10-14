#!/usr/bin/env python3
"""Build the cinematic Kids Jerseys Instagram reel from the raw phone clips.

Usage: python3 build.py <raw_clip_dir> <output.mp4>

Raw clips are the 20260920_*.mp4 files from the Drive folder (4K, 60fps, portrait).
Look follows kids-apparel campaign films: candid play, warm/matte "summer haze" grade,
slow motion on emotion and movement, hard cuts, no on-screen text, natural park sound.
"""
import os
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30

# (clip, source start s, source duration s, speed)
# 0.5 = slow-mo for laughs, hair, jumps, fabric; ~0.8-1.0 keeps rhythm on print/crest shots.
EDL = [
    ("182739", 0.20, 1.30, 0.50),  # girl laughing, France 10 - hook
    ("182440", 0.15, 0.85, 0.50),  # Barça kid flying jump
    ("182420", 0.30, 1.40, 0.80),  # Lamine Yamal 10 back print
    ("182427", 0.20, 1.10, 0.60),  # Yamal 10 playing with friends
    ("182700", 0.70, 1.20, 0.60),  # Barça home kit smile
    ("182649", 0.00, 1.40, 0.90),  # Portugal crest close-up
    ("182601", 0.10, 0.80, 0.80),  # ZAHRA 02 back print
    ("182436", 0.60, 0.90, 0.80),  # ZAHRA 02 walking away
    ("182412", 0.40, 1.60, 0.80),  # Germany away kit
    ("182903", 0.00, 0.90, 0.90),  # Germany crest detail
    ("182305", 4.00, 1.30, 0.50),  # pastel kit fabric close-up
    ("182728", 1.10, 1.10, 0.50),  # pink bow + 02
    ("182222", 2.60, 1.60, 0.60),  # Barça kid sprinting at camera
    ("182214", 3.00, 0.90, 0.80),  # girl in blue 10
    ("182135", 1.80, 1.70, 0.50),  # toddler in Germany kit turns to camera
]

# Warm, matte "summer haze": warmer white balance, lifted blacks, soft highlight roll-off.
GRADE = (
    "colortemperature=temperature=5600:mix=0.6,"
    "colorbalance=rs=0.03:bs=-0.02:rh=0.05:gh=0.02:bh=-0.05,"
    "curves=all='0/0.06 0.25/0.26 0.5/0.52 0.75/0.77 1/0.95',"
    "eq=contrast=0.97:saturation=0.95:gamma=1.02"
)


def main():
    raw, out = sys.argv[1], sys.argv[2]
    tmp = tempfile.mkdtemp()
    # Render each shot separately (decoding 15 4K streams at once runs out of memory),
    # then join with hard cuts via the concat demuxer.
    segs = []
    for i, (clip, ss, dur, speed) in enumerate(EDL):
        outdur = dur / speed
        last = i == len(EDL) - 1
        v = (
            f"trim=0:{dur},setpts=(PTS-STARTPTS)/{speed},fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,{GRADE}"
        )
        # Park sound plays at real speed under the slow-mo so it never sounds warped.
        a = f"asetpts=PTS-STARTPTS,aresample=48000,apad,atrim=0:{outdur:.3f},volume=0.8"
        a += f",afade=t=in:d=0.03,afade=t=out:st={outdur - 0.03:.3f}:d=0.03"
        if i == 0:
            v += ",fade=t=in:d=0.4"
        if last:
            v += f",fade=t=out:st={outdur - 0.6:.3f}:d=0.6"
            a += f",afade=t=out:st={outdur - 0.6:.3f}:d=0.6"
        seg = os.path.join(tmp, f"seg{i:02d}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-ss", f"{ss}", "-t", f"{max(dur, outdur):.3f}",
            "-i", os.path.join(raw, f"20260920_{clip}.mp4"),
            "-vf", v, "-af", a, "-t", f"{outdur:.3f}",
            "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            seg,
        ], check=True)
        segs.append(seg)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
        "-c", "copy", "-movflags", "+faststart", out,
    ], check=True)


if __name__ == "__main__":
    main()
