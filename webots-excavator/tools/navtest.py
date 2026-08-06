"""Checks the site is actually drivable before the planner goes in the controller."""

import heapq
import math

MACHINE_R = 0.75          # the machine's own footprint radius, plus margin
CELL = 0.15
LIMIT = 5.7               # stay inside the fence

HOMES = {
    "white":  (0.6557,  0.7813), "green":  (0.8356,  0.5851),
    "red":    (0.9585,  0.3488), "brown":  (1.0161,  0.0889),
    "yellow": (1.0045, -0.1771), "blue":   (0.9244, -0.4311),
}
TOWERS = ((0.5974, -0.6186), (0.2080, -0.8345))

OBSTACLES = [
    (2.9, 1.9, 0.16), (3.2, 0.8, 0.16), (3.2, -0.7, 0.16), (2.9, -1.8, 0.16),
    (2.0, 2.8, 0.16), (1.9, -2.9, 0.16), (3.3, 1.9, 0.16), (3.4, -1.5, 0.16),
    (0.9, 4.5, 0.85), (2.7, 4.5, 0.85), (-0.9, 4.5, 0.85), (4.5, 4.5, 0.85),
    (-3.8, -4.3, 0.85), (-2.0, -4.8, 0.85),
    (-4.8, -2.4, 1.70), (-4.4, 3.4, 2.00), (-2.6, 4.4, 0.40), (1.1, -5.0, 0.90),
    (3.4, 3.4, 0.65), (4.4, 2.9, 0.65),
    (4.5, -3.1, 0.90), (-3.2, -5.0, 1.50),
    (-0.65, -4.85, 0.55), (2.6, -4.7, 0.50),
    (3.6, 2.8, 1.30), (3.4, -4.6, 1.00), (-4.6, 2.2, 1.50), (-1.5, 4.6, 1.10),
    (5.0, -0.6, 0.90),
    (4.6, 2.2, 0.55), (-0.7, 5.0, 0.80), (3.9, -3.9, 0.50), (5.2, 3.4, 0.50),
    (2.9, 3.9, 0.25), (-2.2, -4.6, 0.25), (-4.6, -4.6, 1.75),
]
for x, y in list(HOMES.values()):
    OBSTACLES.append((x, y, 0.18))
for x, y in TOWERS:
    OBSTACLES.append((x, y, 0.20))

N = int(2 * LIMIT / CELL) + 1


def to_cell(x, y):
    return (int(round((x + LIMIT) / CELL)), int(round((y + LIMIT) / CELL)))


def to_world(i, j):
    return (i * CELL - LIMIT, j * CELL - LIMIT)


def blocked(i, j):
    x, y = to_world(i, j)
    if abs(x) > LIMIT or abs(y) > LIMIT:
        return True
    for ox, oy, orad in OBSTACLES:
        if (x - ox) ** 2 + (y - oy) ** 2 < (orad + MACHINE_R) ** 2:
            return True
    return False


GRID = [[blocked(i, j) for j in range(N)] for i in range(N)]
free = sum(not GRID[i][j] for i in range(N) for j in range(N))
print("grid %dx%d, free cells %d (%.0f%%)" % (N, N, free, 100 * free / (N * N)))

print("\nfree space (. = drivable, # = blocked, X = machine home):")
for j in range(N - 1, -1, -2):
    row = ""
    for i in range(0, N, 1):
        x, y = to_world(i, j)
        if abs(x) < 0.35 and abs(y) < 0.35:
            row += "X"
        else:
            row += "#" if GRID[i][j] else "."
    print("  " + row)


def plan(start, goal):
    s, g = to_cell(*start), to_cell(*goal)
    if GRID[s[0]][s[1]] or GRID[g[0]][g[1]]:
        return None
    openq = [(0, s)]
    came, cost = {s: None}, {s: 0.0}
    while openq:
        _, cur = heapq.heappop(openq)
        if cur == g:
            path = []
            while cur:
                path.append(to_world(*cur))
                cur = came[cur]
            return path[::-1]
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
                    h = math.hypot(nb[0] - g[0], nb[1] - g[1])
                    heapq.heappush(openq, (nc + h, nb))
    return None


# flood fill from the work spot to see what is actually reachable
from collections import deque
ROAD = (-1.9, 0.0)
start = to_cell(*ROAD)
print("\nwork spot (0,0) blocked:", GRID[to_cell(0,0)[0]][to_cell(0,0)[1]])
print("road point %s blocked:" % (ROAD,), GRID[start[0]][start[1]])
seen = {start}
q = deque([start])
while q:
    c = q.popleft()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            nb = (c[0] + di, c[1] + dj)
            if (0 <= nb[0] < N and 0 <= nb[1] < N and nb not in seen
                    and not GRID[nb[0]][nb[1]]):
                seen.add(nb); q.append(nb)
print("reachable from road point: %d cells of %d free" % (len(seen), free))
xs = [to_world(*c)[0] for c in seen]; ys = [to_world(*c)[1] for c in seen]
print("reachable extent: x %.1f..%.1f   y %.1f..%.1f" % (min(xs), max(xs), min(ys), max(ys)))

print("\nroutes from the road point:")
for name, pt in (("P1", (-2.7, 0.6)), ("P2", (-1.8, -2.2)), ("P3", (0.0, 2.6)),
                 ("P4", (-3.6, -1.6)), ("P5", (1.2, 3.2))):
    p = plan(ROAD, pt)
    print("   %s %-14s %s" % (name, str(pt),
                              "path %d steps" % len(p) if p else "NO PATH"))
