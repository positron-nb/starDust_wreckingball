"""3D renders of the WB-700 CAD (PyVista/VTK, off-screen) with leader-line callouts.

Every image is generated from build_parts() -- the same geometry that the checks use.
"""
from __future__ import annotations

import math
import os

import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pyvista as pv  # noqa: E402

from wb700_model import build_parts  # noqa: E402

pv.global_theme.font.family = "arial"
W, H = 2400, 1700
CURVED = ("SH", "ST-01", "ST-02", "ST-03", "DR-0", "SG-01", "SG-02", "SG-03", "BL", "PW-05")


def pv_mesh(solid, tol=0.35, ang=0.2):
    v, f = solid.tessellate(tol, ang)
    if not f:
        return None
    v = np.array([[p.x, p.y, p.z] for p in v])
    f = np.array(f)
    return pv.PolyData(v, np.hstack([np.full((len(f), 1), 3), f]).ravel()).clean()


def add_part(pl, p, mesh=None, opacity=None, color=None, edges=False):
    if mesh is None:
        fine = p.pid.startswith(("SH-0", "BL"))
        mesh = pv_mesh(p.solid, tol=0.15 if fine else 0.35, ang=0.05 if fine else 0.2)
    if mesh is None or mesh.n_cells == 0:
        return None
    op = p.opacity if opacity is None else opacity
    if op <= 0:
        return mesh
    smooth = p.pid.startswith(CURVED)
    pl.add_mesh(mesh, color=color or p.color, opacity=op, smooth_shading=smooth,
                split_sharp_edges=True, specular=0.25, specular_power=20, ambient=0.18, diffuse=0.85,
                show_edges=False)
    if edges:
        fe = mesh.extract_feature_edges(feature_angle=35, boundary_edges=True, non_manifold_edges=False,
                                        manifold_edges=False)
        if fe.n_cells:
            pl.add_mesh(fe, color=(0.25, 0.3, 0.38), line_width=1.6, opacity=0.6)
    return mesh


def new_plotter(parallel=False):
    pl = pv.Plotter(off_screen=True, window_size=(W, H), lighting="three lights")
    pl.set_background("white")
    try:
        pl.enable_anti_aliasing("ssaa")
    except Exception:  # noqa: BLE001
        pass
    if parallel:
        pl.enable_parallel_projection()
    return pl


def world_to_px(pl, pts):
    ren = pl.renderer
    out = []
    for p in pts:
        ren.SetWorldPoint(float(p[0]), float(p[1]), float(p[2]), 1.0)
        ren.WorldToDisplay()
        x, y, _ = ren.GetDisplayPoint()
        out.append((x, H - y))
    return out


def _text_px(texts, fontsize, dpi=200):
    """Width/height in pixels of each (possibly multi-line) label at the given font size."""
    fig = plt.figure(figsize=(4, 4), dpi=dpi)
    r = fig.canvas.get_renderer()
    out = []
    for t in texts:
        tt = fig.text(0, 0, t, fontsize=fontsize)
        bb = tt.get_window_extent(renderer=r)
        out.append((bb.width, bb.height))
    plt.close(fig)
    return out


def annotate(img, anchors_px, labels, path, title=None, subtitle=None, footer=None,
             crop=None, fontsize=15, triad=None):
    """Place labels in left/right margins (sized to the longest label) with leader lines."""
    dpi = 200
    if crop is not None:
        x0, y0, x1, y1 = crop
        img = img[y0:y1, x0:x1]
        anchors_px = [(a[0] - x0, a[1] - y0) for a in anchors_px]
        if triad is not None:
            triad = [(a[0] - x0, a[1] - y0) for a in triad]
    h, w = img.shape[:2]
    sizes = _text_px(labels, fontsize, dpi)
    left = [(i, a) for i, a in enumerate(anchors_px) if a[0] < w / 2]
    right = [(i, a) for i, a in enumerate(anchors_px) if a[0] >= w / 2]
    mL = int(max([sizes[i][0] for i, _ in left], default=0) + 70)
    mR = int(max([sizes[i][0] for i, _ in right], default=0) + 70)
    top, bot = 150, 90
    tw = w + mL + mR
    th = h + top + bot
    fig = plt.figure(figsize=(tw / dpi, th / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, tw)
    ax.set_ylim(th, 0)
    ax.axis("off")
    ax.imshow(img, extent=(mL, mL + w, top + h, top))
    for side, items in (("L", left), ("R", right)):
        items.sort(key=lambda t: t[1][1])
        n = len(items)
        if not n:
            continue
        ys = np.array([a[1] + top for _, a in items], dtype=float)
        hs = np.array([sizes[i][1] for i, _ in items], dtype=float)
        for k in range(1, n):          # push apart, respecting multi-line heights
            ys[k] = max(ys[k], ys[k - 1] + (hs[k - 1] + hs[k]) / 2 + 14)
        over = ys[-1] + hs[-1] / 2 - (top + h + 40)
        if over > 0:
            ys -= over
            for k in range(n - 2, -1, -1):
                ys[k] = min(ys[k], ys[k + 1] - (hs[k] + hs[k + 1]) / 2 - 14)
        for (i, a), yl in zip(items, ys):
            ax_ = (a[0] + mL, a[1] + top)
            if side == "L":
                tx, ha, lx = mL - 30, "right", mL - 22
            else:
                tx, ha, lx = mL + w + 30, "left", mL + w + 22
            ax.plot([lx, ax_[0]], [yl, ax_[1]], color=(0.15, 0.2, 0.3), lw=1.1)
            ax.plot([ax_[0]], [ax_[1]], "o", ms=5, color=(0.85, 0.1, 0.1), mec="white", mew=0.8)
            ax.text(tx, yl, labels[i], ha=ha, va="center", fontsize=fontsize, color=(0.1, 0.12, 0.18),
                    linespacing=1.15)
    if title:
        ax.text(30, 52, title, fontsize=fontsize + 8, fontweight="bold", va="center", color=(0.08, 0.1, 0.16))
    if subtitle:
        ax.text(30, 108, subtitle, fontsize=fontsize - 1, va="center", color=(0.3, 0.33, 0.4))
    if footer:
        ax.text(30, th - 40, footer, fontsize=fontsize - 4, va="center", color=(0.35, 0.37, 0.42))
    if triad is not None:
        o, ex, ey, ez = triad
        base = np.array([mL + 90, top + h - 70], dtype=float)
        for tip, lab, col in ((ex, "X fwd", (0.8, 0.1, 0.1)), (ey, "Y left", (0.1, 0.6, 0.15)),
                              (ez, "Z up", (0.1, 0.2, 0.8))):
            d = np.array(tip) - np.array(o)
            nrm = np.linalg.norm(d)
            if nrm < 1e-6:
                continue
            d = d / nrm * 70
            ax.annotate("", xy=base + d, xytext=base,
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=2.2))
            ax.text(*(base + d * 1.32), lab, color=col, fontsize=fontsize - 3, ha="center", va="center",
                    fontweight="bold")
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def triad_px(pl, center=(0, 0, 0), L=100.0):
    c = np.array(center, dtype=float)
    return world_to_px(pl, [c, c + (L, 0, 0), c + (0, L, 0), c + (0, 0, L)])


def part_by(parts, pid):
    for p in parts:
        if p.pid == pid:
            return p
    raise KeyError(pid)


def anchor(parts, pid, off=(0, 0, 0)):
    c = part_by(parts, pid).solid.Center()
    return (c.x + off[0], c.y + off[1], c.z + off[2])


def crop_to_content(img, pad=40):
    mask = (img[..., :3] < 250).any(axis=2)
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return (0, 0, img.shape[1], img.shape[0])
    return (max(xs.min() - pad, 0), max(ys.min() - pad, 0),
            min(xs.max() + pad, img.shape[1]), min(ys.max() + pad, img.shape[0]))


FOOT = ("WB-700 Phase 1 concept CAD - generated by cad/build_all.py from wb700_params.py | "
        "grey/blue boxes = PLACEHOLDER envelopes for unselected purchased parts | units: mm")


# --------------------------------------------------------------------------- figures
def _surface_pt(R, y, ang_deg):
    """Point on the sphere of radius R at lateral coordinate y, angle measured in XZ from +X."""
    r = math.sqrt(max(R * R - y * y, 0.0))
    a = math.radians(ang_deg)
    return (r * math.cos(a), y, r * math.sin(a))


def render_iso(P, figdir):
    parts = build_parts(P, include_envelopes=False)
    pl = new_plotter()
    for p in parts:
        add_part(pl, p, edges=p.pid in ("SH-01", "SH-02", "SH-03"))
    for pid in ("SH-01", "SH-02"):
        try:
            pl.add_silhouette(pv_mesh(part_by(parts, pid).solid, 0.15, 0.05), color=(0.3, 0.38, 0.5),
                              line_width=2.0)
        except Exception:  # noqa: BLE001
            pass
    pl.camera_position = [(1450, 1050, 620), (0, 0, -35), (0, 0, 1)]
    pl.render()
    img = pl.screenshot(return_img=True)
    labels = [
        (_surface_pt(P.R_o, 120, 62), "Clear PC hemisphere, OD 700 mm, wall 3 mm"),
        (_surface_pt(P.R_o, 70, -32), "Clear PU tape band over seam (0.35 mm)"),
        (anchor(parts, "ST-02", (0, 20, 0)), "Left polar hub (non-rotating, flush):\nmanual disconnect + charge port"),
        (anchor(parts, "SE-01", (6, 0, 0)), "Camera Module 3 Wide on\npitch-stabilising servo"),
        (anchor(parts, "DR-01", (0, -40, 0)), "Drive gearmotor L (placeholder)"),
        (anchor(parts, "SH-21", (0, 0, 50)), "Ring gear 72T on pole flange (R)"),
        (anchor(parts, "ST-12", (1.5, 62, -38)), "Stator box frame (6061, 3 mm)"),
        (anchor(parts, "PW-10", (20, 0, 10)), "6S1P Li-ion pack, 97 Wh"),
        (anchor(parts, "BL-04", (0, -90, 25)), "Arc ballast plates (steel, tunable)"),
        (anchor(parts, "BB-01", (0, 0, 40)), "Steering bob hanger (tilts +/-30 deg)"),
        (anchor(parts, "SA-04", (0, 0, 0)), "E-stop receiver / safety supervisor"),
        (anchor(parts, "DV-01", (0, 0, 0)), "Dual drive motor driver"),
        (anchor(parts, "CP-01", (0, 0, 26)), "Raspberry Pi 5 (vision + navigation)"),
    ]
    px = world_to_px(pl, [a for a, _ in labels])
    tri = triad_px(pl)
    pl.close()
    annotate(img, px, [t for _, t in labels], os.path.join(figdir, "Isometric_Render.png"),
             title="WB-700 - isometric view (shell translucent)",
             subtitle="Pendulum-driven ball | 700 mm shell | stationary-axle stator | twin geared drive | tilting ballast bob",
             footer=FOOT, crop=crop_to_content(img), triad=tri)


def _cut_keep_y_ge(parts, y_cut):
    big = cq.Solid.makeBox(2000, 2000, 2000, cq.Vector(-1000, y_cut, -1000))
    out = []
    for p in parts:
        try:
            s = p.solid.intersect(big)
            if s.Volume() <= 1e-3:
                continue
        except Exception:  # noqa: BLE001
            continue
        cut_faces = [f for f in s.Faces()
                     if abs(f.Center().y - y_cut) < 1e-3 and abs(abs(f.normalAt(f.Center()).y) - 1) < 1e-6]
        out.append((p, s, cut_faces))
    return out


def render_section(P, figdir):
    """Mid-plane cutaway: plane y = 0, right half removed, viewed from the right-front."""
    y_cut = 0.0
    parts = build_parts(P, include_envelopes=False)
    cut = _cut_keep_y_ge(parts, y_cut)
    pl = new_plotter()
    for p, s, faces in cut:
        fine = p.pid.startswith(("SH-0", "BL"))
        m = pv_mesh(s, tol=0.15 if fine else 0.35, ang=0.05 if fine else 0.2)
        if m is None:
            continue
        op = {"SH-01": 0.10, "SH-02": 0.10, "SH-03": 0.40, "SH-04": 0.12}.get(p.pid, p.opacity)
        if op <= 0:
            continue
        add_part(pl, p, mesh=m, opacity=op, edges=p.pid in ("SH-01",))
        if op < 0.3:
            continue
        for f in faces:  # section faces: darker tone + black outline
            fm = pv_mesh(f, 0.2, 0.1)
            if fm is None:
                continue
            fm = fm.translate((0, -0.3, 0), inplace=False)
            pl.add_mesh(fm, color=tuple(0.55 * c for c in p.color), opacity=1.0, ambient=0.4)
            fe = fm.extract_feature_edges(boundary_edges=True, feature_edges=False, manifold_edges=False,
                                          non_manifold_edges=False)
            if fe.n_cells:
                pl.add_mesh(fe, color="black", line_width=1.6)
    ring = pv.Circle(radius=P.R_o, resolution=360).rotate_x(90, inplace=False)
    pl.add_mesh(ring.extract_feature_edges(), color=(0.2, 0.3, 0.45), line_width=3)
    pl.camera_position = [(520, -1600, 330), (0, 60, -70), (0, 0, 1)]
    pl.render()
    img = pl.screenshot(return_img=True)

    def c_of(pid, off=(0, 0, 0)):
        for p, s, _ in cut:
            if p.pid == pid:
                c = s.Center()
                return (c.x + off[0], c.y + off[1], c.z + off[2])
        return anchor(parts, pid, off)

    a60 = math.radians(60)
    labels = [
        ((P.R_o * math.cos(a60), 0.0, P.R_o * math.sin(a60)), "PC shell 3 mm (section edge)"),
        ((0.0, 7.0, -P.R_i + 2.5), "Clear spigot band (equatorial joint)"),
        ((0.0, 0.5, -13.5), "Stationary hollow axle 30 x 3 (cut)"),
        ((0.0, 0.5, 18.0), "IMU on axle saddle"),
        ((158.4, 50.0, 22.0), "Camera Module 3 Wide + pitch servo"),
        ((60.0, 0.5, -45.0), "Steering pivot shaft (cut), 45 mm below axle"),
        ((137.0, 0.5, -60.0), "Self-locking steering worm gearmotor"),
        ((0.0, 0.5, -229.0), "Battery 6S1P 21700 (cut)"),
        ((78.0, 0.5, -290.0), "Arc ballast plates, R215-R265 about pivot (cut)"),
        ((102.5, 0.5, -150.0), "Bob hanger (cut)"),
        (c_of("ST-02", (0, 0, 45)), "Left hub: manual disconnect + charge port"),
        (c_of("SH-20", (0, 0, 52)), "Ring gear 72T (shell) / pinion 18T (stator)"),
        (c_of("CP-02", (0, 0, 0)), "Motor-control MCU (rear plate)"),
        ((-123.5, 0.5, -10.0), "Rear plate (cut)"),
    ]
    px = world_to_px(pl, [a for a, _ in labels])
    tri = triad_px(pl)
    pl.close()
    annotate(img, px, [t for _, t in labels], os.path.join(figdir, "Cross_Section.png"),
             title="WB-700 - cross-section render on the mid-plane y = 0 (right half removed)",
             subtitle="Black-outlined dark faces are true section faces of the CAD solids; shell translucent; camera at y = +50 mm",
             footer=FOOT, crop=crop_to_content(img), triad=tri)


def render_exploded(P, figdir):
    parts = build_parts(P, explode=190.0, include_envelopes=False)
    pl = new_plotter()
    for p in parts:
        add_part(pl, p, opacity=(0.28 if p.pid in ("SH-01", "SH-02") else None),
                 edges=p.pid in ("SH-01", "SH-02", "SH-03"))
    pl.camera_position = [(1900, 1350, 700), (0, -40, -90), (0, 0, 1)]
    pl.render()
    img = pl.screenshot(return_img=True)
    labels = [
        ("SH-01", (0, 120, 230), "1  Left hemisphere (stays on stator)"),
        ("SH-02", (0, -120, 230), "2  Right hemisphere (slides off along -Y)"),
        ("SH-03", (0, 0, 300), "3  Clear spigot band + 4 key tabs"),
        ("ST-03", (0, 0, 0), "4  Right hub + M12 preload bolt"),
        ("SH-21", (0, 0, 45), "5  Right ring gear (slides out of mesh)"),
        ("ST-02", (0, 0, 0), "6  Left hub: disconnect, charge port, LED"),
        ("DR-01", (0, 0, 0), "7  Gearmotor L + arm + pinion"),
        ("DR-02", (0, 0, 0), "8  Gearmotor R + arm + pinion"),
        ("ST-12", (0, -40, 40), "9  Stator box frame"),
        ("CP-01", (0, 0, 0), "10 Raspberry Pi 5 + MCU"),
        ("SE-01", (0, 0, 0), "11 Camera + pitch servo"),
        ("SG-04", (0, 0, 0), "12 Steering worm gearmotor"),
        ("PW-10", (0, 0, 0), "13 Battery (out along -Y)"),
        ("BL-01", (0, 0, 0), "14 Arc ballast plates"),
        ("BB-03", (0, 0, 0), "15 Bob tray + hangers"),
        ("SE-03", (0, 0, 0), "16 IMU"),
        ("SA-01", (0, 0, 0), "17 Contactor + brake relays"),
        ("DV-01", (0, 0, 0), "18 Dual drive motor driver"),
    ]
    px = world_to_px(pl, [anchor(parts, pid, off) for pid, off, _ in labels])
    tri = triad_px(pl)
    pl.close()
    annotate(img, px, [t for *_, t in labels], os.path.join(figdir, "Exploded_Assembly.png"),
             title="WB-700 - exploded assembly",
             subtitle="Service: pull arming plug (6) -> left hub down -> remove one M12 bolt (4) -> lift (2); gears (5) disengage axially",
             footer=FOOT, crop=crop_to_content(img), triad=tri, fontsize=14)


def render_all(P, out_dir, figdir):
    os.makedirs(figdir, exist_ok=True)
    for fn in (render_iso, render_section, render_exploded):
        fn(P, figdir)
        print("[render]", fn.__name__, "ok")
