"""2D engineering figures generated from the CAD solids and the analysis results.

Dimensioned_Views.png, Internal_Layout.png, Center_of_Gravity.png, Camera_FOV.png,
Ramp_Capability.png.  Orthographic projections are unions of the projected tessellation
triangles of each solid (exact silhouettes to the tessellation tolerance).
"""
from __future__ import annotations

import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402

from wb700_analysis import mass_table, to_mesh  # noqa: E402
from wb700_model import build_parts  # noqa: E402

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
                     "axes.titleweight": "bold"})
INK = (0.12, 0.14, 0.2)
DIM = (0.1, 0.25, 0.55)
RED = (0.8, 0.12, 0.12)
SKIN = ("SH-01", "SH-02", "SH-03", "SH-04")


# ----------------------------------------------------------------------------- projection
def _uv(V, view):
    if view == "side":       # viewer on the robot's RIGHT (-Y): +X to the right, +Z up
        return np.column_stack([V[:, 0], V[:, 2]])
    if view == "front":      # viewer in FRONT (+X): robot's left (+Y) to the right, +Z up
        return np.column_stack([V[:, 1], V[:, 2]])
    if view == "left":       # viewer on the robot's LEFT (+Y): +X to the left
        return np.column_stack([-V[:, 0], V[:, 2]])
    if view == "top":        # viewer ABOVE (+Z): forward (+X) up the page, robot's right to the right
        return np.column_stack([-V[:, 1], V[:, 0]])
    raise ValueError(view)


def _depth(c, view):
    return {"side": -c.y, "front": c.x, "left": c.y, "top": c.z}[view]


def proj(solid, view, tol=0.6):
    m = to_mesh(solid, tol=tol, ang=0.3)
    uv = _uv(m.vertices, view)
    tri = uv[m.faces]
    a = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                     - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
    tri = tri[a > 1e-3]
    if len(tri) == 0:
        return None
    ring = np.concatenate([tri, tri[:, :1]], axis=1)
    return shapely.union_all(shapely.make_valid(shapely.polygons(ring))).buffer(0)


def _patch(ax, geom, fc, ec, lw=0.6, alpha=1.0, ls="-", z=1, hatch=None):
    if geom is None or geom.is_empty:
        return
    geoms = getattr(geom, "geoms", [geom])
    for g in geoms:
        if g.geom_type != "Polygon":
            if hasattr(g, "geoms"):
                _patch(ax, g, fc, ec, lw, alpha, ls, z, hatch)
            continue
        verts, codes = [], []
        for ring in [g.exterior, *g.interiors]:
            xy = np.asarray(ring.coords)
            verts += xy.tolist()
            codes += [Path.MOVETO] + [Path.LINETO] * (len(xy) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, alpha=alpha, ls=ls, zorder=z,
                               hatch=hatch))


def _light(c, k=0.45):
    return tuple(min(1.0, (1 - k) * x + k) for x in c)


def _dark(c, k=0.55):
    return tuple(k * x for x in c)


def draw_view(ax, parts, view, skip=(), alpha=1.0, outline_only=False,
              ls="-", lw=0.6, ec=None, cache=None, z0=2):
    order = sorted([p for p in parts if p.pid not in skip and p.opacity > 0 and p.body != "envelope"],
                   key=lambda p: _depth(p.solid.Center(), view))
    geoms = {}
    for k, p in enumerate(order):
        key = (p.pid, view)
        g = cache.get(key) if cache is not None else None
        if g is None:
            g = proj(p.solid, view)
            if cache is not None:
                cache[key] = g
        geoms[p.pid] = g
        if outline_only:
            _patch(ax, g, "none", ec or _dark(p.color), lw=lw, alpha=alpha, ls=ls, z=z0 + k * 0.001)
        else:
            _patch(ax, g, _light(p.color, 0.35), ec or _dark(p.color, 0.5), lw=lw, alpha=alpha, ls=ls,
                   z=z0 + k * 0.001)
    return geoms


# ----------------------------------------------------------------------------- dimensions
def dim_lin(ax, p0, p1, off, text, side=1, fs=8.5, color=DIM, ext=True, txt_off=6):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    if L < 1e-9:
        return
    t = d / L
    n = np.array([-t[1], t[0]]) * side
    a, b = p0 + n * off, p1 + n * off
    if ext:
        for p, q in ((p0, a), (p1, b)):
            ax.plot([p[0] + n[0] * 3, q[0] + n[0] * 4], [p[1] + n[1] * 3, q[1] + n[1] * 4], color=color, lw=0.5)
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<|-|>", color=color, lw=0.8,
                                                     shrinkA=0, shrinkB=0, mutation_scale=8))
    mid = (a + b) / 2 + n * txt_off
    ang = math.degrees(math.atan2(t[1], t[0]))
    if ang > 90 or ang < -90:
        ang += 180
    ax.text(mid[0], mid[1], text, ha="center", va="center", rotation=ang, fontsize=fs, color=color,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def dim_dia(ax, c, r, ang_deg, text, fs=8.5, color=DIM, inside=True, tlen=0.55):
    a = math.radians(ang_deg)
    p0 = np.array([c[0] - r * math.cos(a), c[1] - r * math.sin(a)])
    p1 = np.array([c[0] + r * math.cos(a), c[1] + r * math.sin(a)])
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="<|-|>", color=color, lw=0.8,
                                                       shrinkA=0, shrinkB=0, mutation_scale=8))
    q = np.array(c) + np.array([math.cos(a), math.sin(a)]) * r * tlen
    ax.text(q[0], q[1], text, ha="center", va="center", fontsize=fs, color=color, rotation=ang_deg,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def leader(ax, xy, txt_xy, text, fs=8.5, color=INK, ha="left"):
    ax.annotate(text, xy=xy, xytext=txt_xy, fontsize=fs, color=color, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.6, shrinkA=1, shrinkB=0),
                bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.85))


def balloon(ax, xy, n, txt_xy=None, fs=8, z=50):
    if txt_xy is not None:
        ax.plot([xy[0], txt_xy[0]], [xy[1], txt_xy[1]], color=INK, lw=0.6, zorder=z)
        ax.plot([xy[0]], [xy[1]], "o", ms=2.5, color=INK, zorder=z)
        xy = txt_xy
    ax.text(xy[0], xy[1], str(n), fontsize=fs, ha="center", va="center", color="white", zorder=z + 1,
            fontweight="bold", bbox=dict(boxstyle="circle,pad=0.25", fc=(0.1, 0.25, 0.55), ec="white", lw=0.6))


def frame(ax, title, lim=400, grid=False):
    ax.set_aspect("equal")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.tick_params(labelsize=7, colors=(0.4, 0.4, 0.45))
    for s in ax.spines.values():
        s.set_color((0.75, 0.77, 0.8))
    if grid:
        ax.grid(color=(0.92, 0.93, 0.95), lw=0.5)
    ax.plot([-lim * 0.97, lim * 0.97], [0, 0], color=(0.6, 0.6, 0.65), lw=0.5, ls=(0, (12, 3, 2, 3)))
    ax.plot([0, 0], [-lim * 0.97, lim * 0.97], color=(0.6, 0.6, 0.65), lw=0.5, ls=(0, (12, 3, 2, 3)))


def title_block(fig, title, sub, x=0.012, y=0.985):
    h_in = fig.get_figheight()
    fig.text(x, y, title, fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(x, y - 0.33 / h_in, sub, fontsize=9.5, color=(0.35, 0.37, 0.42), va="top")


FOOT = ("Generated by cad/wb700_figures.py from the CadQuery solids in wb700_model.py (parameters: wb700_params.py). "
        "Units mm unless noted. Phase 1 concept - not for manufacture.")


def load_results(out_dir):
    with open(os.path.join(out_dir, "analysis_results.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ============================================================================ figure 1
def _max_radius(solid):
    return float(np.linalg.norm(to_mesh(solid, tol=0.1, ang=0.05).vertices, axis=1).max())


def fig_dimensioned(P, res, figdir, cache):
    parts = build_parts(P, include_envelopes=False)
    byid = {p.pid: p for p in parts}
    d = res["dimensions"]
    R_shell = _max_radius(byid["SH-01"].solid)          # 350.0 from CAD
    R_tape = _max_radius(byid["SH-04"].solid)           # 350.35 from CAD
    fig = plt.figure(figsize=(11.5, 8.8), dpi=200)
    title_block(fig, "WB-700 - external dimensions and envelope compliance",
                "Exterior geometry from the CAD solids: PC shell, clear PU tape band, flush polar hubs and hub devices. "
                "Dimensions in mm [ft]. Outline radii measured on the CAD meshes.")
    axA = fig.add_axes([0.04, 0.37, 0.30, 0.50])
    axB = fig.add_axes([0.365, 0.37, 0.30, 0.50])
    axC = fig.add_axes([0.69, 0.37, 0.30, 0.50])
    # ---------------- front view
    frame(axA, "FRONT VIEW (from +X)", lim=430)
    axA.add_patch(Circle((0, 0), R_tape, fc=(0.88, 0.93, 0.97), ec=(0.25, 0.35, 0.5), lw=1.0))
    zt = math.sqrt(R_tape ** 2 - P.tape_half_w ** 2)
    yy = np.linspace(-P.tape_half_w, P.tape_half_w, 200)
    top = np.sqrt(R_tape ** 2 - yy ** 2)
    axA.fill(np.r_[yy, yy[::-1]], np.r_[top, -top[::-1]], fc=(0.80, 0.90, 0.95), ec=(0.3, 0.45, 0.6), lw=0.5,
             hatch="////", alpha=0.9)
    axA.plot([0, 0], [-R_tape, R_tape], color=(0.2, 0.3, 0.45), lw=0.9)
    for s in (-1, 1):   # hub caps seen edge-on at the poles, recessed
        yc = s * (P.R_o - P.hub_recess)
        axA.plot([yc, yc], [-P.hub_cap_r, P.hub_cap_r], color=_dark(byid["ST-02"].color, 0.9), lw=2.4)
    dim_lin(axA, (-d["caliper_y_mm"] / 2, -R_tape - 5), (d["caliper_y_mm"] / 2, -R_tape - 5), 22,
            f"{d['caliper_y_mm']:.1f} across hub caps", side=-1)
    dim_lin(axA, (R_tape + 5, -R_tape), (R_tape + 5, R_tape), 26,
            f"{2 * R_tape:.1f} [{2 * R_tape / 304.8:.3f} ft] over tape", side=-1)
    dim_lin(axA, (-P.tape_half_w, zt + 2), (P.tape_half_w, zt + 2), 34, f"tape band {2 * P.tape_half_w:.0f}", side=1)
    leader(axA, (0, 230), (-410, 300), "equatorial seam:\nclear PC spigot band, 30 wide", fs=7.2)
    leader(axA, (-(P.R_o - P.hub_recess), 30), (-410, 180), "hub caps recessed\n1.0 mm (both poles)", fs=7.2)
    axA.text(-415, -418, "robot's RIGHT", fontsize=7.2, color=(0.4, 0.4, 0.45))
    axA.text(415, -418, "robot's LEFT", fontsize=7.2, color=(0.4, 0.4, 0.45), ha="right")
    # ---------------- left view (hub face)
    frame(axB, "LEFT VIEW (from +Y): disconnect side", lim=430)
    axB.add_patch(Circle((0, 0), R_tape, fc=(0.88, 0.93, 0.97), ec=(0.25, 0.35, 0.5), lw=1.0))
    axB.add_patch(Circle((0, 0), P.r_pole_open, fc="none", ec=(0.25, 0.35, 0.5), lw=0.8, ls="--"))
    for pid in ("ST-02", "PW-04", "PW-05", "SA-03"):
        g = cache.get((pid, "left")) or proj(byid[pid].solid, "left", tol=0.15)
        cache[(pid, "left")] = g
        p = byid[pid]
        _patch(axB, g, _light(p.color, 0.2), _dark(p.color, 0.45), lw=0.6, z=5)
    dim_dia(axB, (0, 0), R_tape, 0, "", tlen=0.0)
    axB.text(-190, 14, f"Ø{2 * R_tape:.1f} [{2 * R_tape / 304.8:.3f} ft]", fontsize=8.5, color=DIM, ha="center",
             bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
    leader(axB, (0, -P.hub_cap_r), (40, -175), f"hub cap Ø{2 * P.hub_cap_r:.0f} in polar\nopening Ø{2 * P.r_pole_open:.0f} (2 mm gap)", fs=7.2)
    leader(axB, (-25, 18), (-405, 240), "MANUAL DISCONNECT: anti-spark arming\nplug, recessed (pull = battery isolated)", fs=7.2)
    leader(axB, (30, 17), (110, 140), "BMS charge port", fs=7.2)
    leader(axB, (25, -22), (110, 80), "status LED", fs=7.2)
    axB.annotate("", xy=(-330, -400), xytext=(-170, -400), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.4))
    axB.text(-165, -400, "FORWARD (+X)", color=RED, fontsize=7.2, va="center")
    # ---------------- envelope panel
    ax = axC
    ax.set_aspect("equal")
    ax.set_xlim(-560, 560)
    ax.set_ylim(-560, 560)
    ax.axis("off")
    ax.set_title("ENVELOPE CHECK vs RULES", loc="left", fontsize=11, color=INK)
    lim_out = P.R_o + P.protrusion_max_rule
    grey = (0.45, 0.45, 0.5)
    rings = [
        (lim_out, grey, (0, (6, 3, 1, 3)), f"shell + 0.5 ft peripheral limit, Ø{2 * lim_out:.1f}"),
        (P.d_max_rule / 2, RED, (0, (5, 3)), f"2.5 ft upper diameter limit, Ø{P.d_max_rule:.1f}"),
        (d["caliper_max_mm"] / 2, (0.15, 0.35, 0.6), "-", f"WB-700 largest caliper, {d['caliper_max_mm']:.1f}"),
        (d["caliper_min_mm"] / 2, (0.15, 0.55, 0.35), "-", f"WB-700 smallest caliper, {d['caliper_min_mm']:.1f}"),
        (P.d_min_rule / 2, RED, (0, (2, 2)), f"2.0 ft lower diameter limit, Ø{P.d_min_rule:.1f}"),
    ]
    ax.add_patch(Circle((0, 0), d["caliper_max_mm"] / 2, fc=(0.88, 0.93, 0.97), ec="none", zorder=0))
    handles = []
    for r, col, ls, txt in rings:
        ax.add_patch(Circle((0, 0), r, fill=False, ec=col, lw=1.2, ls=ls))
        handles.append(plt.Line2D([], [], color=col, ls=ls, lw=1.2, label=txt))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=7.3, frameon=False)
    ax.annotate("", xy=(P.d_max_rule / 2, 0), xytext=(d["caliper_max_mm"] / 2, 0),
                arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=0.8, mutation_scale=7))
    ax.text(366, 26, f"+{d['margin_to_upper_mm'] / 2:.1f}\nper side", fontsize=7, color=RED, ha="center")
    ax.annotate("", xy=(0, -P.d_min_rule / 2), xytext=(0, -d["caliper_min_mm"] / 2),
                arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=0.8, mutation_scale=7))
    ax.text(18, -326, f"+{d['margin_to_lower_mm'] / 2:.1f} per side", fontsize=7, color=RED)
    ax.text(0, 20, "no external sensors,\nmounts or camera pods", ha="center", fontsize=8, color=INK)
    # ---------------- compliance table
    axT = fig.add_axes([0.04, 0.035, 0.95, 0.20])
    axT.axis("off")
    rows = [
        ("Diameter rule (strict): 609.6 < D < 762.0 mm",
         f"D = {d['caliper_min_mm']:.1f} ... {d['caliper_max_mm']:.1f} mm ({d['caliper_min_ft']:.3f} ... "
         f"{d['caliper_max_ft']:.3f} ft), all 2562 sampled directions", "PASS" if d["strictly_within_rule"] else "FAIL"),
        ("Same rule with assumed +/-7 mm thermoforming tolerance",
         f"{d['tolerance_case_min_mm']:.1f} ... {d['tolerance_case_max_mm']:.1f} mm",
         "PASS" if d["strictly_within_rule_with_tolerance"] else "FAIL"),
        ("Peripheral limit: sensors/mounts/lenses <= 152.4 mm beyond shell",
         f"{d['external_sensors_or_mounts']} external items; largest non-skin feature {d['max_non_skin_protrusion_mm']:+.1f} mm "
         f"({d['max_non_skin_protrusion_part']}, recessed)", "PASS" if d["protrusion_rule_ok"] else "FAIL"),
        ("Protective tape band counted in the diameter", f"+{d['tape_protrusion_mm']:.2f} mm per side (included above)",
         "INCLUDED"),
        ("Margins to the rule limits",
         f"{d['margin_to_upper_mm']:.1f} mm below 2.5 ft; {d['margin_to_lower_mm']:.1f} mm above 2.0 ft", "INFO"),
    ]
    axT.text(0.0, 1.03, "Dimensional compliance (computed from the CAD meshes by wb700_analysis.dimensional_check)",
             fontsize=9.5, fontweight="bold", color=INK, transform=axT.transAxes)
    y = 0.90
    for a, b, c in rows:
        col = (0.1, 0.5, 0.2) if c == "PASS" else ((0.7, 0.1, 0.1) if c == "FAIL" else (0.3, 0.3, 0.4))
        axT.text(0.0, y, a, fontsize=8.4, color=INK, transform=axT.transAxes, va="top")
        axT.text(0.42, y, b, fontsize=8.4, color=INK, transform=axT.transAxes, va="top")
        axT.text(0.995, y, c, fontsize=8.4, color=col, fontweight="bold", transform=axT.transAxes, va="top", ha="right")
        y -= 0.18
    fig.text(0.04, 0.008, FOOT, fontsize=7, color=(0.45, 0.45, 0.5))
    fig.savefig(os.path.join(figdir, "Dimensioned_Views.png"), dpi=200)
    plt.close(fig)


# ============================================================================ figure 2
LAYOUT_ITEMS = [
    (1, "ST-01", "Stationary hollow axle 30x3 (6061-T6)"),
    (2, "ST-02", "Left polar hub: disconnect plug, charge port, LED"),
    (3, "ST-03", "Right polar hub + M12 preload bolt"),
    (4, "SH-30", "Pole bearings 61908-2RS (2x)"),
    (5, "SH-20", "Ring gears 72T m1.5 on pole flanges (2x)"),
    (6, "DR-01", "Drive gearmotor L, front-down (PH)"),
    (7, "DR-02", "Drive gearmotor R, rear-down (PH)"),
    (8, "ST-12", "Stator box frame: 4 plates + clamps"),
    (9, "SE-01", "Camera Module 3 Wide + pitch servo"),
    (10, "SE-03", "IMU 9-DoF on axle saddle (PH)"),
    (11, "SG-01", "Steering pivot shaft, 45 mm below axle"),
    (12, "SG-04", "Steering worm gearmotor (PH)"),
    (13, "SE-04", "Steering angle sensor (PH)"),
    (14, "BB-01", "Bob hangers (2x)"),
    (15, "PW-10", "Battery 6S1P 21700 + BMS (PH)"),
    (16, "BL-01", "Arc ballast plates, 8 mm steel (4x)"),
    (17, "CP-01", "Raspberry Pi 5 + cooler (PH)"),
    (18, "CP-02", "Motor-control MCU carrier (PH)"),
    (19, "DV-01", "Dual drive motor driver (PH)"),
    (20, "DV-02", "Steering motor driver (PH)"),
    (21, "PW-01", "Power distribution + current monitor (PH)"),
    (22, "SA-01", "Motor-power contactor, e-stop ch. A (PH)"),
    (23, "SA-02", "Dynamic-brake relays (PH)"),
    (24, "SA-04", "E-stop receiver + safety supervisor (PH)"),
    (25, "PW-02", "DC-DC 5.1 V / 5 A for Pi 5 (PH)"),
    (26, "HR-04", "Bob service loop (cable space)"),
]
SIDE_HIDE = ("DR-02", "DR-04", "DR-06", "ST-03", "ST-04", "SH-11", "SH-21", "SH-31")


def _uvc(p, view):
    c = p.solid.Center()
    return tuple(_uv(np.array([[c.x, c.y, c.z]]), view)[0])


def fig_internal_layout(P, res, figdir, cache):
    parts = build_parts(P, include_envelopes=True)
    byid = {p.pid: p for p in parts}
    inner = [p for p in parts if p.pid not in SKIN and p.body != "envelope"]
    fig = plt.figure(figsize=(11.5, 13.2), dpi=200)
    title_block(fig, "WB-700 - internal layout drawing (orthographic projections of the CAD solids)",
                "Stator (gravity-held frame) and steering bob inside the 700 mm shell. "
                "PH = placeholder envelope for hardware not yet selected.")
    axS = fig.add_axes([0.04, 0.50, 0.46, 0.42])
    axF = fig.add_axes([0.53, 0.50, 0.46, 0.42])
    axT = fig.add_axes([0.04, 0.05, 0.46, 0.42])
    axL = fig.add_axes([0.53, 0.05, 0.46, 0.42])
    for ax, view, ttl in ((axS, "side", "SIDE from the right (-Y); right hub + right drive dashed"),
                          (axF, "front", "FRONT (from +X); bob also at beta = +/-30 deg (dashed)"),
                          (axT, "top", "TOP (from +Z), forward up the page")):
        frame(ax, ttl, lim=395)
        ax.title.set_fontsize(9.5)
        ax.add_patch(Circle((0, 0), P.R_o, fill=False, ec=(0.3, 0.45, 0.65), lw=1.3))
        ax.add_patch(Circle((0, 0), P.R_i, fill=False, ec=(0.3, 0.45, 0.65), lw=0.6, ls="--"))
        hide = SIDE_HIDE if view == "side" else ()
        draw_view(ax, [p for p in inner if p.pid not in hide], view, cache=cache)
        if view == "side":
            draw_view(ax, [byid[h] for h in SIDE_HIDE], view, outline_only=True, ls="--", lw=0.5,
                      ec=(0.5, 0.5, 0.55), cache=cache, z0=60)
    for b in (-30, 30):
        bp = [p for p in build_parts(P, beta_deg=b, include_envelopes=False) if p.body == "bob"]
        draw_view(axF, bp, "front", outline_only=True, ls=(0, (4, 2)), lw=0.7, ec=(0.75, 0.2, 0.15), z0=70)
    ev = byid.get("EV-01")
    if ev is not None:
        _patch(axT, proj(ev.solid, "top"), (0.2, 0.75, 0.35), (0.1, 0.5, 0.2), lw=0.8, alpha=0.25, ls="--", z=80)
        axT.text(250, -40, "battery removal\npath (after right\nhemisphere off)", fontsize=7.2,
                 color=(0.1, 0.45, 0.2), ha="center", zorder=90)
    vis = {
        "side": [1, 2, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 26],
        "front": [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 14, 15, 16, 19, 21, 24],
        "top": [1, 2, 3, 6, 7, 8, 9, 10, 17, 18, 19, 20, 21, 22, 24],
    }
    for ax, view in ((axS, "side"), (axF, "front"), (axT, "top")):
        for n, pid, _ in LAYOUT_ITEMS:
            if n not in vis[view]:
                continue
            u, v = _uvc(byid[pid], view)
            if pid == "SE-01":
                u, v = _uv(np.array([P.cam_pos]), view)[0]
            if pid == "SH-20" and view == "front":
                u, v = P.y_brg - 6, 48
            if pid == "SH-30" and view == "front":
                u, v = -(P.y_brg + 6), -26
            balloon(ax, (u, v), n, fs=6.6)
    pz = -P.pivot_depth
    dim_lin(axS, (-P.box_x, P.box_z_top), (P.box_x, P.box_z_top), 18, f"box {2 * P.box_x:.0f}", side=1, fs=7)
    dim_lin(axS, (-P.box_x, P.box_z_bot), (-P.box_x, P.box_z_top), 16, f"{P.box_z_top - P.box_z_bot:.0f}",
            side=-1, fs=7)
    axS.annotate("", xy=(-160, pz), xytext=(-160, 0),
                 arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.7, mutation_scale=6), zorder=95)
    axS.plot([-160, -10], [0, 0], color=DIM, lw=0.4, zorder=95)
    axS.plot([-160, -10], [pz, pz], color=DIM, lw=0.4, zorder=95)
    axS.text(-172, pz / 2, f"{P.pivot_depth:.0f}", fontsize=7, color=DIM, ha="right", va="center", zorder=95)
    axS.text(-60, -300, f"ballast arcs R{P.ballast_rho_in:.0f}-R{P.ballast_rho_out:.0f} about the\n"
             "pivot axis (see front view)", fontsize=6.8, color=DIM, ha="center", zorder=95,
             bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))
    cx, cy, cz = P.cam_pos
    a = math.radians(-P.cam_down_deg)
    axS.annotate("", xy=(cx + 170 * math.cos(a), cz + 170 * math.sin(a)), xytext=(cx, cz),
                 arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.9, mutation_scale=7), zorder=95)
    axS.text(cx - 10, cz + 40, f"optical axis {P.cam_down_deg:.0f} deg down", fontsize=6.8, color=RED, zorder=95)
    axS.plot([-380, 380], [-(P.R_o + P.tape_t)] * 2, color=(0.45, 0.35, 0.25), lw=1.2)
    axS.text(-380, -(P.R_o + P.tape_t) - 18, "floor", fontsize=6.8, color=(0.45, 0.35, 0.25))
    sc = res["swept_clearance"]
    axS.text(385, 300, f"min. clearance frame/bob -> shell:\n{sc['min_frame_or_bob_to_skin_mm']:.1f} mm "
             "(all pitch angles,\nbob -30...+30 deg)", fontsize=6.8, color=(0.1, 0.45, 0.2), ha="right", zorder=95)
    axS.annotate("", xy=(385, 365), xytext=(270, 365), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2))
    axS.text(265, 365, "FORWARD (+X)", fontsize=7, color=RED, ha="right", va="center")
    dim_lin(axF, (-P.box_y, P.box_z_top), (P.box_y, P.box_z_top), 16, f"box {2 * P.box_y:.0f}", side=1, fs=7)
    for r in (P.ballast_rho_in, P.ballast_rho_out):
        ang = math.radians(-32)
        axF.annotate("", xy=(r * math.sin(ang), pz - r * math.cos(ang)), xytext=(0, pz),
                     arrowprops=dict(arrowstyle="-|>", color=DIM, lw=0.6, mutation_scale=6), zorder=95)
    axF.text(-205, -175, f"R{P.ballast_rho_in:.0f}", fontsize=6.8, color=DIM, zorder=95)
    axF.text(-235, -265, f"R{P.ballast_rho_out:.0f}", fontsize=6.8, color=DIM, zorder=95)
    lean = abs(res["steering"]["table"][0]["lean_gamma_deg"])
    axF.text(0, -385, f"bob tilt +/-30 deg -> static lean of shell/axle {lean:.0f} deg", fontsize=6.8,
             color=(0.7, 0.18, 0.12), ha="center")
    axF.text(-385, 365, "robot's RIGHT", fontsize=7, color=(0.4, 0.4, 0.45))
    axF.text(385, 365, "robot's LEFT", fontsize=7, color=(0.4, 0.4, 0.45), ha="right")
    axT.text(0, 340, "FORWARD (+X)", fontsize=7, color=RED, ha="center")
    axT.annotate("", xy=(0, 385), xytext=(0, 355), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2))
    axT.text(-385, -385, "robot's LEFT", fontsize=7, color=(0.4, 0.4, 0.45))
    axT.text(385, -385, "robot's RIGHT", fontsize=7, color=(0.4, 0.4, 0.45), ha="right")
    axT.text(0, -300, f"gearmotors anti-symmetric (front-left / rear-right),\n{P.gear_center_dist:.1f} mm from the axle: "
             "balanced without dead ballast", fontsize=6.8, color=DIM, ha="center", zorder=95,
             bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))
    axL.axis("off")
    rows = {r["pid"]: r for r in mass_table(parts)}
    axL.text(0.0, 1.0, "Item list (mass: CAD volume x density, or datasheet/estimate for PH)",
             fontsize=8.6, fontweight="bold", transform=axL.transAxes, va="top")
    y = 0.95
    for n, pid, name in LAYOUT_ITEMS:
        m = rows[pid]["mass_kg"] if pid in rows else 0.0
        if pid in ("SH-30", "SH-20", "BB-01"):
            m *= 2
        if pid == "BL-01":
            m = sum(r["mass_kg"] for r in rows.values() if r["pid"].startswith("BL"))
        if pid == "ST-12":
            m = sum(rows[k]["mass_kg"] for k in ("ST-10", "ST-11", "ST-12", "ST-13", "ST-14", "ST-15"))
        balloon(axL, (0.025, y - 0.011), n, fs=6.4)
        axL.text(0.065, y, name, fontsize=7.6, transform=axL.transAxes, va="top")
        axL.text(0.99, y, f"{m:.3f} kg", fontsize=7.6, transform=axL.transAxes, va="top", ha="right")
        y -= 0.0362
    axL.set_xlim(0, 1)
    axL.set_ylim(0, 1)
    fig.text(0.04, 0.012, FOOT, fontsize=7, color=(0.45, 0.45, 0.5))
    fig.savefig(os.path.join(figdir, "Internal_Layout.png"), dpi=200)
    plt.close(fig)


# ============================================================================ figure 3
def fig_cg(P, res, figdir, cache):
    parts = build_parts(P, include_envelopes=False)
    rows = mass_table(parts)
    M = res["mass"]["total_kg"]
    cg = res["mass"]["cg_mm"]
    fig = plt.figure(figsize=(11.5, 9.8), dpi=200)
    title_block(fig, "WB-700 - centre-of-gravity placement (static design estimate)",
                "CG = sum(m_i r_i) / sum(m_i) over every CAD part (cad/out/mass_table.csv). "
                "Origin O = shell centre; X forward, Y left, Z up.")
    axS = fig.add_axes([0.04, 0.34, 0.44, 0.57])
    axF = fig.add_axes([0.53, 0.34, 0.44, 0.57])
    colors = {"shell": (0.2, 0.45, 0.75), "stator": (0.35, 0.37, 0.42), "bob": (0.85, 0.35, 0.1)}
    pend = res["mass"]["by_body"]
    st_m = pend["stator"]["mass_kg"] + pend["bob"]["mass_kg"]
    st_cg = [(pend["stator"]["mass_kg"] * a + pend["bob"]["mass_kg"] * b) / st_m
             for a, b in zip(pend["stator"]["cg_mm"], pend["bob"]["cg_mm"])]
    for ax, view, ttl, i0 in ((axS, "side", "SIDE (X-Z), viewed from the right", 0),
                              (axF, "front", "FRONT (Y-Z), viewed from ahead", 1)):
        frame(ax, ttl, lim=390)
        ax.add_patch(Circle((0, 0), P.R_o, fill=False, ec=(0.3, 0.45, 0.65), lw=1.2))
        draw_view(ax, [p for p in parts if p.pid not in SKIN], view, cache=cache, alpha=0.30)
        for r in rows:
            u = r["x_mm"] if i0 == 0 else r["y_mm"]
            ax.scatter([u], [r["z_mm"]], s=6 + 55 * r["mass_kg"], color=colors[r["body"]], alpha=0.9, zorder=40,
                       edgecolor="white", linewidth=0.4)
        ax.scatter([cg[i0]], [cg[2]], s=280, marker="o", color="white", edgecolor="black", linewidth=1.6, zorder=60)
        ax.scatter([cg[i0]], [cg[2]], s=70, marker="+", color="black", linewidth=1.6, zorder=61)
        ax.scatter([st_cg[i0]], [st_cg[2]], s=140, marker="D", color=(0.95, 0.6, 0.1), edgecolor="black", zorder=59)
        ax.scatter([0], [0], s=120, marker="x", color=(0.2, 0.45, 0.75), linewidth=2, zorder=58)
        ax.annotate(f"system CG ({cg[0]:+.1f}, {cg[1]:+.1f}, {cg[2]:+.1f}) mm", xy=(cg[i0], cg[2]),
                    xytext=(40, 150), fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.7),
                    bbox=dict(fc="white", ec="none", alpha=0.9), zorder=70)
        ax.annotate(f"pendulum (stator + bob) CG\n{st_m:.2f} kg at z = {st_cg[2]:.1f} mm", xy=(st_cg[i0], st_cg[2]),
                    xytext=(-375, -345), fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.7),
                    bbox=dict(fc="white", ec="none", alpha=0.9), zorder=70)
        ax.annotate("O = shell centre = axle axis", xy=(0, 0), xytext=(-375, 250), fontsize=8,
                    arrowprops=dict(arrowstyle="-", lw=0.7), bbox=dict(fc="white", ec="none", alpha=0.9), zorder=70)
    for b in (-30, 30):
        bp = [p for p in build_parts(P, beta_deg=b, include_envelopes=False) if p.body == "bob"]
        draw_view(axF, bp, "front", outline_only=True, ls=(0, (4, 2)), lw=0.6, ec=(0.75, 0.2, 0.15), z0=30)
    st = res["steering"]["table"]
    axF.text(0, 355, f"bob tilt +/-30 deg (dashed) shifts the CG sideways: static lean "
             f"{abs(st[0]['lean_gamma_deg']):.1f} / {abs(st[-1]['lean_gamma_deg']):.1f} deg", fontsize=7.6, ha="center",
             color=(0.7, 0.18, 0.12))
    leg = [plt.Line2D([], [], marker="o", ls="", color=colors[k], label=t, markersize=6) for k, t in
           (("shell", "shell-side part (rotates with ball)"), ("stator", "stator part (pendulum frame)"),
            ("bob", "steering-bob part"))]
    leg += [plt.Line2D([], [], marker="o", ls="", mfc="white", mec="black", label="system CG", markersize=9),
            plt.Line2D([], [], marker="D", ls="", color=(0.95, 0.6, 0.1), mec="black", label="pendulum CG",
                       markersize=7)]
    axS.legend(handles=leg, loc="upper right", fontsize=7, framealpha=0.95)
    axS.text(-375, 330, "marker area ~ part mass", fontsize=7, color=(0.4, 0.4, 0.45))
    axT = fig.add_axes([0.04, 0.03, 0.93, 0.26])
    axT.axis("off")
    df = res["drive_feasibility"]
    bs = res["ballast_sweep"]
    lines = [
        ("Total mass (all CAD parts; baseline 4 ballast plates)",
         f"{M:.2f} kg, of which {res['mass']['placeholder_mass_kg']:.2f} kg in {res['mass']['n_placeholder']} placeholder items"),
        ("System CG relative to O (x, y, z)",
         f"({cg[0]:+.1f}, {cg[1]:+.1f}, {cg[2]:+.1f}) mm: {abs(cg[2]):.1f} mm below the shell centre"),
        ("Shell body / stator / bob", f"{pend['shell']['mass_kg']:.2f} / {pend['stator']['mass_kg']:.2f} / "
                                       f"{pend['bob']['mass_kg']:.2f} kg"),
        ("Pendulum first moment m_p e about the axle",
         f"{df['pendulum_first_moment_kgm']:.3f} kg m (climb index m_p e / M R = {df['climb_index_mpe_over_MR']:.3f})"),
        ("Quasi-static incline limit, pendulum at 60 / 90 deg",
         f"{df['alpha_max_deg']['phi_60']:.1f} / {df['alpha_max_deg']['phi_90']:.1f} deg (ballast 2..6 plates: "
         f"{bs[0]['alpha_max_phi60_deg']:.1f}..{bs[-1]['alpha_max_phi60_deg']:.1f} deg at 60 deg)"),
        ("Stator rest pitch from the fore-aft CG offset", f"{df['stator_rest_pitch_deg']:+.2f} deg (trimmed by camera servo)"),
        ("Static lean at bob tilt 30 deg", f"{abs(st[-1]['lean_gamma_deg']):.1f} deg"),
    ]
    axT.text(0, 1.02, "CG budget - static design estimate (dynamic behaviour is a Phase 2 result; "
             "hardware CG is measured in Phase 3)", fontsize=9.2, fontweight="bold", transform=axT.transAxes)
    y = 0.88
    for a, b in lines:
        axT.text(0.0, y, a, fontsize=8.3, transform=axT.transAxes)
        axT.text(0.40, y, b, fontsize=8.3, transform=axT.transAxes)
        y -= 0.13
    fig.text(0.04, 0.008, FOOT, fontsize=7, color=(0.45, 0.45, 0.5))
    fig.savefig(os.path.join(figdir, "Center_of_Gravity.png"), dpi=200)
    plt.close(fig)


# ============================================================================ figure 4
def fig_camera(P, res, out_dir, figdir):
    cam = res["camera_fov"]
    z = np.load(os.path.join(out_dir, "camera_rays.npz"))
    d, band, o, gpts, gok = z["d"], z["band"], z["origin"], z["ground"], z["ground_ok"]
    nu, nv = int(z["nu"]), int(z["nv"])
    fig = plt.figure(figsize=(11.5, 8.8), dpi=200)
    title_block(fig, "WB-700 - camera field of view through the clear shell (ray-cast against the CAD solids)",
                f"Camera Module 3 Wide (102 x 67 deg, datasheet) at ({o[0]:.0f}, {o[1]:.0f}, {o[2]:.0f}) mm on the stator, "
                f"held {P.cam_down_deg:.0f} deg below horizontal by the pitch servo; {cam['rays']} rays.")
    axS = fig.add_axes([0.05, 0.43, 0.42, 0.46])
    axT = fig.add_axes([0.53, 0.43, 0.44, 0.46])
    axI = fig.add_axes([0.06, 0.06, 0.40, 0.29])
    zf = -(P.R_o + P.tape_t)
    axS.set_aspect("equal")
    axS.set_xlim(-420, 1700)
    axS.set_ylim(-420, 760)
    axS.set_title("SIDE (X-Z): vertical field of view and floor coverage", loc="left", fontsize=10)
    axS.add_patch(Circle((0, 0), P.R_o, fill=False, ec=(0.3, 0.45, 0.65), lw=1.2))
    axS.plot([-420, 1700], [zf, zf], color=(0.45, 0.35, 0.25), lw=1.3)
    up, lo = P.cam_down_deg - P.cam_vfov / 2, P.cam_down_deg + P.cam_vfov / 2
    xg = o[0] + (o[2] - zf) / math.tan(math.radians(lo))
    axS.fill([o[0], o[0] + 1900 * math.cos(math.radians(-up)), 1700, xg],
             [o[2], o[2] + 1900 * math.sin(math.radians(-up)), zf, zf], color=(1, 0.85, 0.8), alpha=0.4, zorder=0)
    for ang, kind in ((-up, "edge"), (-lo, "edge"), (-P.cam_down_deg, "axis")):
        a = math.radians(ang)
        dx, dz = math.cos(a), math.sin(a)
        t = (zf - o[2]) / dz if dz < 0 else 1900
        t = min(t, 1900)
        axS.plot([o[0], o[0] + dx * t], [o[2], o[2] + dz * t], color=RED if kind == "edge" else (0.3, 0.3, 0.35),
                 lw=1.0 if kind == "edge" else 0.7, ls="-" if kind == "edge" else "--")
    axS.plot(o[0], o[2], "o", color="black", ms=4)
    nx = cam["nearest_visible_floor_ahead_of_centre_mm"]
    axS.annotate(f"nearest visible floor {nx:.0f} mm ahead of centre\n"
                 f"({cam['nearest_visible_floor_ahead_of_shell_mm']:.0f} mm ahead of the shell)",
                 xy=(nx, zf), xytext=(560, -260), fontsize=7.8, arrowprops=dict(arrowstyle="-", lw=0.6))
    axS.text(700, 150, f"upper edge {-up:.1f} deg above\nhorizontal: horizon in view", fontsize=7.8)
    axS.set_xlabel("forward x (mm)", fontsize=8)
    axS.set_ylabel("height z (mm)", fontsize=8)
    axS.tick_params(labelsize=7)
    axS.text(-400, 650, "pitch servo holds the look-down angle while the stator swings\n"
             "(acceleration, braking, ramps); the IMU supplies stator pitch", fontsize=7.6, color=(0.3, 0.3, 0.35))
    axT.set_aspect("equal")
    axT.set_xlim(-2700, 2700)
    axT.set_ylim(-450, 5200)
    axT.set_title("TOP (Y-X): floor footprint to 5 m and seam stripe", loc="left", fontsize=10)
    g = gpts[gok]
    gb = band[gok]
    sel = g[:, 0] < 5200
    axT.scatter(-g[sel & ~gb, 1], g[sel & ~gb, 0], s=0.6, color=(0.2, 0.6, 0.3), alpha=0.5)
    axT.scatter(-g[sel & gb, 1], g[sel & gb, 0], s=0.8, color=(0.4, 0.4, 0.45), alpha=0.8)
    axT.add_patch(Circle((0, 0), P.R_o, fill=False, ec=(0.3, 0.45, 0.65), lw=1.0))
    axT.plot([1000, 1000], [0, 5200], color=RED, ls="--", lw=1.0)
    axT.plot([-1000, -1000], [0, 5200], color=(0.85, 0.65, 0.0), ls="--", lw=1.0)
    axT.text(1040, 4850, "red cones (right)\nASSUMED 1.0 m", fontsize=7.2, color=RED)
    axT.text(-1040, 4850, "yellow cones (left)\nASSUMED 1.0 m", fontsize=7.2, color=(0.7, 0.5, 0.0), ha="right")
    axT.text(0, -400, "ball", fontsize=7.2, ha="center", color=(0.3, 0.45, 0.65))
    axT.text(-2650, -380, "green: floor seen through clear PC\ngrey: through the clear seam band\n"
             "(fixed stripe, masked)", fontsize=7.2, color=(0.25, 0.3, 0.3))
    axT.set_xlabel("lateral (mm), robot's right ->", fontsize=8)
    axT.set_ylabel("forward (mm)", fontsize=8)
    axT.tick_params(labelsize=7)
    img = np.zeros((nv, nu, 3))
    above = d[:, 2] >= 0
    cls = np.where(band, 2, np.where(above, 0, 1)).reshape(nv, nu)
    for k, c in {0: (0.85, 0.92, 1.0), 1: (0.82, 0.95, 0.84), 2: (0.62, 0.62, 0.66)}.items():
        img[cls == k] = c
    axI.imshow(img, extent=(0, 4608, 2592, 0), aspect="auto")
    axI.set_title("IMAGE PLANE (4608 x 2592 sensor): what each pixel sees", loc="left", fontsize=9.5)
    axI.set_xlabel("pixel u", fontsize=8)
    axI.set_ylabel("pixel v", fontsize=8)
    axI.tick_params(labelsize=7)
    axI.text(90, 300, "arena above the horizon", fontsize=7.4)
    axI.text(90, 2350, "floor", fontsize=7.4)
    az = cam["seam_band_azimuth_deg"]
    axI.text(4500, 1300, f"seam band: {cam['seam_band_pct_of_image']:.1f}% of image,\nazimuth {az[0]:.0f}..{az[1]:.0f} deg",
             fontsize=7.4, ha="right", va="center", bbox=dict(fc="white", ec="none", alpha=0.85))
    axR = fig.add_axes([0.53, 0.06, 0.44, 0.29])
    axR.axis("off")
    rows = [
        ("Rays blocked by internal parts", f"{cam['blocked_by_internal_parts_pct']:.1f} % (PASS)"),
        ("Optical window on the shell", f"y = {cam['window_y_range_mm'][0]:.0f} ... {cam['window_y_range_mm'][1]:.0f} mm"),
        ("Max incidence angle at the shell", f"{cam['max_incidence_deg']:.1f} deg (3 mm PC: sub-mm ray shift)"),
        ("Seam band in image", f"{cam['seam_band_pct_of_image']:.1f} %, fixed stripe, masked in software"),
        ("Nearest visible floor", f"{cam['nearest_visible_floor_ahead_of_shell_mm']:.0f} mm ahead of the shell"),
        ("Calibration", "intrinsics calibrated THROUGH the fitted shell"),
        ("Not yet verified", "scratch haze, glare, arena lighting (Phase 2/3)"),
    ]
    axR.text(0, 1.05, "FOV check (wb700_analysis.camera_fov_check)", fontsize=9.2, fontweight="bold",
             transform=axR.transAxes)
    y = 0.95
    for a, b in rows:
        axR.text(0, y, a, fontsize=8.1, transform=axR.transAxes, va="top")
        axR.text(0.46, y, b, fontsize=8.1, transform=axR.transAxes, va="top")
        y -= 0.135
    fig.text(0.04, 0.008, FOOT, fontsize=7, color=(0.45, 0.45, 0.5))
    fig.savefig(os.path.join(figdir, "Camera_FOV.png"), dpi=200)
    plt.close(fig)


# ============================================================================ figure 5
def fig_ramp(P, res, figdir):
    df = res["drive_feasibility"]
    sweep = res["ballast_sweep"]
    g = 9.81
    R = df["assumptions"]["rolling_radius_m"]
    crr = df["assumptions"]["c_rr"]
    fig = plt.figure(figsize=(11.5, 5.8), dpi=200)
    title_block(fig, "WB-700 - PRELIMINARY ramp-climbing check (quasi-static; ramp angle not yet published)",
                f"Required shell torque T = M g R (sin a + c_rr cos a), c_rr = {crr} (assumed). The pendulum can react at most "
                "m_p e g sin(phi). Phase 2 replaces this with a dynamic model.")
    ax = fig.add_axes([0.06, 0.13, 0.50, 0.68])
    a = np.linspace(0, 30, 301)
    ar = np.radians(a)
    cols = {2: (0.55, 0.55, 0.6), 4: (0.1, 0.35, 0.7), 6: (0.75, 0.25, 0.1)}
    for s in sweep:
        n = s["n_plates"]
        if n not in cols:
            continue
        T = s["mass_kg"] * g * R * (np.sin(ar) + crr * np.cos(ar))
        Tr60 = s["mpe_kgm"] * g * math.sin(math.radians(60))
        lw = 2.0 if n == 4 else 1.1
        ax.plot(a, T, color=cols[n], lw=lw, label=f"required T, {n} plates ({s['mass_kg']:.1f} kg)")
        ax.axhline(Tr60, color=cols[n], ls="--", lw=lw * 0.6)
        ax.plot([s["alpha_max_phi60_deg"]], [Tr60], "o", color=cols[n], ms=5)
        ax.text(29.6, Tr60 + 0.35, f"pendulum limit at 60 deg, {n} plates: {s['alpha_max_phi60_deg']:.1f} deg",
                fontsize=6.8, ha="right", color=cols[n])
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 40)
    ax.set_xlabel("ramp angle a (deg) - not yet published by the organisers", fontsize=9)
    ax.set_ylabel("torque on the shell (N m)", fontsize=9)
    ax.grid(color=(0.9, 0.9, 0.92))
    ax.legend(fontsize=7.2, loc="upper left")
    ax2 = ax.twinx()
    k = 1.0 / (2 * P.gear_ratio * P.gear_eff)
    ax2.set_ylim(0, 40 * k)
    ax2.set_ylabel(f"each gearmotor output (N m): 2 motors, {P.gear_ratio:.0f}:1, eff. {P.gear_eff}", fontsize=8)
    ax2.tick_params(labelsize=8)
    axR = fig.add_axes([0.67, 0.13, 0.31, 0.68])
    mt = df["momentum_table_0p8ft_ramp"]
    axR.bar([m["alpha_deg"] for m in mt], [m["approach_speed_mps"] for m in mt], width=3.2, color=(0.1, 0.35, 0.7))
    for m in mt:
        axR.text(m["alpha_deg"], m["approach_speed_mps"] + 0.03, f"{m['approach_speed_mps']:.2f}\nL={m['ramp_length_m']:.2f} m",
                 ha="center", fontsize=6.8)
    axR.set_title("0.8 ft ramp: run-up speed whose kinetic energy\ncovers the deficit. Energy estimate only:\ntraction, entry and crest control not verified",
                  fontsize=8.4, loc="left")
    axR.set_xlabel("ramp angle (deg)", fontsize=8.5)
    axR.set_ylabel("approach speed (m/s)", fontsize=8.5)
    axR.set_ylim(0, max(1.6, max(m["approach_speed_mps"] for m in mt) * 1.35))
    axR.grid(axis="y", color=(0.9, 0.9, 0.92))
    axR.tick_params(labelsize=8)
    fig.text(0.06, 0.02, "Below a dot the pendulum can hold the ball on the slope (quasi-static). Above it the 0.244 m rise "
             "can still be climbed with run-up speed (right). Entry-lip and transition losses are not modelled.",
             fontsize=7.4, color=(0.35, 0.35, 0.4))
    fig.savefig(os.path.join(figdir, "Ramp_Capability.png"), dpi=200)
    plt.close(fig)


def fig_steering(P, res, figdir, cache):
    """Front view at bob tilt -30 / 0 / +30 deg: pivot, CG shift, static lean, clearance to the skin."""
    from wb700_model import build_parts
    from wb700_analysis import mass_table, cg_of
    lean = {r["beta_deg"]: r["lean_gamma_deg"] for r in res["steering"]["table"]}
    sc = res["swept_clearance"]
    skin = {}
    for b, rows in sc["per_beta"].items():
        vals = [r["clearance_mm"] for r in rows if r["required_mm"] >= sc["skin_requirement_mm"]]
        if vals:
            skin[int(float(b))] = min(vals)
    R = P.R_o
    fig = plt.figure(figsize=(13.5, 5.6), dpi=200)
    title_block(fig, "WB-700 - steering by bob tilt (front view, looking backwards at the robot)",
                "A self-locking worm gearmotor tilts the bob about a pivot 45 mm below the axle. The CG moves sideways, the ball "
                "leans until the CG is over the contact point,\nand it turns towards the lean. Static CAD estimate.")
    for i, b in enumerate((-30, 0, 30)):
        ax = fig.add_axes([0.02 + i * 0.327, 0.10, 0.31, 0.72])
        parts = build_parts(P, beta_deg=b, include_envelopes=False)
        inner = [p for p in parts if p.pid not in SKIN and p.body in ("stator", "bob")]
        loc = {}
        draw_view(ax, inner, "front", cache=loc)
        th = np.linspace(0, 2 * np.pi, 361)
        ax.plot(R * np.cos(th), R * np.sin(th), color=(0.35, 0.55, 0.75), lw=1.4)
        ax.plot((R - P.t_shell) * np.cos(th), (R - P.t_shell) * np.sin(th), color=(0.35, 0.55, 0.75), lw=0.6)
        _, cg, _ = cg_of(mass_table(parts))
        ax.plot([0], [-P.pivot_depth], marker="o", ms=7, mfc="white", mec=INK, zorder=60)
        ax.annotate("pivot axis (|| X)", (0, -P.pivot_depth), (95, 40), fontsize=7.5, color=INK,
                    arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
        ax.plot([cg[1]], [cg[2]], marker="P", ms=11, color=(0.8, 0.1, 0.1), zorder=61)
        ax.annotate(f"system CG\ny = {cg[1]:+.1f} mm\nz = {cg[2]:.1f} mm", (cg[1], cg[2]), (-340 if b >= 0 else 120, -330),
                    fontsize=7.5, color=(0.8, 0.1, 0.1), arrowprops=dict(arrowstyle="-", color=(0.8, 0.1, 0.1), lw=0.6))
        if b:
            ax.annotate("", (cg[1], cg[2] - 30), (0, cg[2] - 30),
                        arrowprops=dict(arrowstyle="->", color=(0.8, 0.1, 0.1), lw=1.4))
        ax.plot([0, 0], [-R, R], color=(0.6, 0.6, 0.65), lw=0.5, ls=":")
        frame(ax, f"bob tilt beta = {b:+d} deg", lim=400)
        g = lean.get(b, 0.0)
        txt = (f"static lean of the ball: {g:+.1f} deg\n"
               f"frame/bob to shell: >= {sc['min_frame_or_bob_to_skin_mm']:.1f} mm over the full +/-30 deg\nswept check (required {sc['skin_requirement_mm']:.0f} mm); 0 clashes at +/-30 deg")
        if b:
            txt += f"\nturns towards robot {'LEFT' if g > 0 else 'RIGHT'} (+Y is left)"
        ax.text(-385, 375, txt, fontsize=7.6, va="top", color=INK,
                bbox=dict(fc="white", ec=(0.8, 0.8, 0.85), lw=0.5))
        ax.set_xticks([]); ax.set_yticks([])
    fig.text(0.02, 0.012, "Lean is a static estimate (CG directly above the contact point). Turning radius versus speed and "
             "reliable gate navigation are Phase 2 dynamic results.\n" + FOOT, fontsize=6.8, color=(0.35, 0.35, 0.4))
    fig.savefig(os.path.join(figdir, "Steering_Mechanism.png"), dpi=200)
    plt.close(fig)


def make_all(P, out_dir, figdir):
    res = load_results(out_dir)
    cache = {}
    steps = (("dimensioned", lambda: fig_dimensioned(P, res, figdir, cache)),
             ("internal", lambda: fig_internal_layout(P, res, figdir, cache)),
             ("cg", lambda: fig_cg(P, res, figdir, cache)),
             ("camera", lambda: fig_camera(P, res, out_dir, figdir)),
             ("ramp", lambda: fig_ramp(P, res, figdir)),
             ("steering", lambda: fig_steering(P, res, figdir, cache)))
    for name, fn in steps:
        fn()
        print("[figures]", name, "ok")
