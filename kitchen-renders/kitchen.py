"""Small kitchen - Enscape-style Cycles renders.
Plan coords in inches: x = east (0..108), py = south (0..75), z = up.
Blender: X = x, Y = -py, Z = z (scaled to metres).
Usage: python kitchen.py <shot> <width> <samples> <out.png>
"""
import bpy, bmesh, math, sys
from mathutils import Vector

S = 0.0254
shot, RES_W, SAMPLES, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = scene.collection
OBJS = []

# ---------------------------------------------------------------- materials
def srgb(c):
    return tuple(((v / 255) / 12.92) if (v / 255) <= 0.04045 else (((v / 255) + 0.055) / 1.055) ** 2.4 for v in c)

def principled(name, color, rough=0.5, metal=0.0, coat=0.0, trans=0.0, emit=None, estr=0.0, ior=1.5, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.08
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    return m

def tile_mat(name, axes, c1, c2, mortar, bw, rh, mortar_size, rough, offset=0.5):
    m = principled(name, c1, rough)
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    b = n["Principled BSDF"]
    geo = n.new("ShaderNodeNewGeometry")
    sep = n.new("ShaderNodeSeparateXYZ")
    comb = n.new("ShaderNodeCombineXYZ")
    l.new(geo.outputs["Position"], sep.inputs[0])
    l.new(sep.outputs[axes[0]], comb.inputs[0])
    l.new(sep.outputs[axes[1]], comb.inputs[1])
    br = n.new("ShaderNodeTexBrick")
    br.offset = offset
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = mortar_size
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = bw
    br.inputs["Row Height"].default_value = rh
    l.new(comb.outputs[0], br.inputs["Vector"])
    l.new(br.outputs["Color"], b.inputs["Base Color"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    l.new(br.outputs["Fac"], inv.inputs[1])
    l.new(inv.outputs[0], bump.inputs["Height"])
    l.new(bump.outputs[0], b.inputs["Normal"])
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = rough
    mr.inputs["To Max"].default_value = 0.7
    l.new(br.outputs["Fac"], mr.inputs[0])
    l.new(mr.outputs[0], b.inputs["Roughness"])
    return m

def granite():
    m = principled("granite", (0.01, 0.01, 0.01), 0.22, coat=0.15)
    nt = m.node_tree; n, l = nt.nodes, nt.links
    b = n["Principled BSDF"]
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 260; nz.inputs["Detail"].default_value = 8
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.55
    ramp.color_ramp.elements[0].color = (0.008, 0.008, 0.009, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.05, 0.047, 0.045, 1)
    l.new(nz.outputs["Fac"], ramp.inputs[0])
    l.new(ramp.outputs[0], b.inputs["Base Color"])
    return m

def wood():
    m = principled("wood", (0.4, 0.2, 0.08), 0.45)
    nt = m.node_tree; n, l = nt.nodes, nt.links
    b = n["Principled BSDF"]
    w = n.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = 6; w.inputs["Distortion"].default_value = 6
    w.inputs["Detail"].default_value = 3
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb((150, 95, 55)), 1)
    ramp.color_ramp.elements[1].color = (*srgb((200, 145, 95)), 1)
    l.new(w.outputs["Fac"], ramp.inputs[0])
    l.new(ramp.outputs[0], b.inputs["Base Color"])
    return m

M = {
    "wall": principled("wall", srgb((236, 231, 222)), 0.9),
    "ceil": principled("ceil", srgb((245, 244, 240)), 0.95),
    "green": principled("green", srgb((14, 150, 112)), 0.32, coat=0.6),
    "greenin": principled("greenin", srgb((10, 110, 82)), 0.5),
    "white": principled("white", srgb((240, 239, 234)), 0.35, coat=0.3),
    "whitein": principled("whitein", srgb((228, 226, 220)), 0.6),
    "steel": principled("steel", (0.75, 0.75, 0.74), 0.28, metal=1.0),
    "chrome": principled("chrome", (0.9, 0.9, 0.9), 0.08, metal=1.0),
    "black": principled("black", (0.012, 0.012, 0.013), 0.4),
    "blackglass": principled("blackglass", (0.005, 0.005, 0.006), 0.04, coat=1.0),
    "iron": principled("iron", (0.02, 0.02, 0.02), 0.6, metal=0.6),
    "brass": principled("brass", (0.7, 0.5, 0.2), 0.3, metal=1.0),
    "plinth": principled("plinth", srgb((70, 70, 72)), 0.6),
    "glass": principled("glass", (0.95, 0.98, 0.97), 0.02, trans=1.0),
    "frosted": principled("frosted", (0.95, 0.98, 0.97), 0.18, trans=1.0),
    "frame": principled("frame", srgb((235, 235, 232)), 0.4),
    "ceramic": principled("ceramic", srgb((245, 243, 238)), 0.15),
    "terracotta": principled("terracotta", srgb((190, 100, 70)), 0.6),
    "sage": principled("sage", srgb((150, 170, 150)), 0.3),
    "navy": principled("navy", srgb((40, 60, 95)), 0.25),
    "leaf": principled("leaf", srgb((50, 110, 45)), 0.45),
    "orange": principled("orange", srgb((235, 120, 20)), 0.35),
    "lemon": principled("lemon", srgb((240, 210, 40)), 0.35),
    "led": principled("led", (1, 1, 1), 0.5, emit=(1.0, 0.82, 0.62), estr=25),
    "downlight": principled("downlight", (1, 1, 1), 0.5, emit=(1.0, 0.85, 0.7), estr=40),
    "flame": principled("flame", (0, 0, 0), 0.5, emit=(0.2, 0.4, 1.0), estr=6),
    "granite": granite(),
    "wood": wood(),
    "floor": tile_mat("floor", ("X", "Y"), srgb((205, 198, 186)), srgb((196, 189, 177)), srgb((150, 145, 138)),
                      24 * S, 24 * S, 0.003, 0.28, offset=0.0),
    "tileN": tile_mat("tileN", ("X", "Z"), srgb((248, 248, 245)), srgb((238, 240, 238)), srgb((200, 198, 192)),
                      6 * S, 3 * S, 0.0018, 0.06),
    "tileE": tile_mat("tileE", ("Y", "Z"), srgb((248, 248, 245)), srgb((238, 240, 238)), srgb((200, 198, 192)),
                      6 * S, 3 * S, 0.0018, 0.06),
}

# ---------------------------------------------------------------- geometry helpers
def _obj(name, bm, mat, grp, bevel, smooth_sides=False):
    me = bpy.data.meshes.new(name)
    if smooth_sides:
        for f in bm.faces:
            f.smooth = abs(f.normal.z) < 0.5
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.data.materials.append(mat)
    coll.objects.link(o)
    o["grp"] = grp
    if bevel:
        md = o.modifiers.new("bev", "BEVEL")
        md.width = bevel * S; md.segments = 2; md.limit_method = "ANGLE"
        md.harden_normals = False
    OBJS.append(o)
    return o

def box(name, x0, x1, py0, py1, z0, z1, mat, grp="", bevel=0.06):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    c = Vector(((x0 + x1) / 2 * S, -(py0 + py1) / 2 * S, (z0 + z1) / 2 * S))
    d = Vector((abs(x1 - x0) * S, abs(py1 - py0) * S, abs(z1 - z0) * S))
    for v in bm.verts:
        v.co = Vector((v.co.x * d.x, v.co.y * d.y, v.co.z * d.z)) + c
    return _obj(name, bm, M[mat] if isinstance(mat, str) else mat, grp, bevel if min(d) > 2.5 * bevel * S else 0)

def cyl(name, x, py, z0, h, r, mat, grp="", r2=None, seg=48, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r * S, radius2=(r if r2 is None else r2) * S, depth=h * S)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((x * S, -py * S, (z0 + h / 2) * S)))
    bm.normal_update()
    return _obj(name, bm, M[mat], grp, bevel, smooth_sides=True)

def sphere(name, x, py, z, r, mat, grp="", scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r * S)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector((x * S, -py * S, z * S))
    for f in bm.faces:
        f.smooth = True
    return _obj(name, bm, M[mat], grp, 0)

def cup(name, x, py, z0, h, r, mat, grp, wall=0.15):
    """open-top cylinder via boolean"""
    o = cyl(name, x, py, z0, h, r, mat, grp, seg=40)
    inner = cyl(name + "_in", x, py, z0 + wall * 2, h + 1, r - wall, mat, grp, seg=40)
    md = o.modifiers.new("cut", "BOOLEAN"); md.object = inner; md.operation = "DIFFERENCE"; md.solver = "EXACT"
    inner.hide_render = True; inner.hide_viewport = True
    return o

def cut(target, cutter):
    md = target.modifiers.new("cut", "BOOLEAN"); md.object = cutter; md.operation = "DIFFERENCE"; md.solver = "EXACT"
    target.modifiers.move(len(target.modifiers) - 1, 0)
    cutter.hide_render = True; cutter.hide_viewport = True

# wall-relative helpers. a = along wall (plan x for N/S, plan py for E), d = depth from wall face.
def wbox(name, wall, a0, a1, d0, d1, z0, z1, mat, grp, bevel=0.06):
    if wall == "N":
        return box(name, a0, a1, d0, d1, z0, z1, mat, grp, bevel)
    if wall == "E":
        return box(name, 108 - d1, 108 - d0, a0, a1, z0, z1, mat, grp, bevel)
    if wall == "S":
        return box(name, a0, a1, 75 - d1, 75 - d0, z0, z1, mat, grp, bevel)

GAP = 0.125
T = 0.75

def door(name, wall, a0, a1, z0, z1, d, mat, grp, handle=None):
    """front panel whose outer face is at depth d. handle = ('v'|'h', a_center, z_center, length)"""
    wbox(name, wall, a0 + GAP / 2, a1 - GAP / 2, d - T, d, z0 + GAP / 2, z1 - GAP / 2, mat, grp, bevel=0.08)
    if handle:
        o, ac, zc, L = handle
        if o == "v":
            wbox(name + "_h", wall, ac - 0.25, ac + 0.25, d, d + 0.9, zc - L / 2, zc + L / 2, "steel", grp, bevel=0.1)
        else:
            wbox(name + "_h", wall, ac - L / 2, ac + L / 2, d, d + 0.9, zc - 0.25, zc + 0.25, "steel", grp, bevel=0.1)

def open_box(name, wall, a0, a1, z0, z1, depth, mat, grp, shelves=(), back=True):
    t = 0.75
    wbox(name + "_top", wall, a0, a1, 0, depth, z1 - t, z1, mat, grp)
    wbox(name + "_bot", wall, a0, a1, 0, depth, z0, z0 + t, mat, grp)
    wbox(name + "_l", wall, a0, a0 + t, 0, depth, z0, z1, mat, grp)
    wbox(name + "_r", wall, a1 - t, a1, 0, depth, z0, z1, mat, grp)
    if back:
        wbox(name + "_back", wall, a0, a1, 0, 0.5, z0, z1, mat, grp)
    for i, zs in enumerate(shelves):
        wbox(f"{name}_sh{i}", wall, a0 + t, a1 - t, 0.5, depth - 0.5, zs - t / 2, zs + t / 2, mat, grp)

# ---------------------------------------------------------------- room shell
H = 108
box("floor", 0, 114, -6, 81, -1, 0, "floor", "floor", 0)
box("floorext", -80, 0, -6, 81, -1, 0, "floor", "floorext", 0)
box("ceiling", -6, 114, -6, 81, H, H + 4, "ceil", "ceil", 0)
box("wallN", -6, 114, -6, 0, 0, H, "wall", "wallN", 0)
box("wallS", -6, 114, 75, 81, 0, H, "wall", "wallS", 0)
# east wall with window opening py 22..46, z 44..70
WY0, WY1, WZ0, WZ1 = 22, 46, 44, 70
box("wallE_a", 108, 114, 0, WY0, 0, H, "wall", "wallE", 0)
box("wallE_b", 108, 114, WY1, 75, 0, H, "wall", "wallE", 0)
box("wallE_c", 108, 114, WY0, WY1, 0, WZ0, "wall", "wallE", 0)
box("wallE_d", 108, 114, WY0, WY1, WZ1, H, "wall", "wallE", 0)
# bulkhead/beam on the open west side
box("beam", -6, 0, -6, 81, H - 8, H, "wall", "beam", 0)

# window: frame, mullion, glass, interior sill
F = 1.75
box("win_fl", 108.5, 112.5, WY0, WY0 + F, WZ0, WZ1, "frame", "E", 0.1)
box("win_fr", 108.5, 112.5, WY1 - F, WY1, WZ0, WZ1, "frame", "E", 0.1)
box("win_fb", 108.5, 112.5, WY0, WY1, WZ0, WZ0 + F, "frame", "E", 0.1)
box("win_ft", 108.5, 112.5, WY0, WY1, WZ1 - F, WZ1, "frame", "E", 0.1)
box("win_mul", 108.5, 112.5, (WY0 + WY1) / 2 - 0.9, (WY0 + WY1) / 2 + 0.9, WZ0, WZ1, "frame", "E", 0.1)
box("win_glass", 110.3, 110.6, WY0 + 0.5, WY1 - 0.5, WZ0 + 0.5, WZ1 - 0.5, "glass", "E", 0)
box("win_sill", 106.2, 108.5, WY0 - 1.5, WY1 + 1.5, WZ0 - 0.75, WZ0, "white", "E", 0.1)

# backsplash tile skins
box("tileN", 0, 108, 0, 0.3, 33, 56, "tileN", "N", 0)
box("tileE1", 107.7, 108, 0, 75, 33, WZ0 - 0.75, "tileE", "E", 0)
box("tileE2", 107.7, 108, 0, WY0 - 1.5, WZ0 - 0.75, 55, "tileE", "E", 0)
box("tileE3", 107.7, 108, WY1 + 1.5, 75, WZ0 - 0.75, 55, "tileE", "E", 0)
box("tileS", 0, 50, 74.7, 75, 33, 50, "tileN", "S", 0)

# ---------------------------------------------------------------- base cabinets
ZP, ZB, ZC = 4, 31.5, 33  # plinth top, carcass top, counter top

# --- run 1 (north wall, x 0..108, front at d=21)
box("N_plinth", 0, 108, 0, 18, 0, ZP, "plinth", "N", 0)
box("N_carc", 0, 108, 0, 21 - T, ZP, ZB, "greenin", "N")
box("N_end", 0, 0.75, 0, 21, ZP - 3.5, ZB, "green", "N")  # exposed end panel
dz = ZP + 0.3
door("N_d1", "N", 0.75, 13.75, dz, ZB, 21, "green", "N", ("v", 11.7, 25, 6))
door("N_d2", "N", 13.75, 27, dz, ZB, 21, "green", "N", ("v", 15.6, 25, 6))
dh = (ZB - dz) / 3
for i in range(3):
    z0 = dz + i * dh
    door(f"N_dr{i}", "N", 27, 58, z0, z0 + dh, 21, "green", "N", ("h", 42.5, z0 + dh * 0.62, 8))
door("N_d3", "N", 58, 69, dz, ZB, 21, "green", "N", ("v", 65.5, 25, 6))
door("N_d4", "N", 69, 87, dz, ZB, 21, "green", "N", ("v", 84.5, 17, 6))
box("N_top", 0, 108, 0, 22, ZB, ZC, "granite", "N", 0.12)

# hob (gas, black glass, 3 burners)
box("hob", 29, 57, 2.5, 19.5, ZC, ZC + 0.4, "blackglass", "N", 0.1)
for i, (bx, by, r) in enumerate([(35, 11, 2.6), (43, 11, 1.9), (51, 11, 2.6)]):
    cyl(f"burner{i}", bx, by, ZC + 0.4, 0.6, r * 0.75, "iron", "N")
    cyl(f"cap{i}", bx, by, ZC + 1.0, 0.25, r * 0.5, "brass", "N")
    L_ = r * 1.35
    box(f"grx{i}", bx - L_, bx + L_, by - 0.2, by + 0.2, ZC + 1.3, ZC + 1.65, "iron", "N", 0)
    box(f"gry{i}", bx - 0.2, bx + 0.2, by - L_, by + L_, ZC + 1.3, ZC + 1.65, "iron", "N", 0)
for k in range(3):  # knobs on front edge
    cyl(f"knob{k}", 39 + k * 4, 19.0, ZC + 0.4, 0.8, 0.6, "steel", "N")

# --- run 2 (east wall, py 21..75, front at d=21)
box("E_plinth", 90, 108, 21, 75, 0, ZP, "plinth", "E", 0)
ecarc = box("E_carc", 87.75, 108, 21, 75, ZP, ZB, "greenin", "E")
door("E_fill", "E", 21, 22, dz, ZB, 21, "green", "E")
door("E_d1", "E", 22, 40.5, dz, ZB, 21, "green", "E", ("v", 24.2, 17, 6))
door("E_d2", "E", 40.5, 57.75, dz, ZB, 21, "green", "E", ("v", 55.2, 26, 6))
door("E_d3", "E", 57.75, 75, dz, ZB, 21, "green", "E", ("v", 60.3, 26, 6))
etop = box("E_top", 86, 108, 22, 75, ZB, ZC, "granite", "E", 0.12)

# sink (top-mount stainless) py 47..68
sink = box("sink", 90, 105, 47, 68, 24.5, ZC + 0.25, "steel", "E", 0.15)
sink_in = box("sink_in", 91.5, 103.5, 48.5, 66.5, 25, 45, "steel", "E", 0)
cut(sink, sink_in)
top_cut = box("top_cut", 91.5, 103.5, 48.5, 66.5, 25, 45, "steel", "E", 0)
cut(etop, top_cut)
c2 = box("carc_cut", 90, 105, 47, 68, 24.4, 40, "steel", "E", 0)
cut(ecarc, c2)
cyl("drain", 97.5, 57.5, 25.0, 0.1, 1.5, "chrome", "E")
# gooseneck faucet
cv = bpy.data.curves.new("faucet", "CURVE"); cv.dimensions = "3D"
cv.bevel_depth = 0.45 * S; cv.bevel_resolution = 6
sp = cv.splines.new("NURBS")
pts = [(104.2, 57.5, ZC), (104.2, 57.5, 40), (104.2, 57.5, 46), (101, 57.5, 48.5), (98.2, 57.5, 46), (98.2, 57.5, 42.5)]
sp.points.add(len(pts) - 1)
for p, (x, py, z) in zip(sp.points, pts):
    p.co = (x * S, -py * S, z * S, 1)
sp.use_endpoint_u = True; sp.order_u = 3
fo = bpy.data.objects.new("faucet", cv); fo.data.materials.append(M["chrome"]); coll.objects.link(fo); fo["grp"] = "E"; OBJS.append(fo)
cyl("faucet_base", 104.2, 57.5, ZC, 1.0, 1.0, "chrome", "E")
box("faucet_lever", 104.0, 104.4, 57.3, 57.7, 39.5, 40.0, "chrome", "E", 0)
box("faucet_lever2", 103.0, 104.4, 57.3, 57.7, 39.6, 40.0, "chrome", "E", 0)

# --- run 3 (south wall, x 0..50, depth 14)
box("S_plinth", 0, 50, 64, 75, 0, ZP, "plinth", "S", 0)
box("S_carc", 0, 50, 61 + T, 75, ZP, ZB, "greenin", "S")
box("S_end", 49.25, 50, 61, 75, ZP - 3.5, ZB, "green", "S")
door("S_d1", "S", 14.2, 31.6, dz, ZB, 14, "green", "S", ("v", 29.0, 25, 6))
door("S_d2", "S", 31.6, 49.25, dz, ZB, 14, "green", "S", ("v", 34.2, 25, 6))
dh4 = (ZB - dz) / 4
for i in range(4):
    z0 = dz + i * dh4
    door(f"S_dr{i}", "S", 0.75, 14.2, z0, z0 + dh4, 14, "green", "S", ("h", 7.5, z0 + dh4 * 0.6, 4.5))
box("S_endw", 0, 0.75, 61, 75, ZP - 3.5, ZB, "green", "S")
box("S_top", 0, 51, 60, 75, ZB, ZC, "granite", "S", 0.12)

# ---------------------------------------------------------------- wall cabinets
# --- run 1 uppers (depth 14, z 50..84)
DU = 14
def closed(name, wall, a0, a1, z0, z1, depth, grp, doors):
    wbox(name + "_carc", wall, a0, a1, 0, depth - T, z0, z1, "whitein", grp)
    for i, (b0, b1, c0, c1, h) in enumerate(doors):
        door(f"{name}_{i}", wall, b0, b1, c0, c1, depth, "white", grp, h)

closed("NU1", "N", 0, 28, 56, 84, DU, "N", [(0, 28, 56, 70, ("h", 14, 63, 6)), (0, 28, 70, 84, ("h", 14, 77, 6))])
closed("NSp1", "N", 0, 28.5, 50, 56, DU, "N", [(0, 28.5, 50, 56, None)])
closed("NU2", "N", 28, 39, 63, 84, DU, "N", [(28, 39, 63, 84, None)])
closed("NU3", "N", 47, 58, 63, 84, DU, "N", [(47, 58, 63, 84, None)])
open_box("Nopen", "N", 58, 63.5, 56, 84, DU, "white", "N", shelves=(70,))
closed("NU4", "N", 63.5, 92, 56, 84, DU, "N", [(63.5, 92, 56, 70, ("h", 77.75, 63, 6)), (63.5, 92, 70, 84, ("h", 77.75, 77, 6))])
closed("NSp2", "N", 58, 92, 50, 56, DU, "N", [(58, 92, 50, 56, None)])
# corner unit
box("corner_u", 92, 108, 0, 16, 55, 83, "white", "N")
# hood + chimney
box("hood", 28, 58, 0, 19, 57, 63, "black", "N", 0.15)
box("hood_trim", 28.3, 57.7, 18.6, 19.2, 56.6, 57.6, "steel", "N", 0.05)
box("hood_filter", 30, 56, 2, 17.5, 56.9, 57.0, "steel", "N", 0)
box("chimney", 39, 47, 0, 10, 63, H, "black", "N", 0.1)

# --- run 2 uppers (depth 16)
DE = 16
closed("EU", "E", 16, 75, 83, H, DE, "E", [
    (16, 36.5, 83, H, ("v", 34, 88.5, 7)),
    (36.5, 55.75, 83, H, ("v", 53.4, 88.5, 7)),
    (55.75, 75, 83, H, ("v", 58.1, 88.5, 7)),
])
open_box("Eband", "E", 16, 75, 77, 83, DE, "white", "E")
closed("EL", "E", 51, 75, 55, 77, DE, "E", [(51, 75, 55, 77, ("h", 63, 58.5, 7))])

# --- run 3 uppers (depth 12), plan x = 108 - elevation x
DS = 12
open_box("Sopen1", "S", 38.8, 49.5, 60, 83, DS, "white", "S", shelves=(67.8, 74.6))
closed("SU1", "S", 24.2, 38.8, 60, 83, DS, "S", [(24.2, 38.8, 60, 83, ("v", 26.6, 69, 6))])
open_box("Sopen2", "S", 13.6, 24.2, 60, 83, DS, "white", "S", shelves=(67.8, 74.6))
closed("SU2", "S", 0, 13.6, 55, 83, DS, "S", [(0, 13.6, 55, 83, ("v", 2.2, 67, 6))])
open_box("Scup", "S", 13.6, 49.5, 50, 60, DS, "white", "S")
open_box("Sbelow", "S", 0, 13.6, 50, 55, DS, "white", "S")
# sliding glass doors (two overlapping panes with thin frames)
for i, (a0, a1, d) in enumerate([(14.3, 32.5, DS + 0.15), (30.6, 48.8, DS + 0.6)]):
    wbox(f"Sglass{i}", "S", a0, a1, d, d + 0.2, 50.8, 59.2, "glass", "S", 0)
    wbox(f"Sgf{i}a", "S", a0, a0 + 0.5, d - 0.05, d + 0.25, 50.8, 59.2, "steel", "S", 0)
    wbox(f"Sgf{i}b", "S", a1 - 0.5, a1, d - 0.05, d + 0.25, 50.8, 59.2, "steel", "S", 0)
wbox("Strack", "S", 13.6, 49.5, DS - 0.2, DS + 1.0, 59.2, 59.7, "steel", "S", 0)

# exterior seen through the window
box("ground", 114, 2500, -1500, 1500, -30, -29, principled("grass", srgb((110, 135, 80)), 0.9), "ext", 0)

# ---------------------------------------------------------------- lighting fixtures
LEDS = []
def led(name, x0, x1, py0, py1, z, grp, power):
    box(name, x0, x1, py0, py1, z - 0.2, z, "led", grp, 0)
    L = bpy.data.lights.new(name + "_L", "AREA"); L.shape = "RECTANGLE"
    L.size = abs(x1 - x0) * S; L.size_y = abs(py1 - py0) * S
    L.energy = power; L.color = (1.0, 0.84, 0.66)
    o = bpy.data.objects.new(name + "_L", L); coll.objects.link(o)
    o.location = ((x0 + x1) / 2 * S, -(py0 + py1) / 2 * S, (z - 0.25) * S)
    o["grp"] = grp

led("ledN1", 1, 27.5, 9, 10, 50, "N", 18)
led("ledN2", 59, 91, 9, 10, 50, "N", 20)
led("ledE", 98, 99, 52, 74, 55, "E", 15)
led("ledS", 15, 48, 65, 66, 50, "S", 16)
led("ledCup", 15, 48, 66, 67, 59.2, "S", 5)
led("ledHood", 31, 55, 9, 13, 56.8, "N", 15)

for i, (x, py) in enumerate([(30, 38), (70, 38)]):
    cyl(f"dl{i}", x, py, H - 0.3, 0.3, 2.2, "downlight", "ceil")
    cyl(f"dlr{i}", x, py, H - 0.35, 0.35, 2.8, "chrome", "ceil")
    L = bpy.data.lights.new(f"dlL{i}", "SPOT"); L.energy = 55; L.spot_size = math.radians(110); L.spot_blend = 0.8
    L.shadow_soft_size = 1.5 * S; L.color = (1.0, 0.86, 0.72)
    o = bpy.data.objects.new(f"dlL{i}", L); coll.objects.link(o)
    o.location = (x * S, -py * S, (H - 1) * S)

# sun through the east window + sky
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.2; sun.angle = math.radians(1.5); sun.color = (1.0, 0.93, 0.82)
so = bpy.data.objects.new("sun", sun); coll.objects.link(so)
sdir = Vector((-0.80, -0.30, -0.52)).normalized()   # light travelling west, slightly north->south, downward
so.rotation_euler = sdir.to_track_quat("-Z", "Y").to_euler()

world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
wn = world.node_tree.nodes; wl = world.node_tree.links
bg = wn["Background"]
sky = wn.new("ShaderNodeTexSky")
try:
    sky.sky_type = "MULTIPLE_SCATTERING"
except Exception:
    pass
sky.sun_disc = False
sky.sun_elevation = math.asin(-sdir.z)
sky.sun_rotation = math.atan2(-sdir.y, -sdir.x)
bg2 = wn.new("ShaderNodeBackground"); bg2.inputs[0].default_value = (0.92, 0.92, 0.93, 1); bg2.inputs[1].default_value = 1.0
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(sky.outputs[0], bg.inputs[0])
bg.inputs[1].default_value = 0.35
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg.outputs[0], mix.inputs[1]); wl.new(bg2.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wn["World Output"].inputs[0])

# ---------------------------------------------------------------- props / styling
cup("pot", 35, 11, ZC + 1.6, 5.0, 4.0, "steel", "N")
cyl("pot_lid", 35, 11, ZC + 6.6, 0.4, 4.1, "steel", "N", r2=3.6)
sphere("pot_knob", 35, 11, ZC + 7.2, 0.6, "black", "N")
cyl("kettle", 51, 11, ZC + 1.6, 6.0, 3.0, "navy", "N", r2=2.2)
cyl("kettle_lid", 51, 11, ZC + 7.6, 0.6, 1.6, "navy", "N")
box("board", 70, 84, 6, 17, ZC, ZC + 0.7, "wood", "N", 0.2)
box("board2", 73, 85, 1.5, 2.5, ZC, ZC + 13, "wood", "N", 0.2)
cup("utensil", 64, 6, ZC, 6, 2.0, "ceramic", "N")
for k, (dx, dy, h) in enumerate([(-0.6, 0, 6), (0.5, 0.4, 7), (0.1, -0.6, 6.5)]):
    cyl(f"spoon{k}", 64 + dx, 6 + dy, ZC + 1, h + 4, 0.3, "wood", "N")
for k, x in enumerate([3, 9, 15, 21]):  # jars on top of N uppers
    pass
# jars in N open niche
cyl("nj1", 60.75, 6, 56.75, 5.5, 1.7, "glass", "N"); cyl("nj1l", 60.75, 6, 62.25, 0.8, 1.75, "wood", "N")
cyl("nj2", 60.75, 6, 70.4, 4.5, 1.7, "terracotta", "N")
# plant + soap near window/sink
cyl("plantpot", 101, 27, ZC, 4.2, 2.7, "terracotta", "E", r2=2.2)
for k in range(9):
    a = k * 2.4
    sphere(f"leaf{k}", 101 + math.cos(a) * 1.8, 27 + math.sin(a) * 1.8, ZC + 6.5 + (k % 3) * 1.4, 1.6, "leaf", "E",
           scale=(1.0, 0.45, 1.6))
cyl("soap", 104, 45, ZC, 6, 1.1, "sage", "E")
cyl("soapcap", 104, 45, ZC + 6, 1.0, 0.4, "chrome", "E")
cup("mug_e", 95, 33, ZC, 3.6, 1.6, "ceramic", "E")
# jars/ cups in S open shelves and cup cabinet
for k, (x, z, m) in enumerate([(41.5, 60.75, "ceramic"), (46, 60.75, "sage"), (42.5, 68.55, "glass"), (46.5, 68.55, "glass"),
                               (44, 75.35, "terracotta"), (16.5, 60.75, "navy"), (21, 60.75, "ceramic"), (19, 68.55, "glass"),
                               (17, 75.35, "sage"), (21.3, 75.35, "ceramic")]):
    cyl(f"sj{k}", x, 69, z, 4.2 if m == "glass" else 3.4, 1.5, m, "S")
for k in range(7):
    x = 16.5 + k * 4.6
    cup(f"cup{k}", x, 68.5, 50.75, 3.4, 1.4, ["ceramic", "sage", "terracotta", "ceramic", "navy", "ceramic", "sage"][k], "S")
# fruit bowl on S counter
bw_ = sphere("bowl", 28, 67.5, ZC + 2.2, 4.5, "ceramic", "S", scale=(1, 1, 0.5))
cut_b = box("bowlcut", 20, 36, 60, 75, ZC + 2.2, ZC + 10, "ceramic", "S", 0)
cut(bw_, cut_b)
for k, (dx, dy, m) in enumerate([(-1.5, -1, "orange"), (1.6, -0.6, "orange"), (0, 1.6, "lemon"), (0.2, -0.3, "lemon")]):
    sphere(f"fruit{k}", 28 + dx, 67.5 + dy, ZC + 2.6 + (1.5 if k == 3 else 0), 1.5, m, "S")
box("tray", 38, 48, 63, 72, ZC, ZC + 0.5, "wood", "S", 0.15)
cyl("bottle1", 41, 67.5, ZC + 0.5, 8, 1.2, "glass", "S")
cyl("bottle2", 44.5, 66.5, ZC + 0.5, 6.5, 1.3, "navy", "S")

# ---------------------------------------------------------------- cameras
SHOTS = {
    # name: (cam pos (x,py,z), target (x,py,z), lens mm, hide groups, aspect, shift_y, ortho_scale)
    "01_hero":   ((-22, 42, 57), (90, 36, 46), 18, set(), 1.5, 0.0, None),
    "02_elev1":  ((48, 125, 52), (58, 0, 52), 22, {"wallS", "S"}, 1.5, 0.05, None),
    "03_elev2":  ((-20, 42, 54), (108, 40, 54), 24, set(), 1.5, 0.05, None),
    "04_elev3":  ((45, -40, 52), (38, 75, 50), 26, {"wallN", "N"}, 1.5, 0.05, None),
    "05_stove":  ((54, 50, 58), (40, 6, 44), 30, {"wallS", "S"}, 1.25, 0.0, None),
    "06_sink":   ((66, 32, 56), (106, 50, 45), 28, set(), 1.25, 0.0, None),
    "07_cups":   ((44, 30, 56), (28, 75, 56), 28, {"wallN", "N"}, 1.25, 0.0, None),
    "08_axo":    ((-170, 95, 300), (60, 37, 45), 0, {"ceil", "beam", "floorext"}, 1.5, 0.0, 5.4),
    # true isometric: view direction (1,1,1) from the south-west corner
    "09_iso":    ((54 - 300, 37 + 300, 45 + 300), (54, 37, 45), 0, {"ceil", "beam", "floorext"}, 1.0, 0.0, 4.4),
}
pos, tgt, lens, hide, aspect, shift, oscale = SHOTS[shot]
if shot == "09_iso":
    # section-cut look: near (south) wall cut down low, dark poche caps on cut wall tops
    for o in OBJS:
        if o.name == "wallS":
            o.hide_render = True
    box("wallS_cut", -6, 114, 75, 81, 0, 36, "wall", "cut", 0)
    box("cap_S", -6, 114, 75, 81, 36, 36.3, "plinth", "cut", 0)
    box("cap_N", -6, 114, -6, 0, H, H + 0.3, "plinth", "cut", 0)
    box("cap_E", 108, 114, -6, 75, H, H + 0.3, "plinth", "cut", 0)
cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d); coll.objects.link(cam); scene.camera = cam
cam.location = Vector((pos[0] * S, -pos[1] * S, pos[2] * S))
t = Vector((tgt[0] * S, -tgt[1] * S, tgt[2] * S))
cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
cam_d.sensor_width = 36
cam_d.shift_y = shift
cam_d.clip_start = 0.05
if oscale:
    cam_d.type = "ORTHO"; cam_d.ortho_scale = oscale
else:
    cam_d.lens = lens

for o in bpy.data.objects:
    if shot in ("08_axo", "09_iso") and o.get("grp") in ("ceil", "beam", "ext"):
        o.hide_render = True
    if o.get("grp") in hide:
        o.visible_camera = False
        if o.get("grp") in ("ceil", "beam"):
            o.visible_shadow = True

# ---------------------------------------------------------------- render settings
scene.render.engine = "CYCLES"
c = scene.cycles
c.device = "CPU"
c.samples = SAMPLES
c.use_adaptive_sampling = True
c.adaptive_threshold = 0.015
c.use_denoising = True
try:
    c.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
c.max_bounces = 10; c.diffuse_bounces = 5; c.glossy_bounces = 4; c.transmission_bounces = 10
c.caustics_reflective = False; c.caustics_refractive = False
c.blur_glossy = 1.0
c.sample_clamp_indirect = 8
scene.render.resolution_x = RES_W
scene.render.resolution_y = int(RES_W / aspect)
scene.render.resolution_percentage = 100
scene.render.threads_mode = "AUTO"
vs = scene.view_settings
vs.view_transform = "AgX"
for look in ("AgX - Medium High Contrast", "Medium High Contrast", "AgX - Base Contrast"):
    try:
        vs.look = look; break
    except Exception:
        pass
vs.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("DONE", OUT)
