"""Checks the three camera pods actually touch the hull, not just look close.

Each pod used to float free of the machine body - nothing connected it to
anything - which read as a random dark cube next to the excavator. Eyeballing
a render got the fix wrong twice in a row (a curved surface and a bracket
narrower than the housing both look fine from some angles while still having
a real gap), so this checks it properly: samples the pod's whole mount face on
a grid and finds the worst point, rather than trusting one camera angle.

    python3 tools/campod_check.py
"""

import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "gen_world.py")).read()


def box_contains(p, center, half):
    return all(abs(p[i] - center[i]) <= half[i] + 1e-9 for i in range(3))


def cyl_y_contains(p, center, r, half_len):
    """A ycyl: axis along Y, circular cross-section in the XZ plane."""
    if abs(p[1] - center[1]) > half_len + 1e-9:
        return False
    dx, dz = p[0] - center[0], p[2] - center[2]
    return math.hypot(dx, dz) <= r + 1e-9


def worst_face_gap(hull_fns, mount_x, centre, half=(0.03, 0.035, 0.03), n=11):
    """The largest gap anywhere on the pod's mount face; negative = overlap."""
    worst = -1e9
    for j in range(n):
        for k in range(n):
            y = centre[1] - half[1] + 2 * half[1] * j / (n - 1)
            z = centre[2] - half[2] + 2 * half[2] * k / (n - 1)
            if any(f((mount_x, y, z)) for f in hull_fns):
                worst = max(worst, -0.001)
                continue
            found = 999.0
            for step in range(1, 300):
                if any(f((mount_x + 0.001 * step, y, z)) for f in hull_fns):
                    found = 0.001 * step
                    break
            worst = max(worst, found)
    return worst


# ---- pull the rig positions straight out of the generator, not a copy ----
m = re.search(r"cam_rigs = \[(.*?)\]\n", src, re.S)
assert m, "could not find cam_rigs in gen_world.py"
rigs = {}
for mm in re.finditer(
        r'\("(camera_\w+)",\s*\(([-\d.]+), ([-\d.]+), ([-\d.]+)\),\s*(-?1)',
        m.group(1)):
    name, x, y, z, look = mm.groups()
    rigs[name] = ((float(x), float(y), float(z)), int(look))

for name in ("camera_front_left", "camera_front_right", "camera_rear"):
    assert name in rigs, "campod_check.py is out of date: %s not found" % name

# ---- the hull pieces each pod is meant to sit flush against ----
CAB = ((0.10, 0.26, 0.36), (0.23, 0.21, 0.26))
BRACKET = ((0.28, -0.12, 0.13), (0.11, 0.03, 0.14))
PIN = ((0.30, 0.0, 0.16), 0.055, 0.16)
CWT_BOX = ((-0.54, 0, 0.19), (0.10, 0.35, 0.16))
CWT_CYL = ((-0.63, 0, 0.19), 0.15, 0.35)
CWT_PLATE = ((-0.702, 0, 0.055), (0.015, 0.31, 0.045))

CHECKS = {
    "camera_front_left": [lambda p: box_contains(p, *CAB)],
    "camera_front_right": [lambda p: box_contains(p, *BRACKET),
                           lambda p: cyl_y_contains(p, *PIN)],
    "camera_rear": [lambda p: box_contains(p, *CWT_BOX),
                    lambda p: cyl_y_contains(p, *CWT_CYL),
                    lambda p: box_contains(p, *CWT_PLATE)],
}

bad = False
for name, (centre, look) in rigs.items():
    mount_x = centre[0] - look * 0.03
    gap = worst_face_gap(CHECKS[name], mount_x, centre)
    ok = gap <= 0.001
    bad = bad or not ok
    print("  %-4s %-20s worst gap on the mount face: %+.4f m"
          % ("ok" if ok else "FAIL", name, gap))

sys.exit(1 if bad else 0)
