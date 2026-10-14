#!/usr/bin/env python3
"""Build the fun, fast-paced Kids Jerseys Instagram reel from the raw phone clips.

Usage: python3 build.py <raw_clip_dir> <output.mp4> [--only 0,3,5]

Raw clips are the 20260920_*.mp4 files from the Drive folder (4K, 60fps, portrait).
~14s of quick hard cuts, bright and colourful grade, punch-in zooms, light motion blur,
natural park sound. No on-screen text, no light leaks, flares or flashes.
--only renders just those shots (for checking effects) and skips the final join.
"""
import os
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30

# fx: "blur" = light motion blur, "push" = punch-in zoom during the shot.
# (clip, source start s, source duration s, speed, zoom, centre x, centre y, fx)
EDL = [
    ("182420", 0.75, 1.00, 1.00, 1.25, 0.50, 0.45, ""),       # HOOK: Lamine Yamal 10
    ("182440", 0.30, 0.70, 0.50, 1.45, 0.55, 0.35, "blur"),   # Barça kid flying jump
    ("182427", 0.30, 0.70, 1.00, 1.35, 0.55, 0.65, "blur"),   # Yamal 10 playing
    ("182700", 1.00, 0.90, 1.00, 1.25, 0.50, 0.55, ""),       # Barça home kit smile
    ("182323", 0.00, 0.70, 1.00, 1.20, 0.50, 0.45, "push"),   # Barça kid catching breath
    ("182222", 2.85, 0.85, 1.00, 1.30, 0.45, 0.60, ""),       # Barça kid sprinting at camera
    ("182649", 0.40, 1.00, 1.10, 1.00, 0.50, 0.50, ""),       # Portugal crest
    ("182601", 0.10, 0.60, 1.00, 1.00, 0.50, 0.50, ""),       # ZAHRA 02 back print
    ("182430", 0.00, 0.60, 1.00, 1.20, 0.50, 0.45, ""),       # Portugal 02 by fairground lights
    ("182412", 0.80, 1.10, 1.00, 1.30, 0.45, 0.62, "push"),   # Germany away kit smile
    ("182903", 0.00, 0.55, 1.00, 1.00, 0.50, 0.50, ""),       # Germany crest detail
    ("182232", 3.30, 0.70, 1.00, 1.00, 0.50, 0.50, "push"),   # toddler stares into the lens
    ("182654", 0.90, 0.80, 1.00, 1.15, 0.50, 0.50, "blur"),   # pastel kit running
    ("182728", 1.20, 0.90, 1.00, 1.20, 0.60, 0.60, ""),       # pink bow + 02
    ("182305", 4.00, 1.40, 0.60, 1.00, 0.50, 0.50, ""),       # END: pastel kit fabric close-up
]

# Bright, punchy, colourful: more saturation and contrast, a touch of brightness.
GRADE = (
    "eq=contrast=1.08:brightness=0.03:saturation=1.22,"
    "vibrance=intensity=0.25,"
    "curves=all='0/0 0.25/0.24 0.5/0.53 0.75/0.8 1/1'"
)

def build_segment(raw, tmp, i, shot, last):
    clip, ss, dur, speed, zoom, cx, cy, fx = shot
    fx = fx.split()
    outdur = dur / speed
    v = (
        f"[0:v]trim=0:{dur},"
        f"crop=w=iw/{zoom}:h=ih/{zoom}:x='max(0,min(iw-ow,{cx}*iw-ow/2))':"
        f"y='max(0,min(ih-oh,{cy}*ih-oh/2))',"
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
    )
    if "push" in fx:
        z = f"(1+0.12*t/{dur})"
        v += (f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,"
              f"crop={W}:{H},")
    if "blur" in fx:
        v += "tmix=frames=3:weights='1 2 1',"
    v += f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},{GRADE},format=yuv420p"
    if last:
        v += f",fade=t=out:st={outdur - 0.5:.3f}:d=0.5"
    graph = [v + "[v]"]
    # Park sound at real speed, short fades at each cut so hard cuts don't click.
    a = (f"[0:a]asetpts=PTS-STARTPTS,aresample=48000,apad,atrim=0:{outdur:.3f},"
         f"afade=t=in:d=0.02,afade=t=out:st={outdur - 0.02:.3f}:d=0.02")
    if last:
        a += f",afade=t=out:st={outdur - 0.5:.3f}:d=0.5"
    graph.append(a + "[a]")
    gfile = os.path.join(tmp, f"g{i:02d}.txt")
    with open(gfile, "w") as f:
        f.write(";\n".join(graph))
    seg = os.path.join(tmp, f"seg{i:02d}.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{ss}", "-t", f"{max(dur, outdur):.3f}",
        "-i", os.path.join(raw, f"20260920_{clip}.mp4"),
        "-filter_complex_script", gfile, "-map", "[v]", "-map", "[a]", "-t", f"{outdur:.3f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        seg,
    ], check=True)
    return seg


def main():
    raw, out = sys.argv[1], sys.argv[2]
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    tmp = tempfile.mkdtemp()
    segs = []
    for i, shot in enumerate(EDL):
        if only is not None and i not in only:
            continue
        segs.append(build_segment(raw, tmp, i, shot, i == len(EDL) - 1))
    if only is not None:
        os.makedirs(out, exist_ok=True)
        for s in segs:
            os.replace(s, os.path.join(out, os.path.basename(s)))
        return
    # Hard cuts via the concat demuxer; one loudness pass over the park sound.
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
        "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out,
    ], check=True)


if __name__ == "__main__":
    main()
