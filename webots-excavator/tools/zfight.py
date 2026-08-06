"""Finds coplanar box faces in the world - the cause of shimmering / flicker."""

import sys

import numpy as np

import render as R

BOXES = []


def collect(node, T, Rm):
    kind = node.kind
    if kind in ("Pose", "Transform", "Group", "Solid", "Robot"):
        t = (R.nums(node.fields.get("translation")) + [0.0, 0.0, 0.0])[:3]
        r = R.nums(node.fields.get("rotation"))
        M = R.rot_matrix(*r) if len(r) == 4 else np.eye(3)
        for ch in node.fields.get("children", []):
            if isinstance(ch, R.Node):
                collect(ch, T + Rm @ np.array(t), Rm @ M)
        return
    if kind == "HingeJoint":
        ep = node.fields.get("endPoint")
        if isinstance(ep, R.Node):
            collect(ep, T, Rm)
        return
    if kind == "Shape":
        geo = node.fields.get("geometry")
        if not isinstance(geo, R.Node) or geo.kind != "Box":
            return
        s = R.nums(geo.fields.get("size"))[:3]
        # only axis-aligned boxes: a rotated panel cannot be exactly coplanar
        if not np.allclose(np.abs(Rm), np.eye(3), atol=1e-6):
            return
        half = np.abs(Rm @ np.array(s)) / 2
        BOXES.append((T - half, T + half))


world = sys.argv[1]
roots = R.parse_world(open(world).read())
for n in roots:
    if n.kind in ("Solid", "Robot", "Pose", "Group", "Transform"):
        collect(n, np.zeros(3), np.eye(3))

print("axis-aligned boxes:", len(BOXES))
lo = np.array([b[0] for b in BOXES])
hi = np.array([b[1] for b in BOXES])

EPS = 3e-4
hits = []
for i in range(len(BOXES)):
    # boxes whose AABBs overlap box i
    ov = np.all((lo < hi[i] - 1e-9) & (hi > lo[i] + 1e-9), axis=1)
    ov[i] = False
    for j in np.nonzero(ov)[0]:
        if j < i:
            continue
        for ax in range(3):
            others = [a for a in range(3) if a != ax]
            # they must genuinely share area on the other two axes
            area = 1.0
            for a in others:
                area *= max(0.0, min(hi[i][a], hi[j][a]) - max(lo[i][a], lo[j][a]))
            if area < 1e-4:
                continue
            for fa in (lo[i][ax], hi[i][ax]):
                for fb in (lo[j][ax], hi[j][ax]):
                    if abs(fa - fb) < EPS:
                        hits.append((round(float(fa), 4), "xyz"[ax], round(area, 4),
                                     tuple(np.round(lo[i], 3)), tuple(np.round(lo[j], 3))))

print("coplanar face pairs:", len(hits))
seen = set()
for f, ax, area, a, b in sorted(hits, key=lambda h: -h[2])[:25]:
    k = (f, ax, a, b)
    if k in seen:
        continue
    seen.add(k)
    print("   %s = %-8s shared area %6.4f m^2   boxes at %s / %s" % (ax, f, area, a, b))
