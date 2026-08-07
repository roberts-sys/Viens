"""Generates construction_site.wbt. Loops let us add a lot of repeated detail
(track grousers, sprocket teeth, scaffolding, lattice) without hand-writing it."""

import math

import os

# writes into ../worlds/ next to this script
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "worlds", "construction_site.wbt")

# ---------------------------------------------------------------- geometry
CUBE = 0.16
COLOURS = ("blue", "yellow", "brown", "red", "green", "white")
# Home pads are spread right round the yard, so the machine has a real drive to
# each one. Every position below was checked to have a ring of parking spots at
# arm's length that is clear of the props and of every other pad, and to be
# reachable from where the machine starts. See tools/navtest.py.
HOMES = {
    "blue":   (4.80, 1.80),
    "yellow": (-0.20, 4.55),
    "brown":  (-3.95, 3.30),
    "red":    (-4.70, -1.70),
    "green":  (-0.20, -3.95),
    "white":  (3.80, -3.20),
}
TOWERS = ((-2.20, -0.70), (2.30, -0.70))
CUBE_COLOURS = {
    "blue":   (0.10, 0.32, 0.80),
    "yellow": (0.95, 0.78, 0.10),
    "brown":  (0.42, 0.26, 0.13),
    "red":    (0.80, 0.13, 0.10),
    "green":  (0.13, 0.55, 0.22),
    "white":  (0.90, 0.90, 0.88),
}
ROCK_COLOURS = {
    "blue":   ((0.42, 0.45, 0.50), (0.32, 0.35, 0.40), (0.54, 0.57, 0.62)),
    "yellow": ((0.72, 0.62, 0.38), (0.58, 0.48, 0.28), (0.84, 0.75, 0.52)),
    "brown":  ((0.40, 0.30, 0.22), (0.30, 0.22, 0.16), (0.52, 0.41, 0.30)),
    "red":    ((0.55, 0.28, 0.22), (0.42, 0.20, 0.16), (0.68, 0.40, 0.32)),
    "green":  ((0.38, 0.44, 0.32), (0.28, 0.34, 0.24), (0.50, 0.56, 0.42)),
    "white":  ((0.76, 0.75, 0.71), (0.62, 0.61, 0.58), (0.88, 0.87, 0.84)),
}

# ---------------------------------------------------------------- the site
# Every solid thing standing on the ground, in one table. The visuals are
# placed from it, the collision bodies are generated from it, and the
# controller's obstacle map is written out from it as site_map.py - so the
# picture, the physics and the route planner cannot drift apart.
#
#   kind "box": dims (sx, sy, sz)     kind "cyl": dims (radius, height)
#   Both sit on the ground. "full" props are left out of the lite world.
#   "extra" is for the visual builder only (a colour, usually).
#
#            id           x      y     yaw    kind   dims                 full   extra
PROPS = [
    ("barrier",     -0.64,   7.54,  0.0000, "box", (1.62, 0.42, 0.51),  False, None),
    ("barrier",     -2.64,   7.54,  0.0000, "box", (1.62, 0.42, 0.51),  True,  None),
    ("barrier",     -7.54,  -2.33, -1.5708, "box", (1.62, 0.42, 0.51),  True,  None),
    ("barrier",      0.46,  -7.54,  0.0000, "box", (1.62, 0.42, 0.51),  True,  None),
    ("barrier",      7.54,   0.51, -1.5708, "box", (1.62, 0.42, 0.51),  False, None),
    ("barrier",      7.54,   2.41, -1.5708, "box", (1.62, 0.42, 0.51),  True,  None),
    ("barrow",       4.88,  -7.49,  0.0000, "box", (0.96, 0.52, 0.55),  True,  None),
    ("bricks",       3.69,  -7.35,  0.0000, "box", (1.00, 0.80, 0.68),  True,  0.5),
    ("bricks",       7.35,   3.99, -1.5708, "box", (1.00, 0.80, 0.54),  True,  0.42),
    ("cabledrum",    7.45,   5.20, -1.5708, "box", (0.86, 0.60, 0.84),  True,  None),
    ("cone",         4.30,   2.40,  0.0000, "cyl", (0.11, 0.34),        False, None),
    ("cone",         4.20,  -1.40,  0.0000, "cyl", (0.11, 0.34),        False, None),
    ("cone",        -4.30,   2.20,  0.0000, "cyl", (0.11, 0.34),        False, None),
    ("cone",        -4.20,  -2.00,  0.0000, "cyl", (0.11, 0.34),        False, None),
    ("cone",         2.30,   4.40,  0.0000, "cyl", (0.11, 0.34),        True,  None),
    ("cone",        -2.40,   4.30,  0.0000, "cyl", (0.11, 0.34),        True,  None),
    ("cone",         2.10,  -4.40,  0.0000, "cyl", (0.11, 0.34),        True,  None),
    ("cone",        -2.20,  -4.35,  0.0000, "cyl", (0.11, 0.34),        True,  None),
    ("container",   -4.83,  -7.13,  0.0000, "box", (3.14, 1.24, 1.24),  False, None),
    ("drums",       -7.20,  -5.85,  0.0000, "cyl", (0.55, 0.60),        True,  None),
    ("generator",   -7.28,  -4.22, -1.5708, "box", (1.55, 0.95, 0.97),  True,  None),
    ("mast",         5.98,  -7.33,  0.0000, "cyl", (0.42, 4.20),        True,  None),
    ("mixer",       -5.99,   7.41,  0.0000, "box", (0.82, 0.68, 0.92),  True,  None),
    ("office",       4.72,   6.58,  0.0000, "box", (3.35, 2.35, 1.35),  True,  None),
    ("pile",         1.61,   6.70,  0.0000, "cyl", (1.05, 0.62),        True,  (0.52, 0.49, 0.43)),
    ("pile",        -6.80,   1.74,  0.0000, "cyl", (0.95, 0.55),        False, (0.43, 0.34, 0.25)),
    ("pile",        -6.90,  -0.36,  0.0000, "cyl", (0.85, 0.50),        True,  (0.46, 0.38, 0.28)),
    ("pile",        -1.81,  -6.50,  0.0000, "cyl", (1.25, 0.78),        False, (0.4, 0.31, 0.22)),
    ("pile",         6.30,  -2.02,  0.0000, "cyl", (1.45, 0.88),        False, (0.38, 0.3, 0.21)),
    ("pipes",        2.23,  -7.26,  0.0000, "box", (1.52, 0.98, 0.84),  True,  None),
    ("rebar",       -7.50,   4.70, -1.5708, "box", (3.40, 0.50, 0.10),  True,  None),
    ("sandbags",    -4.52,   7.45,  0.0000, "box", (1.35, 0.60, 0.26),  True,  None),
    ("sign",         0.30,   4.50,  0.0000, "cyl", (0.09, 1.75),        True,  (0.9, 0.15, 0.12)),
    ("sign",         0.20,  -4.50,  0.0000, "cyl", (0.09, 1.75),        True,  (0.95, 0.75, 0.05)),
    ("timber",       7.30,  -5.08, -1.5708, "box", (2.65, 0.90, 0.46),  True,  None),
    ("toilet",       7.50,   6.15, -1.5708, "box", (0.50, 0.50, 1.08),  True,  None),
]
FENCE = 8.0       # the fenced yard runs from -FENCE to +FENCE on both axes


def props_of(pid, full):
    """Every prop with this id that belongs in this world."""
    return [q for q in PROPS if q[0] == pid and (full or not q[6])]


def plan_radius(kind, dims):
    """The radius the route planner should keep clear of this prop."""
    return dims[0] if kind == "cyl" else math.hypot(dims[0] / 2.0, dims[1] / 2.0)


# ---------------------------------------------------------------- palette
YEL   = (0.93, 0.69, 0.08)
YEL_D = (0.84, 0.61, 0.06)
DARK  = (0.16, 0.17, 0.19)
CHAR  = (0.10, 0.10, 0.11)
GREY  = (0.30, 0.31, 0.33)
STEEL = (0.62, 0.64, 0.67)
CHROME= (0.78, 0.80, 0.82)
GLASS = (0.10, 0.14, 0.18)
ORANGE= (0.85, 0.35, 0.06)
DIRT  = (0.45, 0.36, 0.27)
CONC  = (0.66, 0.65, 0.62)


def v(t):
    return " ".join("%.5f" % x for x in t)


def indent(s, n):
    pad = " " * n
    return "\n".join(pad + ln if ln.strip() else ln for ln in s.split("\n"))


def app(color, rough=0.8, metal=0.2, transp=None, emis=None):
    s = "PBRAppearance {\n  baseColor %s\n  roughness %.2f\n  metalness %.2f\n" % (
        v(color), rough, metal)
    if transp is not None:
        s += "  transparency %.2f\n" % transp
    if emis is not None:
        s += "  emissiveColor %s\n" % v(emis)
    return s + "}"


def shape(geom, color, rough=0.8, metal=0.2, transp=None, emis=None):
    return "Shape {\n  appearance %s\n  geometry %s\n}" % (
        indent(app(color, rough, metal, transp, emis), 2).lstrip(),
        indent(geom, 2).lstrip())


def def_shape(defname, geom, color, rough=0.8, metal=0.2, transp=None, emis=None):
    """Like shape(), but the appearance node carries a DEF.

    Used for the one shape the controller needs to reach after the world is
    built and modify live (the cab beacon, which blinks) - getFromDef() finds
    it, and emissiveColor is a field of the appearance node itself, so DEF'ing
    the appearance rather than the Shape saves a hop.
    """
    return "Shape {\n  appearance DEF %s %s\n  geometry %s\n}" % (
        defname, indent(app(color, rough, metal, transp, emis), 2).lstrip(),
        indent(geom, 2).lstrip())


def pose(children, t=(0, 0, 0), rot=None):
    if isinstance(children, str):
        children = [children]
    body = "\n".join(indent(c, 4) for c in children)
    s = "Pose {\n  translation %s\n" % v(t)
    if rot is not None:
        s += "  rotation %s\n" % (" ".join("%.6f" % x for x in rot))
    return s + "  children [\n%s\n  ]\n}" % body


def box(size, t=(0, 0, 0), rot=None, color=GREY, **kw):
    return pose(shape("Box {\n  size %s\n}" % v(size), color, **kw), t, rot)


def cyl(h, r, t=(0, 0, 0), rot=None, color=GREY, sub=16, **kw):
    g = "Cylinder {\n  height %.5f\n  radius %.5f\n  subdivision %d\n}" % (h, r, sub)
    return pose(shape(g, color, **kw), t, rot)


def cone(h, r, t=(0, 0, 0), rot=None, color=DIRT, sub=20, **kw):
    g = "Cone {\n  bottomRadius %.5f\n  height %.5f\n  subdivision %d\n}" % (r, h, sub)
    return pose(shape(g, color, **kw), t, rot)


def vcyl(h, r, t, color=GREY, sub=16, **kw):
    """Upright cylinder. Webots cylinders are already Z-aligned, so no rotation."""
    return cyl(h, r, t, None, color, sub, **kw)


def ycyl(h, r, t, color=GREY, sub=16, **kw):
    """Cylinder lying along the Y axis (across the machine): wheels, hinge pins."""
    return cyl(h, r, t, (1, 0, 0, 1.5708), color, sub, **kw)


def xcyl(h, r, t, color=GREY, sub=16, **kw):
    """Cylinder lying along the X axis (fore-and-aft)."""
    return cyl(h, r, t, (0, 1, 0, 1.5708), color, sub, **kw)


def ucone(h, r, t, color=DIRT, sub=20, **kw):
    """Upright cone STANDING ON ITS BASE at t.

    Webots centres a Cone on its own axis, so a cone drawn at ground level has
    half of itself underground. This shifts it up by half its height.
    """
    return cone(h, r, (t[0], t[1], t[2] + h / 2.0), None, color, sub, **kw)


def aim(d):
    """Axis-angle rotating the cylinder's local +z axis onto direction d."""
    n = math.sqrt(sum(c * c for c in d))
    dh = [c / n for c in d]
    dot = dh[2]
    if dot > 0.999999:
        return (1.0, 0.0, 0.0, 0.0)
    if dot < -0.999999:
        return (1.0, 0.0, 0.0, math.pi)
    ax = (-dh[1], dh[0], 0.0)          # (0,0,1) x dh
    m = math.sqrt(sum(c * c for c in ax))
    return (ax[0] / m, ax[1] / m, ax[2] / m, math.acos(dot))


def strut(p0, p1, r, color=STEEL, sub=10, **kw):
    """A cylinder running from p0 to p1 — rams, hoses, handrails, lattice."""
    d = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in d))
    mid = [(p0[i] + p1[i]) / 2 for i in range(3)]
    return cyl(L, r, mid, aim(d), color, sub, **kw)


def group(children, t=(0, 0, 0), yaw=0.0):
    return pose(children, t, (0, 0, 1, yaw))


# ======================================================================
#  EXCAVATOR
# ======================================================================
def track(side):
    """One track assembly. side = +1 (left) or -1 (right)."""
    y = 0.30 * side
    p = []
    p.append(box((0.93, 0.16, 0.155), (0, y, 0.1575), color=DARK, rough=0.85, metal=0.4))
    # idler + sprocket
    for x, r in ((0.48, 0.13), (-0.48, 0.13)):
        p.append(ycyl(0.20, r, (x, y, 0.13), color=(0.22, 0.23, 0.25), sub=24, metal=0.5))
        p.append(ycyl(0.10, 0.05, (x, y, 0.13), color=CHROME, sub=16, metal=0.9, rough=0.3))
    # sprocket teeth
    for i in range(10):
        a = i * math.pi / 5
        p.append(box((0.035, 0.20, 0.045),
                     (-0.48 + 0.145 * math.cos(a), y, 0.13 + 0.145 * math.sin(a)),
                     (0, 1, 0, -a), color=(0.28, 0.29, 0.31), metal=0.6))
    # belts
    p.append(box((0.96, 0.22, 0.05), (0, y, 0.025), color=CHAR, rough=1))
    p.append(box((0.96, 0.22, 0.05), (0, y, 0.235), color=CHAR, rough=1))
    # belt wrapping around the ends
    for cx, sgn in ((0.48, 1), (-0.48, -1)):
        for i in range(6):
            a = -math.pi / 2 + i * math.pi / 5
            aa = a if sgn > 0 else math.pi - a
            p.append(box((0.05, 0.22, 0.045),
                         (cx + 0.155 * math.cos(aa), y, 0.13 + 0.155 * math.sin(aa)),
                         (0, 1, 0, -aa), color=CHAR, rough=1))
    # grousers (tread bars)
    for i in range(7):
        x = -0.42 + i * 0.14
        p.append(box((0.04, 0.24, 0.03), (x, y, 0.005), color=(0.14, 0.14, 0.15), rough=1))
        p.append(box((0.04, 0.24, 0.03), (x, y, 0.255), color=(0.14, 0.14, 0.15), rough=1))
    # road wheels + carrier rollers
    for x in (-0.30, -0.10, 0.10, 0.30):
        p.append(ycyl(0.16, 0.06, (x, y, 0.06), color=(0.25, 0.26, 0.28), metal=0.5))
    for x in (-0.2, 0.2):
        p.append(ycyl(0.10, 0.035, (x, y, 0.245), color=(0.25, 0.26, 0.28), metal=0.5))
    # hub bolt circles on the idler and the sprocket
    for hx in (0.48, -0.48):
        for i in range(6):
            a = i * math.pi / 3
            p.append(ycyl(0.022, 0.010, (hx + 0.062 * math.cos(a), y + 0.101 * side,
                                         0.13 + 0.062 * math.sin(a)),
                          CHROME, 6, metal=0.9, rough=0.3))
    # bolt heads along the track frame
    for i in range(8):
        p.append(ycyl(0.02, 0.011, (-0.42 + i * 0.12, y + 0.081 * side, 0.215),
                      (0.34, 0.35, 0.37), 6, metal=0.7))
    # mud scrapers front and rear
    for sx in (0.40, -0.40):
        p.append(box((0.02, 0.20, 0.07), (sx, y, 0.075), color=(0.30, 0.31, 0.33), metal=0.6))
    # track tension adjuster + mud guard
    p.append(xcyl(0.09, 0.045, (0.33, y, 0.19), CHROME, 12, metal=0.9))
    p.append(box((0.44, 0.26, 0.02), (0, y, 0.30), color=DARK, rough=0.9))
    # travel motor
    p.append(ycyl(0.12, 0.09, (-0.48, y - 0.13 * side, 0.13), color=GREY, sub=16, metal=0.6))
    return p


def undercarriage():
    p = []
    for s in (1, -1):
        p += track(s)
    p.append(box((0.72, 0.46, 0.14), (0, 0, 0.20), color=(0.20, 0.21, 0.23), metal=0.4))
    p.append(box((0.90, 0.14, 0.10), (0, 0.30, 0.24), color=(0.20, 0.21, 0.23), metal=0.4))
    p.append(box((0.90, 0.14, 0.10), (0, -0.30, 0.24), color=(0.20, 0.21, 0.23), metal=0.4))
    p.append(vcyl(0.10, 0.30, (0, 0, 0.29), color=GREY, sub=32, rough=0.6, metal=0.8))
    # slew ring bolts
    for i in range(12):
        a = i * math.pi / 6
        p.append(vcyl(0.03, 0.014, (0.265 * math.cos(a), 0.265 * math.sin(a), 0.345),
                      color=CHROME, sub=8, metal=0.9, rough=0.3))
    p.append(vcyl(0.16, 0.07, (0, 0, 0.24), color=(0.35, 0.36, 0.38), metal=0.7))
    return p


def cab():
    p = []
    cx, cy = 0.10, 0.26
    p.append(box((0.46, 0.42, 0.52), (cx, cy, 0.36), color=YEL, rough=0.7, metal=0.3))
    # ROPS corner posts
    for dx in (-0.22, 0.22):
        for dy in (-0.20, 0.20):
            p.append(box((0.04, 0.04, 0.54), (cx + dx, cy + dy, 0.36), color=DARK, metal=0.5))
    # glazing
    p.append(box((0.02, 0.34, 0.38), (cx + 0.234, cy, 0.40), color=GLASS, rough=0.15, metal=0.1))
    p.append(box((0.34, 0.02, 0.34), (cx, cy + 0.214, 0.40), color=GLASS, rough=0.15, metal=0.1))
    p.append(box((0.34, 0.02, 0.34), (cx, cy - 0.214, 0.40), color=GLASS, rough=0.15, metal=0.1))
    p.append(box((0.02, 0.34, 0.30), (cx - 0.234, cy, 0.38), color=GLASS, rough=0.15, metal=0.1))
    # door frame + handle
    p.append(box((0.015, 0.36, 0.44), (cx - 0.242, cy, 0.36), color=YEL_D, rough=0.7))
    p.append(strut((cx - 0.255, cy - 0.10, 0.34), (cx - 0.255, cy - 0.10, 0.44), 0.012, CHROME,
                   metal=0.9, rough=0.3))
    # wiper
    p.append(strut((cx + 0.245, cy - 0.12, 0.28), (cx + 0.245, cy + 0.06, 0.44), 0.008, CHAR))
    # roof + hatch + beacon
    p.append(box((0.50, 0.46, 0.04), (cx, cy, 0.64), color=YEL_D, rough=0.75))
    p.append(box((0.18, 0.20, 0.015), (cx + 0.06, cy, 0.665), color=GLASS, rough=0.2))
    p.append(vcyl(0.03, 0.03, (cx - 0.16, cy, 0.675), color=DARK))
    # the beacon's appearance is DEF'd so the controller can make it blink
    p.append(pose(
        def_shape("BEACON_MAT",
                 "Cylinder {\n  height 0.07000\n  radius 0.03500\n  subdivision 16\n}",
                 (0.95, 0.4, 0.05), rough=0.35, emis=(0.6, 0.16, 0.0)),
        (cx - 0.16, cy, 0.705)))
    # roof work lights
    for dy in (-0.14, 0.14):
        p.append(box((0.06, 0.07, 0.06), (cx + 0.20, cy + dy, 0.69), color=DARK))
        p.append(box((0.015, 0.06, 0.05), (cx + 0.232, cy + dy, 0.69),
                     color=(1, 0.97, 0.85), rough=0.1, emis=(1, 0.93, 0.7)))
    # mirrors
    for dy, s in ((0.24, 1), (-0.24, -1)):
        p.append(strut((cx + 0.20, cy + dy, 0.60), (cx + 0.26, cy + dy + 0.10 * s, 0.66),
                       0.008, CHAR))
        p.append(box((0.02, 0.05, 0.08), (cx + 0.27, cy + dy + 0.12 * s, 0.67), color=DARK))
    # rubber seals framing each pane
    for dz, hh in ((0.595, 0.02), (0.205, 0.02)):
        p.append(box((0.03, 0.38, hh), (cx + 0.236, cy, dz), color=(0.10, 0.10, 0.12)))
    for dy2 in (0.185, -0.185):
        p.append(box((0.03, 0.02, 0.40), (cx + 0.236, cy + dy2, 0.40), color=(0.10, 0.10, 0.12)))
    for dy2 in (0.216, -0.216):
        p.append(box((0.38, 0.022, 0.02), (cx, cy + dy2, 0.585), color=(0.10, 0.10, 0.12)))
        p.append(box((0.38, 0.022, 0.02), (cx, cy + dy2, 0.225), color=(0.10, 0.10, 0.12)))
    # guard bars in front of the roof lights
    for dy2 in (-0.14, 0.14):
        for k in (-0.018, 0.018):
            p.append(box((0.012, 0.012, 0.06), (cx + 0.243, cy + dy2 + k, 0.69),
                         color=(0.35, 0.36, 0.38), metal=0.7))
    # window mullions + sun visor + antenna
    for dz in (0.24, 0.56):
        p.append(box((0.025, 0.36, 0.025), (cx + 0.238, cy, dz), color=YEL_D, rough=0.75))
    p.append(box((0.05, 0.34, 0.02), (cx + 0.215, cy, 0.575), (0, 1, 0, 0.35),
                 color=(0.20, 0.20, 0.22), rough=0.8))
    p.append(strut((cx - 0.20, cy - 0.20, 0.66), (cx - 0.22, cy - 0.20, 0.86), 0.006, CHAR, 6))
    # interior: seat, armrests, joystick consoles, foot pedals
    p.append(box((0.16, 0.17, 0.05), (cx - 0.04, cy, 0.19), color=(0.12, 0.12, 0.14)))
    p.append(box((0.06, 0.17, 0.22), (cx - 0.11, cy, 0.32), (0, 1, 0, -0.12),
                 color=(0.12, 0.12, 0.14)))
    p.append(box((0.10, 0.19, 0.03), (cx - 0.04, cy, 0.30), color=(0.15, 0.15, 0.17)))
    for dy in (-0.10, 0.10):
        p.append(box((0.11, 0.05, 0.05), (cx + 0.02, cy + dy, 0.245), color=(0.15, 0.15, 0.17)))
        p.append(strut((cx + 0.03, cy + dy, 0.265), (cx + 0.045, cy + dy, 0.34), 0.010, CHAR))
        p.append(vcyl(0.022, 0.016, (cx + 0.045, cy + dy, 0.35), color=(0.55, 0.12, 0.10), sub=8))
        p.append(box((0.07, 0.05, 0.015), (cx + 0.17, cy + dy * 0.6, 0.135),
                     (0, 1, 0, 0.2), color=(0.18, 0.18, 0.20)))
    # monitor screen, roof grab handle, door hinges, latch
    p.append(box((0.02, 0.09, 0.07), (cx + 0.14, cy + 0.15, 0.34), (0, 0, 1, -0.3),
                 color=(0.08, 0.10, 0.13), emis=(0.05, 0.12, 0.10)))
    p.append(box((0.03, 0.03, 0.09), (cx + 0.14, cy + 0.15, 0.28), color=(0.18, 0.18, 0.20)))
    p.append(strut((cx - 0.16, cy + 0.17, 0.60), (cx + 0.04, cy + 0.17, 0.60), 0.008, CHROME))
    for dz in (0.22, 0.50):
        p.append(box((0.02, 0.03, 0.04), (cx - 0.248, cy + 0.17, dz),
                     color=(0.35, 0.36, 0.38), metal=0.8))
    p.append(box((0.015, 0.05, 0.02), (cx - 0.252, cy - 0.12, 0.39), color=CHROME, metal=0.9))
    return p


def house():
    p = []
    # deck
    p.append(box((1.06, 0.74, 0.10), (-0.02, 0, 0.05), color=YEL, rough=0.7, metal=0.3))
    p.append(box((1.00, 0.68, 0.03), (-0.02, 0, 0.005), color=(0.22, 0.23, 0.25), rough=0.85))
    for i in range(6):
        p.append(box((0.02, 0.56, 0.008), (-0.40 + i * 0.13, 0.02, 0.102),
                     color=(0.75, 0.56, 0.06), rough=0.9))
    # engine housing + grille + hatch
    p.append(box((0.50, 0.64, 0.34), (-0.30, -0.04, 0.27), color=YEL, rough=0.7, metal=0.3))
    for i in range(7):
        p.append(box((0.012, 0.44, 0.022), (-0.552, -0.04, 0.16 + i * 0.035),
                     color=DARK, rough=0.9))
    p.append(box((0.34, 0.50, 0.012), (-0.30, -0.04, 0.447), color=YEL_D, rough=0.75))
    for dy in (-0.20, 0.12):
        p.append(box((0.05, 0.03, 0.02), (-0.44, dy - 0.04, 0.452), color=CHROME, metal=0.9))
    p.append(box((0.03, 0.05, 0.02), (-0.15, -0.04, 0.452), color=CHROME, metal=0.9))
    p.append(box((0.24, 0.02, 0.24), (-0.42, -0.343, 0.27), color=DARK, rough=0.9))
    # exhaust + heat shield
    p.append(vcyl(0.22, 0.035, (-0.30, -0.24, 0.55), color=(0.18, 0.18, 0.19), metal=0.6))
    p.append(vcyl(0.03, 0.05, (-0.30, -0.24, 0.67), color=(0.12, 0.12, 0.13), metal=0.6))
    p.append(vcyl(0.10, 0.05, (-0.30, -0.24, 0.49), color=CHROME, metal=0.9, rough=0.35))
    # tanks
    p.append(vcyl(0.30, 0.10, (-0.08, -0.26, 0.28), color=GREY, rough=0.6, metal=0.7))
    p.append(vcyl(0.03, 0.04, (-0.08, -0.26, 0.44), color=CHROME, metal=0.9))
    p.append(box((0.26, 0.16, 0.22), (0.18, -0.27, 0.21), color=YEL_D, rough=0.7))
    p.append(vcyl(0.03, 0.035, (0.18, -0.27, 0.334), color=CHROME, metal=0.9))
    # toolbox
    p.append(box((0.20, 0.14, 0.12), (-0.02, -0.29, 0.16), color=(0.20, 0.21, 0.23), metal=0.4))
    # counterweight + hazard stripes + tow hook
    # Kept deliberately short: the rear used to overhang the tracks by 0.37 m,
    # which read as out of proportion. It now overhangs by 0.20 m.
    p.append(box((0.20, 0.70, 0.32), (-0.54, 0, 0.19), color=YEL_D, rough=0.75, metal=0.3))
    p.append(ycyl(0.70, 0.15, (-0.63, 0, 0.19), YEL_D, 20, rough=0.75))
    p.append(box((0.03, 0.62, 0.09), (-0.702, 0, 0.055), color=YEL_D, rough=0.75))
    for i in range(6):
        p.append(box((0.018, 0.09, 0.075), (-0.720, -0.28 + i * 0.113, 0.055),
                     color=CHAR if i % 2 else (0.95, 0.8, 0.05), rough=0.8))
    p.append(box((0.08, 0.10, 0.06), (-0.74, 0, 0.10), color=DARK, metal=0.6))
    # handrails
    p.append(strut((0.36, 0.38, 0.10), (0.36, 0.38, 0.36), 0.013, CHROME, metal=0.9, rough=0.3))
    p.append(strut((0.36, 0.38, 0.36), (0.10, 0.42, 0.36), 0.013, CHROME, metal=0.9, rough=0.3))
    p.append(strut((-0.50, 0.34, 0.10), (-0.50, 0.34, 0.30), 0.013, CHROME, metal=0.9, rough=0.3))
    p.append(box((0.18, 0.14, 0.03), (0.30, 0.46, 0.06), color=(0.22, 0.23, 0.25), rough=0.9))
    p.append(box((0.18, 0.14, 0.03), (0.30, 0.46, -0.06), color=(0.22, 0.23, 0.25), rough=0.9))
    p += cab()
    # bolt heads round the deck edge
    for i in range(12):
        p.append(vcyl(0.014, 0.011, (-0.49 + i * 0.091, 0.355, 0.10), (0.34, 0.35, 0.37),
                      6, metal=0.8))
        p.append(vcyl(0.014, 0.011, (-0.49 + i * 0.091, -0.355, 0.10), (0.34, 0.35, 0.37),
                      6, metal=0.8))
    # rivet rows on the counterweight face, each row sat on the drum's surface
    for i in range(8):
        for dz in (0.08, 0.32):
            surf = -0.63 - math.sqrt(max(0.0, 0.15 ** 2 - (dz - 0.19) ** 2))
            p.append(xcyl(0.014, 0.009, (surf - 0.004, -0.28 + i * 0.08, dz),
                          (0.72, 0.53, 0.05), 6, metal=0.7))
    # extra grille slats and a hatch handle
    for i in range(6):
        p.append(box((0.010, 0.40, 0.016), (-0.554, 0.20, 0.17 + i * 0.036),
                     color=DARK, rough=0.9))
    p.append(strut((-0.20, 0.10, 0.455), (-0.20, 0.22, 0.455), 0.010, CHROME, metal=0.9))
    # tread bars on the steps
    for i in range(3):
        p.append(box((0.02, 0.13, 0.012), (0.245 + i * 0.05, 0.46, 0.077),
                     color=(0.35, 0.36, 0.38), metal=0.7))
        p.append(box((0.02, 0.13, 0.012), (0.245 + i * 0.05, 0.46, -0.043),
                     color=(0.35, 0.36, 0.38), metal=0.7))
    # handrail stanchions
    for hx in (0.36, 0.20, 0.04):
        p.append(vcyl(0.05, 0.010, (hx, 0.40, 0.13), (0.45, 0.46, 0.48), 6, metal=0.8))
    # exhaust clamp rings
    for dz in (0.48, 0.60):
        p.append(vcyl(0.018, 0.045, (-0.30, -0.24, dz), (0.30, 0.31, 0.33), 10, metal=0.8))
    # battery box, air filter canister, hose reel
    p.append(box((0.16, 0.13, 0.11), (-0.47, -0.25, 0.155), color=(0.16, 0.17, 0.19), metal=0.4))
    p.append(box((0.17, 0.14, 0.012), (-0.47, -0.25, 0.216), color=(0.35, 0.36, 0.38), metal=0.6))
    p.append(xcyl(0.20, 0.055, (-0.30, 0.24, 0.50), (0.55, 0.56, 0.58), 16, metal=0.6))
    p.append(xcyl(0.03, 0.06, (-0.42, 0.24, 0.50), (0.30, 0.31, 0.33), 16))
    p.append(vcyl(0.05, 0.07, (0.04, -0.28, 0.245), color=(0.20, 0.21, 0.23), sub=16, metal=0.5))
    # counterweight bolt heads
    for dy in (-0.24, -0.08, 0.08, 0.24):
        p.append(xcyl(0.02, 0.018, (-0.736, dy, 0.30), CHROME, 8, metal=0.9))
    # boom bracket + pin
    for dy in (0.12, -0.12):
        p.append(box((0.22, 0.06, 0.28), (0.28, dy, 0.13), color=(0.22, 0.23, 0.25), metal=0.5))
    p.append(ycyl(0.32, 0.055, (0.30, 0, 0.16), CHROME, 20, metal=0.9, rough=0.3))
    # boom lift rams, angled up towards the boom
    for dy in (0.20, -0.20):
        p.append(strut((0.02, dy, 0.14), (0.30, dy, 0.34), 0.05, GREY, 16, metal=0.8, rough=0.5))
        p.append(strut((0.28, dy, 0.33), (0.46, dy, 0.46), 0.026, CHROME, 16, metal=1, rough=0.25))
    return p


def camera_pod(t, look_sign, color=(0.12, 0.12, 0.13)):
    """A small camera housing: box, lens, sun hood and two mounting bolts.

    t is the BACK of the housing, meant to sit flush against the hull - the
    caller is responsible for choosing a t that actually touches something,
    which is what stops these floating.  look_sign is +1 if the camera looks
    along +x, -1 along -x.
    """
    hx = t[0] + look_sign * 0.03      # the lens face
    p = [box((0.06, 0.07, 0.06), t, color=color, rough=0.5, metal=0.3)]
    p.append(xcyl(0.030, 0.018, (hx, t[1], t[2]), color=CHAR, sub=10, metal=0.6, rough=0.25))
    p.append(box((0.010, 0.075, 0.012), (hx - look_sign * 0.006, t[1], t[2] + 0.033),
                 color=(0.30, 0.31, 0.33), metal=0.5))
    for dy in (-0.026, 0.026):
        p.append(xcyl(0.012, 0.006, (t[0] - look_sign * 0.020, t[1] + dy, t[2] - 0.027),
                      color=(0.45, 0.46, 0.48), sub=6, metal=0.8))
    return p


def boom():
    p = []
    p.append(box((0.35, 0.16, 0.13), (0.16, 0, 0.05), (0, 1, 0, -0.303), YEL, rough=0.7, metal=0.3))
    p.append(box((0.33, 0.15, 0.12), (0.47, 0, 0.05), (0, 1, 0, 0.3217), YEL, rough=0.7, metal=0.3))
    # gusset plates along the bend
    for dy in (0.083, -0.083):
        p.append(box((0.14, 0.012, 0.15), (0.32, dy, 0.10), color=YEL_D, rough=0.75))
    p.append(box((0.10, 0.17, 0.02), (0.32, 0, 0.135), color=YEL_D, rough=0.75))
    # pivot ears + pins
    p.append(ycyl(0.19, 0.065, (0, 0, 0), GREY, 20, metal=0.8, rough=0.6))
    p.append(ycyl(0.22, 0.032, (0, 0, 0), CHROME, 16, metal=0.9, rough=0.3))
    p.append(ycyl(0.16, 0.055, (0.62, 0, 0), GREY, 20, metal=0.8, rough=0.6))
    p.append(ycyl(0.19, 0.028, (0.62, 0, 0), CHROME, 16, metal=0.9, rough=0.3))
    # stick ram on top
    p.append(strut((0.26, 0, 0.18), (0.50, 0, 0.14), 0.05, GREY, 16, metal=0.8, rough=0.5))
    p.append(strut((0.48, 0, 0.145), (0.66, 0, 0.10), 0.026, CHROME, 16, metal=1, rough=0.25))
    # hydraulic hoses
    for dy in (0.086, -0.086):
        p.append(strut((0.03, dy, -0.03), (0.30, dy, 0.03), 0.014, CHAR, 8, rough=0.9))
        p.append(strut((0.30, dy, 0.03), (0.60, dy, -0.02), 0.014, CHAR, 8, rough=0.9))
    p.append(strut((0.05, 0.05, -0.05), (0.34, 0.05, 0.00), 0.011, (0.35, 0.12, 0.10), 8))
    p.append(strut((0.05, -0.05, -0.05), (0.34, -0.05, 0.00), 0.011, (0.35, 0.12, 0.10), 8))
    # boom work light + lifting eye
    p.append(box((0.05, 0.06, 0.05), (0.30, 0.10, 0.17), color=DARK))
    p.append(box((0.012, 0.05, 0.04), (0.327, 0.10, 0.17), color=(1, 0.97, 0.85),
                 rough=0.1, emis=(1, 0.93, 0.7)))
    p.append(box((0.05, 0.015, 0.06), (0.20, 0, 0.155), color=CHROME, metal=0.9))
    # grease nipples at the pivots, hose clamps, and a hazard stripe decal
    for x in (0.0, 0.62):
        for sy in (0.10, -0.10):
            p.append(ycyl(0.02, 0.010, (x, sy, 0.0), CHROME, 6, metal=0.9))
    for x in (0.16, 0.34, 0.52):
        p.append(box((0.018, 0.20, 0.018), (x, 0, -0.035), color=(0.30, 0.31, 0.33), metal=0.6))
    for i in range(4):
        p.append(box((0.045, 0.012, 0.055), (0.10 + i * 0.05, 0.081, 0.06),
                     color=CHAR if i % 2 else (0.95, 0.80, 0.05), rough=0.8))
    # bolts through the gusset plates
    for dy in (0.090, -0.090):
        for k in range(3):
            p.append(ycyl(0.016, 0.009, (0.27 + k * 0.05, dy, 0.10), CHROME, 6, metal=0.9))
    # pin retainer plates and their bolts
    for x in (0.0, 0.62):
        for dy in (0.100, -0.100):
            p.append(ycyl(0.012, 0.030, (x, dy, 0), (0.30, 0.31, 0.33), 10, metal=0.8))
            p.append(ycyl(0.018, 0.008, (x, dy, 0.038), CHROME, 6, metal=0.9))
    # ram gland nuts and hose fittings
    for dy in (0.10, -0.10):
        p.append(xcyl(0.022, 0.050, (0.345, dy, 0.135), (0.35, 0.36, 0.38), 10, metal=0.8))
        p.append(xcyl(0.018, 0.020, (0.05, dy, 0.14), (0.42, 0.43, 0.45), 8, metal=0.8))
    p.append(xcyl(0.024, 0.055, (0.575, 0, 0.157), (0.35, 0.36, 0.38), 10, metal=0.8))
    # weld bead strips along the bend
    for dy in (0.081, -0.081):
        p.append(box((0.12, 0.014, 0.014), (0.32, dy, 0.017), (0, 1, 0, 0.3),
                     color=(0.72, 0.54, 0.06), rough=0.9))
    return p


def stick():
    p = []
    p.append(box((0.40, 0.14, 0.16), (0.19, 0, 0.01), color=YEL, rough=0.7, metal=0.3))
    p.append(box((0.18, 0.10, 0.11), (0.46, 0, 0), color=YEL_D, rough=0.7, metal=0.3))
    for dy in (0.074, -0.074):
        p.append(box((0.34, 0.012, 0.13), (0.22, dy, 0.02), color=YEL_D, rough=0.75))
    p.append(ycyl(0.15, 0.055, (0, 0, 0), GREY, 20, metal=0.8, rough=0.6))
    p.append(ycyl(0.18, 0.028, (0, 0, 0), CHROME, 16, metal=0.9, rough=0.3))
    p.append(ycyl(0.13, 0.045, (0.52, 0, 0), GREY, 20, metal=0.8, rough=0.6))
    p.append(ycyl(0.16, 0.024, (0.52, 0, 0), CHROME, 16, metal=0.9, rough=0.3))
    # grapple ram + H-link
    p.append(strut((0.06, 0, 0.13), (0.30, 0, 0.11), 0.04, GREY, 16, metal=0.8, rough=0.5))
    p.append(strut((0.28, 0, 0.115), (0.44, 0, 0.08), 0.022, CHROME, 16, metal=1, rough=0.25))
    for dy in (0.055, -0.055):
        p.append(strut((0.44, dy, 0.08), (0.52, dy, 0.01), 0.016, GREY, 10, metal=0.7))
        p.append(strut((0.10, dy, -0.06), (0.48, dy, -0.03), 0.012, CHAR, 8, rough=0.9))
    p.append(box((0.20, 0.15, 0.012), (0.24, 0, -0.078), color=(0.30, 0.31, 0.33), metal=0.6))
    # wear pads, hose clamps, grease nipples, maker's plate
    for x in (0.14, 0.32):
        p.append(box((0.016, 0.16, 0.016), (x, 0, -0.072), color=(0.35, 0.36, 0.38), metal=0.6))
    for sy in (0.078, -0.078):
        p.append(ycyl(0.018, 0.009, (0.52, sy, 0), CHROME, 6, metal=0.9))
        p.append(ycyl(0.018, 0.009, (0, sy, 0), CHROME, 6, metal=0.9))
    p.append(box((0.07, 0.012, 0.04), (0.20, 0.072, 0.06), color=(0.72, 0.73, 0.75), metal=0.8))
    # gusset bolts
    for dy in (0.081, -0.081):
        for k in range(3):
            p.append(ycyl(0.016, 0.008, (0.10 + k * 0.10, dy, 0.02), CHROME, 6, metal=0.9))
    # pin retainers
    for x in (0.0, 0.52):
        for dy in (0.082, -0.082):
            p.append(ycyl(0.010, 0.026, (x, dy, 0), (0.30, 0.31, 0.33), 10, metal=0.8))
    # ram gland nut, hose fittings, wear strip bolts
    p.append(xcyl(0.020, 0.042, (0.305, 0, 0.112), (0.35, 0.36, 0.38), 10, metal=0.8))
    for dy in (0.075, -0.075):
        p.append(xcyl(0.016, 0.017, (0.09, dy, -0.058), (0.42, 0.43, 0.45), 8, metal=0.8))
        p.append(box((0.014, 0.014, 0.030), (0.24, dy * 0.75, -0.082),
                     color=CHROME, metal=0.9))
    return p



def tine(phi):
    """One grapple tine. Authored pointing along +x, then rotated to azimuth phi.

    The tooth (the fourth shape below) is load-bearing: its position and
    rotation match the tine's collision Group in excavator() exactly, and the
    whole grip depends on exactly where its tip ends up (see tools/tines.py).
    It is not moved here. Everything else is cosmetic and free to refine - the
    old single constant-width block is now two tapered segments with a visible
    knuckle between them, for a slimmer, more articulated look, and the pads
    nearest the tip are recoloured dark and rough to read as a grippy surface.
    """
    s = []
    # tapered upper body: wider at the hinge, narrower toward the tooth, both
    # segments sitting inside the same envelope the single old block used to
    s.append(box((0.044, 0.050, 0.075), (0, 0, -0.0375), color=ORANGE, rough=0.6, metal=0.45))
    s.append(box((0.036, 0.042, 0.075), (0, 0, -0.112), color=ORANGE, rough=0.6, metal=0.45))
    s.append(ycyl(0.052, 0.023, (0, 0, -0.075), color=(0.30, 0.31, 0.33), sub=12, metal=0.85))
    for dy in (-0.019, 0.019):
        s.append(ycyl(0.009, 0.028, (0, dy, -0.075), color=(0.45, 0.46, 0.48), sub=8, metal=0.85))
    s.append(box((0.011, 0.052, 0.11), (0.026, 0, -0.075),
                 color=(0.72, 0.28, 0.04), rough=0.7))
    # the tooth - LOAD-BEARING, matches the collision Group exactly
    s.append(pose(shape("Box {\n  size 0.045 0.050 0.135\n}",
                        (0.80, 0.33, 0.05), 0.65, 0.4),
                  (-0.020, 0, -0.198), (0, 1, 0, 0.24)))
    # grip pads at the tip: dark and rough rather than bare metal, so it
    # reads as a surface built to hold on rather than just clamp
    for dy in (-0.014, 0.014):
        s.append(box((0.030, 0.022, 0.055), (-0.046, dy, -0.262),
                     color=(0.14, 0.14, 0.15), rough=0.95, metal=0.05))
        s.append(xcyl(0.012, 0.006, (-0.030, dy, -0.238), CHROME, 6, metal=0.9))
    s.append(ycyl(0.058, 0.019, (0, 0, 0), (0.30, 0.31, 0.33), 10, metal=0.8))
    for dy in (0.030, -0.030):
        s.append(ycyl(0.009, 0.024, (0, dy, 0), (0.42, 0.43, 0.45), 8, metal=0.8))
    return [pose(s, (0, 0, 0), (0, 0, 1, phi))]


def grapple_visuals():
    """The rotating grapple head the tines hang from."""
    p = []
    p.append(vcyl(0.06, 0.075, (0, 0, 0.01), color=(0.35, 0.36, 0.38), sub=20, metal=0.85))
    p.append(vcyl(0.05, 0.095, (0, 0, -0.035), color=ORANGE, sub=20, rough=0.65, metal=0.4))
    p.append(vcyl(0.045, 0.115, (0, 0, -0.075), color=ORANGE, sub=20, rough=0.65, metal=0.4))
    p.append(vcyl(0.03, 0.060, (0, 0, -0.105), color=(0.35, 0.36, 0.38), sub=16, metal=0.8))
    for i in range(10):
        a = i * math.pi / 5
        p.append(vcyl(0.018, 0.009, (0.093 * math.cos(a), 0.093 * math.sin(a), -0.008),
                      color=CHROME, sub=6, metal=0.9, rough=0.3))
    # a ram and a hose per tine, angled out to the tine it drives - slimmer
    # than the collar itself, so the rams read as linkages rather than blocks
    for k in range(5):
        a = k * 2 * math.pi / 5
        c, s2 = math.cos(a), math.sin(a)
        p.append(strut((0.035 * c, 0.035 * s2, -0.020),
                       (0.080 * c, 0.080 * s2, -0.072), 0.016, GREY, 10, metal=0.8))
        p.append(strut((0.075 * c, 0.075 * s2, -0.068),
                       (0.104 * c, 0.104 * s2, -0.100), 0.011, CHROME, 8, metal=1, rough=0.25))
        p.append(strut((0.030 * c, 0.030 * s2, 0.030),
                       (0.068 * c, 0.068 * s2, -0.030), 0.008, CHAR, 6, rough=0.9))
    return p


def excavator():
    tines = ""
    for k in range(5):
        phi = k * 2 * math.pi / 5
        cx, cy = 0.105 * math.cos(phi), 0.105 * math.sin(phi)
        ax, ay = -math.sin(phi), math.cos(phi)
        tines += """
HingeJoint {
  jointParameters HingeJointParameters {
    axis %.6f %.6f 0
    anchor %.4f %.4f -0.08
    minStop -0.67
    maxStop 0
  }
  device [
    RotationalMotor {
      name "tine_%d_motor"
      maxVelocity 1.2
      maxTorque 10
      minPosition -0.62
      maxPosition -0.06
    }
    PositionSensor {
      name "tine_%d_sensor"
    }
  ]
  endPoint Solid {
    translation %.4f %.4f -0.08
    children [
%s
    ]
    name "tine_%d"
    contactMaterial "grip"
    boundingObject Group {
      children [
        Pose {
          translation 0 0 -0.075
          children [
            Box {
              size 0.05 0.055 0.15
            }
          ]
        }
        Pose {
          translation -0.020 0 -0.198
          rotation 0 1 0 0.24
          children [
            Box {
              size 0.045 0.050 0.135
            }
          ]
        }
        Pose {
          translation -0.046 0 -0.262
          children [
            Box {
              size 0.045 0.055 0.045
            }
          ]
        }
      ]
    }
    physics Physics {
      density -1
      mass 1.2
    }
  }
}""" % (ax, ay, cx, cy, k, k, cx, cy,
        "\n".join(indent(c, 6) for c in tine(phi)), k)

    # the grapple head, hanging from the rotator
    grapple_head = """
HingeJoint {
  jointParameters HingeJointParameters {
    axis 0 0 1
    anchor 0 0 -0.07
  }
  device [
    RotationalMotor {
      name "rotator_motor"
      maxVelocity 1.8
      maxTorque 300
    }
    PositionSensor {
      name "rotator_sensor"
    }
  ]
  endPoint DEF GRAPPLE Solid {
    translation 0 0 -0.07
    children [
%s
%s
    ]
    name "grapple"
    boundingObject Pose {
      translation 0 0 -0.05
      children [
        Box {
          size 0.23 0.23 0.16
        }
      ]
    }
    physics Physics {
      density -1
      mass 12
      damping Damping {
        linear 0.3
        angular 0.3
      }
    }
  }
}""" % ("\n".join(indent(c, 6) for c in grapple_visuals()), indent(tines, 6))

    # the wrist keeps the whole head plumb; the rotator spins it about vertical
    wrist_head = [
        vcyl(0.10, 0.075, (0, 0, -0.02), color=GREY, sub=20, metal=0.85, rough=0.5),
        box((0.17, 0.19, 0.08), (0, 0, 0.01), color=ORANGE, rough=0.65, metal=0.4),
        vcyl(0.035, 0.085, (0, 0, -0.055), color=(0.30, 0.31, 0.33), sub=20, metal=0.85),
        ycyl(0.20, 0.028, (0, 0, 0.03), CHROME, 12, metal=0.9, rough=0.3),
    ]
    for i in range(8):
        a = i * math.pi / 4
        wrist_head.append(vcyl(0.014, 0.008,
                               (0.062 * math.cos(a), 0.062 * math.sin(a), -0.072),
                               color=CHROME, sub=6, metal=0.9, rough=0.3))

    grapple = """
HingeJoint {
  jointParameters HingeJointParameters {
    axis 0 1 0
    anchor 0.52 0 0
    minStop -1.65
    maxStop 0.95
  }
  device [
    RotationalMotor {
      name "wrist_motor"
      maxVelocity 1.6
      maxTorque 600
      minPosition -1.6
      maxPosition 0.9
    }
    PositionSensor {
      name "wrist_sensor"
    }
  ]
  endPoint Solid {
    translation 0.52 0 0
    children [
%s
%s
    ]
    name "wrist_head"
    boundingObject Pose {
      translation 0 0 -0.02
      children [
        Box {
          size 0.17 0.19 0.14
        }
      ]
    }
    physics Physics {
      density -1
      mass 8
      damping Damping {
        linear 0.3
        angular 0.3
      }
    }
  }
}""" % ("\n".join(indent(c, 6) for c in wrist_head), indent(grapple_head, 6))

    stick_j = """
HingeJoint {
  jointParameters HingeJointParameters {
    axis 0 1 0
    anchor 0.62 0 0
    minStop 0
    maxStop 2.25
  }
  device [
    RotationalMotor {
      name "stick_motor"
      maxVelocity 1.1
      maxTorque 1800
      minPosition 0.2
      maxPosition 2.2
    }
    PositionSensor {
      name "stick_sensor"
    }
  ]
  endPoint Solid {
    translation 0.62 0 0
    children [
%s
%s
    ]
    name "stick"
    boundingObject Pose {
      translation 0.26 0 0.01
      children [
        Box {
          size 0.52 0.14 0.16
        }
      ]
    }
    physics Physics {
      density -1
      mass 30
      damping Damping {
        linear 0.3
        angular 0.3
      }
    }
  }
}""" % ("\n".join(indent(c, 6) for c in stick()), indent(grapple, 6))

    boom_j = """
HingeJoint {
  jointParameters HingeJointParameters {
    axis 0 1 0
    anchor 0.3 0 0.16
    minStop -1.45
    maxStop 0
  }
  device [
    RotationalMotor {
      name "boom_motor"
      maxVelocity 1
      maxTorque 3000
      minPosition -1.4
      maxPosition -0.1
    }
    PositionSensor {
      name "boom_sensor"
    }
  ]
  endPoint Solid {
    translation 0.3 0 0.16
    children [
%s
%s
    ]
    name "boom"
    boundingObject Pose {
      translation 0.31 0 0.05
      children [
        Box {
          size 0.62 0.16 0.16
        }
      ]
    }
    physics Physics {
      density -1
      mass 60
      damping Damping {
        linear 0.3
        angular 0.3
      }
    }
  }
}""" % ("\n".join(indent(c, 6) for c in boom()), indent(stick_j, 6))

    # Each camera sits in a flush-mounted pod - box, lens, hood, bolts - with
    # no gap to the hull behind it. They used to float free of the body by
    # 0.09-0.25 m (nothing connected them to anything), which read as a
    # random dark cube next to the machine while driving. The pod position
    # given here is the BACK of the housing, touching the hull; the lens
    # (and the Camera device itself) pokes 0.03 m further out, in whatever
    # direction that camera looks.
    # Every one of these was checked numerically (not by eye) against the
    # actual nearby hull geometry - see the mount face's worst-case gap in
    # tools/campod_check.py - so "flush" here means truly touching, not
    # eyeballed close.
    cam_rigs = [("camera_front_left", (0.34, 0.26, 0.30), 1, 1.1, None),
                ("camera_front_right", (0.30, -0.12, 0.17), 1, 1.1, None),
                ("camera_rear", (-0.70, 0.0, 0.30), -1, 1.2, (0, 0, 1, 3.141593))]
    cam_blocks = []
    for name, t, look, fov, rot in cam_rigs:
        hx = t[0] + look * 0.03
        cam_blocks += camera_pod(t, look)
        rot_line = ("\n  rotation %s" % " ".join("%.6f" % x for x in rot)) if rot else ""
        cam_blocks.append("""Camera {
  translation %.4f %.4f %.4f%s
  name "%s"
  fieldOfView %.1f
  width 160
  height 120
}""" % (hx, t[1], t[2], rot_line, name, fov))
    cams = "\n".join(cam_blocks)

    house_j = """
HingeJoint {
  jointParameters HingeJointParameters {
    axis 0 0 1
    anchor 0 0 0.34
  }
  device [
    RotationalMotor {
      name "slew_motor"
      maxVelocity 1.1
      maxTorque 4000
    }
    PositionSensor {
      name "slew_sensor"
    }
  ]
  endPoint Solid {
    translation 0 0 0.34
    children [
%s
%s
%s
    ]
    name "house"
    boundingObject Pose {
      translation -0.1 0 0.2
      children [
        Box {
          size 1.24 0.76 0.5
        }
      ]
    }
    physics Physics {
      density -1
      mass 300
      damping Damping {
        linear 0.4
        angular 0.4
      }
    }
  }
}""" % ("\n".join(indent(c, 6) for c in house()), indent(cams, 6), indent(boom_j, 6))


    # ---- driven wheels, hidden inside the track shells ----
    wheels = ""
    for nm, wx, wy in (("fl", 0.36, 0.30), ("fr", 0.36, -0.30),
                       ("rl", -0.36, 0.30), ("rr", -0.36, -0.30)):
        wheels += """
HingeJoint {
  jointParameters HingeJointParameters {
    axis 0 1 0
    anchor %.3f %.3f 0.13
  }
  device [
    RotationalMotor {
      name "wheel_%s_motor"
      maxVelocity 14
      maxTorque 2000
    }
    PositionSensor {
      name "wheel_%s_sensor"
    }
  ]
  endPoint Solid {
    translation %.3f %.3f 0.13
    rotation 1 0 0 1.5708
    children [
      Shape {
        appearance PBRAppearance {
          baseColor 0.14 0.14 0.15
          roughness 1
          metalness 0.2
        }
        geometry Cylinder {
          height 0.15
          radius 0.13
          subdivision 16
        }
      }
    ]
    name "wheel_%s"
    boundingObject Cylinder {
      height 0.15
      radius 0.13
      subdivision 16
    }
    physics Physics {
      density -1
      mass 18
    }
  }
}""" % (wx, wy, nm, nm, wx, wy, nm)

    return """DEF EXCAVATOR Robot {
  translation 0 0 0
  children [
%s
%s
%s
  ]
  name "excavator"
  boundingObject Group {
    children [
      Pose {
        translation 0 0.3 0.20
        children [
          Box {
            size 1.16 0.24 0.20
          }
        ]
      }
      Pose {
        translation 0 -0.3 0.20
        children [
          Box {
            size 1.16 0.24 0.20
          }
        ]
      }
      Pose {
        translation 0 0 0.25
        children [
          Box {
            size 0.72 0.46 0.18
          }
        ]
      }
    ]
  }
  physics Physics {
    density -1
    mass 650
    centerOfMass [
      -0.04 0 0.12
    ]
  }
  controller "excavator_controller"
  selfCollision TRUE
  supervisor TRUE
}""" % ("\n".join(indent(c, 4) for c in undercarriage()), indent(wheels, 4),
        indent(house_j, 4))



# ======================================================================
#  Background structures. Deliberately built from a few large forms
#  rather than lattice-work: at this distance only the silhouette reads,
#  and struts cost draw calls the graphics card cannot spare.
# ======================================================================
def skyline(t, size, h, yaw=0.0):
    p = [box((size[0], size[1], h), (0, 0, h / 2), color=(0.60, 0.59, 0.58), rough=1)]
    for f in range(1, int(h / 1.6)):
        p.append(box((size[0] + 0.08, size[1] + 0.08, 0.10), (0, 0, f * 1.6),
                     color=(0.50, 0.49, 0.48), rough=1))
    for f in range(int(h / 1.6)):
        p.append(box((size[0] + 0.06, size[1] * 0.55, 0.55), (0, 0, f * 1.6 + 0.85),
                     color=(0.28, 0.32, 0.38), rough=0.4))
    return group(p, t, yaw)


def crane(t, yaw=0.0):
    H, JIB = 11.0, 8.5
    p = [box((0.55, 0.55, H), (0, 0, H / 2), color=YEL, rough=0.7, metal=0.4),
         box((0.75, 0.75, 0.25), (0, 0, 0.12), color=(0.55, 0.55, 0.56), rough=1)]
    for i in range(6):
        p.append(box((0.62, 0.62, 0.10), (0, 0, 0.9 + i * 1.75), color=YEL_D, rough=0.7))
    p.append(box((0.95, 0.95, 0.70), (0, 0, H + 0.35), color=YEL, rough=0.7, metal=0.4))
    p.append(box((0.60, 0.66, 0.55), (0.72, 0, H + 0.75), color=(0.25, 0.28, 0.33)))
    p.append(box((JIB, 0.42, 0.42), (JIB / 2 - 0.4, 0, H + 0.9), color=YEL, rough=0.7, metal=0.4))
    p.append(box((3.0, 0.40, 0.40), (-1.9, 0, H + 0.9), color=YEL, rough=0.7, metal=0.4))
    p.append(box((0.9, 0.55, 0.45), (-3.1, 0, H + 0.9), color=(0.38, 0.39, 0.41)))
    p.append(box((0.35, 0.35, 1.7), (0, 0, H + 1.6), color=YEL_D, rough=0.7))
    p.append(strut((0, 0, H + 2.4), (JIB - 0.6, 0, H + 1.05), 0.035, (0.35, 0.36, 0.38), 6))
    p.append(strut((0, 0, H + 2.4), (-3.0, 0, H + 1.05), 0.035, (0.35, 0.36, 0.38), 6))
    p.append(box((0.45, 0.45, 0.30), (5.4, 0, H + 0.65), color=(0.35, 0.36, 0.38)))
    p.append(strut((5.4, 0, H + 0.55), (5.4, 0, H - 3.2), 0.022, (0.30, 0.31, 0.33), 6))
    p.append(box((0.55, 0.55, 0.45), (5.4, 0, H - 3.45), color=(0.85, 0.62, 0.08)))
    return group(p, t, yaw)


def frame_building(t, yaw=0.0):
    p = []
    for i in range(3):
        for j in range(3):
            p.append(box((0.30, 0.30, 6.4), (i * 2.6, j * 2.6, 3.2),
                         color=(0.68, 0.67, 0.65), rough=1))
    for f in range(1, 4):
        p.append(box((5.7, 5.7, 0.22), (2.6, 2.6, f * 2.1), color=(0.72, 0.71, 0.69), rough=1))
    p.append(box((5.7, 0.22, 1.5), (2.6, 5.3, 3.2), color=(0.66, 0.65, 0.63), rough=1))
    p.append(box((0.22, 5.7, 1.5), (5.3, 2.6, 5.3), color=(0.66, 0.65, 0.63), rough=1))
    for k in range(4):
        p.append(box((0.06, 0.06, 1.1), (0.6 + k * 1.5, 5.3, 6.9),
                     color=(0.45, 0.35, 0.25), rough=1))
    return group(p, t, yaw)


def scaffold_wall(t, yaw=0.0):
    p = []
    for i in range(5):
        p.append(strut((i * 1.3, 0, 0), (i * 1.3, 0, 6.2), 0.05, (0.62, 0.64, 0.66), 6))
        p.append(strut((i * 1.3, 0.9, 0), (i * 1.3, 0.9, 6.2), 0.05, (0.62, 0.64, 0.66), 6))
    for lv in range(1, 4):
        z = lv * 2.0
        p.append(strut((0, 0, z), (5.2, 0, z), 0.045, (0.62, 0.64, 0.66), 6))
        p.append(strut((0, 0.9, z), (5.2, 0.9, z), 0.045, (0.62, 0.64, 0.66), 6))
        p.append(box((5.2, 0.85, 0.05), (2.6, 0.45, z + 0.04), color=(0.55, 0.42, 0.26), rough=1))
        p.append(box((5.2, 0.05, 0.35), (2.6, 0.0, z + 0.35), color=(0.55, 0.42, 0.26), rough=1))
    p.append(box((5.4, 0.06, 6.0), (2.6, 0.95, 3.1), color=(0.55, 0.58, 0.55),
                 rough=0.95))
    return group(p, t, yaw)


def silo2(t):
    p = [vcyl(3.0, 0.75, (0, 0, 3.3), color=(0.82, 0.83, 0.84), sub=16, rough=0.7, metal=0.5),
         ucone(0.8, 0.75, (0, 0, 4.8), color=(0.75, 0.76, 0.78), sub=16, rough=0.7, metal=0.5),
         cone(1.0, 0.75, (0, 0, 1.3), (1, 0, 0, 3.141593), (0.78, 0.79, 0.80), 16,
              rough=0.7, metal=0.5),
         vcyl(0.30, 0.16, (0, 0, 0.75), color=(0.45, 0.46, 0.48), sub=12, metal=0.6)]
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        p.append(strut((1.0 * math.cos(a), 1.0 * math.sin(a), 0),
                       (0.55 * math.cos(a), 0.55 * math.sin(a), 1.9), 0.07,
                       (0.55, 0.56, 0.58), 8, metal=0.6))
    # a caged ladder up the side, a platform ring below the dome, and a
    # fill-pipe elbow at the top - the plainest of the shared structures
    # before this, so it's the one that gets the detail pass
    for z in [0.5 + 0.7 * i for i in range(6)]:
        p.append(strut((0.76, -0.18, z), (0.76, 0.18, z), 0.018, CHAR, 6))
    for dy in (-0.18, 0.18):
        p.append(strut((0.76, dy, 0.3), (0.76, dy, 4.4), 0.020, (0.35, 0.36, 0.38), 6))
    p.append(vcyl(0.10, 0.82, (0, 0, 4.65), color=(0.45, 0.46, 0.48), sub=14, metal=0.6))
    p.append(xcyl(0.5, 0.05, (0.3, 0, 5.55), color=(0.45, 0.46, 0.48), sub=8, metal=0.5))
    p.append(vcyl(0.4, 0.05, (0.55, 0, 5.35), color=(0.45, 0.46, 0.48), sub=8, metal=0.5))
    return group(p, t)

# ======================================================================
#  SCENERY
# ======================================================================
def traffic_cone(t):
    """A proper traffic cone: black base, orange body, white reflective band.

    The band is made by stacking three cones, each slightly wider than the one
    it covers, so the white ring follows the taper instead of being a collar
    stuck around it.
    """
    ORG = (0.93, 0.30, 0.03)
    S = 0.55        # the machine is ~1:2.5 scale, so cones scale to match it
    return group([
        box((0.34 * S, 0.34 * S, 0.025 * S), (0, 0, 0.0125 * S),
            color=(0.11, 0.11, 0.12), rough=0.9),
        ucone(0.55 * S, 0.150 * S, (0, 0, 0.025 * S), color=ORG, rough=0.55, sub=20),
        ucone(0.365 * S, 0.105 * S, (0, 0, 0.210 * S), color=(0.96, 0.96, 0.94),
              rough=0.35, sub=20),
        ucone(0.250 * S, 0.076 * S, (0, 0, 0.330 * S), color=ORG, rough=0.55, sub=20),
    ], t)


def barrier(t, yaw=0.0):
    return group([box((1.6, 0.42, 0.16), (0, 0, 0.08), color=CONC, rough=0.95),
                  box((1.6, 0.24, 0.24), (0, 0, 0.30), color=(0.70, 0.69, 0.66), rough=0.95),
                  box((1.62, 0.30, 0.06), (0, 0, 0.45), color=(0.62, 0.61, 0.58), rough=0.95),
                  box((0.30, 0.26, 0.10), (0.45, 0, 0.30), color=(0.95, 0.5, 0.05), rough=0.9),
                  box((0.30, 0.26, 0.10), (-0.45, 0, 0.30), color=(0.95, 0.5, 0.05), rough=0.9)],
                 t, yaw)


def drum(t, color=(0.20, 0.45, 0.25)):
    return group([vcyl(0.58, 0.17, (0, 0, 0.29), color=color, sub=20, rough=0.6, metal=0.4),
                  vcyl(0.04, 0.18, (0, 0, 0.16), color=color, sub=20, metal=0.5),
                  vcyl(0.04, 0.18, (0, 0, 0.42), color=color, sub=20, metal=0.5),
                  vcyl(0.02, 0.16, (0, 0, 0.585), color=(0.35, 0.36, 0.38), sub=20, metal=0.6)], t)


def dump_truck(t, yaw=0.0):
    p = []
    p.append(box((5.2, 2.2, 0.35), (0, 0, 0.95), color=(0.25, 0.26, 0.28), metal=0.5))
    p.append(box((1.9, 2.3, 1.5), (1.7, 0, 1.75), color=(0.85, 0.25, 0.10), rough=0.6, metal=0.4))
    p.append(box((0.08, 1.9, 0.75), (2.62, 0, 2.05), color=GLASS, rough=0.15))
    p.append(box((3.2, 2.4, 1.1), (-1.1, 0, 1.7), color=(0.85, 0.25, 0.10), rough=0.6, metal=0.4))
    p.append(box((3.2, 2.5, 0.12), (-1.1, 0, 1.2), color=(0.35, 0.30, 0.26), rough=0.9))
    p.append(box((0.12, 2.4, 1.1), (-2.7, 0, 1.75), color=(0.75, 0.22, 0.09), rough=0.6))
    p.append(cone(0.55, 0.95, (-1.1, 0, 1.78), color=(0.42, 0.34, 0.25)))
    for x in (1.7, -0.6, -1.7):
        for sy in (1, -1):
            p.append(ycyl(0.42, 0.55, (x, 1.05 * sy, 0.55), color=(0.09, 0.09, 0.10), sub=24, rough=1))
            p.append(ycyl(0.44, 0.24, (x, 1.05 * sy, 0.55), color=(0.55, 0.56, 0.58), sub=20, metal=0.7))
    p.append(box((0.3, 0.3, 0.5), (2.4, 1.05, 2.7), color=(0.30, 0.31, 0.33)))
    return group(p, t, yaw)


def silo(t):
    p = [vcyl(3.2, 1.05, (0, 0, 3.4), color=(0.82, 0.83, 0.84), sub=24, rough=0.7, metal=0.5),
         cone(1.1, 1.05, (0, 0, 4.0), color=(0.75, 0.76, 0.78), rough=0.7, metal=0.5),
         cone(1.3, 1.05, (0, 0, 1.8), rot=(1, 0, 0, -1.5708), color=(0.78, 0.79, 0.80),
              rough=0.7, metal=0.5)]
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        p.append(strut((1.4 * math.cos(a), 1.4 * math.sin(a), 0),
                       (0.75 * math.cos(a), 0.75 * math.sin(a), 1.9), 0.09,
                       (0.55, 0.56, 0.58), 10, metal=0.6))
    return group(p, t)


def scaffold(t, bays=4, levels=3, yaw=0.0):
    p = []
    for i in range(bays + 1):
        x = i * 1.6
        for dy in (0, 1.2):
            p.append(strut((x, dy, 0), (x, dy, levels * 1.7), 0.045, (0.60, 0.62, 0.64), 8,
                           metal=0.7))
    for lv in range(1, levels + 1):
        z = lv * 1.7
        for dy in (0, 1.2):
            p.append(strut((0, dy, z), (bays * 1.6, dy, z), 0.04, (0.60, 0.62, 0.64), 8, metal=0.7))
        for i in range(bays + 1):
            p.append(strut((i * 1.6, 0, z), (i * 1.6, 1.2, z), 0.04, (0.60, 0.62, 0.64), 8,
                           metal=0.7))
        for i in range(bays):
            p.append(strut((i * 1.6, 0, z - 1.7), ((i + 1) * 1.6, 0, z), 0.032,
                           (0.55, 0.57, 0.59), 8, metal=0.7))
        p.append(box((bays * 1.6, 1.1, 0.05), (bays * 0.8, 0.6, z + 0.03),
                     color=(0.55, 0.42, 0.26), rough=1))
    return group(p, t, yaw)


def building_frame(t, nx=4, ny=3, floors=3, yaw=0.0):
    p = []
    for i in range(nx):
        for j in range(ny):
            p.append(box((0.36, 0.36, floors * 3.2), (i * 3.4, j * 3.4, floors * 1.6),
                         color=(0.68, 0.67, 0.65), rough=1))
    for f in range(1, floors + 1):
        z = f * 3.2
        p.append(box(((nx - 1) * 3.4 + 0.8, (ny - 1) * 3.4 + 0.8, 0.26),
                     ((nx - 1) * 1.7, (ny - 1) * 1.7, z), color=(0.72, 0.71, 0.69), rough=1))
        for i in range(nx):
            p.append(box((0.26, (ny - 1) * 3.4, 0.5), (i * 3.4, (ny - 1) * 1.7, z - 0.35),
                         color=(0.64, 0.63, 0.61), rough=1))
    return group(p, t, yaw)


def tower_crane(t, yaw=0.0):
    p = []
    H = 24.0
    for dx, dy in ((-0.7, -0.7), (0.7, -0.7), (0.7, 0.7), (-0.7, 0.7)):
        p.append(strut((dx, dy, 0), (dx, dy, H), 0.13, YEL, 8, metal=0.5))
    for i in range(int(H / 2.4)):
        z = i * 2.4
        for a, b in (((-0.7, -0.7), (0.7, -0.7)), ((0.7, -0.7), (0.7, 0.7)),
                     ((0.7, 0.7), (-0.7, 0.7)), ((-0.7, 0.7), (-0.7, -0.7))):
            p.append(strut((a[0], a[1], z), (b[0], b[1], z), 0.06, YEL_D, 6, metal=0.5))
            p.append(strut((a[0], a[1], z), (b[0], b[1], z + 2.4), 0.05, YEL_D, 6, metal=0.5))
    p.append(box((2.2, 2.2, 1.6), (0, 0, H + 0.8), color=YEL, rough=0.7, metal=0.4))
    p.append(box((1.3, 1.4, 1.3), (1.4, 0, H + 1.6), color=(0.30, 0.31, 0.33)))
    for dy in (-0.45, 0.45):
        p.append(strut((-1, dy, H + 1.6), (17, dy, H + 1.6), 0.13, YEL, 8, metal=0.5))
        p.append(strut((-1, dy, H + 2.6), (-7, dy, H + 2.6), 0.11, YEL, 8, metal=0.5))
        p.append(strut((-1, dy, H + 1.6), (-7, dy, H + 1.6), 0.11, YEL, 8, metal=0.5))
    for i in range(0, 17, 2):
        p.append(strut((i, -0.45, H + 1.6), (i + 2, 0.45, H + 1.6), 0.05, YEL_D, 6, metal=0.5))
        p.append(strut((i, -0.45, H + 1.6), (i, 0.45, H + 1.6), 0.05, YEL_D, 6, metal=0.5))
    p.append(strut((0, 0, H + 5.5), (16, 0, H + 1.8), 0.05, (0.35, 0.36, 0.38), 6, metal=0.8))
    p.append(strut((0, 0, H + 5.5), (-6.5, 0, H + 2.4), 0.05, (0.35, 0.36, 0.38), 6, metal=0.8))
    p.append(box((1.2, 1.6, 4.2), (0, 0, H + 3.7), color=YEL_D, rough=0.7, metal=0.4))
    p.append(box((2.6, 1.6, 0.9), (-6.4, 0, H + 1.9), color=(0.40, 0.41, 0.43)))
    p.append(strut((12, 0, H + 1.5), (12, 0, H - 6), 0.03, (0.30, 0.31, 0.33), 6, metal=0.9))
    p.append(box((0.7, 0.7, 0.9), (12, 0, H - 6.5), color=(0.35, 0.36, 0.38), metal=0.7))
    return group(p, t, yaw)


def pylon(t, h=9.0):
    """A lattice power pylon: four splayed legs and three crossarms."""
    p = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(strut((sx * 0.9, sy * 0.9, 0), (sx * 0.22, sy * 0.22, h),
                           0.10, (0.45, 0.46, 0.48), 6))
    for z, w in ((h * 0.55, 2.6), (h * 0.76, 2.2), (h * 0.93, 1.6)):
        p.append(box((0.20, 2 * w, 0.18), (0, 0, z), color=(0.45, 0.46, 0.48)))
        for sy in (-1, 1):
            p.append(vcyl(0.55, 0.05, (0, sy * w * 0.9, z + 0.30),
                          color=(0.28, 0.29, 0.31), sub=6))
    p.append(box((0.55, 0.55, 0.45), (0, 0, h + 0.22), color=(0.45, 0.46, 0.48)))
    return group(p, t)


def tree(t, h=3.4, r=1.4, leaf=(0.22, 0.36, 0.16)):
    """A root flare, a tapered two-piece trunk, and three foliage tiers
    shading from a dark undertone to a sun-catching highlight, rather than one
    flat colour - reads far better at a distance than a uniform green cone."""
    dark = mix(leaf, (0.05, 0.09, 0.03), 0.4)
    light = mix(leaf, (0.68, 0.66, 0.34), 0.30)
    trunk_h = h * 0.5
    return group([
        ucone(0.10, 0.20, (0, 0, 0), color=(0.22, 0.16, 0.11), sub=8, rough=1),
        vcyl(trunk_h * 0.60, 0.150, (0, 0, trunk_h * 0.30), color=(0.28, 0.20, 0.13),
             sub=8, rough=1),
        vcyl(trunk_h * 0.44, 0.095, (0, 0, trunk_h * 0.82), color=(0.25, 0.18, 0.12),
             sub=8, rough=1),
        ucone(h * 0.42, r, (0, 0, h * 0.20), color=dark, sub=10, rough=1),
        ucone(h * 0.46, r * 0.78, (0, 0, h * 0.42), color=leaf, sub=10, rough=1),
        ucone(h * 0.40, r * 0.52, (0, 0, h * 0.66), color=light, sub=10, rough=1),
    ], t)


def van(t, yaw=0.0, body=(0.86, 0.87, 0.88)):
    return group([box((4.6, 2.0, 1.5), (0, 0, 1.15), color=body, rough=0.5, metal=0.3),
                  box((1.7, 2.0, 0.95), (1.65, 0, 2.08), color=body, rough=0.5,
                      metal=0.3),
                  box((0.10, 1.8, 0.6), (2.52, 0, 2.14), color=GLASS, rough=0.15),
                  box((4.8, 2.1, 0.28), (0, 0, 0.5), color=(0.24, 0.25, 0.27))] +
                 [ycyl(0.36, 0.45, (dx, dy, 0.45), CHAR, 12)
                  for dx in (1.5, -1.5) for dy in (1.05, -1.05)], t, yaw)


def conveyor(t, yaw=0.0, length=9.0, rise=4.2):
    """A long inclined belt feeding a stockpile - reads well at a distance."""
    p = [box((length, 1.0, 0.22), (length / 2, 0, rise / 2), (0, 1, 0, -rise / length),
             color=(0.55, 0.45, 0.10), rough=0.8),
         box((length, 0.10, 0.30), (length / 2, 0.52, rise / 2),
             (0, 1, 0, -rise / length), color=(0.40, 0.33, 0.08), rough=0.85),
         box((length, 0.10, 0.30), (length / 2, -0.52, rise / 2),
             (0, 1, 0, -rise / length), color=(0.40, 0.33, 0.08), rough=0.85),
         box((1.6, 1.6, 0.5), (0, 0, 0.25), color=(0.35, 0.36, 0.38)),
         strut((length * 0.55, 0, 0), (length * 0.55, 0, rise * 0.62), 0.12, STEEL, 8),
         strut((length * 0.85, 0, 0), (length * 0.85, 0, rise * 0.92), 0.12, STEEL, 8),
         ucone(rise * 0.9, 3.4, (length + 1.6, 0, 0), color=(0.44, 0.36, 0.26), sub=14)]
    return group(p, t, yaw)


def scenery(full=True):
    p = []
    # ---- ground wear, puddles, spoil ----
    p.append(box((7.0, 5.4, 0.0008), (1.8, 0.2, 0.0006), color=(0.36, 0.29, 0.22), rough=1))
    p.append(box((7.2, 3.4, 0.0008), (-3.0, -2.2, 0.0018), (0, 0, 1, 0.4),
                 color=(0.38, 0.31, 0.24), rough=1))
    p.append(box((4.6, 1.3, 0.0008), (4.6, -3.6, 0.0030), (0, 0, 1, -0.3),
                 color=(0.33, 0.27, 0.20), rough=1))
    p.append(box((6.2, 1.3, 0.0008), (-4.2, 4.8, 0.0042), (0, 0, 1, 0.25),
                 color=(0.20, 0.16, 0.12), rough=1))
    for t, s in (((3.4, -1.8), 0.7), ((-2.4, 3.0), 0.5), ((5.2, 1.4), 0.6)):
        p.append(box((s * 1.6, s, 0.0008), (t[0], t[1], 0.0054), color=(0.24, 0.24, 0.22),
                     rough=0.1, metal=0.3))

    for _, x, y, _, _, dims, _, c in props_of("pile", full):
        p.append(ucone(dims[1], dims[0], (x, y, 0), color=c))
        p += pile_chunks(x, y, dims[0], dims[1], c)
    # ---- cones, barriers ----
    for _, x, y, _, _, _, _, _ in props_of("cone", full):
        p.append(traffic_cone((x, y, 0)))
    for _, x, y, yaw, _, _, _, _ in props_of("barrier", full):
        p.append(barrier((x, y, 0), yaw))
    # ---- container, office, toilet, generator ----
    for _, x, y, yaw, _, _, _, _ in props_of("container", full):
        p.append(group([box((3.0, 1.2, 1.24), (0, 0, 0.62), color=(0.55, 0.18, 0.13),
                            rough=0.75, metal=0.35)] +
                       [box((0.05, 1.22, 1.1), (-1.4 + i * 0.28, 0, 0.62),
                            color=(0.48, 0.15, 0.11), rough=0.75, metal=0.35)
                        for i in range(11)] +
                       [box((0.06, 1.16, 1.2), (1.52, 0, 0.62), color=(0.42, 0.14, 0.10),
                            rough=0.75, metal=0.4),
                        box((0.03, 0.08, 0.9), (1.56, 0.25, 0.62), color=CHROME, metal=0.9),
                        box((0.03, 0.08, 0.9), (1.56, -0.25, 0.62), color=CHROME, metal=0.9)],
                       (x, y, 0), yaw))
    # ---- home pads + tower pad (always present) ----
    # each layer sits proud of the one below so no two faces share a plane
    for colour in COLOURS:
        x, y = HOMES[colour]
        p.append(box((0.34, 0.34, 0.0012), (x, y, 0.0072), color=(0.92, 0.92, 0.90),
                     rough=0.9))
        p.append(box((0.26, 0.26, 0.0012), (x, y, 0.0090), color=CUBE_COLOURS[colour],
                     rough=0.9))
    for tx, ty in TOWERS:
        p.append(box((0.36, 0.36, 0.0012), (tx, ty, 0.0072), color=(0.92, 0.92, 0.90),
                     rough=0.9))
        p.append(box((0.28, 0.28, 0.0012), (tx, ty, 0.0090), color=(0.30, 0.30, 0.30),
                     rough=0.9))

    # ---- distant skyline and hills (cheap, and they keep the horizon alive) ----
    for t2, s2, h2, y2 in (((24.0, 8.0), (6.5, 6.0), 9.0, -0.4),
                           ((-11.0, 23.0), (7.0, 5.0), 6.0, 0.7),
                           ((15.0, -19.5), (6.0, 6.5), 7.5, 0.15),
                           ((15.5, -12.0), (5.5, 5.5), 6.4, 0.2),
                           ((18.5, 4.0), (5.0, 7.5), 4.8, -0.3),
                           ((-18.0, -17.0), (7.0, 5.0), 5.6, 0.5),
                           ((1.0, 19.0), (8.5, 4.5), 8.0, 0.0),
                           ((-20.0, 4.0), (5.5, 6.5), 7.2, 0.4),
                           ((9.0, 17.0), (6.0, 6.0), 5.0, 1.1)):
        p.append(skyline((t2[0], t2[1], 0), s2, h2, y2))
    for t2, r2, h2 in (((-24, 16), 5.0, 2.6), ((22, -20), 6.5, 3.2), ((-6, 24), 5.5, 2.2),
                       ((0, -27), 6.2, 3.0), ((27, 11), 5.6, 2.8), ((-27, -8), 6.0, 2.4)):
        p.append(ucone(h2, r2, (t2[0], t2[1], -0.3), color=(0.46, 0.42, 0.33), sub=14))

    # ---- perimeter fence ----
    # In every world, not just the full one: the site is meant to be
    # somewhere the machine cannot leave, and the lite world had no
    # boundary at all.
    #
    # These panels are OPAQUE on purpose. They used to be transparency 0.5,
    # and four 16 m alpha-blended surfaces ring the whole site, so the camera
    # looks through at least one of them from almost any angle. That is a lot
    # of blending to do every frame and it was the difference between the world
    # that drew and the world that came up black. Nothing else in either world
    # is see-through now either.
    span = 2 * FENCE
    for sgn in (1, -1):
        p.append(box((span, 0.03, 1.15), (0, FENCE * sgn, 0.63), color=(0.95, 0.45, 0.05),
                     rough=0.9))
        p.append(box((span, 0.05, 0.06), (0, FENCE * sgn, 1.20), color=(0.85, 0.40, 0.04),
                     rough=0.9))
        p.append(box((0.03, span, 1.15), (FENCE * sgn, 0, 0.63), color=(0.95, 0.45, 0.05),
                     rough=0.9))
        p.append(box((0.05, span, 0.06), (FENCE * sgn, 0, 1.20), color=(0.85, 0.40, 0.04),
                     rough=0.9))
        for i in range(6):
            k = -FENCE + FENCE * 2 * (i + 1) / 7.0
            p.append(vcyl(1.30, 0.04, (k, FENCE * sgn, 0.65), color=(0.45, 0.46, 0.48),
                          sub=8, metal=0.5))
            p.append(vcyl(1.30, 0.04, (FENCE * sgn, k, 0.65), color=(0.45, 0.46, 0.48),
                          sub=8, metal=0.5))
        p.append(vcyl(1.30, 0.045, (FENCE * sgn, FENCE, 0.65), color=(0.45, 0.46, 0.48),
                      sub=8, metal=0.5))
        p.append(vcyl(1.30, 0.045, (FENCE * sgn, -FENCE, 0.65), color=(0.45, 0.46, 0.48),
                      sub=8, metal=0.5))

    # ---- distant background structures ----
    # Cheap ones (silhouette-only, no lattice) go in every world so the lite
    # world - the one that actually renders on weaker graphics cards - is not
    # bare beyond the fence. The four heaviest assemblies (both cranes, the
    # frame building, the dump truck: 99 shapes between them) stay full-only.
    # worn ground under the structures that get walked/driven round in real
    # use, so they read as used rather than freshly placed
    p.append(box((2.6, 2.0, 0.0008), (-9.5, 5.2, 0.0024), color=(0.36, 0.34, 0.30), rough=1))
    p.append(box((3.0, 2.2, 0.0008), (10.5, 6.0, 0.0024), (0, 0, 1, 0.35),
                 color=(0.34, 0.30, 0.24), rough=1))
    p.append(pylon((-13.0, -2.0, 0), 9.5))
    p.append(pylon((-14.5, 5.2, 0), 8.6))
    # yaw 2.5 used to send the belt's incline back across the fence corner -
    # its centreline dipped inside by 0.02 m at one point, which is exactly
    # the sliver visible in a render. This placement was checked (not just
    # eyeballed) to clear the fence by >=1.3 m along its whole length,
    # including the belt's own width, not just its centreline.
    p.append(conveyor((10.0, 6.3, 0), 0.25))
    p.append(silo2((-9.5, 5.2, 0)))
    for t, h, r, leaf in (((11.6, -2.2), 3.6, 1.5, (0.20, 0.34, 0.15)),
                          ((12.4, 0.6), 3.1, 1.3, (0.24, 0.38, 0.17)),
                          ((11.9, 3.4), 3.9, 1.6, (0.19, 0.32, 0.14)),
                          ((13.1, -5.0), 3.3, 1.4, (0.23, 0.37, 0.16)),
                          ((2.5, -12.4), 3.7, 1.5, (0.21, 0.35, 0.15)),
                          ((5.6, -12.9), 3.2, 1.3, (0.24, 0.38, 0.17)),
                          ((-1.8, -12.6), 4.0, 1.7, (0.19, 0.33, 0.14)),
                          ((-5.2, -13.2), 3.4, 1.4, (0.22, 0.36, 0.16))):
        p.append(tree((t[0], t[1], 0), h, r, leaf))

    if not full:
        return p

    for _, x, y, yaw, _, _, _, _ in props_of("office", full):
        p.append(group([box((3.2, 2.2, 1.26), (0, 0, 0.63), color=(0.86, 0.87, 0.85), rough=0.8),
                        box((3.35, 2.35, 0.1), (0, 0, 1.3), color=(0.45, 0.46, 0.48), rough=0.85),
                        # the window and the door stand at slightly different
                        # depths in the wall, so no two faces share a plane
                        box((0.06, 1.5, 0.55), (1.630, 0.2, 0.75), color=GLASS, rough=0.2),
                        box((0.05, 0.7, 1.05), (1.622, -0.7, 0.55),
                            color=(0.55, 0.56, 0.58)),
                        box((0.05, 0.06, 0.1), (1.68, -0.42, 0.6), color=CHROME, metal=0.9),
                        box((1.0, 0.5, 0.12), (1.9, -0.7, 0.06), color=(0.45, 0.46, 0.48)),
                        strut((1.62, 0.9, 0), (1.62, 0.9, 1.3), 0.04, (0.5, 0.5, 0.52), 8)],
                       (x, y, 0), yaw))
    for _, x, y, yaw, _, _, _, _ in props_of("toilet", full):
        p.append(group([box((0.46, 0.46, 1.02), (0, 0, 0.51), color=(0.18, 0.42, 0.65),
                            rough=0.7),
                        box((0.50, 0.50, 0.05), (0, 0, 1.05), color=(0.14, 0.34, 0.52)),
                        box((0.02, 0.26, 0.76), (0.235, 0, 0.50), color=(0.14, 0.34, 0.52)),
                        box((0.02, 0.05, 0.05), (0.25, 0.09, 0.55), color=(0.75, 0.76, 0.78))],
                       (x, y, 0), yaw))
    for _, x, y, yaw, _, _, _, _ in props_of("generator", full):
        p.append(group([box((1.5, 0.9, 0.9), (0, 0, 0.45), color=(0.85, 0.62, 0.08), rough=0.7),
                        box((1.55, 0.95, 0.1), (0, 0, 0.92), color=(0.70, 0.51, 0.06)),
                        vcyl(0.3, 0.06, (-0.6, 0.3, 1.05), color=DARK)],
                       (x, y, 0), yaw))
    # ---- materials ----
    for _, x, y, yaw, _, _, _, bh in props_of("bricks", full):
        stack = [box((1.0, 0.8, 0.12), (0, 0, 0.06), color=(0.55, 0.42, 0.26), rough=1),
                 box((0.9, 0.7, bh), (0, 0, 0.12 + bh / 2), color=(0.60, 0.31, 0.22), rough=1)]
        if bh > 0.45:
            stack.append(box((0.9, 0.7, 0.06), (0, 0, 0.12 + bh + 0.03),
                             color=(0.62, 0.62, 0.65)))
        p.append(group(stack, (x, y, 0), yaw))
    for _, x, y, yaw, _, _, _, _ in props_of("timber", full):
        for i in range(3):
            p.append(box((2.6, 0.9, 0.14), (x + 0.05 * i, y, 0.07 + i * 0.16),
                         (0, 0, 1, yaw), color=(0.62, 0.48, 0.30), rough=1))
    for _, x, y, _, _, _, _, _ in props_of("pipes", full):
        for py, pz in ((y + 0.25, 0.22), (y - 0.25, 0.22), (y, 0.60)):
            p.append(xcyl(1.5, 0.24, (x, py, pz), (0.63, 0.62, 0.60), 20, rough=0.95))
            p.append(xcyl(1.52, 0.13, (x, py, pz), (0.40, 0.39, 0.38), 20, rough=1))
    for _, x, y, yaw, _, _, _, _ in props_of("rebar", full):
        p.append(box((3.4, 0.5, 0.1), (x, y, 0.05), (0, 0, 1, yaw),
                     color=(0.42, 0.30, 0.20), rough=0.9, metal=0.5))
    for _, x, y, _, _, _, _, _ in props_of("drums", full):
        for i, (dx, dy) in enumerate(((-0.25, 0.15), (0.25, 0.10), (0.0, -0.30))):
            p.append(drum((x + dx, y + dy, 0),
                          (0.20, 0.45, 0.25) if i % 2 else (0.55, 0.35, 0.10)))
    # wheelbarrow
    for _, x, y, yaw, _, _, _, _ in props_of("barrow", full):
        p.append(group([box((0.75, 0.5, 0.22), (0, 0, 0.42), (0, 1, 0, 0.15),
                            color=(0.35, 0.36, 0.38), metal=0.5),
                        ycyl(0.09, 0.16, (0.45, 0, 0.16), color=CHAR, sub=16),
                        strut((-0.35, 0.2, 0.3), (0.3, 0.2, 0.45), 0.02, (0.5, 0.5, 0.52), 8),
                        strut((-0.35, -0.2, 0.3), (0.3, -0.2, 0.45), 0.02, (0.5, 0.5, 0.52), 8)],
                       (x, y, 0), yaw))
    # ---- floodlight mast + signs ----
    for _, x, y, _, _, _, _, _ in props_of("mast", full):
        p.append(group([box((0.8, 0.8, 0.12), (0, 0, 0.06), color=(0.35, 0.36, 0.38)),
                        vcyl(4.0, 0.08, (0, 0, 2.0), color=(0.85, 0.62, 0.08), sub=12, metal=0.5),
                        box((0.5, 0.9, 0.28), (0, 0, 4.05), color=(0.30, 0.31, 0.33)),
                        box((0.06, 0.8, 0.22), (0.26, 0, 4.05), color=(1, 0.97, 0.85),
                            rough=0.1, emis=(1, 0.94, 0.72))],
                       (x, y, 0)))
    for _, x, y, _, _, _, _, c in props_of("sign", full):
        p.append(group([vcyl(1.5, 0.035, (0, 0, 0.75), color=(0.55, 0.56, 0.58), sub=10),
                        box((0.04, 0.5, 0.5), (0, 0, 1.5), color=c, rough=0.6),
                        box((0.05, 0.36, 0.36), (0.01, 0, 1.5), color=(0.95, 0.95, 0.93))],
                       (x, y)))
    # ---- cable drum, sandbags, cement mixer ----
    for _, x, y, yaw, _, _, _, _ in props_of("cabledrum", full):
        p.append(group([ycyl(0.55, 0.42, (0, 0, 0.42), (0.52, 0.40, 0.24), 16, rough=1),
                        ycyl(0.60, 0.14, (0, 0, 0.42), (0.30, 0.25, 0.18), 12, rough=1),
                        ycyl(0.10, 0.30, (0, 0, 0.42), (0.20, 0.20, 0.22), 12, rough=0.9)],
                       (x, y, 0), yaw))
    for _, x, y, _, _, _, _, _ in props_of("sandbags", full):
        for i in range(5):
            p.append(box((0.42, 0.26, 0.13),
                         (x - 0.44 + (i % 3) * 0.44, y - 0.1 + (i // 3) * 0.28,
                          0.065 + (i // 3) * 0.13),
                         (0, 0, 1, 0.1 * i), color=(0.58, 0.54, 0.42), rough=1))
    for _, x, y, yaw, _, _, _, _ in props_of("mixer", full):
        p.append(group([box((0.70, 0.60, 0.16), (0, 0, 0.08), color=(0.35, 0.36, 0.38)),
                        ucone(0.55, 0.34, (0, 0, 0.16), color=(0.80, 0.55, 0.10), sub=14,
                              rough=0.7),
                        vcyl(0.22, 0.20, (0, 0, 0.70), color=(0.80, 0.55, 0.10), sub=14,
                             rough=0.7),
                        ycyl(0.10, 0.16, (0.30, 0, 0.30), (0.30, 0.31, 0.33), 12, metal=0.6)],
                       (x, y, 0), yaw))

    # ---- the heaviest background assemblies: full world only ----
    p.append(crane((-13.5, 9.5, 0), -0.5))
    p.append(crane((16.0, 12.5, 0), 2.2))
    p.append(frame_building((-16.5, -11.0, 0), 0.25))
    p.append(scaffold_wall((-16.9, -11.6, 0), 0.25))
    p.append(van((10.8, -7.6, 0), 0.45))
    p.append(van((13.2, -9.4, 0), -0.30, (0.72, 0.24, 0.18)))
    p.append(dump_truck((-8.6, -6.2, 0), 0.55))
    return p


def site_collision(full):
    """One static body carrying a collision volume for every solid prop.

    Nothing here is drawn - the visuals already do that. This is what stops the
    machine driving through the container, and it is generated from the same
    PROPS table the route planner is generated from, so the two agree by
    construction. A Solid with no physics never moves, so these are walls.
    """
    vols = []
    for _, x, y, yaw, kind, dims, only_full, _ in PROPS:
        if only_full and not full:
            continue
        if kind == "cyl":
            r, h = dims
            geom = "Cylinder {\n  height %.4f\n  radius %.4f\n  subdivision 12\n}" % (h, r)
            rot = None
        else:
            h = dims[2]
            geom = "Box {\n  size %s\n}" % v(dims)
            rot = (0, 0, 1, yaw) if abs(yaw) > 1e-6 else None
        vols.append(pose(geom, (x, y, h / 2.0), rot))
    # the perimeter fence, so the machine cannot wander off the site
    for sgn in (1, -1):
        vols.append(pose("Box {\n  size %s\n}" % v((2 * FENCE + 0.2, 0.08, 1.20)),
                         (0, FENCE * sgn, 0.60)))
        vols.append(pose("Box {\n  size %s\n}" % v((0.08, 2 * FENCE + 0.2, 1.20)),
                         (FENCE * sgn, 0, 0.60)))
    return """Solid {
  name "site_collision"
  boundingObject Group {
    children [
%s
    ]
  }
}""" % "\n".join(indent(c, 6) for c in vols)


def site_map():
    """The obstacle list the controller plans around, written from PROPS."""
    rows = []
    for pid, x, y, _, kind, dims, only_full, _ in PROPS:
        rows.append("    (%7.3f, %7.3f, %5.3f),   # %s%s"
                    % (x, y, plan_radius(kind, dims), pid,
                       "" if not only_full else "  (full world only)"))
    return '''"""Where every solid thing on the site is.

Generated by tools/gen_world.py - do not edit by hand. Regenerating the world
regenerates this too, so the machine can never plan a route through something
that is actually there.

Each entry is (x, y, radius): the radius the machine's centre must stay
outside of, before its own footprint is added.
"""

FENCE = %.2f          # the yard runs from -FENCE to +FENCE on both axes

OBSTACLES = [
%s
]
''' % (FENCE, "\n".join(rows))


# ======================================================================
#  Assemble
# ======================================================================

def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def pile_chunks(cx, cy, r, h, base):
    """A few angular chunks sitting on a spoil pile's actual surface, so it
    reads as loose rock and rubble rather than a smooth dirt cone.

    A cone tapers, so a chunk placed at a radius chosen independently of its
    height ends up buried inside the solid mass rather than visible on the
    surface (found by rendering, not by eye - the first version of this was
    invisible). The radius here is always the cone's own surface radius at
    that chunk's height, nudged outward by half the chunk's own size so it
    is guaranteed to poke out rather than sit exactly on the tangent line.

    Deterministic (index-based jitter, not random), so gen_world.py keeps
    producing the same output on every run.
    """
    dark, light = mix(base, (0, 0, 0), 0.30), mix(base, (1, 1, 1), 0.22)
    p = []
    for i in range(4):
        a = i * 1.571 + 0.35
        zf = 0.10 + 0.08 * (i % 2)             # low on the pile, as a fraction of h
        zz = h * zf
        surf_r = r * (1 - zf)                  # the cone's own radius at that height
        s = 0.11 + 0.03 * (i % 2)
        rr = surf_r + s * 0.45
        p.append(box((s, s * 0.8, s * 0.65),
                     (cx + rr * math.cos(a), cy + rr * math.sin(a), zz),
                     (0, 0, 1, a * 1.8), color=light if i % 2 else dark, rough=1))
    return p


def rock_shapes(base, dark, light):
    """An angular rock, sized to fill a CUBE cell.

    Six masses give the silhouette; on top of those go broken facets, quartz
    veins, shadowed crevices, a patch of lichen on the weathered side and grit
    stuck to the bottom, so no two faces of a stone look alike. Every piece is
    tinted from the stone's own three colours, so each rock keeps its identity.
    """
    vein = mix(light, (1.0, 1.0, 1.0), 0.45)
    moss = mix(base, (0.30, 0.42, 0.18), 0.55)
    grit = mix(dark, (0.0, 0.0, 0.0), 0.25)
    return [
        # tilted off the vertical, so the stone has no flat horizontal top
        box((0.130, 0.120, 0.100), (0, 0, -0.012), (0.55, 0.42, 0.72, 0.55),
            color=base, rough=0.95),
        box((0.112, 0.100, 0.092), (0.018, -0.020, 0.030), (0.30, -0.36, 0.88, 0.85),
            color=light, rough=0.95),
        box((0.094, 0.112, 0.082), (-0.028, 0.022, 0.020), (0, 1, 0, 0.42), color=dark,
            rough=0.95),
        box((0.074, 0.070, 0.070), (0.038, 0.036, -0.030), (1, 0, 0, 0.55), color=dark,
            rough=0.95),
        box((0.056, 0.052, 0.050), (-0.042, -0.038, 0.038), (0, 1, 0, 0.90), color=light,
            rough=0.95),
        box((0.044, 0.062, 0.034), (0.048, -0.030, 0.046), (0, 0, 1, 1.15), color=base,
            rough=0.95),
        # broken facets, each standing proud of the mass under it
        box((0.046, 0.040, 0.030), (-0.050, 0.030, -0.030), (1, 0, 0, 0.75),
            color=light, rough=0.92),
        box((0.038, 0.044, 0.026), (0.030, 0.052, 0.006), (0, 1, 0, 1.25),
            color=base, rough=0.92),
        box((0.034, 0.030, 0.036), (-0.020, -0.052, -0.008), (0, 0, 1, 0.62),
            color=light, rough=0.92),
        box((0.030, 0.036, 0.024), (0.056, 0.008, -0.004), (1, 0, 0, 1.05),
            color=dark, rough=0.92),
        box((0.028, 0.026, 0.022), (-0.044, 0.010, 0.050), (0, 1, 0, 0.55),
            color=dark, rough=0.92),
        # quartz veins
        box((0.070, 0.010, 0.008), (0.004, -0.034, 0.052), (0, 0, 1, 0.50),
            color=vein, rough=0.55, metal=0.15),
        box((0.008, 0.058, 0.007), (-0.036, 0.004, 0.044), (0, 1, 0, 0.30),
            color=vein, rough=0.55, metal=0.15),
        box((0.040, 0.007, 0.006), (0.034, 0.020, -0.044), (0, 0, 1, -0.9),
            color=vein, rough=0.55, metal=0.15),
        # crevices, shadowed
        box((0.052, 0.006, 0.014), (0.010, 0.030, 0.044), (0, 0, 1, -0.4),
            color=grit, rough=1),
        box((0.006, 0.046, 0.012), (0.040, -0.012, 0.018), (1, 0, 0, 0.3),
            color=grit, rough=1),
        # lichen on the weathered side
        box((0.040, 0.034, 0.006), (-0.026, 0.028, 0.052), (0, 0, 1, 0.8),
            color=moss, rough=1),
        box((0.020, 0.024, 0.005), (0.006, 0.044, 0.040), (0, 0, 1, -0.6),
            color=moss, rough=1),
        box((0.016, 0.018, 0.005), (-0.048, -0.026, 0.030), (0, 1, 0, 0.4),
            color=moss, rough=1),
        # grit stuck to it
        box((0.014, 0.012, 0.010), (0.052, 0.038, 0.012), (0, 1, 0, 0.9),
            color=grit, rough=1),
        box((0.011, 0.014, 0.009), (-0.056, -0.014, 0.006), (1, 0, 0, 1.2),
            color=grit, rough=1),
        box((0.010, 0.010, 0.008), (0.024, -0.056, 0.026), (0, 0, 1, 0.4),
            color=light, rough=1),
        box((0.009, 0.012, 0.007), (-0.010, 0.056, -0.020), (0, 1, 0, 0.7),
            color=base, rough=1),
    ]


def rock_node(defname, name, xy, base, dark, light):
    return """DEF %s Solid {
  translation %.4f %.4f %.5f
  children [
%s
  ]
  name "%s"
  contactMaterial "load"
  boundingObject Box {
    size %s
  }
  physics Physics {
    density -1
    mass 2.0
  }
}""" % (defname, xy[0], xy[1], CUBE / 2 + 0.001,
        "\n".join(indent(c, 4) for c in rock_shapes(base, dark, light)),
        name, v((CUBE, CUBE, CUBE)))


def cube_node(defname, name, xy, color):
    return """DEF %s Solid {
  translation %.4f %.4f %.5f
  children [
    Shape {
      appearance PBRAppearance {
        baseColor %s
        roughness 0.55
        metalness 0.1
      }
      geometry Box {
        size %s
      }
    }
  ]
  name "%s"
  contactMaterial "load"
  boundingObject Box {
    size %s
  }
  physics Physics {
    density -1
    mass 2.0
  }
}""" % (defname, xy[0], xy[1], CUBE / 2 + 0.001, v(color),
        v((CUBE, CUBE, CUBE)), name, v((CUBE, CUBE, CUBE)))


HEADER = """#VRML_SIM R2023b utf8
# Construction site with a tracked excavator that stacks and unstacks coloured cubes.
# Built entirely from Webots' built-in nodes - no external PROTO files are loaded.
#
# castShadows is FALSE below. Shadow casting doubles the draw work for every
# object in the scene and can black out the viewport on weaker graphics
# hardware. If your machine handles it, set it back to TRUE for a nicer image.

WorldInfo {
  basicTimeStep 16
  defaultDamping Damping {
    linear 0.1
    angular 0.2
  }
  contactProperties [
    ContactProperties {
      material1 "grip"
      material2 "load"
      coulombFriction [
        2.8
      ]
      bounce 0
      softCFM 0.0002
    }
    ContactProperties {
      material1 "load"
      material2 "load"
      coulombFriction [
        0.9
      ]
      bounce 0
      softCFM 0.0001
    }
    ContactProperties {
      material1 "load"
      material2 "default"
      coulombFriction [
        1.1
      ]
      bounce 0
      softCFM 0.0001
    }
    ContactProperties {
      coulombFriction [
        1.2
      ]
      bounce 0
      softCFM 0.0001
    }
  ]
}
Viewpoint {
  orientation 0.810800 0.311600 0.495500 1.319500
  position 3.0 -2.6 2.0
}
Background {
  skyColor [
    0.53 0.68 0.86
  ]
}
DirectionalLight {
  direction 0.55 0.4 -0.85
  color 1 0.92 0.78
  intensity 2.4
  castShadows FALSE
}
DirectionalLight {
  direction -0.6 -0.5 -0.55
  color 0.70 0.76 0.92
  intensity 0.9
}
DirectionalLight {
  direction 0 0 1
  color 0.5 0.44 0.36
  intensity 0.35
}
Solid {
  children [
    Shape {
      appearance PBRAppearance {
        baseColor 0.45 0.36 0.27
        roughness 1
        metalness 0
      }
      geometry Plane {
        size 80 80
      }
    }
  ]
  name "ground"
  boundingObject Plane {
    size 80 80
  }
}"""

def build(path, full):
    parts = [HEADER]
    parts.append("Solid {\n  children [\n%s\n  ]\n  name \"site_scenery\"\n}" %
                 "\n".join(indent(c, 4) for c in scenery(full)))
    parts.append(site_collision(full))
    parts.append(excavator())
    for i, colour in enumerate(COLOURS):
        parts.append(cube_node("CUBE_%s" % colour.upper(), "cube_%s" % colour,
                               HOMES[colour], CUBE_COLOURS[colour]))
    for i, colour in enumerate(COLOURS):
        parts.append(rock_node("ROCK_%s" % colour.upper(), "rock_%s" % colour,
                               (i * 0.6, -25.0), *ROCK_COLOURS[colour]))
    with open(path, "w") as f:
        f.write("\n".join(parts) + "\n")
    txt = open(path).read()
    print("%-28s shapes: %4d   lines: %6d   braces: %d  brackets: %d" % (
        path.rsplit("/", 1)[-1], txt.count("geometry "), txt.count("\n"),
        txt.count("{") - txt.count("}"), txt.count("[") - txt.count("]")))


WORLDS = os.path.dirname(OUT)
build(os.path.join(WORLDS, "construction_site.wbt"), True)
build(os.path.join(WORLDS, "construction_site_lite.wbt"), False)

MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "controllers",
                   "excavator_controller", "site_map.py")
with open(MAP, "w") as f:
    f.write(site_map())
print("%-28s obstacles: %4d" % ("site_map.py", len(PROPS)))
