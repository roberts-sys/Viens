"""Checks the world and the controller agree, before Webots ever opens them.

Run it after regenerating the world:

    python3 tools/gen_world.py
    python3 tools/verify.py

It checks the things that have actually gone wrong in the past: joint devices
the controller asks for that the world does not have, arm targets past the end
of the arm, pads with nowhere to park, and parts of the machine that would be
inside each other now that self-collision is on.
"""

import math
import os
import sys
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CTRL = os.path.join(HERE, "..", "controllers", "excavator_controller")
sys.path.insert(0, CTRL)

from site_map import OBSTACLES, FENCE           # noqa: E402

fails = []
warns = []


def check(ok, what, detail=""):
    print("  %-4s %s%s" % ("ok" if ok else "FAIL", what, ("   " + detail) if detail else ""))
    if not ok:
        fails.append(what)


def warn(ok, what, detail=""):
    if not ok:
        print("  %-4s %s%s" % ("warn", what, ("   " + detail) if detail else ""))
        warns.append(what)


# --------------------------------------------------------------------------
# Pull the controller's constants without importing it (it needs Webots).
# --------------------------------------------------------------------------
src = open(os.path.join(CTRL, "excavator_controller.py")).read()
C = {}
for name in ("BOOM_PIVOT_R", "BOOM_PIVOT_Z", "BOOM_LEN", "STICK_LEN", "TIP_OFFSET",
             "GRAB_DROP", "CUBE", "JAW_OPEN", "JAW_GRIP", "TRANSIT_Z", "APPROACH_DZ",
             "RELEASE_GAP", "MACHINE_R", "SWEEP_R", "STANDOFF", "PAD_R", "CELL",
             "HELD_TOL", "TINES", "PARK_MIN", "PARK_MAX", "SEAT_RISE",
             "EDGE_MARGIN", "MANUAL_GAIN", "BORDER_WARN_AT",
             "BORDER_WARN_FULL", "LIFT_CHECK", "GRIP_LATERAL",
             "STUCK_WINDOW", "STUCK_EPS", "DRIVE_SPEED"):
    m = re.search(r"^%s\s*=\s*([-\d.]+)" % name, src, re.M)
    assert m, "controller has no %s" % name
    C[name] = float(m.group(1))

HOMES = eval(re.search(r"^HOMES = (\{.*?^\})", src, re.M | re.S).group(1))
TOWERS = eval(re.search(r"^TOWERS = (\(.*?\))$", src, re.M).group(1))
LAYOUTS = eval(re.search(r"^LAYOUTS = (\[.*?^\])", src, re.M | re.S).group(1))

REACH = C["BOOM_LEN"] + C["STICK_LEN"]
LIMIT = FENCE - C["EDGE_MARGIN"]
N = int(2 * LIMIT / C["CELL"]) + 1


# --------------------------------------------------------------------------
print("\nworld file")
# --------------------------------------------------------------------------
for world in ("construction_site.wbt", "construction_site_lite.wbt"):
    path = os.path.join(HERE, "..", "worlds", world)
    txt = open(path).read()
    check(txt.count("{") == txt.count("}") and txt.count("[") == txt.count("]"),
          "%s brackets balance" % world,
          "%d braces, %d brackets" % (txt.count("{"), txt.count("[")))
    check("EXTERNPROTO" not in txt and ".proto" not in txt,
          "%s loads no external PROTOs" % world)
    check("selfCollision TRUE" in txt, "%s has self-collision on" % world)
    check(txt.count('contactMaterial "grip"') == int(C["TINES"]),
          "%s: all %d tines are grip material" % (world, int(C["TINES"])),
          "found %d" % txt.count('contactMaterial "grip"'))
    check(txt.count('contactMaterial "load"') == 12,
          "%s: all 12 objects are load material" % world,
          "found %d" % txt.count('contactMaterial "load"'))
    check('material1 "grip"' in txt and 'material2 "load"' in txt,
          "%s defines the grip/load friction pair" % world)
    check("site_collision" in txt, "%s has collision bodies for the props" % world)
    check("Fog {" not in txt, "%s has no fog" % world,
          "removed on request - it read as too heavy-handed")

    # every device the controller asks for must exist
    wanted = set(re.findall(r'getDevice\("([^"]+)"\)', src))
    wanted |= {"tine_%d_motor" % i for i in range(int(C["TINES"]))}
    wanted |= {"wheel_%s_motor" % n for n in ("fl", "fr", "rl", "rr")}
    wanted |= {"track_%s_%s_motor" % (tag, name) for tag in ("l", "r")
              for name in ("end0", "end1", "road0", "road1", "road2", "road3",
                           "carrier0", "carrier1")}
    wanted = {w for w in wanted if "%" not in w}
    have = set(re.findall(r'name "([a-z_0-9]+)"', txt))
    missing = sorted(wanted - have)
    check(not missing, "%s has every device the controller opens" % world,
          "missing: %s" % ", ".join(missing) if missing else "%d devices" % len(wanted))

    for d in sorted(set(re.findall(r'getFromDef\("([A-Z_%s]+)"\)', src))):
        if "%" in d:
            continue
        check("DEF %s " % d in txt, "%s defines %s" % (world, d))
    for colour in ("BLUE", "YELLOW", "BROWN", "RED", "GREEN", "WHITE"):
        check("DEF CUBE_%s " % colour in txt and "DEF ROCK_%s " % colour in txt,
              "%s defines the %s cube and rock" % (world, colour.lower()))

    # The visible track rollers are purely cosmetic spinners: they must not
    # carry a physics node (that would make them dynamic bodies for no
    # reason - 16 extra rigid bodies per machine, simulated for nothing,
    # since setVelocity() on an inf-position motor already spins a kinematic
    # joint without one) and must not add any geometry the shape count
    # doesn't already know about, since they only rearrange shapes that were
    # already being drawn as static parts of the track.
    roller_block = re.search(r'name "track_l_end0"(?:(?!HingeJoint).)*', txt, re.S)
    check(roller_block is not None and "physics" not in roller_block.group(0),
          "%s: track rollers are kinematic, not dynamic bodies" % world)


# --------------------------------------------------------------------------
print("\ninverse kinematics")
# --------------------------------------------------------------------------
def ik_local(x, y, z):
    slew = math.atan2(y, x)
    r = math.hypot(x, y)
    dr = r - C["BOOM_PIVOT_R"]
    dz = (z + C["TIP_OFFSET"]) - C["BOOM_PIVOT_Z"]
    d = math.hypot(dr, dz)
    d = min(d, REACH - 1e-3)
    d = max(d, abs(C["BOOM_LEN"] - C["STICK_LEN"]) + 1e-3)
    cos_a = (d * d + C["BOOM_LEN"] ** 2 - C["STICK_LEN"] ** 2) / (2 * C["BOOM_LEN"] * d)
    a1 = math.atan2(dz, dr) + math.acos(max(-1.0, min(1.0, cos_a)))
    bx = C["BOOM_LEN"] * math.cos(a1)
    bz = C["BOOM_LEN"] * math.sin(a1)
    a2 = math.atan2(dz - bz, dr - bx)
    return (slew, -a1, -(a2 - a1), a2, -slew)


def fk(q):
    """Joint angles back to the grab point, to prove the IK is right."""
    slew, qb, qs, qw, _ = q
    a1 = -qb
    a2 = a1 - qs
    r = C["BOOM_PIVOT_R"] + C["BOOM_LEN"] * math.cos(a1) + C["STICK_LEN"] * math.cos(a2)
    z = (C["BOOM_PIVOT_Z"] + C["BOOM_LEN"] * math.sin(a1)
         + C["STICK_LEN"] * math.sin(a2) - C["TIP_OFFSET"])
    return r * math.cos(slew), r * math.sin(slew), z


def reachable(r, z):
    """Is a target at radius r, height z, inside the arm's envelope?"""
    dr = r - C["BOOM_PIVOT_R"]
    dz = (z + C["TIP_OFFSET"]) - C["BOOM_PIVOT_Z"]
    return math.hypot(dr, dz) <= REACH - 1e-3


worst = 0.0
for r in [x / 100.0 for x in range(40, 140, 3)]:
    for z in [x / 100.0 for x in range(5, 110, 5)]:
        if not reachable(r, z):
            continue
        for a in (0.0, 1.0, -2.5, 3.0):
            tgt = (r * math.cos(a), r * math.sin(a), z)
            got = fk(ik_local(*tgt))
            worst = max(worst, max(abs(g - t) for g, t in zip(got, tgt)))
check(worst < 1e-9, "IK and FK agree everywhere in the envelope",
      "worst error %.1e m" % worst)

# every height the controller actually commands, at the working distance
S = C["STANDOFF"]
heights = []
for level in range(3):
    centre = C["CUBE"] * level + C["CUBE"] / 2
    heights += [("place level %d" % (level + 1), centre + C["RELEASE_GAP"]),
                ("approach level %d" % (level + 1), centre + C["APPROACH_DZ"])]
heights += [("grab off the ground", C["CUBE"] / 2),
            ("lift clear", C["CUBE"] / 2 + C["APPROACH_DZ"]),
            ("carry", C["TRANSIT_Z"])]
for what, z in heights:
    ok = reachable(S, z)
    dr = S - C["BOOM_PIVOT_R"]
    dz = (z + C["TIP_OFFSET"]) - C["BOOM_PIVOT_Z"]
    check(ok, "reach at %.2f m for %s" % (S, what),
          "z %.2f, arm %.0f%% extended" % (z, 100 * math.hypot(dr, dz) / REACH))


# --------------------------------------------------------------------------
print("\nself-collision clearances")
# --------------------------------------------------------------------------
# The tines hang below the grapple in a cone; the house and the tracks are the
# two things they could be swung into now that self-collision is on.
HOUSE = (-0.72, 0.52, -0.38, 0.38, 0.33, 0.83)      # x0 x1 y0 y1 z0 z1, world
TRACKS = (-0.58, 0.58, -0.42, 0.42, 0.00, 0.30)
TINE_R = 0.25            # tine tip swing radius, wide open
TINE_DROP = 0.40         # how far the tines hang below the grapple origin


def box_gap(box, cx, cy, cz, r, drop):
    """Clearance between a vertical cylinder and an axis-aligned box."""
    x0, x1, y0, y1, z0, z1 = box
    dx = max(x0 - cx, 0.0, cx - x1)
    dy = max(y0 - cy, 0.0, cy - y1)
    lo, hi = cz - drop, cz
    dz = max(z0 - hi, 0.0, lo - z1)
    return math.hypot(math.hypot(dx, dy), dz) - r


poses = [("travel", 0.95, 0.0, 0.55)]
for what, z in heights:
    poses.append((what, S, 0.0, z))
for name, x, y, z in poses:
    q = ik_local(x, y, z)
    gx, gy, gz = x, y, z + C["GRAB_DROP"]     # the grapple origin sits above the target
    gh = box_gap(HOUSE, gx, gy, gz, TINE_R, TINE_DROP)
    gt = box_gap(TRACKS, gx, gy, gz, TINE_R, TINE_DROP)
    check(gh > 0.02 and gt > 0.02, "grapple clears the machine at the %s pose" % name,
          "house %+.3f m, tracks %+.3f m" % (gh, gt))


# --------------------------------------------------------------------------
print("\narm stops")
# --------------------------------------------------------------------------
# selfCollision cannot police two solids joined by a joint, so the boom would
# otherwise fold straight through the house. These are the limits that stop it,
# and the controller must carry the same numbers so manual mode agrees.
LIMS = {}
for name in ("BOOM_LIM", "STICK_LIM", "WRIST_LIM"):
    m = re.search(r"^%s = \(([-\d.]+), ([-\d.]+)\)" % name, src, re.M)
    check(m is not None, "the controller declares %s" % name)
    if m:
        LIMS[name] = (float(m.group(1)), float(m.group(2)))

world = open(os.path.join(HERE, "..", "worlds", "construction_site.wbt")).read()
for motor, key in (("boom_motor", "BOOM_LIM"), ("stick_motor", "STICK_LIM"),
                   ("wrist_motor", "WRIST_LIM")):
    m = re.search(r'name "%s".*?minPosition ([-\d.]+).*?maxPosition ([-\d.]+)'
                  % motor, world, re.S)
    check(m is not None, "%s has stops in the world" % motor)
    if m and key in LIMS:
        got = (float(m.group(1)), float(m.group(2)))
        check(abs(got[0] - LIMS[key][0]) < 1e-6 and abs(got[1] - LIMS[key][1]) < 1e-6,
              "%s stops match the controller" % motor,
              "world %s, controller %s" % (got, LIMS[key]))

# Webots requires the physical stops to straddle zero and to contain the motor
# range, or it refuses to load the world.
for motor in ("boom_motor", "stick_motor", "wrist_motor"):
    # the stops sit in the jointParameters just above the motor, so the match
    # must not be allowed to run back into the joint before it
    blk = re.search(r"minStop ([-\d.]+)\s+maxStop ([-\d.]+)"
                    r"(?:(?!minStop).)*?name \"%s\""
                    r"(?:(?!minStop).)*?minPosition ([-\d.]+)"
                    r"\s+maxPosition ([-\d.]+)" % motor, world, re.S)
    check(blk is not None, "%s has physical stops too" % motor)
    if blk:
        lo, hi, plo, phi = (float(blk.group(i)) for i in range(1, 5))
        check(lo <= 0 <= hi, "%s stops straddle zero as Webots requires" % motor,
              "minStop %+.2f, maxStop %+.2f" % (lo, hi))
        check(lo <= plo and phi <= hi, "%s motor range sits inside its stops" % motor,
              "%.2f..%.2f inside %.2f..%.2f" % (plo, phi, lo, hi))

# the stops must not bind on anything the routine actually asks for
for level in range(3):
    centre = C["CUBE"] * level + C["CUBE"] / 2
    for z in (centre + C["RELEASE_GAP"], centre + C["APPROACH_DZ"]):
        for r in (C["PARK_MIN"], C["STANDOFF"], C["PARK_MAX"]):
            q = ik_local(r, 0.0, z)
            inside = (LIMS["BOOM_LIM"][0] <= q[1] <= LIMS["BOOM_LIM"][1]
                      and LIMS["STICK_LIM"][0] <= q[2] <= LIMS["STICK_LIM"][1]
                      and LIMS["WRIST_LIM"][0] <= q[3] <= LIMS["WRIST_LIM"][1])
            check(inside, "stops leave room for level %d at %.2f m, z %.2f"
                  % (level + 1, r, z))

check(C["PARK_MIN"] - C["CUBE"] * math.sqrt(2) / 2 > C["SWEEP_R"],
      "even the closest allowed parking clears the counterweight sweep",
      "%.2f m nearest corner vs %.2f m sweep"
      % (C["PARK_MIN"] - C["CUBE"] * math.sqrt(2) / 2, C["SWEEP_R"]))
check("clamp_arm" in src and src.count("clamp_arm(") >= 3,
      "manual mode clamps the arm to the same stops")
check(0.0 < C["MANUAL_GAIN"] <= 1.0, "manual gain is a sensible fraction",
      "%.0f%% of full speed" % (100 * C["MANUAL_GAIN"]))

# The border warning must never fire while the machine is driving itself: the
# planner is kept further inside the fence than the warning ever reaches.
check(C["EDGE_MARGIN"] > C["BORDER_WARN_AT"],
      "the autonomous routine never sets the border warning off",
      "planner stops %.2f m from the fence, warning starts at %.2f m"
      % (C["EDGE_MARGIN"], C["BORDER_WARN_AT"]))
check(C["BORDER_WARN_FULL"] < C["BORDER_WARN_AT"],
      "the border warning fades in rather than snapping on",
      "solid at %.2f m, gone by %.2f m" % (C["BORDER_WARN_FULL"], C["BORDER_WARN_AT"]))
check("setLabel" in src, "the border warning is drawn over the 3D view")

# The beacon must actually vary, not just sit on one colour, and the world
# must define the DEF the controller looks it up by (the generic getFromDef
# loop above already checks BEACON_MAT exists in both worlds).
BEACON_LOW = eval(re.search(r"^BEACON_LOW = (\(.*?\))", src, re.M).group(1))
BEACON_HIGH = eval(re.search(r"^BEACON_HIGH = (\(.*?\))", src, re.M).group(1))
check(BEACON_LOW != BEACON_HIGH, "the beacon's two extremes are actually different colours")
m = re.search(r"^BEACON_PERIOD = ([\d.]+)", src, re.M)
check(m is not None and 1.0 < float(m.group(1)) < 6.0,
      "the beacon pulses at a slow, deliberate rate",
      "%.2f s per full pulse" % float(m.group(1)) if m else "not found")
check("blink_beacon()" in src and "def blink_beacon" in src,
      "the beacon is driven every step")
check("math.cos" in src and "glow = " in src,
      "the beacon fades smoothly rather than snapping between two states")
check("_beacon_last" in src and "> 0.01" in src,
      "the beacon field is only written when the colour has moved enough to matter")

# The machine must notice it is wedged against something the static map did
# not know about, and try a different approach, rather than either freezing
# or silently pretending a failed leg succeeded.
check("class Stuck" in src, "there is a Stuck exception to signal no progress")
check("def progress_guard" in src, "a shared progress guard exists")
check(src.count("guard()") >= 2,
      "the progress guard runs inside both goto() and creep()",
      "found %d call sites" % src.count("guard()"))
check("except Stuck" in src, "something catches Stuck and reacts to it")
check(re.search(r"def dock_at\([^)]*attempts", src) is not None,
      "dock_at() takes multiple attempts, so a stuck leg can be rerouted")
# a reroute is only real if standoff_spot()/plan() run again inside the retry
# loop, rather than the same route being tried a second time
dock_body = re.search(r"def dock_at\(.*?\n\n\ndef ", src, re.S)
check(dock_body is not None and dock_body.group(0).count("standoff_spot(") >= 1
      and "for attempt in range(attempts)" in dock_body.group(0),
      "the retry recomputes standoff_spot()/plan() from wherever it stopped,"
      " not just repeating the same route")
check(C["STUCK_WINDOW"] < 10.0,
      "a stuck leg is noticed in well under the old 60 s flat timeout",
      "%.1f s" % C["STUCK_WINDOW"])
# goto()'s slowest commanded speed is a floor of 0.3 x DRIVE_SPEED (see the
# "v = DRIVE_SPEED * min(1.0, max(0.3, dist))" line): even crawling at that
# floor, genuinely-moving-but-slow driving must clear STUCK_EPS well inside
# one STUCK_WINDOW, or ordinary slow driving would trip the detector.
min_speed = C["DRIVE_SPEED"] * 0.3
check(min_speed * C["STUCK_WINDOW"] > 3 * C["STUCK_EPS"],
      "the slowest normal driving speed comfortably clears the stuck threshold",
      "%.2f m/s floor x %.1f s window = %.2f m, vs a %.2f m epsilon"
      % (min_speed, C["STUCK_WINDOW"], min_speed * C["STUCK_WINDOW"], C["STUCK_EPS"]))

# Proof of grip has to be more than nearness, or an object lying on the ground
# under a low arm looks held.
check("gripped(" in src and "ground_z" in src,
      "a grab is proved by the object rising, not by how near it is")
check(C["LIFT_CHECK"] > C["GRIP_LATERAL"], "the proof lift is bigger than the slop it allows",
      "lifts %.2f m, allows %.2f m sideways" % (C["LIFT_CHECK"], C["GRIP_LATERAL"]))


# --------------------------------------------------------------------------
print("\nbackground structures vs the fence")
# --------------------------------------------------------------------------
# An angled structure placed just beyond the fence can still have its far end
# swing back across a corner and clip the fence panels - the centreline can
# look clear while the actual (wider) footprint is not. Caught this once by
# eye on the conveyor (its yaw sent the belt back across the north-east
# corner by 0.02 m); this checks the real footprint, not just where it starts.
#
# Clearing the fence is not enough on its own, either: the first fix cleared
# the fence but grazed a skyline block instead (its footprint was never
# checked against anything else nearby). This checks the conveyor's whole
# footprint against the fence, every skyline block, and both cranes, all
# pulled from gen_world.py's own source rather than copied - so none of them
# can silently drift out of sync with what actually gets built.
gw_src = open(os.path.join(HERE, "gen_world.py")).read()
m = re.search(r'p\.append\(conveyor\(\(([-\d.]+), ([-\d.]+), 0\), ([-\d.]+)\)\)', gw_src)
check(m is not None, "conveyor placement found in gen_world.py")
if m:
    cx, cy, cyaw = float(m.group(1)), float(m.group(2)), float(m.group(3))
    HALF_W = 0.6   # belt width plus its side rails
    footprint = []
    for i in range(61):
        s = 9.0 * i / 60.0
        bx, by = cx + s * math.cos(cyaw), cy + s * math.sin(cyaw)
        px, py = -math.sin(cyaw), math.cos(cyaw)
        footprint += [(bx + w * px, by + w * py) for w in (-HALF_W, HALF_W)]

    worst = min(max(abs(x), abs(y)) - FENCE for x, y in footprint)
    check(worst > 0.3, "the conveyor's whole footprint clears the fence",
          "worst clearance %+.3f m" % worst)

    sky_m = re.search(r"for t2, s2, h2, y2 in \((.*?)\):\n\s*p\.append\(skyline",
                      gw_src, re.S)
    check(sky_m is not None, "skyline blocks found in gen_world.py")
    if sky_m:
        blocks = re.findall(
            r"\(\(([-\d.]+), ([-\d.]+)\), \(([-\d.]+), ([-\d.]+)\)", sky_m.group(1))
        worst = 1e9
        for bx, by, sx, sy in blocks:
            bx, by, sx, sy = float(bx), float(by), float(sx) + 0.08, float(sy) + 0.08
            for x, y in footprint:
                gap = max(abs(x - bx) - sx / 2, abs(y - by) - sy / 2)
                worst = min(worst, gap)
        check(worst > 0.3, "the conveyor's footprint clears every skyline block",
              "worst clearance %+.3f m" % worst)

    cranes = re.findall(r'p\.append\(crane\(\(([-\d.]+), ([-\d.]+), 0\)', gw_src)
    check(len(cranes) >= 1, "at least one crane found in gen_world.py")
    CRANE_R = 9.0   # mast to jib tip, generous - see crane()
    worst = 1e9
    for cxs, cys in cranes:
        ccx, ccy = float(cxs), float(cys)
        for x, y in footprint:
            worst = min(worst, math.hypot(x - ccx, y - ccy) - CRANE_R)
    check(worst > 0.3, "the conveyor's footprint clears both cranes",
          "worst clearance %+.3f m" % worst)


print("\nsite: parking and routes")
# --------------------------------------------------------------------------
PADS = [(x, y, C["PAD_R"]) for x, y in HOMES.values()]
PADS += [(x, y, C["PAD_R"]) for x, y in TOWERS]


def cell_of(x, y):
    return (int(round((x + LIMIT) / C["CELL"])), int(round((y + LIMIT) / C["CELL"])))


def world_of(i, j):
    return (i * C["CELL"] - LIMIT, j * C["CELL"] - LIMIT)


GRID = []
for i in range(N):
    col = []
    for j in range(N):
        x, y = world_of(i, j)
        bad = abs(x) > LIMIT or abs(y) > LIMIT
        if not bad:
            for ox, oy, orad in OBSTACLES + PADS:
                if (x - ox) ** 2 + (y - oy) ** 2 < (orad + C["MACHINE_R"]) ** 2:
                    bad = True
                    break
        col.append(bad)
    GRID.append(col)

free = sum(not GRID[i][j] for i in range(N) for j in range(N))
print("  grid %dx%d, %d cells drivable (%.0f%%)" % (N, N, free, 100.0 * free / (N * N)))

from collections import deque                     # noqa: E402

start = cell_of(0, 0)
check(not GRID[start[0]][start[1]], "the machine's start position is clear")
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
check(len(seen) > 0.9 * free, "the drivable area is one connected yard",
      "%d of %d cells reachable from the start" % (len(seen), free))

check(C["STANDOFF"] > C["SWEEP_R"],
      "the working distance clears the counterweight sweep",
      "%.2f m standoff vs %.2f m sweep" % (C["STANDOFF"], C["SWEEP_R"]))

named = list(HOMES.items()) + [("build site %d" % (i + 1), t) for i, t in enumerate(TOWERS)]
spots = {}
for name, (tx, ty) in named:
    others = [(px, py, pr) for px, py, pr in PADS
              if math.hypot(px - tx, py - ty) > 0.05]
    good = []
    for k in range(24):
        b = k * math.pi / 12
        sx, sy = tx + S * math.cos(b), ty + S * math.sin(b)
        c = cell_of(sx, sy)
        if not (0 <= c[0] < N and 0 <= c[1] < N) or GRID[c[0]][c[1]] or c not in seen:
            continue
        if any(math.hypot(sx - px, sy - py) < pr + C["MACHINE_R"]
               for px, py, pr in others):
            continue
        good.append((sx, sy))
    check(len(good) >= 4, "somewhere to park by %s" % name,
          "%d of 24 bearings usable" % len(good))
    warn(len(good) >= 8, "only %d parking bearings by %s" % (len(good), name))
    if good:
        spots[name] = good[0]

# and the machine must be able to get from any one of them to any other
missing = []
for a, pa in spots.items():
    for b, pb in spots.items():
        if a >= b:
            continue
        if cell_of(*pa) not in seen or cell_of(*pb) not in seen:
            missing.append("%s -> %s" % (a, b))
check(not missing, "every pad's parking spot is reachable from every other",
      "; ".join(missing) if missing else "%d pads" % len(spots))

# nothing may be standing inside a prop
for name, (tx, ty) in named:
    close = [(ox, oy, orad) for ox, oy, orad in OBSTACLES
             if math.hypot(tx - ox, ty - oy) < orad + C["PAD_R"]]
    check(not close, "%s is not inside a prop" % name)

# The counterweight sweeps a circle when the machine slews. A finished stack
# stands taller than the counterweight is off the ground, so the only thing
# keeping them apart is parking far enough away.
top = C["CUBE"] * max(len(s) for lay in LAYOUTS for s in lay)
half_diag = C["CUBE"] * math.sqrt(2) / 2
gap = (C["STANDOFF"] - half_diag) - C["SWEEP_R"]
check(gap > 0.05, "the counterweight swings clear of a finished stack",
      "%.2f m stack, nearest corner %.3f m out, sweep %.2f m, clearance %+.3f m"
      % (top, C["STANDOFF"] - half_diag, C["SWEEP_R"], gap))


print("\n%s   %d checks failed, %d warnings"
      % ("PASS" if not fails else "FAIL", len(fails), len(warns)))
sys.exit(1 if fails else 0)
