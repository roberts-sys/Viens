# Excavator on a construction site

A tracked excavator with a five-tine grapple and three cameras. It picks up six
objects one at a time, stacks them into two towers of three, takes both towers
apart and puts every object back on its coloured home pad — then does it all
again in a different order, so different objects end up on top. Then it loops
forever.

It drives itself around the site between work cycles, planning a route around
everything it knows is there.

Press **M** in the 3D view to take manual control, **C** / **R** to switch
between the cubes and the rocks.

## Getting updates

This folder lives in the `roberts-sys/Viens` repository on the branch
`claude/webots-setup-jty9lv`. To pick up changes, run `git pull` in your clone —
no downloading and no unzipping, and the folder layout stays put so Webots keeps
finding the controller.

## Rebuilding the world

`worlds/*.wbt` are generated. `tools/gen_world.py` writes both of them; run it
from the `tools` folder after editing and it overwrites them in place. The other
scripts there are the checks used while building this: `render.py` draws a world
to a PNG without needing Webots, `zfight.py` finds surfaces that would flicker,
and `navtest.py` prints a map of where the machine can drive.

Everything is built from Webots' built-in nodes. No external PROTO files are
loaded, so the "Skipped PROTO" errors from before cannot happen here.

## Running it

1. Open Webots.
2. **File → Open World...** → `worlds/construction_site.wbt`
3. Press ▶.

Three small camera windows appear in the corner of the 3D view — those are the
excavator's own cameras. The console prints each move as it happens
(`placing blue at level 1`, `returning brown to its home pad`, ...).

### Driving it yourself

Click the 3D view, press **M**, and the machine is yours:

| key | does |
|---|---|
| arrow keys | drive and steer (skid steer, like the real thing) |
| `Q` / `E` | slew the body left / right |
| `W` / `S` | boom up / down |
| `A` / `D` | stick in / out |
| `T` / `G` | rotate the grapple |
| `Z` / `X` | close / open the tines |

Press **M** again to hand it back. The autonomous routine picks up from the
start of a cycle, wherever you happened to leave the machine — the arm works
out its targets from the machine's actual position, so it does not need to be
put back where it started.

### How it drives itself without running anything over

The controller keeps a map of the site: every cone, barrier, pile, container,
pallet and pipe stack, plus all eight pads. Each is a circle, grown by the
machine's own footprint radius, and stamped into a 15 cm grid. Routes come from
an A* search across the cells that are left, so a planned path physically
cannot pass through anything on that list.

Two details make it work in a yard this tight:

* **The work spot is a dock, not a waypoint.** Parked in the middle of its own
  pads, the machine has under 25 cm of clearance — the grid says that cell is
  blocked, and rightly so. It reverses 1.9 m straight back through the one
  clear sector (no pads sit behind it) before the planner takes over, and creeps
  back in the same way at the end.
* **The yard was opened up.** With everything where it was, only 10% of the
  site was drivable and the work spot was a sealed pocket. The cones, barriers,
  pipes, timber, rebar and a couple of spoil piles were moved outward to leave a
  ring road; 94% of the free space is now one connected region.

If a route genuinely cannot be found, the machine says so on the console and
stays where it is rather than guessing.

### Why two towers of three, and not one tower of six

Six stacked objects would stand 0.96 m tall. Two things rule that out:

* the arm cannot reach the approach position above a stack that tall — it is
  past the boom-plus-stick envelope of 1.14 m; and
* the counterweight sweeps a circle 0.95 m across at a height of 0.34 m, so a
  stack that tall would be in the way when the machine slews.

Two stacks of three keep every move at 79% of the reach envelope, and all the
objects sit in the front arc the counterweight never passes over.

### Switching between cubes and rocks

Both sets are in the world at once. While the simulation is running:

1. **Click on the 3D view** so it has keyboard focus.
2. Press **`R`** to work with the **rocks**, or **`C`** to go back to the **cubes**.

The set that is not in use waits off-site, 25 m out, and is swapped in the
moment you press the key. The machine parks whatever it was carrying, the
objects return to their home pads, and the build sequence starts again from the
beginning. There is nothing to reload and no second world file to open.

The six rocks are deliberately different stones — grey granite, sandstone, dark
basalt, red sandstone, mossy greenstone and pale limestone — so you can still
follow which one ends up on top, exactly as with the coloured cubes. They share the cubes' collision box, so they stack
just as reliably.

### If the viewport is black

There are two worlds in `worlds/`, both running the same excavator and the
same controller:

| World | Shapes | What's in it |
|---|---|---|
| `construction_site.wbt` | 921 | full site — cranes, buildings, scaffolding, silo, dump truck |
| `construction_site_lite.wbt` | 681 | same excavator and skyline, no big background structures |

**Both contain the identical, fully detailed excavator** — only the scenery
around it differs.

A black viewport is a *rendering* problem, not a problem with the world file —
it means the graphics card gave up before drawing anything. Shadow casting is
the usual cause, because it makes every object in the scene get drawn a second
time, so `castShadows` is already set to `FALSE` in both worlds. If the full
site is still black, open `construction_site_lite.wbt`: if that one draws
fine, the graphics card simply can't handle the full scene, and the simple
world is the one to use. Both do exactly the same job.

Two other things worth trying from the Webots menus: **View → Optional
Rendering** (turn extras off) and **Tools → Preferences → OpenGL**, where
lowering the ambient occlusion and texture quality settings often fixes a
black or garbled viewport outright.

## What you're looking at

**The machine.** Tracks with idlers, sprockets with teeth, road wheels, carrier
rollers, tension adjusters, travel motors, and a belt of grousers wrapping right
around the ends. A
bolted slew ring the whole upper structure turns on. A cab with ROPS corner
posts, glazing on all four sides, a door with a handle, a wiper, mirrors, a roof
hatch, work lights, a beacon, and a seat with joystick consoles visible through
the glass. An engine housing with a radiator grille, a hinged hatch and latches;
an exhaust stack with a heat shield; hydraulic and fuel tanks with filler caps;
a toolbox; a counterweight with hazard striping and a tow hook; handrails and
steps. A bent boom with gusset plates, pinned ears, hydraulic rams, hoses, a
work light and a lifting eye. A stick with side gussets, a wear plate and
linkage bars. A five-tine orange-peel grapple on a bolted rotator
collar, each tine with its own ram, hose, hinge pin and pair of teeth.

**The cameras.** `camera_front_left` on the cab and `camera_front_right` beside
the boom both look forward over the work area; `camera_rear` sits on the
counterweight looking back. They're mounted on the upper structure, so they
swing around with the machine as it slews.

**The site.** Dirt ground with worn tracks, puddles and an open trench; spoil
piles; traffic cones; concrete barriers; a ribbed shipping container; a site
office with a step and window; a portable toilet; a generator; pallets of
bricks; stacked concrete pipes; timber; oil drums; a rebar bundle; a
wheelbarrow; a cable drum; sandbags; a cement mixer; a floodlight mast; warning
signs; and a fenced perimeter. Beyond the fence: two tower cranes, a concrete
frame building with a scaffolded face, a cement silo, a loaded dump truck,
skyline blocks and hills.

Those background structures are built from a few large forms rather than
lattice-work. Only the silhouette reads at that distance, and struts cost draw
calls the graphics card cannot spare.

## A note on flickering surfaces

If two faces sit at exactly the same depth, the graphics card cannot decide
which is in front and the surface shimmers as the camera moves. The track frame
and the track belt originally shared a top face at z = 0.26 down the whole
length of both sides, which made the machine's flanks flicker. Every applied
detail now stands clear of the surface it is mounted on, and the ground
markings are stacked in thin, separate layers. `zfight.py`-style checks were
used to find them; if you add panels of your own, keep them a millimetre or two
proud rather than exactly flush.

## A note on the primitive axes

Webots aligns both `Cylinder` and `Cone` with their local **Z** axis, not the
Y axis that VRML and most other formats use. A cylinder or cone written with no
rotation therefore stands upright; one that needs to lie across the machine
(wheels, hinge pins) takes `rotation 1 0 0 1.5708`. The generator has separate
`vcyl` / `ycyl` / `xcyl` helpers for exactly this reason.

## How the machine is put together

The `Robot` node now carries `physics` and four driven wheels hidden inside the
track shells, so the machine is a mobile robot rather than the fixed-base
manipulator it used to be. One consequence runs through the whole controller:
arm targets are held in world coordinates and converted into the machine's own
frame through `to_base()` every time, using its live pose. The
tracks are decoration; all the motion happens in the chain above them:

```
slew joint     (rotates the whole upper structure about the vertical axis)
  └─ boom joint      (raises/lowers the big bent beam)
       └─ stick joint    (the forearm)
            └─ wrist joint    (keeps the grapple hanging plumb)
                 └─ rotator joint   (spins the grapple about the vertical)
                      ├─ tine 0 ... tine 4
```

That is five driven axes — slew, boom, stick, wrist, rotator — plus the five
tines, which open and close together. The rotator is commanded to the negative
of the slew angle, so the tines hold a constant heading while the machine
swings: watch the head counter-rotate as the body turns.

**Grabbing** doesn't rely on friction between the jaws and the cube, which is
fragile in simulation. Because the controller is a `Supervisor`, it can instead
pin the cube directly: while a cube is held, every simulation step the
controller reads the grapple's world transform, works out where the point
between the jaws is, and places the cube there with its velocity cleared. The
jaws close around it at the same moment, so it looks like the jaws are doing
the work — but the hold cannot slip or be shaken loose. On release the cube is
handed back to the physics engine a few millimetres above its target and drops
into place. The jaws' collision boxes sit entirely above the cube, so they can
never knock it out of position.

## How the controller decides where to move

`excavator_controller.py` never hard-codes joint angles. It says "put the grab
point at this (x, y, z)" and solves for the angles — inverse kinematics:

- The **slew** angle is just `atan2(y, x)`.
- That leaves a flat two-link problem (boom + stick) solved with the law of
  cosines, taking the *elbow-up* solution — boom raised, stick angled down,
  which is an excavator's natural working posture.
- The **wrist** angle is set to cancel the boom and stick rotations, so the
  grapple hangs straight down no matter where the arm is.

The controller also asks the simulator where each cube *actually* is before
reaching for it, rather than assuming it's where it was left. So a cube that
settles a little off-centre still gets picked up.

Each transfer is: line up high → descend → grab → lift to carry height →
traverse → descend → release → back off.

## Things worth trying

- Change `LAYOUTS` at the top of the controller to stack the cubes in any order
  you like, or add a third layout.
- Move `HOMES` or `TOWER` — the IK works out the new joint angles by itself.
  (The painted pads are drawn at those same coordinates in the world file, so
  move them to match.)
- Slow the machine down for a nicer video: lower `maxVelocity` on the motors in
  the `.wbt` file.
- Add a fourth cube (copy a `DEF CUBE_*` block, give it a new name, DEF and
  home position, and add it to `cubes` in the controller).
- The geometry constants at the top of the controller must match the `.wbt`
  file — if you lengthen the boom in the world, change `BOOM_LEN` too.

## Recording it for the website

Webots can record a run straight to MP4 (the record button in the toolbar, or
**File → Export**). That output drops directly into the same kind of video
embed the site already uses on `autonomous-machinery.html`.
