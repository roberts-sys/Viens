"""Excavator controller.

The arm has five axes: slew, boom, stick, wrist and a rotator that spins the
five-tine grapple about the vertical.

Repeats forever:
  1. stacks the six objects into two towers of three, one at a time,
  2. takes both towers apart again, returning each object to its home pad,
  3. rebuilds them in a different order (different objects end up on top),
  4. takes those apart too.

Press C or R in the 3D view to switch between the cubes and the rocks.

The arm is driven by inverse kinematics: the code says "put the grab point at
this (x, y, z) in the world" and solves for the four joint angles that do it.
"""

from controller import Supervisor
import math

# --------------------------------------------------------------------------
# Machine geometry. These must match construction_site.wbt.
# --------------------------------------------------------------------------
BOOM_PIVOT_R = 0.30   # boom pivot: how far forward of the slew axis
BOOM_PIVOT_Z = 0.50   # boom pivot: height above the ground
BOOM_LEN = 0.62       # boom pivot  -> stick pivot
STICK_LEN = 0.52      # stick pivot -> grapple pivot
TIP_OFFSET = 0.26     # wrist pivot -> the grab point between the tines
GRAB_DROP = 0.19      # grapple head origin -> that same grab point

CUBE = 0.16           # cube edge length

# --------------------------------------------------------------------------
# Motion settings
# --------------------------------------------------------------------------
JAW_OPEN = 0.62       # radians, tines splayed wide
JAW_CLOSED = 0.10     # radians, tines closed around a cube
TINES = 5

TRANSIT_Z = 0.78      # height the grab point travels at while carrying
APPROACH_DZ = 0.25    # how far above a cube to line up before dropping onto it
RELEASE_GAP = 0.008   # let go a few mm high so the cube settles itself

# --------------------------------------------------------------------------
# Where things live. (x, y) in world metres; the machine sits at the origin.
# --------------------------------------------------------------------------
HOMES = {
    "white":  (0.6557,  0.7813),
    "green":  (0.8356,  0.5851),
    "red":    (0.9585,  0.3488),
    "brown":  (1.0161,  0.0889),
    "yellow": (1.0045, -0.1771),
    "blue":   (0.9244, -0.4311),
}
TOWERS = ((0.5974, -0.6186), (0.2080, -0.8345))

# Six objects go up as two stacks of three. A single stack of six would be
# 0.96 m tall: past the arm's reach for the approach above it, and inside the
# circle the counterweight sweeps when the machine slews.
#
# Each layout is [bottom -> top, bottom -> top]. The second puts different
# objects on top of each stack.
LAYOUTS = [
    [["blue", "yellow", "brown"], ["red", "green", "white"]],
    [["white", "red", "blue"], ["brown", "green", "yellow"]],
]

# --------------------------------------------------------------------------
# Driving
# --------------------------------------------------------------------------
WORK = (0.0, 0.0, 0.0)        # where the arm can reach every pad: x, y, heading
ROAD = (-1.9, 0.0)            # first clear point behind the machine
PATROL = ((-2.7, 0.6), (0.0, 2.6), (-1.8, -2.2))

WHEEL_R = 0.13                # wheel radius, for turning m/s into rad/s
DRIVE_SPEED = 0.45            # m/s
TURN_SPEED = 0.9              # rad/s
MACHINE_R = 0.75              # footprint radius used for planning
CELL = 0.15
LIMIT = 5.7

# Everything the machine must not drive into. Kept in step with the world file;
# the six home pads and two tower pads are added below.
OBSTACLES = [
    (2.9, 1.9, 0.16), (3.2, 0.8, 0.16), (3.2, -0.7, 0.16), (2.9, -1.8, 0.16),
    (2.0, 2.8, 0.16), (1.9, -2.9, 0.16), (3.9, 1.5, 0.16), (4.0, -1.2, 0.16),
    (0.9, 4.5, 0.85), (2.7, 4.5, 0.85), (-0.9, 4.5, 0.85), (4.5, 4.5, 0.85),
    (-3.8, -4.3, 0.85), (-2.0, -4.8, 0.85),
    (-4.8, -2.4, 1.70), (-4.4, 3.4, 2.00), (-2.6, 4.4, 0.40), (1.1, -5.0, 0.90),
    (3.4, 3.4, 0.65), (4.4, 2.9, 0.65), (4.5, -3.1, 0.90), (-3.2, -5.0, 1.50),
    (-0.65, -4.85, 0.55), (2.6, -4.7, 0.50),
    (3.6, 2.8, 1.30), (3.4, -4.6, 1.00), (-4.6, 2.2, 1.50), (-1.5, 4.6, 1.10),
    (5.0, -0.6, 0.90), (4.6, 2.2, 0.55), (-0.7, 5.0, 0.80), (3.9, -3.9, 0.50),
    (5.2, 3.4, 0.50), (2.9, 3.9, 0.25), (-2.2, -4.6, 0.25), (-4.6, -4.6, 1.75),
]

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------
robot = Supervisor()
timestep = int(robot.getBasicTimeStep())

slew_m = robot.getDevice("slew_motor")
boom_m = robot.getDevice("boom_motor")
stick_m = robot.getDevice("stick_motor")
wrist_m = robot.getDevice("wrist_motor")
rotator_m = robot.getDevice("rotator_motor")
tine_m = [robot.getDevice("tine_%d_motor" % i) for i in range(TINES)]

# The rotator is the fifth axis: slew, boom, stick, wrist, rotate.
arm_motors = [slew_m, boom_m, stick_m, wrist_m, rotator_m]

arm_sensors = []
for name in ("slew_sensor", "boom_sensor", "stick_sensor", "wrist_sensor",
             "rotator_sensor"):
    s = robot.getDevice(name)
    s.enable(timestep)
    arm_sensors.append(s)
slew_s, rotator_s = arm_sensors[0], arm_sensors[4]

tine_s = robot.getDevice("tine_0_sensor")
tine_s.enable(timestep)

wheel_m = [robot.getDevice("wheel_%s_motor" % n) for n in ("fl", "fr", "rl", "rr")]
for m in wheel_m:
    m.setPosition(float("inf"))
    m.setVelocity(0.0)

# The three cameras. Webots shows each one as a small overlay window.
for cam_name in ("camera_front_left", "camera_front_right", "camera_rear"):
    robot.getDevice(cam_name).enable(timestep * 4)

grapple_node = robot.getFromDef("GRAPPLE")

COLOURS = ("blue", "yellow", "brown", "red", "green", "white")
SETS = {
    "cube": {c: robot.getFromDef("CUBE_%s" % c.upper()) for c in COLOURS},
    "rock": {c: robot.getFromDef("ROCK_%s" % c.upper()) for c in COLOURS},
}
STASH = (0.0, -25.0)      # where the unused set waits, well outside the site

keyboard = robot.getKeyboard()
keyboard.enable(timestep)

base = robot.getSelf()

active = "cube"   # which set the machine is working with right now
held = None       # colour of the object currently in the grapple, or None
manual = False    # True while the operator is driving


class Quit(Exception):
    """Raised when Webots shuts the simulation down."""


class ModeChange(Exception):
    """Raised when the operator switches sets, or enters/leaves manual mode."""


def objs():
    """The set currently in play."""
    return SETS[active]


def park_set(name, at_home):
    """Put a set on its home pads, or away off-site."""
    for i, colour in enumerate(COLOURS):
        node = SETS[name][colour]
        if node is None:
            continue
        if at_home:
            x, y = HOMES[colour]
        else:
            x, y = STASH[0] + i * 0.6, STASH[1]
        node.getField("translation").setSFVec3f([x, y, CUBE / 2 + 0.001])
        node.getField("rotation").setSFRotation([0, 0, 1, 0])
        node.resetPhysics()


KEYS = set()          # keys held down right now
_prev_keys = set()

UP, DOWN, LEFT, RIGHT = 315, 317, 314, 316


def poll_keyboard():
    """M toggles manual driving; C and R swap the cubes and rocks."""
    global active, held, manual, KEYS, _prev_keys
    keys = set()
    k = keyboard.getKey()
    while k != -1:
        keys.add(k & 0xFFFF)
        k = keyboard.getKey()
    KEYS = keys
    pressed = keys - _prev_keys          # act on the press, not on the hold
    _prev_keys = keys

    if ord("M") in pressed:
        manual = not manual
        halt()
        raise ModeChange
    for ch, want in (("C", "cube"), ("R", "rock")):
        if ord(ch) in pressed and want != active:
            active = want
            held = None
            park_set("cube", active == "cube")
            park_set("rock", active == "rock")
            raise ModeChange


# --------------------------------------------------------------------------
# Where the machine is, and how to drive it
# --------------------------------------------------------------------------
def base_pose():
    """The machine's own (x, y, z, heading) in world coordinates."""
    p = base.getPosition()
    m = base.getOrientation()
    return p[0], p[1], p[2], math.atan2(m[3], m[0])


def to_base(wx, wy, wz):
    """A world point expressed in the machine's own frame.

    Once the machine can drive, the pads no longer sit at fixed places relative
    to it, so every arm target goes through here first.
    """
    bx, by, bz, yaw = base_pose()
    dx, dy = wx - bx, wy - by
    c, s = math.cos(-yaw), math.sin(-yaw)
    return (dx * c - dy * s, dx * s + dy * c, wz - bz)


def wheels(left, right):
    """Left and right track speeds in m/s (skid steer)."""
    wheel_m[0].setVelocity(left / WHEEL_R)
    wheel_m[2].setVelocity(left / WHEEL_R)
    wheel_m[1].setVelocity(right / WHEEL_R)
    wheel_m[3].setVelocity(right / WHEEL_R)


def halt():
    wheels(0.0, 0.0)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


# ---- the map: a grid of cells the machine is allowed to occupy ----
PADS = [(x, y, 0.18) for x, y in HOMES.values()] + [(x, y, 0.20) for x, y in TOWERS]
N = int(2 * LIMIT / CELL) + 1


def cell_of(x, y):
    return (int(round((x + LIMIT) / CELL)), int(round((y + LIMIT) / CELL)))


def world_of(i, j):
    return (i * CELL - LIMIT, j * CELL - LIMIT)


def build_grid():
    grid = []
    for i in range(N):
        col = []
        for j in range(N):
            x, y = world_of(i, j)
            bad = abs(x) > LIMIT or abs(y) > LIMIT
            if not bad:
                for ox, oy, orad in OBSTACLES + PADS:
                    if (x - ox) ** 2 + (y - oy) ** 2 < (orad + MACHINE_R) ** 2:
                        bad = True
                        break
            col.append(bad)
        grid.append(col)
    return grid


GRID = build_grid()


def plan(start, goal):
    """A* across the free cells. Returns a list of world points, or None."""
    import heapq
    s, g = cell_of(*start), cell_of(*goal)
    if GRID[s[0]][s[1]] or GRID[g[0]][g[1]]:
        return None
    openq = [(0.0, s)]
    came, cost = {s: None}, {s: 0.0}
    while openq:
        _, cur = heapq.heappop(openq)
        if cur == g:
            out = []
            while cur:
                out.append(world_of(*cur))
                cur = came[cur]
            out.reverse()
            # thin the path out so the follower gets corners, not every cell
            return [out[0]] + out[1::4] + [out[-1]]
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


def goto(tx, ty, tol=0.18, timeout=45.0):
    """Drive to a point: turn towards it, then run at it, correcting as we go."""
    deadline = robot.getTime() + timeout
    while True:
        x, y, _, yaw = base_pose()
        dist = math.hypot(tx - x, ty - y)
        if dist < tol or robot.getTime() > deadline:
            halt()
            return dist < tol
        err = wrap(math.atan2(ty - y, tx - x) - yaw)
        if abs(err) > 0.35:
            turn = TURN_SPEED * (1 if err > 0 else -1) * 0.5
            wheels(-turn, turn)
        else:
            v = DRIVE_SPEED * min(1.0, max(0.25, dist))
            corr = max(-0.35, min(0.35, err)) * 0.5
            wheels(v * (1 - corr), v * (1 + corr))
        step()


def face(heading, tol=0.06, timeout=20.0):
    deadline = robot.getTime() + timeout
    while True:
        _, _, _, yaw = base_pose()
        err = wrap(heading - yaw)
        if abs(err) < tol or robot.getTime() > deadline:
            halt()
            return
        turn = TURN_SPEED * (1 if err > 0 else -1) * min(1.0, max(0.25, abs(err)))
        wheels(-turn * 0.5, turn * 0.5)
        step()


def creep(distance, timeout=25.0):
    """Straight forward (or back, if negative) - used to dock at the work spot."""
    x0, y0, _, _ = base_pose()
    deadline = robot.getTime() + timeout
    sign = 1.0 if distance > 0 else -1.0
    while True:
        x, y, _, _ = base_pose()
        if math.hypot(x - x0, y - y0) >= abs(distance) or robot.getTime() > deadline:
            halt()
            return
        wheels(sign * DRIVE_SPEED * 0.6, sign * DRIVE_SPEED * 0.6)
        step()


def drive_route(goal, label):
    """Plan a route to a point and follow it, reporting what it found."""
    x, y, _, _ = base_pose()
    path = plan((x, y), goal)
    if path is None:
        print("    no clear route to %s - staying put" % label)
        return False
    print("    driving to %s: %d waypoints" % (label, len(path)))
    for wx, wy in path[1:]:
        goto(wx, wy, tol=0.22)
    return True


def travel_pose():
    """Fold the arm in before moving off."""
    drive(ik_local(0.62, 0.0, 0.62), JAW_CLOSED)


def grab_point():
    """World position of the point between the jaws."""
    p = grapple_node.getPosition()
    m = grapple_node.getOrientation()      # row-major 3x3
    # the grab point sits TIP_OFFSET down the grapple's own -z axis
    return (p[0] - m[2] * GRAB_DROP,
            p[1] - m[5] * GRAB_DROP,
            p[2] - m[8] * GRAB_DROP)


def carry():
    """Keep the held cube locked under the grapple.

    Called every simulation step. Rather than relying on friction between the
    jaws (which is fragile), the cube is pinned to the grapple's grab point and
    its velocity is cleared, so it can never be dropped or shaken loose.
    """
    if held is None:
        return
    gx, gy, gz = grab_point()
    node = objs()[held]
    node.getField("translation").setSFVec3f([gx, gy, gz - CUBE / 2])
    # the cube turns with the grapple head: slew plus whatever the rotator adds
    node.getField("rotation").setSFRotation(
        [0, 0, 1, slew_s.getValue() + rotator_s.getValue()])
    node.resetPhysics()


def step(n=1):
    for _ in range(n):
        carry()
        if robot.step(timestep) == -1:
            raise Quit
        poll_keyboard()


def settle(seconds):
    step(max(1, int(seconds * 1000 / timestep)))


# --------------------------------------------------------------------------
# Inverse kinematics
# --------------------------------------------------------------------------
def ik_local(x, y, z):
    """Joint angles putting the grab point at (x, y, z) in the MACHINE's frame.

    The grapple is always kept hanging vertically, which leaves a two-link
    planar problem (boom + stick) once the slew angle is taken care of.
    """
    slew = math.atan2(y, x)
    r = math.hypot(x, y)

    # The stick tip has to sit TIP_OFFSET directly above the grab point.
    dr = r - BOOM_PIVOT_R
    dz = (z + TIP_OFFSET) - BOOM_PIVOT_Z
    d = math.hypot(dr, dz)
    d = min(d, BOOM_LEN + STICK_LEN - 1e-3)
    d = max(d, abs(BOOM_LEN - STICK_LEN) + 1e-3)

    # Elbow-up solution: boom raised, stick angled down — an excavator's
    # natural working posture.
    cos_a = (d * d + BOOM_LEN ** 2 - STICK_LEN ** 2) / (2 * BOOM_LEN * d)
    a1 = math.atan2(dz, dr) + math.acos(max(-1.0, min(1.0, cos_a)))

    # a1 and a2 are the boom's and stick's angles above horizontal.
    bx = BOOM_LEN * math.cos(a1)
    bz = BOOM_LEN * math.sin(a1)
    a2 = math.atan2(dz - bz, dr - bx)

    # Convert to Webots joint angles. The wrist angle cancels the boom and
    # stick rotations so the grapple stays plumb, and the rotator cancels the
    # slew so the tines keep a constant heading as the machine swings round.
    return (slew, -a1, -(a2 - a1), a2, -slew)


def ik(x, y, z):
    """World target -> joint angles, allowing for wherever the machine is parked."""
    return ik_local(*to_base(x, y, z))


# --------------------------------------------------------------------------
# Motion
# --------------------------------------------------------------------------
def set_jaws(opening):
    """Open or close all five tines together (negative angle swings them out)."""
    for m in tine_m:
        m.setPosition(-opening)


def drive(q, jaws, tol=0.012, timeout=12.0):
    """Command the arm to joint angles q and wait until it gets there."""
    for m, target in zip(arm_motors, q):
        m.setPosition(target)
    set_jaws(jaws)

    deadline = robot.getTime() + timeout
    while True:
        step()
        arm_err = max(abs(s.getValue() - t) for s, t in zip(arm_sensors, q))
        jaw_err = abs(tine_s.getValue() + jaws)
        if arm_err < tol and jaw_err < 0.06:
            return
        if robot.getTime() > deadline:
            return


def transfer(colour, dest_xy, level):
    """Move one cube to dest_xy at the given stack level (0 = on the ground)."""
    global held

    # Ask the simulator where the cube actually is, rather than assuming.
    sx, sy, sz = objs()[colour].getPosition()
    src_top = sz + CUBE / 2
    dx, dy = dest_xy
    dst_top = CUBE * (level + 1)

    # line up above the cube, drop onto it, close the jaws
    drive(ik(sx, sy, TRANSIT_Z), JAW_OPEN)
    drive(ik(sx, sy, src_top + APPROACH_DZ), JAW_OPEN)
    drive(ik(sx, sy, src_top), JAW_OPEN)
    set_jaws(JAW_CLOSED)
    settle(0.7)
    held = colour
    settle(0.3)

    # carry it across at a height that clears the tower
    drive(ik(sx, sy, TRANSIT_Z), JAW_CLOSED)
    drive(ik(dx, dy, TRANSIT_Z), JAW_CLOSED)

    # set it down and let go
    drive(ik(dx, dy, dst_top + APPROACH_DZ), JAW_CLOSED)
    drive(ik(dx, dy, dst_top + RELEASE_GAP), JAW_CLOSED)
    held = None
    objs()[colour].resetPhysics()
    settle(0.4)
    drive(ik(dx, dy, dst_top + APPROACH_DZ), JAW_OPEN)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def manual_loop():
    """Hand the machine over to the operator until M is pressed again."""
    print("")
    print("-" * 62)
    print("MANUAL MODE - the machine is yours (press M to hand it back)")
    print("   arrow keys : drive and steer")
    print("   Q / E      : slew the body left / right")
    print("   W / S      : boom up / down")
    print("   A / D      : stick in / out")
    print("   T / G      : rotate the grapple")
    print("   Z / X      : close / open the tines")
    print("-" * 62)

    q = [s.getValue() for s in arm_sensors]
    jaw = JAW_OPEN
    RATE = timestep / 1000.0

    while True:
        v = t = 0.0
        if UP in KEYS:
            v += DRIVE_SPEED
        if DOWN in KEYS:
            v -= DRIVE_SPEED
        if LEFT in KEYS:
            t -= TURN_SPEED * 0.30
        if RIGHT in KEYS:
            t += TURN_SPEED * 0.30
        wheels(v - t, v + t)

        for lo, hi, idx, rate in ((ord("E"), ord("Q"), 0, 0.7),
                                  (ord("S"), ord("W"), 1, 0.5),
                                  (ord("D"), ord("A"), 2, 0.6),
                                  (ord("G"), ord("T"), 4, 0.8)):
            if lo in KEYS:
                q[idx] -= rate * RATE
            if hi in KEYS:
                q[idx] += rate * RATE
        # keep the grapple hanging plumb whatever the boom and stick do
        q[3] = -(q[1] + q[2])
        if ord("Z") in KEYS:
            jaw = max(JAW_CLOSED, jaw - 1.2 * RATE)
        if ord("X") in KEYS:
            jaw = min(JAW_OPEN, jaw + 1.2 * RATE)

        for m, target in zip(arm_motors, q):
            m.setPosition(target)
        set_jaws(jaw)
        step()


def dock():
    """Line up behind the work spot, then creep forward onto it."""
    goto(ROAD[0], ROAD[1], tol=0.30)
    face(0.0)
    x, _, _, _ = base_pose()
    creep(WORK[0] - x)
    face(0.0)
    print("  docked at the work spot")


def patrol():
    """A lap of the site, planned around everything the machine knows about."""
    print("  --- leaving the work spot for a lap of the site")
    travel_pose()
    face(0.0)
    creep(ROAD[0] + 0.15)
    for i, pt in enumerate(PATROL):
        drive_route(pt, "patrol point %d" % (i + 1))
    drive_route(ROAD, "the work approach")
    dock()


def run():
    """Build and dismantle both stacks, over and over, with whatever is in play."""
    drive(ik_local(0.95, 0.0, 0.60), JAW_OPEN)
    cycle = 1
    while True:
        for layout in LAYOUTS:
            print("\n=== cycle %d (%ss)" % (cycle, active))
            for t, stack in enumerate(layout):
                print("  stack %d:  %s  (bottom -> top)" % (t + 1, " / ".join(stack)))
                for level, colour in enumerate(stack):
                    print("    placing %-6s at level %d" % (colour, level + 1))
                    transfer(colour, TOWERS[t], level)

            print("  --- taking both stacks apart")
            for t in reversed(range(len(layout))):
                for level in reversed(range(len(layout[t]))):
                    colour = layout[t][level]
                    print("    returning %-6s to its home pad" % colour)
                    transfer(colour, HOMES[colour], 0)

            patrol()
            drive(ik_local(0.95, 0.0, 0.60), JAW_OPEN)

        cycle += 1


def main():
    step()  # one step so the supervisor can read the scene

    missing = [n for n, s in SETS.items() if any(v is None for v in s.values())]
    if missing:
        print("WARNING: no nodes found for: %s" % ", ".join(missing))

    park_set("cube", True)
    park_set("rock", False)

    print("=" * 62)
    print("Excavator ready.")
    print("  Click the 3D view, then press:")
    print("     M  - take manual control / hand it back")
    print("     C  - work with the CUBES")
    print("     R  - work with the ROCKS")
    print("=" * 62)

    while True:
        try:
            if manual:
                manual_loop()
            else:
                print("\n>>> AUTONOMOUS (%ss) <<<\n" % active)
                run()
        except ModeChange:
            halt()


try:
    main()
except Quit:
    pass
