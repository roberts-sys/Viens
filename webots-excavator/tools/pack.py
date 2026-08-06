"""Lay the site props out around the perimeter, leaving the middle to work in.

Walks the four fence lines and sets each prop down with its long side parallel
to the fence, so nothing intersects anything else and the yard stays open.
"""
import math

FENCE = 8.0
GAP = 0.30          # clear space between neighbours
MARGIN = 0.25       # clear space between a prop and the fence

# id, kind, dims, full-only, extra   (same meaning as PROPS in gen_world.py)
BIG = [
    ("office",    "box", (3.35, 2.35, 1.35), True,  None),
    ("rebar",     "box", (3.40, 0.50, 0.10), True,  None),
    ("container", "box", (3.14, 1.24, 1.24), False, None),
    ("timber",    "box", (2.65, 0.90, 0.46), True,  None),
    ("pile",      "cyl", (1.45, 0.88),       False, (0.38, 0.30, 0.21)),
    ("pile",      "cyl", (1.25, 0.78),       False, (0.40, 0.31, 0.22)),
    ("pile",      "cyl", (1.05, 0.62),       True,  (0.52, 0.49, 0.43)),
    ("pile",      "cyl", (0.95, 0.55),       False, (0.43, 0.34, 0.25)),
    ("pile",      "cyl", (0.85, 0.50),       True,  (0.46, 0.38, 0.28)),
    ("barrier",   "box", (1.62, 0.42, 0.51), False, None),
    ("barrier",   "box", (1.62, 0.42, 0.51), False, None),
    ("barrier",   "box", (1.62, 0.42, 0.51), True,  None),
    ("barrier",   "box", (1.62, 0.42, 0.51), True,  None),
    ("barrier",   "box", (1.62, 0.42, 0.51), True,  None),
    ("barrier",   "box", (1.62, 0.42, 0.51), True,  None),
    ("pipes",     "box", (1.52, 0.98, 0.84), True,  None),
    ("generator", "box", (1.55, 0.95, 0.97), True,  None),
    ("sandbags",  "box", (1.35, 0.60, 0.26), True,  None),
    ("bricks",    "box", (1.00, 0.80, 0.68), True,  0.50),
    ("bricks",    "box", (1.00, 0.80, 0.54), True,  0.42),
    ("barrow",    "box", (0.96, 0.52, 0.55), True,  None),
    ("cabledrum", "box", (0.86, 0.60, 0.84), True,  None),
    ("mixer",     "box", (0.82, 0.68, 0.92), True,  None),
    ("drums",     "cyl", (0.55, 0.60),       True,  None),
    ("toilet",    "box", (0.50, 0.50, 1.08), True,  None),
    ("mast",      "cyl", (0.42, 4.20),       True,  None),
]

# Sides run anticlockwise. Each is (unit along, inward normal, start corner).
SIDES = [
    ("N", (-1.0, 0.0), (0.0, -1.0), (FENCE, FENCE)),
    ("W", (0.0, -1.0), (1.0, 0.0), (-FENCE, FENCE)),
    ("S", (1.0, 0.0), (0.0, 1.0), (-FENCE, -FENCE)),
    ("E", (0.0, 1.0), (-1.0, 0.0), (FENCE, -FENCE)),
]

# deal the props round the four sides so each gets a fair share of the length
buckets = [[], [], [], []]
load = [0.0, 0.0, 0.0, 0.0]
for item in BIG:
    kind, dims = item[1], item[2]
    length = 2 * dims[0] if kind == "cyl" else max(dims[0], dims[1])
    k = load.index(min(load))
    buckets[k].append(item)
    load[k] += length + GAP

out = []
for (name, along, inward, corner), items in zip(SIDES, buckets):
    lengths = [2 * d[2][0] if d[1] == "cyl" else max(d[2][0], d[2][1]) for d in items]
    # keep clear of both corners so the runs on neighbouring sides cannot collide
    CORNER = 1.6
    run = 2 * FENCE - 2 * CORNER
    # spread whatever room is left evenly between neighbours
    gap = (run - sum(lengths)) / max(1, len(items) - 1)
    assert gap >= 0.15, "%s side overloaded: %.2f m of props in %.2f m" % (
        name, sum(lengths), run)
    gap = min(gap, 0.60)
    used = sum(lengths) + gap * (len(items) - 1)
    t = CORNER + (run - used) / 2.0
    for pid, kind, dims, full, extra in items:
        if kind == "cyl":
            length = width = 2 * dims[0]
            yaw = 0.0
        else:
            length, width = max(dims[0], dims[1]), min(dims[0], dims[1])
            # rotate so the long side lies along the fence
            long_is_x = dims[0] >= dims[1]
            base = math.atan2(along[1], along[0])
            yaw = base if long_is_x else base + math.pi / 2
            yaw = (yaw + math.pi / 2) % math.pi - math.pi / 2   # tidy to (-90, 90]
        t += length / 2.0
        inset = MARGIN + width / 2.0     # how far in from the fence its centre sits
        x = corner[0] + along[0] * t + inward[0] * inset
        y = corner[1] + along[1] * t + inward[1] * inset
        out.append((pid, round(x, 2), round(y, 2), round(yaw, 4), kind, dims, full, extra))
        t += length / 2.0 + gap


def footprint(p):
    """Axis-aligned half-extents, so we can check nothing overlaps."""
    _, x, y, yaw, kind, dims = p[:6]
    if kind == "cyl":
        return x, y, dims[0], dims[0]
    c, s = abs(math.cos(yaw)), abs(math.sin(yaw))
    return x, y, dims[0] / 2 * c + dims[1] / 2 * s, dims[0] / 2 * s + dims[1] / 2 * c


def clear_of_all(x, y, r, placed):
    for q in placed:
        qx, qy, qh, qw = footprint(q)
        if abs(x - qx) < qh + r + 0.25 and abs(y - qy) < qw + r + 0.25:
            return False
    return True


# cones and signs: small, dotted round the edge of the working area. Each is
# nudged outward from its nominal spot until it is clear of everything else.
FILLER = [
    ("cone", 4.30, 2.40, False), ("cone", 4.20, -1.40, False),
    ("cone", -4.30, 2.20, False), ("cone", -4.20, -2.00, False),
    ("cone", 2.30, 4.40, True), ("cone", -2.40, 4.30, True),
    ("cone", 2.10, -4.40, True), ("cone", -2.20, -4.35, True),
    ("sign", 0.30, 4.50, True), ("sign", 0.20, -4.50, True),
]
for pid, x, y, full in FILLER:
    dims = (0.11, 0.34) if pid == "cone" else (0.09, 1.75)
    extra = None if pid == "cone" else ((0.90, 0.15, 0.12) if y > 0 else (0.95, 0.75, 0.05))
    d = math.hypot(x, y)
    ux, uy = x / d, y / d
    for k in range(40):
        cx, cy = x - ux * 0.15 * k, y - uy * 0.15 * k    # walk inward until clear
        if clear_of_all(cx, cy, dims[0], out):
            out.append((pid, round(cx, 2), round(cy, 2), 0.0, "cyl", dims, full, extra))
            break
    else:
        print("could not fit %s at (%.1f, %.1f)" % (pid, x, y))


bad = 0
for i in range(len(out)):
    xi, yi, hi, wi = footprint(out[i])
    for j in range(i + 1, len(out)):
        xj, yj, hj, wj = footprint(out[j])
        ox = hi + hj - abs(xi - xj)
        oy = wi + wj - abs(yi - yj)
        if ox > 0.01 and oy > 0.01:
            print("OVERLAP %s/%s by %.2f x %.2f" % (out[i][0], out[j][0], ox, oy))
            bad += 1
print("# overlapping pairs: %d" % bad)

print("\nPROPS = [")
for pid, x, y, yaw, kind, dims, full, extra in sorted(out, key=lambda q: q[0]):
    d = "(%.2f, %.2f)" % dims if kind == "cyl" else "(%.2f, %.2f, %.2f)" % dims
    print('    ("%s",%s %6.2f, %6.2f, %7.4f, "%s", %-20s %-6s %s),'
          % (pid, " " * (10 - len(pid)), x, y, yaw, kind, d + ",",
             str(full) + ",", extra))
print("]")
