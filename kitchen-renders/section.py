"""Section A-A: vertical cut through the centre of the plan (x = 4'-6"), looking east.
Horizontal axis = plan py (north wall at 0 on the left, south wall at 75), vertical = height. Units: inches."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch

OUT = sys.argv[1]
fig = plt.figure(figsize=(16.5, 11.7))  # A3 landscape
ax = fig.add_axes([0.01, 0.05, 0.70, 0.90])
ax.set_aspect("equal"); ax.axis("off")

CUT_LW, BEYOND_LW, THIN = 2.4, 0.9, 0.5
INK, POCHE, CUTFILL = "#111111", "#3a3a3a", "#ffffff"

def rect(u0, u1, z0, z1, lw=BEYOND_LW, fc="none", ec=INK, hatch=None, z=2, ls="-"):
    ax.add_patch(Rectangle((u0, z0), u1 - u0, z1 - z0, lw=lw, fc=fc, ec=ec, hatch=hatch, zorder=z, ls=ls))

def line(u0, z0, u1, z1, lw=BEYOND_LW, c=INK, ls="-", z=3):
    ax.plot([u0, u1], [z0, z1], lw=lw, c=c, ls=ls, zorder=z, solid_capstyle="butt")

def ftin(v):
    v = round(v * 4) / 4
    f, i = int(v // 12), v - 12 * int(v // 12)
    i = int(i) if float(i).is_integer() else i
    return f"{f}'-{i}\""

def dim_h(u0, u1, z, text=None, off=0):
    line(u0, z, u1, z, THIN)
    for u in (u0, u1):
        line(u - 1.2, z - 1.2, u + 1.2, z + 1.2, 1.0)
        line(u, z - 2, u, z + 2, THIN)
    ax.text((u0 + u1) / 2, z + 1.2 + off, text or ftin(u1 - u0), ha="center", va="bottom", fontsize=8.5, family="DejaVu Sans")

def dim_v(u, z0, z1, text=None, side="left"):
    line(u, z0, u, z1, THIN)
    for zz in (z0, z1):
        line(u - 1.2, zz - 1.2, u + 1.2, zz + 1.2, 1.0)
        line(u - 2, zz, u + 2, zz, THIN)
    ax.text(u + (-1.6 if side == "left" else 1.6), (z0 + z1) / 2, text or ftin(z1 - z0), rotation=90,
            ha="right" if side == "left" else "left", va="center", fontsize=8.5)

def label(u, z, text, tu, tz, ha="left"):
    ax.annotate(text, xy=(u, z), xytext=(tu, tz), fontsize=7.5, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.5, color=INK, shrinkA=0, shrinkB=0), zorder=10)
    ax.plot([u], [z], marker="o", ms=2.2, c=INK, zorder=10)

H = 108
# ------------------------------------------------------------------ BEYOND: east wall (elevation 2) in projection
rect(0, 75, 0, H, lw=BEYOND_LW, z=1)                       # east wall face
# subway tile backsplash hint
for zz in range(36, 44, 3):
    line(22, zz, 47, zz, 0.25, "#999", z=1)
for zz in range(36, 55, 3):
    line(47, zz, 51, zz, 0.25, "#999", z=1); line(68, zz, 75, zz, 0.25, "#999", z=1)
# window (py 22..46, z 44..70)
rect(22, 46, 44, 70, lw=1.1)
rect(23.75, 44.25, 45.75, 68.25, lw=0.6)
line(34, 45.75, 34, 68.25, 0.6)
for gu in (26, 37):  # glazing marks
    line(gu, 58, gu + 4, 64, 0.4, "#777"); line(gu + 1.5, 56, gu + 5.5, 62, 0.4, "#777")
rect(20.5, 47.5, 43.25, 44, lw=0.8)                         # sill
# base cabinets (E run) doors
rect(21, 75, 0, 4, lw=BEYOND_LW, fc="#d9d9d9")             # plinth
for a, b, hu, hz in [(22, 40.5, 24.2, 17), (40.5, 57.75, 55.2, 26), (57.75, 75, 60.3, 26)]:
    rect(a + 0.06, b - 0.06, 4.3, 31.45)
    line(hu, hz - 3, hu, hz + 3, 2.2)
rect(21, 75, 31.5, 33, fc="#555555")                          # countertop edge
# sink rim + faucet
rect(47, 68, 33, 33.3, lw=0.8)
line(57.5, 33, 57.5, 46, 1.6); ax.add_patch(matplotlib.patches.Arc((57.5 + 0, 46), 0.01, 0.01))
ax.plot([57.5, 57.5, 58.3, 60.2, 61.4, 61.6], [33, 45, 47.6, 48.3, 47, 42.5], lw=1.6, c=INK, zorder=3)
# upper cabinets on east wall
rect(16, 75, 83, H)
for a, b, hu in [(16, 36.5, 34), (36.5, 55.75, 53.4), (55.75, 75, 58.1)]:
    rect(a + 0.06, b - 0.06, 83.06, H - 0.06)
    line(hu, 85, hu, 92, 2.2)
rect(16, 75, 77, 83)                                         # open shelf band
line(16, 77.75, 75, 77.75, 0.5); line(16, 82.25, 75, 82.25, 0.5)
rect(51, 75, 55, 77)                                         # cabinet over sink
line(59.5, 58.5, 66.5, 58.5, 2.2)
rect(0, 16, 55, 83, ls="--", lw=0.6)                          # corner unit (partly hidden)
# downlight beyond
rect(35.2, 40.8, H - 0.6, H, fc=INK, lw=0.5)

# ------------------------------------------------------------------ BEYOND: north run seen past the cut (x > 54)
rect(0, 14, 50, 56, fc="#f2f2f2", lw=BEYOND_LW, z=3)          # spice unit profile
rect(0, 14, 56, 63, fc="#f2f2f2", lw=BEYOND_LW, z=3)          # wall unit below cut cabinet

# ------------------------------------------------------------------ CUT ELEMENTS
# slab, ceiling, walls (poche)
rect(-6, 81, -8, 0, lw=CUT_LW, fc=POCHE, z=5)
rect(-6, 81, H, H + 8, lw=CUT_LW, fc=POCHE, z=5)
rect(-6, 0, 0, H, lw=CUT_LW, fc=POCHE, z=5)
rect(75, 81, 0, H, lw=CUT_LW, fc=POCHE, z=5)
# tile on north wall (cut)
rect(0, 0.4, 33, 50, lw=1.2, fc="#bbbbbb", z=6)
# north base cabinet (cut through the drawer stack under the hob)
rect(0, 17.5, 0, 4, lw=CUT_LW, fc="#cfcfcf", hatch="////", z=6)          # plinth
rect(0, 20.25, 4, 31.5, lw=CUT_LW, fc=CUTFILL, z=6)                       # carcass
for zz in (4, 13.2, 22.4):                                               # drawer boxes
    rect(1.5, 19.0, zz + 1.2, zz + 7.6, lw=0.7, z=7)
dh = (31.5 - 4.3) / 3
for i in range(3):
    z0 = 4.3 + i * dh
    rect(20.25, 21, z0 + 0.06, z0 + dh - 0.06, lw=1.6, fc="#e0e0e0", z=7)  # drawer fronts
    rect(21, 21.9, z0 + dh * 0.62 - 0.25, z0 + dh * 0.62 + 0.25, lw=0.8, fc=INK, z=7)
rect(0, 22, 31.5, 33, lw=CUT_LW, fc="#777777", hatch="....", z=7)        # granite top
# hob + pot
rect(2.5, 19.5, 33, 33.4, lw=1.4, fc=INK, z=8)
for gu in (6, 10.5, 15):
    rect(gu - 1.2, gu + 1.2, 33.4, 34.6, lw=0.6, fc="#555", z=8)     # burner grates
# cooker hood (cut)
ax.add_patch(Polygon([(0, 57), (19, 57), (19, 62), (12, 63), (0, 63)], closed=True, lw=CUT_LW, fc="#bdbdbd", ec=INK, zorder=8))
line(2, 57.15, 17.5, 57.15, 0.6, z=9)
# upper cabinet cut above the hood (z 63..84)
rect(0, 13.25, 63, 84, lw=CUT_LW, fc=CUTFILL, z=8)
rect(13.25, 14, 63.06, 83.94, lw=1.6, fc="#e0e0e0", z=8)
rect(0.75, 12.5, 73.1, 73.85, lw=0.8, z=8)                             # shelf
rect(0, 14, 84, 108, lw=0, fc="none", z=8)

# ------------------------------------------------------------------ dimensions
dim_h(0, 75, H + 16, "6'-3\" (CLEAR)")
dim_h(0, 21, -16); dim_h(21, 75, -16, "4'-6\" AISLE")
dim_v(-14, 0, H, "9'-0\" (CLEAR HEIGHT)")
dim_v(-26, 0, 33); dim_v(-26, 33, 57); dim_v(-26, 57, 84); dim_v(-26, 84, H)
dim_v(90, 0, 44, side="left"); dim_v(90, 44, 70, side="left"); dim_v(90, 70, 83, side="left"); dim_v(90, 83, H, side="left")

# ------------------------------------------------------------------ annotations
for u, z, t, tz in [(6, 78, "WALL CABINET (CUT)", 78), (9.5, 60, "CHIMNEY HOOD", 60), (7, 53, "SPICE UNIT (BEYOND)", 52),
                    (12, 33.2, "GAS HOB", 41), (5, 32.25, "1 1/2\" BLACK GRANITE TOP", 34.5),
                    (10, 18, "DRAWER UNIT", 18), (8, 2, "4\" PLINTH", 4)]:
    label(u, z, t, -40, tz, ha="right")
for u, z, t, tz in [(70, 96, "UPPER CABINETS TO CEILING", 96), (70, 80, "OPEN SHELF", 80), (70, 66, "CABINET OVER SINK", 66),
                    (44, 50, "NEW WINDOW 2'-0\" x 2'-2\"", 50), (60.5, 44, "SINK + FAUCET", 41),
                    (70, 18, "SINK BASE CABINETS", 18)]:
    label(u, z, t, 100, tz, ha="left")
label(-3, 112, "RCC SLAB", -40, 112, ha="right")
label(78, 100, "WALL", 100, 106, ha="left")

ax.set_xlim(-75, 135); ax.set_ylim(-52, H + 30)
# graphic scale bar (feet)
for k in range(4):
    rect(-4 + k * 12, 8 + k * 12, -30, -28, lw=0.8, fc=INK if k % 2 == 0 else "white", z=5)
    ax.text(-4 + k * 12, -31, str(k), ha="center", va="top", fontsize=7.5)
ax.text(44, -31, "4 FT", ha="center", va="top", fontsize=7.5)

# title block
ax.text(37.5, -40, "SECTION A-A", ha="center", va="top", fontsize=17, weight="bold")
ax.text(37.5, -46.5, "Looking east towards the sink wall", ha="center", va="top", fontsize=9)

# ------------------------------------------------------------------ key plan
kp = fig.add_axes([0.73, 0.52, 0.25, 0.36]); kp.set_aspect("equal"); kp.axis("off")
def kr(x0, x1, y0, y1, **kw):
    kp.add_patch(Rectangle((x0, -y1), x1 - x0, y1 - y0, **kw))
kr(-6, 114, -6, 81, fc=POCHE, ec=INK, lw=1)
kr(0, 108, 0, 75, fc="white", ec=INK, lw=1)
kr(-6.5, 0, 0, 75, fc="white", ec="none")
kr(0, 108, 0, 21, fc="#e6e6e6", ec=INK, lw=0.8)
kr(87, 108, 21, 75, fc="#e6e6e6", ec=INK, lw=0.8)
kr(0, 50, 61, 75, fc="#e6e6e6", ec=INK, lw=0.8)
kr(87, 108, 0, 21, fc="none", ec=INK, lw=0.5, hatch="////")
kr(108, 114, 22, 46, fc="white", ec=INK, lw=0.6)  # window
for t, (x, y) in {"1": (45, 10.5), "2": (97.5, 48), "3": (25, 68)}.items():
    kp.text(x, -y, t, ha="center", va="center", fontsize=10, weight="bold")
kp.plot([54, 54], [14, -89], c=INK, lw=1.2, ls=(0, (8, 3, 2, 3)))
for y in (14, -89):
    kp.add_patch(FancyArrowPatch((54, y), (66, y), arrowstyle="-|>", mutation_scale=12, lw=1.4, color=INK))
    kp.text(50, y, "A", ha="right", va="center", fontsize=11, weight="bold")
kp.set_xlim(-14, 124); kp.set_ylim(-96, 22)
kp.text(54, 24, "KEY PLAN", ha="center", va="bottom", fontsize=11, weight="bold")

# notes
fig.text(0.735, 0.44, "NOTES", fontsize=11, weight="bold", va="top")
notes = [
    "1. Section cut at mid-span of the kitchen (4'-6\" from the",
    "    open side), looking towards the sink wall.",
    "2. Cut elements shown with heavy line / poche;",
    "    elements beyond shown in light line.",
    "3. Counter height 2'-9\" incl. 1 1/2\" granite top.",
    "4. Base cabinets 1'-9\" deep; wall cabinets 1'-2\" deep.",
    "5. Window sill at 3'-8\" a.f.f., head at 5'-10\".",
    "6. All dimensions are clear internal dimensions.",
]
for i, n in enumerate(notes):
    fig.text(0.735, 0.41 - i * 0.022, n, fontsize=8.5, va="top")

fig.savefig(OUT + ".png", dpi=220, facecolor="white")
fig.savefig(OUT + ".pdf", facecolor="white")
print("ok")
