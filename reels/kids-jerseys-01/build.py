#!/usr/bin/env python3
"""Build the cinematic Kids Jerseys Instagram reel from the raw phone clips.

Usage: python3 build.py <raw_clip_dir> <output.mp4>

Raw clips are the 20260920_*.mp4 files from the Drive folder (4K, 60fps, portrait).
Look follows kids-apparel campaign films: candid play, light warm/matte grade, slow motion
and motion blur on movement, tight crops on the jerseys, hard cuts, no on-screen text,
natural park sound. Opens on the Barça Lamine Yamal 10 kit as the hook.
"""
import os
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30

# (clip, source start s, source duration s, speed, zoom, centre x, centre y, motion blur)
# speed 0.5 = slow-mo (60fps source). zoom crops in on the jersey around (cx, cy), given as
# fractions of the frame. Motion blur blends neighbouring source frames, weighted to the
# middle one so the jersey stays readable (handheld footage smears with anything heavier).
EDL = [
    ("182420", 0.75, 0.85, 0.55, 1.25, 0.50, 0.45, 0),  # HOOK: Lamine Yamal 10 back print
    ("182440", 0.15, 0.85, 0.50, 1.45, 0.55, 0.35, 1),  # Barça kid flying jump
    ("182427", 0.20, 1.10, 0.60, 1.35, 0.55, 0.65, 1),  # Yamal 10 playing with friends
    ("182700", 1.00, 1.00, 0.60, 1.25, 0.50, 0.55, 0),  # Barça home kit smile
    ("182222", 2.85, 0.90, 0.60, 1.30, 0.45, 0.60, 0),  # Barça kid sprinting at camera
    ("182739", 0.20, 1.30, 0.50, 1.15, 0.50, 0.55, 0),  # girl laughing, France 10
    ("182649", 0.00, 1.40, 0.90, 1.00, 0.50, 0.50, 0),  # Portugal crest close-up
    ("182601", 0.10, 0.80, 0.80, 1.00, 0.50, 0.50, 0),  # ZAHRA 02 back print
    ("182436", 0.60, 0.90, 0.80, 1.35, 0.55, 0.50, 0),  # ZAHRA 02 walking away
    ("182412", 0.40, 1.60, 0.80, 1.30, 0.45, 0.62, 0),  # Germany away kit
    ("182903", 0.00, 0.90, 0.90, 1.00, 0.50, 0.50, 0),  # Germany crest detail
    ("182305", 4.00, 1.30, 0.50, 1.00, 0.50, 0.50, 0),  # pastel kit fabric close-up
    ("182728", 1.10, 1.10, 0.50, 1.20, 0.60, 0.60, 0),  # pink bow + 02
    ("182214", 3.25, 0.70, 0.70, 1.60, 0.68, 0.58, 1),  # girl in blue 10
    ("182135", 1.80, 1.70, 0.50, 1.30, 0.35, 0.60, 0),  # toddler in Germany kit turns to camera
]

# Lightly warm, matte grade: lifted blacks, soft highlight roll-off, jersey colours kept true.
GRADE = (
    "colortemperature=temperature=6000:mix=0.3,"
    "colorbalance=rs=0.01:rh=0.02:bh=-0.02,"
    "curves=all='0/0.05 0.25/0.26 0.5/0.52 0.75/0.77 1/0.96',"
    "eq=contrast=0.98:saturation=0.97:gamma=1.01"
)


def main():
    raw, out = sys.argv[1], sys.argv[2]
    tmp = tempfile.mkdtemp()
    # Render each shot separately (decoding 15 4K streams at once runs out of memory),
    # then join with hard cuts via the concat demuxer.
    segs = []
    for i, (clip, ss, dur, speed, zoom, cx, cy, blur) in enumerate(EDL):
        outdur = dur / speed
        last = i == len(EDL) - 1
        v = (
            f"trim=0:{dur},"
            f"crop=w=iw/{zoom}:h=ih/{zoom}:x='max(0,min(iw-ow,{cx}*iw-ow/2))':"
            f"y='max(0,min(ih-oh,{cy}*ih-oh/2))',"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
        )
        if blur:
            v += "tmix=frames=3:weights='1 2 1',"
        v += f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},{GRADE}"
        # Park sound plays at real speed under the slow-mo so it never sounds warped.
        a = f"asetpts=PTS-STARTPTS,aresample=48000,apad,atrim=0:{outdur:.3f},volume=0.8"
        a += f",afade=t=in:d=0.03,afade=t=out:st={outdur - 0.03:.3f}:d=0.03"
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
