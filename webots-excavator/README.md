# Excavator on a construction site

A tracked excavator with a five-tine grapple and three cameras, working a 16 x
16 m site on its own.

For each object in turn it plans a route across the yard, drives there, parks at
arm's length, closes the grapple round the object, drives to a build site and
sets it down. Six objects go up as two towers of three, come back down onto
their home pads, then go up again in a different order so different objects end
up on top. Then it starts over.

Press **M** in the 3D view to take over and drive it yourself, **C** / **R** to
switch between the cubes and the rocks.

Everything is built from Webots' built-in nodes. No external PROTO files are
loaded, so the "Skipped PROTO" errors from before cannot happen here.

## Running it

1. Open Webots.
2. **File → Open World...** → `worlds/construction_site.wbt`
3. Press ▶.

Three small camera windows appear in the corner of the 3D view — those are the
excavator's own cameras. The console prints each move as it happens
(`driving to the blue: 14 waypoints, 5.2 m away`, `parked 1.10 m from the
blue`, `placing yellow at level 2`, ...).

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

## How it picks things up

Nothing is teleported. The grapple holds an object the way a real one does:
**the five tines close to a circle 0.123 m across, and the object inside them is
0.160 m across, so it physically cannot fall out.**

The numbers behind that, all from `tools/tines.py`:

| tine opening | tip radius | what it means |
|---|---|---|
| 0.62 (open) | 0.224 m | wide enough to drop over the corners of the object |
| 0.235 | 0.113 m | just touching the corners |
| 0.12 | 0.079 m | now inside the object's width |
| 0.06 (commanded shut) | 0.061 m | 0.123 m across — the object is caged |

The tines stall against the object somewhere between 0.12 and 0.235 and hold it
there with motor torque; the last bit of commanded travel is what supplies the
squeeze. Two things had to be true for this to work at all, and both were
checked before the world was written:

* **The tips never go below z = 0.022**, so they cannot dig into the ground
  while closing — which is what would happen if the grapple simply descended to
  the object's centre and shut.
* **The tips never come closer than 0.022 m to each other**, so with
  self-collision on, the tines cannot jam against one another either.

The whole thing used to work by pinning the object to the grapple every
simulation step, which held perfectly but looked like teleporting. That code is
gone. In exchange, a grip can now genuinely fail — so after every lift the
controller checks the object is still within 0.09 m of the grab point, and if it
is not, it reopens, says so on the console and tries again (three attempts).

An object caged in the tines rests on the tips, about 0.022 m above the point
the arm is aiming at. `SEAT_RISE` in the controller allows for that, so objects
are released about a centimetre above the stack rather than dropped onto it.

## Physics

**Every part of the machine collides with every other part.** `selfCollision` is
on, and each tine now has a collision volume down its whole length — an upper
arm, an angled lower blade and a tooth block. Previously a tine's only collision
shape was a 5 cm box at the very top, which is why the grapple could pass
straight through itself and through anything it tried to pick up.

Webots skips collision between two solids joined directly by a joint, so the
boom does not fight the house it is pinned to; but tine against tine, and the
grapple against the boom and the tracks, are all live. `tools/verify.py` checks
the clearance at every pose the controller actually commands — the tightest is
0.27 m.

**Every prop on the site is solid.** The scenery used to be one `Solid` with no
`boundingObject` at all, so the machine drove straight through the shipping
container. There is now a `site_collision` body carrying a box or cylinder for
every prop, plus four walls for the fence. It has no `physics`, which in Webots
means it never moves — they are walls.

Friction is set per material pair. The tines are `contactMaterial "grip"` and
the objects are `contactMaterial "load"`, so the grapple can hold hard
(coulombFriction 2.2) without making the objects sticky against each other
(0.9) or against the ground (1.1).

## How it drives itself without running anything over

The controller plans across a 0.15 m grid. Each obstacle is a circle, grown by
the machine's own footprint radius of 0.78 m, and stamped out of that grid;
routes come from an A* search over what is left, so a planned path cannot pass
through anything on the list.

The list is not maintained by hand. `tools/gen_world.py` writes
`controllers/excavator_controller/site_map.py` from the same table it builds the
collision bodies from, so **the map the machine plans with and the walls it
would hit are generated from one source.** They cannot drift apart.

Two details make it work:

* **The props were moved onto the perimeter.** They used to be strewn across the
  middle, which left only 22% of the yard drivable and would not fit eight pads.
  They are now packed along the four fence lines with nothing overlapping
  (`tools/pack` logic, checked by `tools/navtest.py`), and the yard was enlarged
  to 16 x 16 m. 34% of the grid is drivable once the pads are stamped out too,
  99% of it in one connected piece, and all 28 pad-to-pad routes exist.
* **Parking is a separate step from routing.** The planner gets the machine to a
  standoff point; then it faces the target and creeps until it is 1.10 m away,
  to within 0.06 m. That distance is not arbitrary — see below.

If a route genuinely cannot be found, the machine says so on the console and
moves on to the next object rather than guessing.

### Why the working distance is 1.10 m

A finished stack of three stands 0.48 m tall. The counterweight sweeps a circle
0.87 m in radius at a height of 0.29 m — lower than the top of the stack. So the
only thing keeping the machine from knocking its own tower over when it slews is
parking far enough back. At 1.10 m the stack's nearest corner is 0.987 m out,
clearing the sweep by 0.117 m.

### Why two towers of three, and not one tower of six

Six stacked objects would stand 0.96 m tall, which is past the arm's reach for
the approach above it. Two stacks of three keep every move inside 87% of the
reach envelope.

## Switching between cubes and rocks

Both sets are in the world at once. While the simulation is running:

1. **Click on the 3D view** so it has keyboard focus.
2. Press **`R`** for the **rocks**, **`C`** for the **cubes**.

The set that is not in use waits off-site, 25 m out. Swapping resets both sets
onto their home pads — that reset is the only place anything is ever moved by
hand, and it never runs while the machine is working.

The six rocks are deliberately different stones — grey granite, sandstone, dark
basalt, red sandstone, mossy greenstone and pale limestone — so you can still
follow which one ends up on top. They share the cubes' collision box, so they
grip and stack the same way.

## If the viewport is black

There are two worlds in `worlds/`, both running the same excavator and the same
controller:

| World | Shapes | What's in it |
|---|---|---|
| `construction_site.wbt` | 930 | full site — cranes, buildings, scaffolding, silo, dump truck |
| `construction_site_lite.wbt` | 682 | same excavator and skyline, no big background structures |

**Both contain the identical, fully detailed excavator** — only the scenery
around it differs.

A black viewport is a *rendering* problem, not a problem with the world file —
it means the graphics card gave up before drawing anything. Shadow casting is
the usual cause, so `castShadows` is already `FALSE` in both worlds. If the full
site is still black, open `construction_site_lite.wbt`.

Two other things worth trying from the Webots menus: **View → Optional
Rendering** (turn extras off) and **Tools → Preferences → OpenGL**, where
lowering the ambient occlusion and texture quality settings often fixes a black
or garbled viewport outright.

## What you're looking at

**The machine.** Tracks with idlers, sprockets with teeth, road wheels, carrier
rollers, tension adjusters, travel motors, and a belt of grousers wrapping right
around the ends. A bolted slew ring the whole upper structure turns on. A cab
with ROPS corner posts, glazing on all four sides, a door with a handle, a
wiper, mirrors, a roof hatch, work lights, a beacon, and a seat with joystick
consoles visible through the glass. An engine housing with a radiator grille, a
hinged hatch and latches; an exhaust stack with a heat shield; hydraulic and
fuel tanks with filler caps; a toolbox; a counterweight with hazard striping and
a tow hook; handrails and steps. A bent boom with gusset plates, pinned ears,
hydraulic rams, hoses, a work light and a lifting eye. A stick with side
gussets, a wear plate and linkage bars. A five-tine orange-peel grapple on a
bolted rotator collar, each tine with its own ram, hose, hinge pin and pair of
teeth.

The counterweight used to overhang the tracks by 0.37 m, which read as out of
proportion. It is now shorter and narrower and overhangs by 0.20 m; the deck and
engine housing were pulled in to match, and the slew sweep dropped from 0.95 m
to 0.87 m.

**The cameras.** `camera_front_left` on the cab and `camera_front_right` beside
the boom both look forward over the work area; `camera_rear` sits on the
counterweight looking back. They are mounted on the upper structure, so they
swing round with the machine as it slews.

**The site.** Dirt ground with worn tracks, puddles and open trenches; spoil
piles; traffic cones; concrete barriers; a ribbed shipping container; a site
office with a step and window; a portable toilet; a generator; pallets of
bricks; stacked concrete pipes; timber; oil drums; a rebar bundle; a
wheelbarrow; a cable drum; sandbags; a cement mixer; a floodlight mast; warning
signs; and a fenced perimeter. Beyond the fence: two tower cranes, a concrete
frame building with a scaffolded face, a cement silo, a loaded dump truck,
skyline blocks and hills.

## A note on the primitive axes

Webots aligns both `Cylinder` and `Cone` with their local **Z** axis, not the Y
axis that VRML and most other formats use. A cylinder or cone written with no
rotation therefore stands upright; one that needs to lie across the machine
(wheels, hinge pins) takes `rotation 1 0 0 1.5708`. The generator has separate
`vcyl` / `ycyl` / `xcyl` helpers for exactly this reason.

## A note on flickering surfaces

If two faces sit at exactly the same depth, the graphics card cannot decide
which is in front and the surface shimmers as the camera moves. Every applied
detail stands clear of the surface it is mounted on, and the ground markings are
stacked in thin, separate layers. `tools/zfight.py` finds the ones that slip
through; if you add panels of your own, keep them a millimetre or two proud
rather than exactly flush.

## How the machine is put together

The `Robot` node carries `physics` and four driven wheels hidden inside the
track shells, so this is a mobile robot, not a fixed-base manipulator. One
consequence runs through the whole controller: arm targets are held in world
coordinates and converted into the machine's own frame through `to_base()` every
time, using its live pose. The tracks are decoration; all the motion happens in
the chain above them:

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

## How the controller decides where to move

`excavator_controller.py` never hard-codes joint angles. It says "put the grab
point at this (x, y, z) in the world" and solves for the angles — inverse
kinematics:

- The **slew** angle is just `atan2(y, x)` in the machine's frame.
- That leaves a flat two-link problem (boom + stick) solved with the law of
  cosines, taking the *elbow-up* solution — boom raised, stick angled down,
  which is an excavator's natural working posture.
- The **wrist** angle cancels the boom and stick rotations, so the grapple hangs
  straight down wherever the arm is.

Because the slew covers a full circle, the machine only has to park somewhere in
the reach annulus — it does not need to be pointing at the object. That is why a
sloppy park still works.

The controller asks the simulator where each object *actually* is before
reaching for it, rather than assuming it is where it was left, so one that
settles a little off-centre still gets picked up.

Each move is: plan a route → drive → park at 1.10 m → line up high → descend →
close → lift and check → drive to the build site → park → descend → release →
back off.

## Rebuilding the world

The `.wbt` files are **generated**. If you edit a world by hand in Webots and
save it, running the generator again overwrites your changes. Change
`tools/gen_world.py` instead:

```
python3 tools/gen_world.py      # writes both worlds and site_map.py
python3 tools/verify.py         # 71 checks; run this before opening Webots
```

`gen_world.py` needs nothing but Python. The other tools need `numpy` and
`pillow` only for `render.py`.

| tool | what it does |
|---|---|
| `gen_world.py` | builds both worlds and writes the controller's obstacle map |
| `verify.py` | devices, DEFs, IK/FK, reach, self-collision clearance, routes |
| `navtest.py` | prints an ASCII map of the drivable yard and checks every route |
| `render.py` | draws a world to a PNG without opening Webots |
| `zfight.py` | finds surfaces that would flicker |

`verify.py` is the one that matters. It reads the controller's constants and the
generated world and checks they agree — every device the controller opens
exists, every arm target is inside the reach envelope, every pad has somewhere
to park, and the grapple clears the machine at every commanded pose. It exits
non-zero if anything fails.

## Getting updates

The project lives in the `Viens` repository on the branch
`claude/webots-setup-jty9lv`. To pick up a change:

* **GitHub Desktop:** click **Fetch origin**, then **Pull origin**.
* **Command line:** `git pull origin claude/webots-setup-jty9lv`

Then in Webots press **Ctrl+Shift+R** (File → Reload World). Do not move the
files out of the folder — Webots finds the controller by its position relative
to the world file.

## Things worth trying

- Change `LAYOUTS` at the top of the controller to stack the objects in any
  order you like, or add a third layout.
- Move `HOMES` or `TOWERS`. The IK works out the new joint angles by itself, and
  the painted pads are drawn from the same values in the generator — change them
  in both, regenerate, then run `verify.py` to confirm the new spots have
  somewhere to park.
- Slow the machine down for a nicer video: lower `DRIVE_SPEED`, or `maxVelocity`
  on the motors in the generator.
- If a grip ever slips, `maxTorque` on the tine motors (currently 8) and
  `coulombFriction` for the grip/load pair (currently 2.2) are the two dials.
- The geometry constants at the top of the controller must match the world — if
  you lengthen the boom in the generator, change `BOOM_LEN` too. `verify.py`
  will not catch that one for you.

## Recording it for the website

Webots can record a run straight to MP4 (the record button in the toolbar, or
**File → Export**). That output drops directly into the same kind of video embed
the site already uses on `autonomous-machinery.html`.
