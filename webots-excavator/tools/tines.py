"""Where the tine tips actually go as the grapple opens and closes.

The whole grab depends on three things:
  - open wide enough to drop over the cube's corners,
  - closed tight enough that the cube cannot fall back out,
  - and never dipping below the ground while doing either.
"""
import math

CUBE = 0.16
HALF = CUBE / 2                 # 0.080 to a face
DIAG = CUBE * math.sqrt(2) / 2  # 0.113 to a corner

HINGE_R = 0.105     # tine hinge, radius from the grapple axis
HINGE_Z = -0.08     # tine hinge, below the grapple origin
TINES = 5
TOOTH_W = 0.055     # tine width across, at the tip

# tooth tip in the tine's own frame, measured off the model
TIP = (-0.061, -0.290)


def tip_at(opening):
    """(radius from the grapple axis, height below the grapple origin)."""
    q = -opening                      # the motor is commanded to -opening
    c, s = math.cos(q), math.sin(q)
    x = TIP[0] * c + TIP[1] * s
    z = -TIP[0] * s + TIP[1] * c
    return HINGE_R + x, HINGE_Z + z


print("opening   tip radius   tip height   gap between neighbouring tips")
for o in (0.62, 0.45, 0.30, 0.235, 0.20, 0.15, 0.12, 0.10, 0.06, 0.02, 0.0):
    r, z = tip_at(o)
    gap = 2 * math.pi * r / TINES - TOOTH_W
    note = ""
    if r > DIAG:
        note = "clears the cube's corners"
    elif r > HALF:
        note = "touching the corners"
    else:
        note = "inside the cube's width - cannot fall out"
    if gap < 0:
        note += "  ** TINES OVERLAP **"
    print("  %.2f      %.3f       %+.3f      %+.3f   %s" % (o, r, z, gap, note))

JAW_OPEN, JAW_GRIP = 0.62, 0.06
ro, zo = tip_at(JAW_OPEN)
rc, zc = tip_at(JAW_GRIP)
print("\nopen  (%.2f): tips at radius %.3f, %.3f below the grapple origin" % (JAW_OPEN, ro, zo))
print("grip  (%.2f): tips at radius %.3f, %.3f below the grapple origin" % (JAW_GRIP, rc, zc))

# The grapple must sit high enough that the tips never touch the ground, and
# low enough that closing them catches the cube rather than sliding over it.
GRAB_DROP = 0.315               # grapple origin -> the cube's centre
cube_centre = CUBE / 2
grapple_z = cube_centre + GRAB_DROP
print("\nwith GRAB_DROP %.3f, picking a cube off the ground:" % GRAB_DROP)
print("   grapple origin sits at z = %.3f" % grapple_z)
lo = min(zo, zc)
print("   lowest the tips ever get: z = %.3f  (%s)"
      % (grapple_z + lo, "clear of the ground" if grapple_z + lo > 0.005 else "** DIGS IN **"))
print("   open tips at z = %.3f, cube top at %.3f  (%s)"
      % (grapple_z + zo, CUBE,
         "tips drop past the top" if grapple_z + zo < CUBE else "** tips stay above the cube **"))
print("   closed tips at z = %.3f, cube bottom at 0.000" % (grapple_z + zc))
print("   closed aperture %.3f across vs cube %.3f across  (%s)"
      % (2 * rc, CUBE, "caged" if 2 * rc < CUBE else "** CUBE FALLS THROUGH **"))

# where the tines first touch, so we know how much squeeze is left
for name, target in (("a face", HALF), ("a corner", DIAG)):
    lo_o, hi_o = 0.0, 0.62
    for _ in range(60):
        mid = (lo_o + hi_o) / 2
        if tip_at(mid)[0] < target:
            lo_o = mid
        else:
            hi_o = mid
    print("   tines meet %-9s at opening %.3f -> %.3f rad of squeeze left"
          % (name, hi_o, hi_o - JAW_GRIP))
