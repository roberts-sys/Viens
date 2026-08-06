"""Minimal Webots .wbt renderer, so changes can be eyeballed before shipping.

Parses the world, walks the transform tree, builds triangle meshes for the
primitives we use, and rasterises with a z-buffer.
"""

import math
import re
import sys

import numpy as np
from PIL import Image

# ------------------------------------------------------------------ parser
TOKEN = re.compile(r'"[^"]*"|[\[\]{}]|[^\s\[\]{}]+')


def tokenize(text):
    text = re.sub(r'#[^\n]*', '', text)
    return TOKEN.findall(text)


class Node:
    def __init__(self, kind):
        self.kind = kind
        self.fields = {}


def is_scalar(tok):
    return (tok[0] in "-+.0123456789" or tok in ("TRUE", "FALSE")
            or tok.startswith('"'))


def parse_node(tk, i):
    if tk[i] == "DEF":
        i += 2                      # skip DEF and its name
    kind = tk[i]
    i += 1
    assert tk[i] == "{", (kind, tk[i:i + 4])
    i += 1
    node = Node(kind)
    while tk[i] != "}":
        name = tk[i]
        i += 1
        if tk[i] == "[":
            i += 1
            items = []
            while tk[i] != "]":
                if is_scalar(tk[i]):
                    items.append(tk[i])
                    i += 1
                else:
                    n, i = parse_node(tk, i)
                    items.append(n)
            i += 1
            node.fields[name] = items
        elif is_scalar(tk[i]):
            vals = []
            while is_scalar(tk[i]):
                vals.append(tk[i])
                i += 1
            node.fields[name] = vals
        else:
            n, i = parse_node(tk, i)
            node.fields[name] = n
    return node, i + 1


def parse_world(text):
    tk = tokenize(text)
    i, roots = 0, []
    while i < len(tk):
        n, i = parse_node(tk, i)
        roots.append(n)
    return roots


def nums(field):
    out = []
    for v in field or []:
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            pass
    return out


# ------------------------------------------------------------- transforms
def rot_matrix(ax, ay, az, ang):
    n = math.sqrt(ax * ax + ay * ay + az * az)
    if n < 1e-12:
        return np.eye(3)
    x, y, z = ax / n, ay / n, az / n
    c, s, C = math.cos(ang), math.sin(ang), 1 - math.cos(ang)
    return np.array([
        [x * x * C + c, x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, y * y * C + c, y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, z * z * C + c]])


# ------------------------------------------------------------------ meshes
def mesh_box(sx, sy, sz):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (2, 3, 7), (2, 7, 6), (1, 2, 6), (1, 6, 5), (0, 4, 7), (0, 7, 3)]
    return np.array(v, float), f


def mesh_cyl(h, r, sub):
    """Webots Cylinder: central axis along the local Z axis."""
    sub = max(6, min(int(sub), 28))
    v, f = [], []
    for i in range(sub):
        a = 2 * math.pi * i / sub
        v.append((r * math.cos(a), r * math.sin(a), -h / 2))
        v.append((r * math.cos(a), r * math.sin(a), h / 2))
    for i in range(sub):
        a, b = 2 * i, 2 * ((i + 1) % sub)
        f += [(a, b, b + 1), (a, b + 1, a + 1)]
    bc, tc = len(v), len(v) + 1
    v += [(0, 0, -h / 2), (0, 0, h / 2)]
    for i in range(sub):
        a, b = 2 * i, 2 * ((i + 1) % sub)
        f += [(bc, b, a), (tc, a + 1, b + 1)]
    return np.array(v, float), f


def mesh_cone(h, r, sub):
    """Webots Cone: axis along local Z, apex at +h/2, base at -h/2."""
    sub = max(6, min(int(sub), 28))
    v, f = [], []
    for i in range(sub):
        a = 2 * math.pi * i / sub
        v.append((r * math.cos(a), r * math.sin(a), -h / 2))
    apex = len(v)
    v.append((0, 0, h / 2))
    base = len(v)
    v.append((0, 0, -h / 2))
    for i in range(sub):
        a, b = i, (i + 1) % sub
        f += [(a, b, apex), (base, b, a)]
    return np.array(v, float), f


def mesh_plane(sx, sy):
    v = np.array([(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0),
                  (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)], float)
    return v, [(0, 1, 2), (0, 2, 3)]


# ------------------------------------------------------------------ walk
TRIS, COLS = [], []


def emit(node, T, R, only=None, depth=0):
    kind = node.kind
    if kind in ("Pose", "Transform", "Group", "Solid", "Robot"):
        t = (nums(node.fields.get("translation")) + [0.0, 0.0, 0.0])[:3]
        r = nums(node.fields.get("rotation"))
        M = rot_matrix(*r) if len(r) == 4 else np.eye(3)
        T2 = T + R @ np.array(t)
        R2 = R @ M
        for ch in node.fields.get("children", []):
            if isinstance(ch, Node):
                emit(ch, T2, R2, only, depth + 1)
        return
    if kind == "HingeJoint":
        ep = node.fields.get("endPoint")
        if isinstance(ep, Node):
            emit(ep, T, R, only, depth + 1)
        return
    if kind == "Shape":
        geo = node.fields.get("geometry")
        app = node.fields.get("appearance")
        col = (0.7, 0.7, 0.7)
        if isinstance(app, Node):
            bc = nums(app.fields.get("baseColor"))
            if len(bc) >= 3:
                col = tuple(bc[:3])
        if not isinstance(geo, Node):
            return
        g = geo.kind
        if g == "Box":
            s = nums(geo.fields.get("size"))
            v, f = mesh_box(*s[:3])
        elif g == "Cylinder":
            v, f = mesh_cyl(nums(geo.fields.get("height"))[0],
                            nums(geo.fields.get("radius"))[0],
                            (nums(geo.fields.get("subdivision")) or [12])[0])
        elif g == "Cone":
            v, f = mesh_cone(nums(geo.fields.get("height"))[0],
                             nums(geo.fields.get("bottomRadius"))[0],
                             (nums(geo.fields.get("subdivision")) or [12])[0])
        elif g == "Plane":
            s = nums(geo.fields.get("size")) or [1, 1]
            v, f = mesh_plane(*s[:2])
        else:
            return
        if only is not None and not only(T):
            return
        w = (R @ v.T).T + T
        for a, b, c in f:
            TRIS.append((w[a], w[b], w[c]))
            COLS.append(col)


# ------------------------------------------------------------------ render
def render(world_path, out_path, cam=None, look=None, W=900, H=620, fov=0.85):
    text = open(world_path).read()
    roots = parse_world(text)

    vp = next((n for n in roots if n.kind == "Viewpoint"), None)
    if cam is None:
        cam = np.array(nums(vp.fields.get("position"))[:3])
    else:
        cam = np.array(cam, float)
    if look is None:
        o = nums(vp.fields.get("orientation"))
        Rv = rot_matrix(*o)
        look = cam + (-Rv[:, 2]) * 3.0
    look = np.array(look, float)

    lights = []
    for n in roots:
        if n.kind == "DirectionalLight":
            d = np.array(nums(n.fields.get("direction"))[:3], float)
            inten = (nums(n.fields.get("intensity")) or [1])[0]
            lights.append((d / np.linalg.norm(d), inten))

    TRIS.clear(); COLS.clear()
    for n in roots:
        if n.kind in ("Solid", "Robot", "Pose", "Group", "Transform"):
            emit(n, np.zeros(3), np.eye(3))

    tris = np.array(TRIS, float)
    cols = np.array(COLS, float)
    print("triangles:", len(tris))

    fwd = look - cam
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0, 0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    V = np.stack([right, up, -fwd])

    cam_v = (tris.reshape(-1, 3) - cam) @ V.T
    cam_v = cam_v.reshape(-1, 3, 3)
    fpx = (W / 2) / math.tan(fov / 2)
    z = -cam_v[:, :, 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        sx = W / 2 + cam_v[:, :, 0] / z * fpx
        sy = H / 2 - cam_v[:, :, 1] / z * fpx

    img = np.zeros((H, W, 3), float)
    img[:] = np.array([0.53, 0.68, 0.86])
    zbuf = np.full((H, W), 1e18)

    n0 = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n0, axis=1, keepdims=True)
    ln[ln == 0] = 1
    n0 = n0 / ln

    order = np.argsort(-z.mean(axis=1))
    for i in order:
        if (z[i] <= 0.05).any():
            continue
        xs, ys = sx[i], sy[i]
        x0, x1 = int(max(0, xs.min())), int(min(W - 1, xs.max()) + 1)
        y0, y1 = int(max(0, ys.min())), int(min(H - 1, ys.max()) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        px, py = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        d = ((ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2]))
        if abs(d) < 1e-9:
            continue
        w0 = ((ys[1] - ys[2]) * (px - xs[2]) + (xs[2] - xs[1]) * (py - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (px - xs[2]) + (xs[0] - xs[2]) * (py - ys[2])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any():
            continue
        zz = w0 * z[i][0] + w1 * z[i][1] + w2 * z[i][2]
        sub = zbuf[y0:y1, x0:x1]
        hit = m & (zz < sub)
        if not hit.any():
            continue
        shade = 0.30
        for d_, inten in lights:
            shade += max(0.0, float(-n0[i] @ d_)) * inten * 0.42
        c = np.clip(cols[i] * min(shade, 1.55), 0, 1)
        sub[hit] = zz[hit]
        img[y0:y1, x0:x1][hit] = c

    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out_path)
    print("wrote", out_path)


if __name__ == "__main__":
    a = sys.argv[1:]
    cam = look = None
    if len(a) >= 8:
        cam = [float(x) for x in a[2:5]]
        look = [float(x) for x in a[5:8]]
    render(a[0], a[1], cam, look)
