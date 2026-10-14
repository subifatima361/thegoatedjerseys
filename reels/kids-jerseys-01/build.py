#!/usr/bin/env python3
"""Build the Kids Jerseys Instagram reel from the raw phone clips.

Usage: python3 build.py <raw_clip_dir> <output.mp4> [--clean]

Raw clips are the 20260920_*.mp4 files from the Drive folder (4K, 60fps, portrait).
--clean renders the same cut without any text overlays.
"""
import os
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_SUB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"

# (clip, source start s, source duration s, speed, headline, subline)
EDL = [
    ("182739", 0.20, 1.40, 0.75, "MINI GOATS", "IN THE BUILDING"),
    ("182440", 0.15, 0.85, 0.50, "", ""),
    ("182420", 0.30, 1.50, 1.00, "BARÇA", "YAMAL 10"),
    ("182427", 0.20, 1.20, 1.00, "", ""),
    ("182700", 0.70, 1.30, 1.00, "BARÇA", "HOME KIT"),
    ("182649", 0.00, 1.40, 1.00, "PORTUGAL", ""),
    ("182601", 0.10, 0.80, 1.00, "THEIR NAME.", "THEIR NUMBER."),
    ("182436", 0.60, 0.90, 1.00, "THEIR NAME.", "THEIR NUMBER."),
    ("182412", 0.40, 1.80, 1.00, "GERMANY", "AWAY KIT"),
    ("182903", 0.00, 1.00, 1.00, "", ""),
    ("182305", 4.00, 1.40, 1.00, "PASTEL", "DRIP"),
    ("182728", 1.10, 1.20, 1.00, "", ""),
    ("182222", 2.60, 1.80, 1.00, "BUILT FOR", "PLAYTIME"),
    ("182214", 3.00, 0.90, 1.00, "", ""),
    ("182135", 1.80, 1.70, 1.00, "KIDS KITS", "DM TO ORDER"),
]
END_HOLD = 1.6  # freeze on the last frame under the CTA
HANDLE = "@thegoatedjerseys"


def text_filters(tmp, i, head, sub, dur, last):
    if not head:
        return ""
    fade = "alpha='min(1,t/0.12)'"
    out = []
    for j, (txt, font, size, y) in enumerate(
        [(head, FONT, 118, "h*0.66"), (sub, FONT_SUB, 72, "h*0.66+135")]
    ):
        if not txt:
            continue
        p = os.path.join(tmp, f"t{i}_{j}.txt")
        with open(p, "w") as f:
            f.write(txt)
        out.append(
            f"drawtext=fontfile={font}:textfile={p}:fontsize={size}:fontcolor=white:"
            f"borderw=6:bordercolor=black@0.85:shadowx=0:shadowy=6:shadowcolor=black@0.5:"
            f"x=(w-text_w)/2:y={y}:{fade}"
        )
    if last:
        p = os.path.join(tmp, "handle.txt")
        with open(p, "w") as f:
            f.write(HANDLE)
        out.append(
            f"drawbox=x=(iw-760)/2:y=ih*0.66+250:w=760:h=110:color=white@0.95:t=fill:"
            f"enable='gte(t,0.25)',"
            f"drawtext=fontfile={FONT_SUB}:textfile={p}:fontsize=64:fontcolor=black:"
            f"x=(w-text_w)/2:y=h*0.66+250+(110-text_h)/2-6:enable='gte(t,0.25)'"
        )
    return "," + ",".join(out)


def main():
    raw, out = sys.argv[1], sys.argv[2]
    clean = "--clean" in sys.argv
    tmp = tempfile.mkdtemp()
    # Render each segment separately (decoding 15 4K streams at once runs out of memory),
    # then join them with the concat demuxer.
    segs = []
    for i, (clip, ss, dur, speed, head, sub) in enumerate(EDL):
        last = i == len(EDL) - 1
        outdur = dur / speed
        v = (
            f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
            f"eq=contrast=1.06:saturation=1.18"
        )
        if last:
            v += f",tpad=stop_mode=clone:stop_duration={END_HOLD}"
            outdur += END_HOLD
        if not clean:
            v += text_filters(tmp, i, head, sub, outdur, last)
        a = "asetpts=PTS-STARTPTS,aresample=48000"
        if speed != 1:
            a += f",atempo={speed}"
        a += f",apad,atrim=0:{outdur:.3f},volume=0.6"
        seg = os.path.join(tmp, f"seg{i:02d}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}",
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
