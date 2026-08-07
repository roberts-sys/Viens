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
2. **File → Open World...** → `worlds/construction_site_lite.wbt`
3. Press ▶.

`construction_site_lite.wbt` is the one to open by default — it has the
identical machine, the same detailed rocks, the same fence and boundary
warning, and a lighter background, at 914 shapes against 1134 for
`construction_site.wbt`. If your graphics card handles the full version
without going black, it has a few extra assemblies (both tower cranes, the
scaffolded frame building, the loaded dump truck, two parked vans) that
lite leaves out — open that one instead. See "If the viewport is black"
below.

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

The boom, stick and wrist stop before they reach the machine — the same hard
stops the autonomous routine runs under, so you cannot fold the arm through the
cab. Steering used to be reversed (right turned left); it is not now.

Everything in manual mode runs at **65% speed** — driving, steering, every arm
joint and the tines. `MANUAL_GAIN` at the top of the controller is the single
dial if you want it quicker or slower again.

### You cannot leave the site

The fence is a wall, so the machine physically cannot get out. Drive at it and
**CANNOT LEAVE CONSTRUCTION SITE** fades up over the 3D view, solid by the time
you are 0.55 m off the fence, and fades away again as you pull back — gone by
1.40 m. It is drawn with `setLabel`, so it sits over the viewport wherever the
camera happens to be pointing.

The route planner keeps 1.60 m clear of the fence, which is further out than the
warning ever reaches, so the machine driving itself never sets it off. That is
checked in `verify.py` rather than left to luck.

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
gone.

### Knowing for certain that it picked something up

Checking "is the object near the grab point?" is not proof, and it was giving
false positives. If a move runs out of time and leaves the arm low, an object
lying **untouched on the ground** sits a few centimetres from the grab point and
looks held.

So the machine now proves it. It notes the object's height before closing,
lifts 0.14 m, and requires all three of:

* the object has **risen** by at least 55% of that lift — this cannot be faked,
* it is within 0.07 m of the grab point sideways and 0.09 m up and down,
* and it has held that way for six simulation steps running, not just one.

Three things were changed to make the first attempt the one that works:

* **It waits for the object to stop moving** before reaching, so it never grabs
  at something still rolling.
* **It aims at the last moment.** The final descent used to be worked out at the
  start of the swing. It is now a function evaluated when the arm gets there, so
  it drops onto wherever the object actually is by then, not where it was.
* **The tines close more slowly** (maxVelocity 2 → 1.2), so they cradle the
  object rather than punting it out from between them.

If the proof fails it opens, says `the blue did not come up`, and tries again —
up to three times.

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
0.27 m. The pairs it *cannot* police are dealt with by hard stops, below.

**The arm has hard stops.** There is a limit to what `selfCollision` can do:
Webots never collides two solids joined *directly* by a joint, so
boom-against-house and stick-against-boom are invisible to it however it is
configured — which is why the boom could still fold down through the machine.
Real excavators stop that with limits in the rams, and so does this one now:

| joint | travel |
|---|---|
| boom | +6° to +80° above horizontal |
| stick | nearly straight out, to folded right back |
| wrist | −1.60 to +0.90 rad |
| tines | shut (0.06) to wide open (0.62) |
| slew, rotator | free, full circle |

They are `minPosition`/`maxPosition` on the motors with `minStop`/`maxStop`
behind them, so they bind on the operator in manual mode exactly as they bind on
the autonomous routine — and the controller clamps its own commands to the same
numbers, so the two can't disagree. The autonomous routine has 12–27° of
headroom against every one of them. `tools/limits.py` prints that, and
`tools/verify.py` fails if the world and the controller ever drift apart.

Everything else — grapple against the tracks, tines against the boom, tine
against tine — is a normal collision pair and the engine handles it.

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
  standoff point, then it faces the target. It only corrects the distance if it
  is outside the usable band of 1.04–1.18 m — the arm solves for wherever the
  machine actually ended up, so there is nothing to gain from shuffling into an
  exact spot, and shuffling is what made it look hesitant.

If a route genuinely cannot be found, the machine says so on the console and
moves on to the next object rather than guessing.

### Why the working distance is 1.04–1.18 m

A finished stack of three stands 0.48 m tall. The counterweight sweeps a circle
0.87 m in radius at a height of 0.29 m — lower than the top of the stack. So the
only thing keeping the machine from knocking its own tower over when it slews is
parking far enough back. It aims for 1.10 m and accepts anything from 1.04 m —
where the stack's nearest corner is still 0.93 m out, clearing the sweep by
0.06 m — to 1.18 m, where the arm is at 94% of its reach.

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

Each is **23 shapes**, up from 6. Six masses give the silhouette, tilted off the
vertical so there is no flat top; over those go broken facets, quartz veins,
shadowed crevices, a patch of lichen on the weathered side, and grit stuck to
the underside. Every piece is tinted from that stone's own three colours, so a
rock still reads as granite or sandstone at a glance.

## If the viewport is black

There are two worlds in `worlds/`, both running the same excavator and the same
controller, and both now carrying the fence, the boundary warning, the detailed
rocks and a slice of background scenery:

| World | Shapes | What's in it |
|---|---|---|
| `construction_site_lite.wbt` | 914 | machine, rocks, fence, pylons, trees, conveyor, silo |
| `construction_site.wbt` | 1134 | all of the above, plus both cranes, the frame building with scaffolding, two vans, and the dump truck |

**Both contain the identical, fully detailed excavator** — only how much
scenery surrounds it differs. Start with `construction_site_lite.wbt`; it is
the default in "Running it" above for exactly this reason.

A black viewport is a *rendering* problem, not a problem with the world file —
it means the graphics card gave up before drawing anything. Shadow casting is
the usual cause, so `castShadows` is already `FALSE` in both worlds, and every
surface in both is fully opaque — a wrapped set of transparent fence panels
used to be the difference between the world that drew and the one that came up
black, so nothing in either world is see-through now.

If a world does come up black, don't guess between the two blindly: the shape
counts above are exact, so if lite goes black too, the ceiling on your card is
below 914 and `tools/gen_world.py` can be trimmed further — say which
background pieces you can live without (pylons, trees, the conveyor, or the
silo are the ones to drop first, in that order) and I'll take them out.

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

**The site, in both worlds.** Dirt ground with worn tracks, puddles and open
trenches; spoil piles; traffic cones; concrete barriers; a shipping container;
a fenced perimeter you cannot leave (below); nine skyline blocks and six
distant hills; and, beyond the fence, two lattice power pylons, a stand of
eight conifers, an inclined conveyor feeding a stockpile, and a cement silo.

**In `construction_site.wbt` only, on top of all that:** a site office with a
step and window, a portable toilet, a generator, pallets of bricks, stacked
concrete pipes, timber, oil drums, a rebar bundle, a wheelbarrow, a cable drum,
sandbags, a cement mixer, a floodlight mast, warning signs, two tower cranes, a
concrete frame building with a scaffolded face, two parked vans and a loaded
dump truck.

Every background structure is built from a few large forms rather than
lattice-work — only the silhouette reads at that distance, and struts cost draw
calls the graphics card cannot spare. That is what makes the lite-world set
affordable: `construction_site_lite.wbt` is 914 shapes against 1134 for the
full world, for four assemblies' difference (99 shapes: the cranes, the frame
building, the dump truck).

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

Each move is: plan a route → drive → park → line up high → descend → close →
lift and check → drive to the build site → park → descend → release → back off.

**The arm does not stop between those steps.** Each swing is a list of
via-points fed to `flow()`, which moves on to the next as soon as the arm is
roughly on the current one, so a pick-up is one continuous movement instead of a
series that each brake to a halt. Routes are followed the same way — `follow()`
does not brake at the corners. The only real wait left is `squeeze()`, which
watches the tine sensor until the tines stop moving, because that is what
"gripped" actually looks like.

## Rebuilding the world

The `.wbt` files are **generated**. If you edit a world by hand in Webots and
save it, running the generator again overwrites your changes. Change
`tools/gen_world.py` instead:

```
python3 tools/gen_world.py      # writes both worlds and site_map.py
python3 tools/verify.py         # 109 checks; run this before opening Webots
```

`gen_world.py` needs nothing but Python. The other tools need `numpy` and
`pillow` only for `render.py`.

| tool | what it does |
|---|---|
| `gen_world.py` | builds both worlds and writes the controller's obstacle map |
| `verify.py` | devices, DEFs, IK/FK, reach, self-collision clearance, routes |
| `navtest.py` | prints an ASCII map of the drivable yard and checks every route |
| `render.py` | draws a world to a PNG without opening Webots |
| `limits.py` | works out the arm's hard stops and what collision has to catch |
| `pack.py` | lays the props round the perimeter with nothing overlapping |
| `tines.py` | the grapple's tip radius against opening angle |
| `zfight.py` | finds surfaces that would flicker |

`verify.py` is the one that matters (109 checks). It reads the controller's constants and the
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
