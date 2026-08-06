"""Prints a map of where the machine can drive, and checks it can reach the pads.

    python3 tools/navtest.py

The obstacle list comes from site_map.py, which the world generator writes, so
this is always testing the site that is actually in the world file - not a copy
that can drift out of date.
"""

import heapq
import math
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
CTRL = os.path.join(HERE, "..", "controllers", "excavator_controller")
sys.path.insert(0, CTRL)

from site_map import OBSTACLES, FENCE            # noqa: E402

src = open(os.path.join(CTRL, "excavator_controller.py")).read()


def const(name):
    return float(re.search(r"^%s\s*=\s*([-\d.]+)" % name, src, re.M).group(1))


MACHINE_R = const("MACHINE_R")
PAD_R = const("PAD_R")
STANDOFF = const("STANDOFF")
CELL = const("CELL")
EDGE_MARGIN = const("EDGE_MARGIN")
LIMIT = FENCE - EDGE_MARGIN

HOMES = eval(re.search(r"^HOMES = (\{.*?^\})", src, re.M | re.S).group(1))
TOWERS = eval(re.search(r"^TOWERS = (\(.*?\))$", src, re.M).group(1))

PADS = [(x, y, PAD_R) for x, y in HOMES.values()]
PADS += [(x, y, PAD_R) for x, y in TOWERS]
BLOCKERS = list(OBSTACLES) + PADS

N = int(2 * LIMIT / CELL) + 1


def to_cell(x, y):
    return (int(round((x + LIMIT) / CELL)), int(round((y + LIMIT) / CELL)))


def to_world(i, j):
    return (i * CELL - LIMIT, j * CELL - LIMIT)


def blocked(i, j):
    x, y = to_world(i, j)
    if abs(x) > LIMIT or abs(y) > LIMIT:
        return True
    return any((x - ox) ** 2 + (y - oy) ** 2 < (orad + MACHINE_R) ** 2
               for ox, oy, orad in BLOCKERS)


GRID = [[blocked(i, j) for j in range(N)] for i in range(N)]
free = sum(not GRID[i][j] for i in range(N) for j in range(N))
print("yard %.0f x %.0f m,  grid %dx%d,  %d cells drivable (%.0f%%)"
      % (2 * FENCE, 2 * FENCE, N, N, free, 100.0 * free / (N * N)))

MARKS = {}
for name, (x, y) in list(HOMES.items()) + [("1", TOWERS[0]), ("2", TOWERS[1])]:
    MARKS[to_cell(x, y)] = name[0].upper()

print("\n. drivable   # blocked   X where the machine starts")
print("letters are the home pads, digits the two build sites\n")
for j in range(N - 1, -1, -2):
    row = ""
    for i in range(N):
        x, y = to_world(i, j)
        if (i, j) in MARKS:
            row += MARKS[(i, j)]
        elif abs(x) < 0.4 and abs(y) < 0.4:
            row += "X"
        else:
            row += "#" if GRID[i][j] else "."
    print("  " + row)


def plan(start, goal):
    s, g = to_cell(*start), to_cell(*goal)
    if GRID[s[0]][s[1]] or GRID[g[0]][g[1]]:
        return None
    openq = [(0.0, s)]
    came, cost = {s: None}, {s: 0.0}
    while openq:
        _, cur = heapq.heappop(openq)
        if cur == g:
            out = []
            while cur:
                out.append(to_world(*cur))
                cur = came[cur]
            return out[::-1]
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == dj == 0:
                    continue
                nb = (cur[0] + di, cur[1] + dj)
                if not (0 <= nb[0] < N and 0 <= nb[1] < N) or GRID[nb[0]][nb[1]]:
                    continue
                nc = cost[cur] + math.hypot(di, dj)
                if nc < cost.get(nb, 1e18):
                    cost[nb] = nc
                    came[nb] = cur
                    heapq.heappush(openq,
                                   (nc + math.hypot(nb[0] - g[0], nb[1] - g[1]), nb))
    return None


start = to_cell(0, 0)
seen, q = {start}, deque([start])
while q:
    c = q.popleft()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            nb = (c[0] + di, c[1] + dj)
            if (0 <= nb[0] < N and 0 <= nb[1] < N and nb not in seen
                    and not GRID[nb[0]][nb[1]]):
                seen.add(nb)
                q.append(nb)
print("\nreachable from the start: %d of %d free cells (%.0f%%)"
      % (len(seen), free, 100.0 * len(seen) / free))


def parking(tx, ty):
    """Every bearing round a pad that the machine could park on."""
    others = [(px, py, pr) for px, py, pr in PADS
              if math.hypot(px - tx, py - ty) > 0.05]
    out = []
    for k in range(24):
        b = k * math.pi / 12
        sx, sy = tx + STANDOFF * math.cos(b), ty + STANDOFF * math.sin(b)
        c = to_cell(sx, sy)
        if not (0 <= c[0] < N and 0 <= c[1] < N) or GRID[c[0]][c[1]] or c not in seen:
            continue
        if any(math.hypot(sx - px, sy - py) < pr + MACHINE_R for px, py, pr in others):
            continue
        out.append((sx, sy))
    return out


print("\nparking, at %.2f m from each pad:" % STANDOFF)
spots = {}
named = list(HOMES.items()) + [("build site 1", TOWERS[0]), ("build site 2", TOWERS[1])]
for name, (x, y) in named:
    good = parking(x, y)
    if good:
        spots[name] = good[0]
    print("   %-13s (%6.2f,%6.2f)   %2d of 24 bearings usable%s"
          % (name, x, y, len(good), "" if good else "   ** NOWHERE TO PARK **"))

print("\nroutes between every pair of pads:")
worst, bad = 0.0, 0
items = list(spots.items())
for a in range(len(items)):
    for b in range(a + 1, len(items)):
        p = plan(items[a][1], items[b][1])
        if p is None:
            print("   NO ROUTE  %s -> %s" % (items[a][0], items[b][0]))
            bad += 1
        else:
            worst = max(worst, len(p) * CELL)
print("   %d pairs checked, %d unroutable, longest route about %.1f m"
      % (len(items) * (len(items) - 1) // 2, bad, worst))
