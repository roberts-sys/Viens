"""Excavator controller.

The arm has five axes: slew, boom, stick, wrist and a rotator that spins the
five-tine grapple about the vertical.

For each object in turn the machine plans a route across the yard, parks at
arm's length from it, closes the grapple round it, drives to a build site and
sets it down. Six objects go up as two towers of three, then come down again
onto their home pads, then go up in a different order.

Press M in the 3D view to take over and drive it yourself, C or R to switch
between the cubes and the rocks.

Nothing is teleported. The grapple holds an object because its five tines close
to a circle 0.12 m across, which is narrower than the 0.16 m object inside
them - the object physically cannot fall out, exactly as with a real grapple.
"""

from controller import Supervisor
import math

from site_map import OBSTACLES, FENCE

# --------------------------------------------------------------------------
# Machine geometry. These must match construction_site.wbt.
# --------------------------------------------------------------------------
BOOM_PIVOT_R = 0.30   # boom pivot: how far forward of the slew axis
BOOM_PIVOT_Z = 0.50   # boom pivot: height above the ground
BOOM_LEN = 0.62       # boom pivot  -> stick pivot
STICK_LEN = 0.52      # stick pivot -> grapple pivot
TIP_OFFSET = 0.385    # wrist pivot -> the centre of a held object
GRAB_DROP = 0.315     # grapple head origin -> that same point

CUBE = 0.16           # object edge length

# --------------------------------------------------------------------------
# The grapple
#
# Tine tip radius against opening angle (see tools/tines.py):
#     0.62 -> 0.224   wide enough to drop over the corners of a 0.16 cube
#     0.24 -> 0.113   just touching the corners
#     0.12 -> 0.079   inside the cube's width
#     0.06 -> 0.061   commanded shut; 0.123 across, so the cube is caged
# The tines stall against the object somewhere around 0.12-0.24 and hold it
# there with motor torque. The tips never drop below z = 0.022, so they cannot
# dig into the ground, and never come closer than 0.022 to each other, so they
# cannot jam against one another either.
# --------------------------------------------------------------------------
JAW_OPEN = 0.62
JAW_GRIP = 0.06       # commanded shut; contact stops them well before this
JAW_TRAVEL = 0.25     # tines tucked in, but not clamped, while driving empty
TINES = 5

TRANSIT_Z = 0.72      # height a carried object travels at
APPROACH_DZ = 0.25    # how far above an object to line up before dropping on it
RELEASE_GAP = 0.01    # let go a centimetre high so it settles itself
SEAT_RISE = 0.022     # a caged object rests on the tine tips, which is this far
                      # above the nominal grab point - allowed for when placing
HELD_TOL = 0.09       # how far an object may sit from the grab point and still
                      # count as held, measured up and down
GRIP_LATERAL = 0.07   # ...and side to side
LIFT_CHECK = 0.14     # lift this far to prove the grip before driving anywhere
RISE_FRAC = 0.55      # the object must come up at least this share of that lift
GRIP_STEADY = 6       # ...and stay there for this many steps running
CARRY_FLOOR = 0.30    # a carried object is always higher than this

# --------------------------------------------------------------------------
# Where things live. (x, y) in world metres.
# --------------------------------------------------------------------------
HOMES = {
    "blue":   (4.80, 1.80),
    "yellow": (-0.20, 4.55),
    "brown":  (-3.95, 3.30),
    "red":    (-4.70, -1.70),
    "green":  (-0.20, -3.95),
    "white":  (3.80, -3.20),
}
TOWERS = ((-2.20, -0.70), (2.30, -0.70))

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
WHEEL_R = 0.13                # wheel radius, for turning m/s into rad/s
DRIVE_SPEED = 0.55            # m/s
TURN_SPEED = 0.9              # rad/s
MACHINE_R = 0.78              # footprint radius used for planning
SWEEP_R = 0.87                # what the counterweight sweeps when it slews
CELL = 0.15
EDGE_MARGIN = 1.6             # planning stays this far inside the fence: the
                              # machine's own half-length plus room to turn, and
                              # far enough out that the autonomous routine never
                              # sets the border warning off
LIMIT = FENCE - EDGE_MARGIN

STANDOFF = 1.10               # distance from the slew axis to the object worked on
PARK_MIN = 1.04               # never work closer: a 3-high stack stands 0.48 m and
                              # the counterweight sweeps at 0.87 m, and the tines
                              # would be back over the tracks
PARK_MAX = 1.18               # never work further: the arm runs out of reach
PAD_R = 0.12                  # an object or a stack, as an obstacle

MANUAL_GAIN = 0.65            # manual controls run at this share of full speed

# How the machine notices it is wedged against something the planner did not
# know about, instead of quietly burning a full timeout doing nothing.
STUCK_WINDOW = 2.2            # seconds between progress checks
STUCK_EPS = 0.05              # metres it must cover in that window
STUCK_TURN_EPS = math.radians(3)   # ...or degrees it must turn, if it is
                              # swinging round to face a new heading rather
                              # than driving straight - that is real progress
                              # too and must not be mistaken for being stuck

# The machine physically cannot leave - the fence is a wall - but drive at it in
# manual mode and it says so. The warning fades in between these two distances
# from the fence line. The route planner never comes within LIMIT of it, so the
# autonomous routine never triggers the message.
BORDER_WARN_AT = 1.40
BORDER_WARN_FULL = 0.55

# --------------------------------------------------------------------------
# Hard stops on the arm. These mirror minPosition/maxPosition in the world file,
# so the operator runs into exactly the same limits the autonomous routine does.
#
# They are needed because Webots does not collide two solids joined directly by
# a joint - so selfCollision can never stop the boom rotating down through the
# house it is pinned to, however it is configured. Every other pair (grapple
# against the tracks, tines against the boom, tine against tine) is collided
# normally. See tools/limits.py.
# --------------------------------------------------------------------------
BOOM_LIM = (-1.40, -0.10)     # boom raised 6 to 80 degrees above horizontal
STICK_LIM = (0.20, 2.20)      # stick nearly straight out, to folded right back
WRIST_LIM = (-1.60, 0.90)
JOINT_LIM = (None, BOOM_LIM, STICK_LIM, WRIST_LIM, None)   # slew and rotator turn freely

BLEND_TOL = 0.14              # how near a via-point counts as "on the way"

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
beacon_node = robot.getFromDef("BEACON_MAT")

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
held = None       # colour of the object in the grapple, or None
manual = False    # True while the operator is driving


class Quit(Exception):
    """Raised when Webots shuts the simulation down."""


class ModeChange(Exception):
    """Raised when the operator switches sets, or enters/leaves manual mode."""


class Dropped(Exception):
    """Raised when the grapple comes up empty, so the move can be retried."""


class Stuck(Exception):
    """Raised when a drive command makes no real progress for too long."""


def objs():
    """The set currently in play."""
    return SETS[active]


def park_set(name, at_home):
    """Put a set on its home pads, or away off-site.

    This is the only place anything is ever moved by hand, and it is a reset -
    it runs at startup and when the operator swaps cubes for rocks, never while
    the machine is working.
    """
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

    The machine drives, so the pads do not sit at fixed places relative to it.
    Every arm target goes through here first, which is why the arm still works
    wherever the machine happens to be parked.
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
    """Stop. The wheel motors hold zero speed, which is also the parking brake."""
    wheels(0.0, 0.0)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def clamp_arm(q):
    """Hold a set of joint angles inside the arm's hard stops."""
    out = list(q)
    for i, lim in enumerate(JOINT_LIM):
        if lim is not None:
            out[i] = max(lim[0], min(lim[1], out[i]))
    return tuple(out)


# ---- the map: a grid of cells the machine is allowed to occupy ----
# OBSTACLES comes from site_map.py, which the world generator writes, so it
# always matches the collision bodies that are actually in the world. The pads
# are added here because an object standing on one must not be driven over.
PADS = [(x, y, PAD_R) for x, y in HOMES.values()] + [(x, y, PAD_R) for x, y in TOWERS]
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


def free_cell(x, y):
    c = cell_of(x, y)
    return 0 <= c[0] < N and 0 <= c[1] < N and not GRID[c[0]][c[1]]


def plan(start, goal):
    """A* across the free cells. Returns a list of world points, or None."""
    import heapq
    s, g = cell_of(*start), cell_of(*goal)
    if not (0 <= s[0] < N and 0 <= s[1] < N and 0 <= g[0] < N and 0 <= g[1] < N):
        return None
    if GRID[g[0]][g[1]]:
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


def progress_guard():
    """Call once each step of a drive loop; raises Stuck if nothing is moving.

    "Nothing moving" means the machine's position AND its heading have both
    barely changed over the window - swinging on the spot to face a new
    direction is real progress and must not trip this, only being wedged with
    the wheels spinning and going nowhere should.
    """
    _, _, _, yaw0 = base_pose()
    state = {"t": robot.getTime(), "xy": base_pose()[:2], "yaw": yaw0}

    def check():
        now = robot.getTime()
        if now - state["t"] < STUCK_WINDOW:
            return
        x, y, _, yaw = base_pose()
        moved = math.hypot(x - state["xy"][0], y - state["xy"][1])
        turned = abs(wrap(yaw - state["yaw"]))
        state["t"], state["xy"], state["yaw"] = now, (x, y), yaw
        if moved < STUCK_EPS and turned < STUCK_TURN_EPS:
            raise Stuck
    return check


def goto(tx, ty, tol=0.18, timeout=60.0, stop=True):
    """Drive to a point: turn towards it, then run at it, correcting as we go.

    With stop=False it does not brake on arrival, so a route can be followed as
    one continuous run instead of stopping at every corner. Raises Stuck rather
    than quietly giving up if the machine is not actually getting anywhere -
    wedged against a prop the static map did not know was in the way, say -
    so the caller gets a chance to try a different approach instead of running
    out the clock doing nothing.
    """
    deadline = robot.getTime() + timeout
    guard = progress_guard()
    while True:
        x, y, _, yaw = base_pose()
        dist = math.hypot(tx - x, ty - y)
        if dist < tol:
            if stop:
                halt()
            return
        if robot.getTime() > deadline:
            halt()
            raise Stuck
        err = wrap(math.atan2(ty - y, tx - x) - yaw)
        if abs(err) > 0.7:
            # too far off to drive out of - swing round on the spot first
            turn = TURN_SPEED * (1 if err > 0 else -1) * 0.6
            wheels(-turn, turn)
        else:
            v = DRIVE_SPEED * min(1.0, max(0.3, dist))
            corr = max(-0.5, min(0.5, err)) * 0.6
            wheels(v * (1 - corr), v * (1 + corr))
        step()
        guard()


def follow(path):
    """Drive a whole route without braking at the corners.

    Lets Stuck propagate rather than pressing on to the next waypoint as if
    nothing happened - a route is only as good as the leg that just failed.
    """
    for i, (wx, wy) in enumerate(path):
        last = i == len(path) - 1
        goto(wx, wy, tol=0.16 if last else 0.34, stop=last)


def face(heading, tol=0.05, timeout=25.0):
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


def creep(distance, timeout=30.0):
    """Straight forward (or back, if negative). Raises Stuck, same as goto()."""
    x0, y0, _, _ = base_pose()
    deadline = robot.getTime() + timeout
    sign = 1.0 if distance > 0 else -1.0
    guard = progress_guard()
    while True:
        x, y, _, _ = base_pose()
        if math.hypot(x - x0, y - y0) >= abs(distance):
            halt()
            return
        if robot.getTime() > deadline:
            halt()
            raise Stuck
        wheels(sign * DRIVE_SPEED * 0.5, sign * DRIVE_SPEED * 0.5)
        step()
        guard()


def standoff_spot(tx, ty):
    """Somewhere to park at arm's length from (tx, ty).

    Tries every bearing round the target, nearest to where the machine already
    is first, and takes the first one that is clear of the props, clear of the
    other pads, and that a route can actually be found to.
    """
    x, y, _, _ = base_pose()
    here = math.atan2(y - ty, x - tx)
    others = [(px, py, pr) for px, py, pr in PADS
              if math.hypot(px - tx, py - ty) > 0.05]
    order = sorted((k * math.pi / 12 for k in range(24)),
                   key=lambda b: abs(wrap(b - here)))
    for b in order:
        sx, sy = tx + STANDOFF * math.cos(b), ty + STANDOFF * math.sin(b)
        if not free_cell(sx, sy):
            continue
        if any(math.hypot(sx - px, sy - py) < pr + MACHINE_R for px, py, pr in others):
            continue
        if plan((x, y), (sx, sy)) is not None:
            return sx, sy
    return None


def dock_at(tx, ty, label, attempts=3):
    """Park within reach of (tx, ty), facing it, at exactly the working distance.

    The last step matters: the counterweight sweeps a circle 0.87 m across when
    the machine slews, so parking any closer than that would knock a finished
    stack over.

    If the machine gets physically wedged on something the static map did not
    know was there, goto()/creep() give up in a couple of seconds rather than
    burning their full timeout doing nothing, and raise Stuck. Caught here:
    the whole attempt restarts from wherever the machine actually stopped,
    which usually means standoff_spot() picks a different bearing and plan()
    finds a different route - a real reroute, not just a second try at the
    same thing.
    """
    for attempt in range(attempts):
        spot = standoff_spot(tx, ty)
        if spot is None:
            print("    nowhere clear to park by %s - skipping" % label)
            return False
        x, y, _, _ = base_pose()
        path = plan((x, y), spot)
        if path is None:
            print("    no clear route to %s - skipping" % label)
            return False
        print("    driving to %s: %d waypoints, %.1f m away"
              % (label, len(path), math.hypot(spot[0] - x, spot[1] - y)))
        try:
            follow(path[1:])

            # Turn to face the work, then correct the distance only if it is
            # outside the usable band. The arm solves for wherever the machine
            # actually ended up, so there is nothing to gain from shuffling
            # into an exact spot.
            x, y, _, _ = base_pose()
            face(math.atan2(ty - y, tx - x))
            for _ in range(3):
                x, y, _, _ = base_pose()
                gap = math.hypot(tx - x, ty - y)
                if PARK_MIN <= gap <= PARK_MAX:
                    break
                creep(gap - STANDOFF)
        except Stuck:
            halt()
            if attempt + 1 < attempts:
                print("    stuck getting to %s - rerouting (attempt %d of %d)"
                      % (label, attempt + 2, attempts))
                continue
            print("    still stuck approaching %s after %d attempts - skipping"
                  % (label, attempts))
            return False

        x, y, _, _ = base_pose()
        gap = math.hypot(tx - x, ty - y)
        if gap < PARK_MIN or gap > PARK_MAX:
            print("    could not park within reach of %s (%.2f m) - skipping" % (label, gap))
            return False
        print("    parked %.2f m from %s" % (gap, label))
        return True
    return False


# --------------------------------------------------------------------------
# The grapple
# --------------------------------------------------------------------------
def grab_point():
    """World position of the point the tines close around."""
    p = grapple_node.getPosition()
    m = grapple_node.getOrientation()      # row-major 3x3
    return (p[0] - m[2] * GRAB_DROP,
            p[1] - m[5] * GRAB_DROP,
            p[2] - m[8] * GRAB_DROP)


def where_is(colour):
    """Live position of an object, straight from the simulator."""
    return objs()[colour].getPosition()


def grip_offset(colour):
    """(sideways, up-and-down, height) of an object about the grab point."""
    node = objs()[colour]
    if node is None:
        return None
    gx, gy, gz = grab_point()
    x, y, z = node.getPosition()
    return math.hypot(x - gx, y - gy), z - gz, z


def in_tines(colour):
    """Is the object sitting where the tines close?"""
    off = grip_offset(colour)
    return off is not None and off[0] < GRIP_LATERAL and abs(off[1]) < HELD_TOL


def holding(colour):
    """Is a carried object still in the grapple?

    Safe to use only while carrying: a carried object is always well off the
    ground, so being near the grab point means something.
    """
    off = grip_offset(colour)
    return off is not None and in_tines(colour) and off[2] > CARRY_FLOOR


def gripped(colour, ground_z):
    """Proof that the object is really in the tines, not just near them.

    Nearness on its own is not proof. If the arm is still low - because a move
    ran out of time, say - an object lying untouched on the ground sits a few
    centimetres from the grab point and looks held. Having *risen* off the
    ground with the arm cannot be faked, so that is what this waits for, and it
    wants to see it hold steady rather than catch it in passing.
    """
    good = 0
    for _ in range(GRIP_STEADY * 3):
        step()
        off = grip_offset(colour)
        if off is None:
            return False
        sideways, updown, z = off
        risen = z - ground_z
        if (sideways < GRIP_LATERAL and abs(updown) < HELD_TOL
                and risen > RISE_FRAC * LIFT_CHECK):
            good += 1
            if good >= GRIP_STEADY:
                return True
        else:
            good = 0
    return False


def wait_still(colour, timeout=1.2):
    """Let an object stop rolling before reaching for it."""
    node = objs()[colour]
    deadline = robot.getTime() + timeout
    while robot.getTime() < deadline:
        v = node.getVelocity()
        if math.hypot(math.hypot(v[0], v[1]), v[2]) < 0.02:
            return
        step()


def border_warning():
    """Fade a message in as the machine closes on the fence, and out again."""
    x, y, _, _ = base_pose()
    gap = FENCE - max(abs(x), abs(y))
    a = (BORDER_WARN_AT - gap) / (BORDER_WARN_AT - BORDER_WARN_FULL)
    a = max(0.0, min(1.0, a))
    robot.setLabel(0, "CANNOT LEAVE CONSTRUCTION SITE",
                   0.035, 0.06, 0.095, 0xDD2211, 1.0 - a, "Arial Black")
    robot.setLabel(1, "turn back", 0.42, 0.20, 0.055, 0xFFCC00,
                   1.0 - max(0.0, (a - 0.45) / 0.55), "Arial")


BEACON_ON = (1.0, 0.35, 0.0)
BEACON_OFF = (0.15, 0.05, 0.0)
BEACON_PERIOD = 0.55          # seconds per half-cycle

_beacon_lit = None


def blink_beacon():
    """Toggle the cab beacon's own glow. Only writes the field when it
    actually changes state, not every step."""
    global _beacon_lit
    if beacon_node is None:
        return
    lit = int(robot.getTime() / BEACON_PERIOD) % 2 == 0
    if lit != _beacon_lit:
        _beacon_lit = lit
        beacon_node.getField("emissiveColor").setSFColor(
            list(BEACON_ON if lit else BEACON_OFF))


def step(n=1):
    for _ in range(n):
        if robot.step(timestep) == -1:
            raise Quit
        border_warning()
        blink_beacon()
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

    # Elbow-up solution: boom raised, stick angled down - an excavator's
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


def drive(q, jaws, tol=0.02, timeout=14.0, wait_jaws=False):
    """Command the arm to joint angles q and wait until it gets there."""
    flow([(q, jaws)], timeout=timeout, wait_jaws=wait_jaws, tol=tol)


def flow(waypoints, timeout=20.0, wait_jaws=False, tol=0.02):
    """Run the arm through a list of (angles, jaw opening) without stopping.

    All but the last are via-points: as soon as the arm is roughly on one it is
    already heading for the next, so a pick-up is one continuous movement rather
    than a series of moves that each stop dead before the next begins.
    """
    deadline = robot.getTime() + timeout
    for i, wp in enumerate(waypoints):
        # a waypoint may be a function, so the arm can re-aim at the last
        # moment using where the object actually is by then
        q, jaws = wp() if callable(wp) else wp
        last = i == len(waypoints) - 1
        want = tol if last else BLEND_TOL
        q = clamp_arm(q)
        for m, target in zip(arm_motors, q):
            m.setPosition(target)
        set_jaws(jaws)
        while True:
            step()
            if max(abs(s.getValue() - t) for s, t in zip(arm_sensors, q)) < want:
                break
            if robot.getTime() > deadline:
                return
        if last and wait_jaws:
            while abs(tine_s.getValue() + jaws) > 0.08 and robot.getTime() < deadline:
                step()


def squeeze(timeout=1.4):
    """Close the tines onto whatever is between them.

    They are commanded shut, but an object stops them well before that. Waiting
    for the commanded angle would always time out, so this waits for them to
    stop moving instead - which is what "gripped" actually looks like.
    """
    set_jaws(JAW_GRIP)
    deadline = robot.getTime() + timeout
    last = tine_s.getValue()
    still = 0
    while robot.getTime() < deadline:
        step()
        now = tine_s.getValue()
        still = still + 1 if abs(now - last) < 0.002 else 0
        last = now
        if still > 3:
            return
    return


def travel_pose():
    """Fold the arm in before moving off."""
    drive(ik_local(1.05, 0.0, 0.55), JAW_TRAVEL)


# --------------------------------------------------------------------------
# One move: fetch an object and put it down somewhere
# --------------------------------------------------------------------------
def pick_up(colour):
    """Park by the object, close the grapple round it and lift it clear."""
    global held
    node = objs()[colour]
    sx, sy, sz = node.getPosition()          # ask the simulator, every time
    if not dock_at(sx, sy, "the %s" % colour):
        raise Dropped

    wait_still(colour)
    sx, sy, sz = node.getPosition()          # it may have settled since

    # One continuous swing: out, over, and down onto the object. The last
    # waypoint is worked out when the arm gets there rather than now, so the
    # descent is aimed at wherever the object actually is by that point - it
    # may have been nudged on the way in.
    flow([(ik(sx, sy, sz + APPROACH_DZ + CUBE), JAW_OPEN),
          (ik(sx, sy, sz + APPROACH_DZ), JAW_OPEN),
          lambda: (ik(*where_is(colour)), JAW_OPEN)], tol=0.012)
    ground_z = where_is(colour)[2]           # height before anything lifts it
    squeeze()

    # Lift a little and prove it came up with us. Being near the grab point is
    # not proof; having left the ground is.
    drive(ik(sx, sy, ground_z + LIFT_CHECK), JAW_GRIP, tol=0.03)
    if not gripped(colour, ground_z):
        print("    the %s did not come up - opening and trying again" % colour)
        drive(ik(sx, sy, ground_z + APPROACH_DZ + CUBE), JAW_OPEN)
        raise Dropped
    held = colour
    print("    got the %s" % colour)
    drive(ik_local(STANDOFF, 0.0, TRANSIT_Z), JAW_GRIP)


def put_down(colour, dest_xy, level, where):
    """Park by the destination and set the object down at that stack level."""
    global held
    dx, dy = dest_xy
    if not dock_at(dx, dy, where):
        raise Dropped
    if not holding(colour):
        print("    dropped the %s on the way - going back for it" % colour)
        held = None
        raise Dropped

    dst_centre = CUBE * level + CUBE / 2
    seat = dst_centre + RELEASE_GAP - SEAT_RISE
    # one continuous swing again: across, over the stack, and down onto it
    flow([(ik(dx, dy, TRANSIT_Z), JAW_GRIP),
          (ik(dx, dy, dst_centre + APPROACH_DZ), JAW_GRIP),
          (ik(dx, dy, seat), JAW_GRIP)])
    held = None
    drive(ik(dx, dy, seat), JAW_OPEN, wait_jaws=True)
    settle(0.15)
    drive(ik(dx, dy, dst_centre + APPROACH_DZ), JAW_OPEN)


def transfer(colour, dest_xy, level, where, attempts=3):
    """Fetch one object and stack it at dest_xy, retrying if the grip fails."""
    global held
    for attempt in range(attempts):
        try:
            pick_up(colour)
            put_down(colour, dest_xy, level, where)
            return True
        except Dropped:
            held = None
            if attempt + 1 < attempts:
                print("    retrying the %s (attempt %d of %d)"
                      % (colour, attempt + 2, attempts))
                travel_pose()
    print("    giving up on the %s for now" % colour)
    return False


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
    print("   the boom, stick and wrist stop before they reach the machine")
    print("   controls run at %d%% speed - MANUAL_GAIN at the top of the file"
          % round(MANUAL_GAIN * 100))
    print("-" * 62)

    q = list(clamp_arm([s.getValue() for s in arm_sensors]))
    jaw = JAW_OPEN
    RATE = timestep / 1000.0

    while True:
        v = t = 0.0
        if UP in KEYS:
            v += DRIVE_SPEED * MANUAL_GAIN
        if DOWN in KEYS:
            v -= DRIVE_SPEED * MANUAL_GAIN
        # wheels(left, right): to turn right the left track must run faster,
        # so RIGHT adds to the left side. This was the wrong way round before.
        if LEFT in KEYS:
            t += TURN_SPEED * 0.30 * MANUAL_GAIN
        if RIGHT in KEYS:
            t -= TURN_SPEED * 0.30 * MANUAL_GAIN
        wheels(v - t, v + t)

        for lo, hi, idx, rate in ((ord("E"), ord("Q"), 0, 0.7),
                                  (ord("S"), ord("W"), 1, 0.5),
                                  (ord("D"), ord("A"), 2, 0.6),
                                  (ord("G"), ord("T"), 4, 0.8)):
            rate *= MANUAL_GAIN
            if lo in KEYS:
                q[idx] -= rate * RATE
            if hi in KEYS:
                q[idx] += rate * RATE
        # keep the grapple hanging plumb whatever the boom and stick do
        q[3] = -(q[1] + q[2])
        # ...then hold the whole lot inside the arm's hard stops, so the
        # operator cannot fold the boom down through the machine either
        q = list(clamp_arm(q))
        if ord("Z") in KEYS:
            jaw = max(JAW_GRIP, jaw - 1.6 * MANUAL_GAIN * RATE)
        if ord("X") in KEYS:
            jaw = min(JAW_OPEN, jaw + 1.6 * MANUAL_GAIN * RATE)

        for m, target in zip(arm_motors, q):
            m.setPosition(target)
        set_jaws(jaw)
        step()


def run():
    """Build and dismantle both stacks, over and over, with whatever is in play."""
    travel_pose()
    cycle = 1
    while True:
        for layout in LAYOUTS:
            print("\n=== cycle %d (%ss)" % (cycle, active))
            for t, stack in enumerate(layout):
                print("  stack %d:  %s  (bottom -> top)" % (t + 1, " / ".join(stack)))
                for level, colour in enumerate(stack):
                    print("    placing %-6s at level %d" % (colour, level + 1))
                    transfer(colour, TOWERS[t], level, "build site %d" % (t + 1))

            print("  --- taking both stacks apart")
            for t in reversed(range(len(layout))):
                for level in reversed(range(len(layout[t]))):
                    colour = layout[t][level]
                    print("    returning %-6s to its home pad" % colour)
                    transfer(colour, HOMES[colour], 0,
                             "the %s home pad" % colour)
            travel_pose()

        cycle += 1


def main():
    step()  # one step so the supervisor can read the scene

    missing = [n for n, s in SETS.items() if any(v is None for v in s.values())]
    if missing:
        print("WARNING: no nodes found for: %s" % ", ".join(missing))

    park_set("cube", True)
    park_set("rock", False)

    free = sum(not GRID[i][j] for i in range(N) for j in range(N))
    print("=" * 62)
    print("Excavator ready.")
    print("  Site map: %d obstacles, %d of %d grid cells drivable (%.0f%%)"
          % (len(OBSTACLES), free, N * N, 100.0 * free / (N * N)))
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
