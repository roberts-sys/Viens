"""The arm's hard stops, and what they leave for the physics engine to catch.

Webots does not collide two solids joined directly by a joint. For this machine
that means these pairs are invisible to selfCollision no matter what:

    Robot <-> house      house <-> boom      boom <-> stick
    stick <-> wrist      wrist <-> grapple   grapple <-> tine

so nothing stops the boom rotating down through the deck it is pinned to. Real
excavators stop that with hard limits in the rams, and so does this one. Every
other pair - grapple against the tracks, tines against the boom, tine against
tine - is collided normally and needs no limit.

The stops below go into the world file as minStop/maxStop on the joints and
minPosition/maxPosition on the motors, so they bind on the operator in manual
mode exactly as they bind on the autonomous routine.

    python3 tools/limits.py
"""

import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CTRL = os.path.join(HERE, "..", "controllers", "excavator_controller")
src = open(os.path.join(CTRL, "excavator_controller.py")).read()


def const(name):
    return float(re.search(r"^%s\s*=\s*([-\d.]+)" % name, src, re.M).group(1))


PR, PZ = const("BOOM_PIVOT_R"), const("BOOM_PIVOT_Z")
BOOM, STICK = const("BOOM_LEN"), const("STICK_LEN")
TIP = const("TIP_OFFSET")
STANDOFF, TRANSIT_Z = const("STANDOFF"), const("TRANSIT_Z")
CUBE, APPROACH_DZ = const("CUBE"), const("APPROACH_DZ")
PARK_MIN, PARK_MAX = const("PARK_MIN"), const("PARK_MAX")

# ---------------------------------------------------------------- the stops
# a1   = the boom's angle above horizontal
# fold = the stick's angle relative to the boom (always negative: the stick
#        hangs forward and down off the end of the boom)
# a2   = a1 + fold, the stick's angle above horizontal
A1 = (0.10, 1.40)        # boom: +6 deg (just off the deck) to +80 deg (near vertical)
FOLD = (-2.20, -0.20)    # stick: folded right back, to nearly straight out
A2 = (-1.60, 0.90)       # wrist: keeps the grapple from flipping over

GRAPPLE_R = 0.25          # tine tips, wide open - the worst case
GRAPPLE_TOP = 0.07
GRAPPLE_BOT = 0.47
HOUSE = (-0.72, 0.52, 0.29, 0.79)          # x0, x1, z0, z1, in the arm's plane
TRACKS = (-0.72, 0.72, 0.00, 0.30)


def cyl_box_gap(cx, top, bot, r, box):
    x0, x1, z0, z1 = box
    dx = max(x0 - cx, 0.0, cx - x1)
    dz = max(z0 - top, 0.0, bot - z1)
    return math.hypot(dx, dz) - r


def wrist_of(a1, a2):
    ex = PR + BOOM * math.cos(a1)
    ez = PZ + BOOM * math.sin(a1)
    return ex + STICK * math.cos(a2), ez + STICK * math.sin(a2)


def ik(r, z):
    dr, dz = r - PR, (z + TIP) - PZ
    d = math.hypot(dr, dz)
    d = min(d, BOOM + STICK - 1e-3)
    d = max(d, abs(BOOM - STICK) + 1e-3)
    cos_a = (d * d + BOOM ** 2 - STICK ** 2) / (2 * BOOM * d)
    a1 = math.atan2(dz, dr) + math.acos(max(-1.0, min(1.0, cos_a)))
    a2 = math.atan2(dz - BOOM * math.sin(a1), dr - BOOM * math.cos(a1))
    return a1, a2


# --------------------------------------------------------------------------
# The stops must not bind on anything the autonomous routine asks for
# --------------------------------------------------------------------------
needed = []
for level in range(3):
    centre = CUBE * level + CUBE / 2
    needed += [(STANDOFF, centre), (STANDOFF, centre + APPROACH_DZ)]
needed += [(STANDOFF, CUBE / 2), (STANDOFF, CUBE / 2 + APPROACH_DZ),
           (STANDOFF, CUBE / 2 + APPROACH_DZ + CUBE),
           (STANDOFF, TRANSIT_Z), (1.05, 0.55)]
for r in (PARK_MIN, STANDOFF, PARK_MAX):
    for z in (0.05, 0.30, 0.55, 0.80):
        needed.append((r, z))

used = [ik(r, z) for r, z in needed]
a1n = (min(a for a, _ in used), max(a for a, _ in used))
fon = (min(b - a for a, b in used), max(b - a for a, b in used))
a2n = (min(b for _, b in used), max(b for _, b in used))

print("what the autonomous routine uses, against the stops:\n")
rows = [("boom  a1", a1n, A1), ("stick fold", fon, FOLD), ("wrist a2", a2n, A2)]
ok = True
for name, need, lim in rows:
    room = min(need[0] - lim[0], lim[1] - need[1])
    good = need[0] >= lim[0] and need[1] <= lim[1]
    ok = ok and good
    print("   %-11s uses %+.3f..%+.3f   stops %+.3f..%+.3f   headroom %+.3f rad (%+.0f deg)%s"
          % (name, need[0], need[1], lim[0], lim[1], room, math.degrees(room),
             "" if good else "   ** THE STOPS BIND **"))
if not ok:
    sys.exit(1)

# --------------------------------------------------------------------------
# What is left inside the stops for the physics engine to catch
# --------------------------------------------------------------------------
STEP = math.radians(2)
worst_h = worst_t = (1e9, (0.0, 0.0))
n1 = int((A1[1] - A1[0]) / STEP) + 1
n2 = int((FOLD[1] - FOLD[0]) / STEP) + 1
for i in range(n1):
    a1 = A1[0] + (A1[1] - A1[0]) * i / (n1 - 1)
    for j in range(n2):
        fold = FOLD[0] + (FOLD[1] - FOLD[0]) * j / (n2 - 1)
        a2 = a1 + fold
        if not (A2[0] <= a2 <= A2[1]):
            continue
        wx, wz = wrist_of(a1, a2)
        gh = cyl_box_gap(wx, wz - GRAPPLE_TOP, wz - GRAPPLE_BOT, GRAPPLE_R, HOUSE)
        gt = cyl_box_gap(wx, wz - GRAPPLE_TOP, wz - GRAPPLE_BOT, GRAPPLE_R, TRACKS)
        if gh < worst_h[0]:
            worst_h = (gh, (a1, fold))
        if gt < worst_t[0]:
            worst_t = (gt, (a1, fold))

print("\ninside the stops, the grapple can still be swung to:")
for what, (gap, at) in (("the house", worst_h), ("the tracks", worst_t)):
    print("   %-10s closest approach %+.3f m   at boom %+.2f, fold %+.2f%s"
          % (what, gap, at[0], at[1],
             "   - collision stops it there" if gap < 0 else ""))
print("\n   Both of those pairs ARE collided by Webots (the grapple's parent is the")
print("   wrist, not the house or the Robot), so the engine catches them. The stops")
print("   exist for boom-against-house and stick-against-boom, which it cannot.")

# --------------------------------------------------------------------------
print("\nstops for the world file (Webots angles: boom = -a1, stick = -fold, wrist = a2):")
print("   boom_motor     minPosition %+.3f   maxPosition %+.3f" % (-A1[1], -A1[0]))
print("   stick_motor    minPosition %+.3f   maxPosition %+.3f" % (-FOLD[1], -FOLD[0]))
print("   wrist_motor    minPosition %+.3f   maxPosition %+.3f" % (A2[0], A2[1]))
