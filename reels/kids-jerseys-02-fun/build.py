#!/usr/bin/env python3
"""Build the fun, fast-paced Kids Jerseys Instagram reel from the raw phone clips.

Usage: python3 build.py <raw_clip_dir> <output.mp4> [--only 0,3,5]

Raw clips are the 20260920_*.mp4 files from the Drive folder (4K, 60fps, portrait).
~15s of quick cuts, bright and colourful grade, light leaks, lens flares and white
flash cuts, punch-in zooms, natural park sound. No on-screen text.
--only renders just those shots (for checking effects) and skips the final join.
"""
import os
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30

# fx: "flash" = cut in from white, "leak" = soft drifting light leak,
#     "flare" = bold anamorphic lens flare sweeping across, "blur" = motion blur,
#     "push" = punch-in zoom during the shot.
# (clip, source start s, source duration s, speed, zoom, centre x, centre y, fx)
EDL = [
    ("182420", 0.75, 1.00, 1.00, 1.25, 0.50, 0.45, "flash flare"),  # HOOK: Lamine Yamal 10
    ("182440", 0.30, 0.70, 0.50, 1.45, 0.55, 0.35, "leak blur"),    # Barça kid flying jump
    ("182427", 0.30, 0.70, 1.00, 1.35, 0.55, 0.65, "blur"),         # Yamal 10 playing
    ("182700", 1.00, 0.90, 1.00, 1.25, 0.50, 0.55, "flash"),        # Barça home kit smile
    ("182323", 0.00, 0.70, 1.00, 1.20, 0.50, 0.45, "push"),         # Barça kid catching breath
    ("182222", 2.85, 0.85, 1.00, 1.30, 0.45, 0.60, "flare"),        # Barça kid sprinting at camera
    ("182649", 0.40, 1.00, 1.10, 1.00, 0.50, 0.50, "leak"),         # Portugal crest
    ("182601", 0.10, 0.60, 1.00, 1.00, 0.50, 0.50, "flash"),        # ZAHRA 02 back print
    ("182430", 0.00, 0.60, 1.00, 1.20, 0.50, 0.45, "flare"),        # Portugal 02 by fairground lights
    ("182412", 0.80, 1.10, 1.00, 1.30, 0.45, 0.62, "leak push"),    # Germany away kit smile
    ("182903", 0.00, 0.55, 1.00, 1.00, 0.50, 0.50, "flash"),        # Germany crest detail
    ("182232", 3.30, 0.70, 1.00, 1.00, 0.50, 0.50, "push"),         # toddler stares into the lens
    ("182654", 0.90, 0.80, 1.00, 1.15, 0.50, 0.50, "blur flare"),   # pastel kit running
    ("182728", 1.20, 0.90, 1.00, 1.20, 0.60, 0.60, "leak"),         # pink bow + 02
    ("182305", 4.00, 1.40, 0.60, 1.00, 0.50, 0.50, "leak"),         # END: pastel kit fabric close-up
]

# Bright, punchy, colourful: more saturation and contrast, a touch of brightness.
GRADE = (
    "eq=contrast=1.08:brightness=0.03:saturation=1.22,"
    "vibrance=intensity=0.25,"
    "curves=all='0/0 0.25/0.24 0.5/0.53 0.75/0.8 1/1'"
)

# Light effects are drawn at quarter resolution (they are soft anyway) and scaled up.
LW, LH = W // 4, H // 4


def gauss(cx, cy, sx, sy):
    return f"exp(-(pow(X-({cx}),2)/(2*pow({sx},2))+pow(Y-({cy}),2)/(2*pow({sy},2))))"


def leak_src(d, flip):
    """Two warm/pink glows drifting across the frame."""
    p = f"(T/{d:.3f})"
    x1 = f"{LW}*({1.1 if flip else -0.1}{'-' if flip else '+'}0.5*{p})"
    x2 = f"{LW}*({-0.05 if flip else 1.05}{'+' if flip else '-'}0.4*{p})"
    b1 = gauss(x1, f"{LH}*0.18", LW * 0.45, LH * 0.30)
    b2 = gauss(x2, f"{LH}*(0.85-0.2*{p})", LW * 0.40, LH * 0.25)
    return (
        f"color=black:s={LW}x{LH}:r={FPS}:d={d:.3f},format=gbrp,"
        f"geq=r='255*min(1,1.0*{b1}+0.95*{b2})':"
        f"g='255*min(1,0.55*{b1}+0.35*{b2})':"
        f"b='255*min(1,0.20*{b1}+0.60*{b2})'"
    )


def flare_src(d, flip):
    """Bright core with a long horizontal streak and a mirrored ghost, sweeping across."""
    p = f"(T/{d:.3f})"
    cx = f"{LW}*({1.2 if flip else -0.2}{'-' if flip else '+'}1.4*{p})"
    cy = f"{LH}*0.28"
    core = gauss(cx, cy, LW * 0.10, LW * 0.10)
    halo = gauss(cx, cy, LW * 0.35, LW * 0.35)
    streak = gauss(cx, cy, LW * 1.2, LH * 0.010)
    ghost = gauss(f"{LW}-({cx})", f"{LH}-({cy})-{LH}*0.25", LW * 0.06, LW * 0.06)
    return (
        f"color=black:s={LW}x{LH}:r={FPS}:d={d:.3f},format=gbrp,"
        f"geq=r='255*min(1,1.0*{core}+0.35*{halo}+0.55*{streak}+0.25*{ghost})':"
        f"g='255*min(1,0.95*{core}+0.30*{halo}+0.80*{streak}+0.45*{ghost})':"
        f"b='255*min(1,0.85*{core}+0.20*{halo}+1.00*{streak}+0.60*{ghost})'"
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
    v += f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},{GRADE},format=gbrp"
    graph = [v + "[base]"]
    light = None
    if "leak" in fx:
        light, opacity = leak_src(outdur, i % 2), 0.7
    elif "flare" in fx:
        light, opacity = flare_src(outdur, i % 2), 0.85
    if light:
        graph.append(f"{light},gblur=sigma=2,scale={W}:{H}:flags=bicubic,format=gbrp[light]")
        graph.append(f"[base][light]blend=all_mode=screen:all_opacity={opacity}[lit]")
        tail = "[lit]"
    else:
        tail = "[base]"
    post = "format=yuv420p"
    if "flash" in fx:
        post += ",fade=t=in:st=0:d=0.12:color=white"
    if last:
        post += f",fade=t=out:st={outdur - 0.5:.3f}:d=0.5"
    graph.append(f"{tail}{post}[v]")
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
