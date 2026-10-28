"""WB-700 Phase 1 checks: mass/CG, dimensional compliance, swept clearances, clashes,
camera field of view, envelopes, and preliminary (assumption-labelled) drive numbers.

Run through build_all.py.  Results -> cad/out/analysis_results.json (+ CSV tables).
"""
from __future__ import annotations

import itertools
import json
import math

import numpy as np
import shapely
import trimesh
from shapely.geometry import box as sbox

from wb700_model import Part, build_parts
from wb700_params import Params

G = 9.81

# tag used to recognise designed contacts (Part.interface_with lists tags of partners)
TAGS = [
    ("SH-01", "shell"), ("SH-02", "shell"), ("SH-03", "band"), ("SH-04", "tape"),
    ("SH-1", "flange"), ("SH-2", "gear"), ("SH-3", "bearing"),
    ("ST-01", "axle"), ("ST-02", "hub"), ("ST-03", "hub"), ("ST-04", "bolt"),
    ("ST-1", "plate"), ("ST-14", "clamp"), ("ST-15", "clamp"), ("ST-20", "fastener"),
    ("PW-04", "device"), ("PW-05", "device"), ("SA-03", "device"),
    ("DR-01", "motor"), ("DR-02", "motor"), ("DR-03", "pinion"), ("DR-04", "pinion"),
    ("DR-05", "arm"), ("DR-06", "arm"),
    ("SG-01", "pivotshaft"), ("SG-02", "pivotbrg"), ("SG-03", "pivotbrg"), ("SG-04", "steermotor"),
    ("SG-1", "bumper"), ("SE-01", "camera"), ("SE-02", "servo"), ("SE-03", "imu"),
    ("SE-04", "sensor"), ("SE-05", "sensor"), ("CP", "device"), ("DV", "device"),
    ("PW-01", "device"), ("PW-02", "device"), ("PW-03", "device"), ("SA-01", "device"),
    ("SA-02", "device"), ("SA-04", "device"), ("HR", "harness"),
    ("BB-01", "hanger"), ("BB-02", "hanger"), ("BB-03", "tray"), ("BB-04", "tiebracket"), ("BB-05", "tiebracket"),
    ("PW-10", "battery"), ("BL", "ballast"), ("EV", "envelope"),
]


def tag_of(pid: str) -> str:
    best = ""
    tag = "?"
    for pre, t in TAGS:
        if pid.startswith(pre) and len(pre) > len(best):
            best, tag = pre, t
    return tag


def designed_contact(a: Part, b: Part) -> bool:
    return tag_of(a.pid) in b.interface_with or tag_of(b.pid) in a.interface_with


# ----------------------------------------------------------------------------- meshes
def to_mesh(solid, tol=0.4, ang=0.25) -> trimesh.Trimesh:
    v, f = solid.tessellate(tol, ang)
    v = np.array([[p.x, p.y, p.z] for p in v], dtype=float)
    f = np.array(f, dtype=np.int64)
    m = trimesh.Trimesh(v, f, process=True)
    return m


def dense_points(mesh: trimesh.Trimesh, max_edge=3.0) -> np.ndarray:
    v, f = trimesh.remesh.subdivide_to_size(mesh.vertices, mesh.faces, max_edge=max_edge, max_iter=12)
    return np.unique(np.round(v, 2), axis=0)


# ----------------------------------------------------------------------------- mass & CG
def mass_table(parts: list[Part]) -> list[dict]:
    rows = []
    for p in parts:
        if p.body == "envelope":
            continue
        c = p.solid.Center()
        rows.append(dict(pid=p.pid, name=p.name, group=p.group, body=p.body, material=p.material,
                         mass_kg=round(p.kg, 4), basis=p.basis, placeholder=p.placeholder,
                         x_mm=round(c.x, 1), y_mm=round(c.y, 1), z_mm=round(c.z, 1),
                         volume_cm3=round(p.solid.Volume() / 1000.0, 2), note=p.note))
    return rows


def cg_of(rows, bodies=None):
    sel = [r for r in rows if bodies is None or r["body"] in bodies]
    m = sum(r["mass_kg"] for r in sel)
    if m == 0:
        return 0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    mx = sum(r["mass_kg"] * r["x_mm"] for r in sel)
    my = sum(r["mass_kg"] * r["y_mm"] for r in sel)
    mz = sum(r["mass_kg"] * r["z_mm"] for r in sel)
    return m, (mx / m, my / m, mz / m), (mx, my, mz)


# ----------------------------------------------------------------------------- checks
def dimensional_check(P: Params, parts: list[Part]) -> dict:
    ext_ids = [p for p in parts if p.body != "envelope"]
    pts = []
    max_r_by_part = {}
    for p in ext_ids:
        m = to_mesh(p.solid, tol=0.2)
        r = np.linalg.norm(m.vertices, axis=1)
        max_r_by_part[p.pid] = float(r.max())
        if r.max() > P.R_o - 40:          # only near-surface geometry matters for calipers
            pts.append(m.vertices[r > P.R_o - 40])
    pts = np.vstack(pts)
    dirs = trimesh.creation.icosphere(subdivisions=4).vertices  # 2562 directions
    proj = pts @ dirs.T
    calipers = proj.max(axis=0) - proj.min(axis=0)
    skin = {"SH-01", "SH-02", "SH-03", "SH-04"}
    non_skin = {k: v - P.R_o for k, v in max_r_by_part.items() if k not in skin}
    worst_pid = max(non_skin, key=non_skin.get)
    d_max, d_min = float(calipers.max()), float(calipers.min())
    res = dict(
        rule_d_min_mm=P.d_min_rule, rule_d_max_mm=P.d_max_rule, rule_protrusion_max_mm=P.protrusion_max_rule,
        nominal_shell_od_mm=P.D_shell,
        caliper_max_mm=round(d_max, 2), caliper_min_mm=round(d_min, 2),
        caliper_max_ft=round(d_max / 304.8, 4), caliper_min_ft=round(d_min / 304.8, 4),
        caliper_x_mm=round(float(np.ptp(pts[:, 0])), 2), caliper_y_mm=round(float(np.ptp(pts[:, 1])), 2),
        caliper_z_mm=round(float(np.ptp(pts[:, 2])), 2),
        margin_to_upper_mm=round(P.d_max_rule - d_max, 2), margin_to_lower_mm=round(d_min - P.d_min_rule, 2),
        tolerance_case_max_mm=round(d_max + P.shell_tol, 2), tolerance_case_min_mm=round(d_min - P.shell_tol, 2),
        tape_protrusion_mm=round(max_r_by_part.get("SH-04", P.R_o) - P.R_o, 3),
        max_non_skin_protrusion_mm=round(non_skin[worst_pid], 3), max_non_skin_protrusion_part=worst_pid,
        external_sensors_or_mounts=0,
    )
    res["strictly_within_rule"] = bool(P.d_min_rule < d_min and d_max < P.d_max_rule)
    res["strictly_within_rule_with_tolerance"] = bool(
        P.d_min_rule < d_min - P.shell_tol and d_max + P.shell_tol < P.d_max_rule)
    res["protrusion_rule_ok"] = bool(non_skin[worst_pid] <= P.protrusion_max_rule)
    return res


def meridional_regions(shell_parts: list[Part]):
    """Axisymmetric shell-side parts -> region in the (r, y) half plane (section z=0, x>=0)."""
    regions = {}
    for p in shell_parts:
        m = to_mesh(p.solid, tol=0.05, ang=0.05)
        sec = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        planar, _ = sec.to_planar(to_2D=np.eye(4), check=False)
        polys = [shapely.make_valid(pg) for pg in planar.polygons_full]
        # chords of the tessellated inner surfaces lie inboard of the true surface -> conservative
        reg = shapely.unary_union(polys).intersection(sbox(0, -2000, 2000, 2000))
        regions[p.pid] = reg
    return regions


def swept_clearance(P: Params, betas=(-30, -15, 0, 15, 30)) -> dict:
    """Min clearance of every stator/bob part to every shell-side part, valid for ALL stator
    pitch angles (shell-side internals are bodies of revolution about the axle)."""
    base = build_parts(P, include_envelopes=False)
    shell_parts = [p for p in base if p.body == "shell" and p.pid not in ("SH-04",)]
    regions = meridional_regions(shell_parts)
    polar_movers = {"ST-02", "ST-03", "ST-04", "PW-04", "PW-05", "SA-03"}

    def requirement(mv, sp):
        # parts located by the polar bearings run on precision gaps; frame/bob vs skin needs margin
        if mv.pid in polar_movers or sp.group in ("POLAR", "DRIVE"):
            return 1.0
        return P.min_moving_clearance

    out = {"per_beta": {}, "worst_margin": None, "skin_requirement_mm": P.min_moving_clearance,
           "polar_requirement_mm": 1.0}
    worst = (1e9, None)
    skin_min = (1e9, "")
    for b in betas:
        parts = build_parts(P, beta_deg=b, include_envelopes=False)
        movers = [p for p in parts if p.body in ("stator", "bob")]
        res_b = []
        for mv in movers:
            pts = dense_points(to_mesh(mv.solid, tol=0.3), max_edge=3.0)
            ry = np.column_stack([np.hypot(pts[:, 0], pts[:, 2]), pts[:, 1]])
            ry = np.unique(np.round(ry, 1), axis=0)
            mp = shapely.points(ry)
            for sp in shell_parts:
                if designed_contact(mv, sp):
                    continue
                reg = regions.get(sp.pid)
                if reg is None or reg.is_empty:
                    continue
                d = shapely.distance(mp, reg)
                dmin = -1.0 if shapely.contains(reg, mp).any() else float(d.min())
                req = requirement(mv, sp)
                res_b.append((dmin - req, dmin, req, mv.pid, sp.pid))
                if req == P.min_moving_clearance and dmin < skin_min[0]:
                    skin_min = (dmin, f"{mv.pid} vs {sp.pid} at beta {b}")
                if dmin - req < worst[0]:
                    worst = (dmin - req, (b, mv.pid, mv.name, sp.pid, sp.name, dmin, req))
        res_b.sort()
        out["per_beta"][str(b)] = [dict(clearance_mm=round(c, 2), required_mm=r, moving=m_, shell_part=s_)
                                   for _, c, r, m_, s_ in res_b[:8]]
    b, mpid, mname, spid, sname, dmin, req = worst[1]
    out["worst_margin"] = dict(margin_mm=round(worst[0], 2), clearance_mm=round(dmin, 2), required_mm=req,
                               beta_deg=b, moving=mpid, moving_name=mname, shell_part=spid, shell_name=sname)
    out["min_frame_or_bob_to_skin_mm"] = round(skin_min[0], 2)
    out["min_frame_or_bob_to_skin_pair"] = skin_min[1]
    out["pass"] = bool(worst[0] >= 0)
    return out


def max_radius_moving(P: Params, betas=(-30, 0, 30)) -> dict:
    """Largest distance from the shell centre reached by the pendulum frame and bob
    (axle, polar hardware and drive modules near the poles are reported by swept_clearance)."""
    out = {}
    for b in betas:
        parts = build_parts(P, beta_deg=b, include_envelopes=False)
        rmax, who = 0.0, ""
        for p in parts:
            if p.body not in ("stator", "bob") or p.group in ("POLAR", "DRIVE") or p.pid in (
                    "ST-01", "PW-04", "PW-05", "SA-03", "SE-05"):
                continue
            r = float(np.linalg.norm(to_mesh(p.solid, 0.3).vertices, axis=1).max())
            if r > rmax:
                rmax, who = r, p.pid
        out[str(b)] = dict(max_radius_mm=round(rmax, 1), part=who)
    return out


def clash_check(P: Params, states=((0, 0), (0, 30), (0, -30), (60, 0), (-60, 0), (35, 30))) -> dict:
    """Exact B-rep intersections between every pair of physical parts (designed contacts excluded)."""
    out = {"states": [], "clashes": []}
    for phi, beta in states:
        parts = [p for p in build_parts(P, phi_deg=phi, beta_deg=beta, include_envelopes=False)]
        bbs = {p.pid: p.solid.BoundingBox() for p in parts}
        n_pairs = n_tested = 0
        for a, b in itertools.combinations(parts, 2):
            n_pairs += 1
            if a.body == b.body == "shell":
                continue  # shell-side parts are bonded/bolted together by design
            if designed_contact(a, b):
                continue
            A, B = bbs[a.pid], bbs[b.pid]
            if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or \
               A.zmax < B.zmin or B.zmax < A.zmin:
                continue
            n_tested += 1
            try:
                vol = a.solid.intersect(b.solid).Volume()
            except Exception:  # noqa: BLE001
                vol = float("nan")
            if not (vol < 0.5):
                out["clashes"].append(dict(phi=phi, beta=beta, a=a.pid, b=b.pid, a_name=a.name,
                                           b_name=b.name, volume_mm3=round(vol, 2)))
        out["states"].append(dict(phi_deg=phi, beta_deg=beta, pairs=n_pairs, bbox_overlaps_tested=n_tested))
    out["pass"] = len(out["clashes"]) == 0
    return out


def envelope_check(P: Params) -> dict:
    parts = build_parts(P)
    env = {p.pid: p for p in parts if p.body == "envelope"}
    res = {}
    allowed = {"EV-01": {"PW-10", "BB-03"}, "EV-02": {"ST-03", "ST-04"}}
    for eid, e in env.items():
        hits = []
        for p in parts:
            if p.body == "envelope" or p.pid in allowed[eid]:
                continue
            if eid == "EV-01" and p.body == "shell" and p.pid in ("SH-02", "SH-11", "SH-21", "SH-31", "SH-03", "SH-04"):
                continue  # these leave with the right hemisphere / are outside the path
            vol = e.solid.intersect(p.solid).Volume()
            if vol > 0.5:
                hits.append(dict(pid=p.pid, name=p.name, volume_mm3=round(vol, 1)))
        res[eid] = dict(name=e.name, obstructions=hits, clear=len(hits) == 0)
    return res


# ----------------------------------------------------------------------------- camera FOV
def camera_rays(P: Params, nu=128, nv=72):
    f = 2.75
    sw, sh = 4608 * 1.4e-3, 2592 * 1.4e-3
    us = (np.arange(nu) + 0.5) / nu * sw - sw / 2
    vs = (np.arange(nv) + 0.5) / nv * sh - sh / 2
    U, Vv = np.meshgrid(us, vs)
    d_cam = np.stack([np.full_like(U, f), -U, -Vv], axis=-1).reshape(-1, 3)  # x fwd, y left(=-u), z up(=-v)
    d_cam /= np.linalg.norm(d_cam, axis=1, keepdims=True)
    a = math.radians(P.cam_down_deg)   # rotation about +Y by +a maps +X to (cos a, 0, -sin a): looks down
    ca, sa = math.cos(a), math.sin(a)
    Ry = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
    d = d_cam @ Ry.T
    return d, (U.reshape(-1), Vv.reshape(-1)), (nu, nv)


def camera_fov_check(P: Params, out_dir: str = "out", beta_deg: float = 0.0, save: bool = True) -> dict:
    parts = build_parts(P, beta_deg=beta_deg, include_envelopes=False)
    o = np.array(P.cam_pos, dtype=float) + np.array([0.5, 0, 0])
    d, (U, Vv), (nu, nv) = camera_rays(P)
    # distance to inner shell surface
    b = d @ o
    c = o @ o - P.R_i ** 2
    s_shell = -b + np.sqrt(b * b - c)
    hitpts = o + d * s_shell[:, None]
    meshes, owners = [], []
    for p in parts:
        if p.body in ("stator", "bob") and p.pid not in ("SE-01", "SE-02"):
            m = to_mesh(p.solid, tol=0.5)
            meshes.append(m)
            owners += [p.pid] * len(m.faces)
    scene = trimesh.util.concatenate(meshes)
    owners = np.array(owners)
    loc, iray, itri = scene.ray.intersects_location(np.repeat(o[None], len(d), 0), d, multiple_hits=False)
    blocked = np.zeros(len(d), bool)
    blockers = {}
    for L, r, t in zip(loc, iray, itri):
        if np.linalg.norm(L - o) < s_shell[r] - 0.5:
            blocked[r] = True
            blockers[owners[t]] = blockers.get(owners[t], 0) + 1
    band = np.abs(hitpts[:, 1]) <= P.band_w / 2
    # ground footprint (flat floor tangent to the ball)
    zf = -(P.R_o + P.tape_t)
    t_g = (zf - o[2]) / np.where(d[:, 2] < -1e-6, d[:, 2], np.nan)
    gpts = o + d * t_g[:, None]
    ok = np.isfinite(t_g) & (t_g > 0)
    near_ground_x = float(np.nanmin(gpts[ok, 0])) if ok.any() else float("nan")
    az = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    res = dict(
        camera_pos_mm=list(map(float, o)), look_down_deg=P.cam_down_deg, hfov_deg=P.cam_hfov, vfov_deg=P.cam_vfov,
        rays=int(len(d)), blocked_by_internal_parts_pct=round(float(100 * blocked.mean()), 3),
        blockers={str(k): int(v) for k, v in blockers.items()},
        seam_band_pct_of_image=round(float(100 * band.mean()), 2),
        seam_band_azimuth_deg=[round(float(az[band].min()), 1), round(float(az[band].max()), 1)] if band.any() else None,
        window_y_range_mm=[round(float(hitpts[:, 1].min()), 1), round(float(hitpts[:, 1].max()), 1)],
        window_z_range_mm=[round(float(hitpts[:, 2].min()), 1), round(float(hitpts[:, 2].max()), 1)],
        max_incidence_deg=round(float(np.degrees(np.arccos(np.clip(np.abs(np.sum(d * hitpts, 1)) /
                                                                    np.linalg.norm(hitpts, axis=1), 0, 1))).max()), 1),
        nearest_visible_floor_ahead_of_centre_mm=round(near_ground_x, 1),
        nearest_visible_floor_ahead_of_shell_mm=round(near_ground_x - P.R_o, 1),
        horizon_in_view=bool((d[:, 2] > 0).any()),
    )
    res["pass"] = bool(res["blocked_by_internal_parts_pct"] < 0.5)
    if not save:
        return res
    np.savez_compressed(f"{out_dir}/camera_rays.npz", d=d, U=U, V=Vv, nu=nu, nv=nv, band=band, blocked=blocked,
                        hit=hitpts, origin=o, ground=gpts, ground_ok=ok)
    return res


def camera_pose_sweep(P: Params, out_dir: str = "out") -> dict:
    """Obstruction and seam stripe for bob tilt -30/0/+30 deg and camera-servo pitch 0/12/24 deg down."""
    rows = []
    for b in (-30, 0, 30):
        for down in (0, 12, 24):
            Q = Params(**{**P.__dict__, "cam_down_deg": down})
            r = camera_fov_check(Q, out_dir, beta_deg=b, save=False)
            rows.append(dict(beta_deg=b, cam_down_deg=down, blocked_pct=r["blocked_by_internal_parts_pct"],
                             seam_pct=r["seam_band_pct_of_image"]))
    return dict(states=rows, max_blocked_pct=max(r["blocked_pct"] for r in rows),
                note="the stator only pitches about the axle (Y), the same axis the shell turns about, so the "
                     "equatorial seam band (plane y=0) projects to a fixed image region for any shell rotation")


# ----------------------------------------------------------------------------- drive numbers
def alpha_limit_deg(k: float, phi_deg: float, c_rr: float) -> float:
    """Steepest steady climb: m_p e g sin(phi) = M g R (sin a + c_rr cos a), with k = m_p e / (M R)."""
    rhs = k * math.sin(math.radians(phi_deg)) / math.sqrt(1 + c_rr ** 2)
    return math.degrees(math.asin(min(1.0, rhs)) - math.atan(c_rr))


def drive_feasibility(P: Params, rows) -> dict:
    """Preliminary, quasi-static, assumption-labelled.  NOT the Phase 2 sizing report."""
    M, cg, mom = cg_of(rows)
    m_p, cg_p, mom_p = cg_of(rows, bodies=("stator", "bob"))
    mpe = math.hypot(mom_p[0], mom_p[2]) / 1000.0           # kg*m
    R = (P.R_o + P.tape_t) / 1000.0
    k = mpe / (M * R)
    alpha_max = {f"phi_{p}": round(alpha_limit_deg(k, p, P.c_rr), 2) for p in (45, 60, 75, 90)}
    alpha_max_no_rr = {f"phi_{p}": round(math.degrees(math.asin(min(1.0, k * math.sin(math.radians(p))))), 2)
                       for p in (45, 60, 75, 90)}
    tbl = []
    for a in (5, 8, 10, 12, 14, 16, 18, 20, 25, 30):
        ar = math.radians(a)
        T = M * G * R * (math.sin(ar) + P.c_rr * math.cos(ar))
        need = T / (mpe * G)
        phi = math.degrees(math.asin(need)) if need <= 1 else None
        tbl.append(dict(alpha_deg=a, shell_torque_Nm=round(T, 2),
                        torque_per_motor_Nm=round(T / (2 * P.gear_ratio * P.gear_eff), 2),
                        pendulum_angle_deg=None if phi is None else round(phi, 1),
                        quasi_static_ok_phi_le_60=bool(phi is not None and phi <= 60)))
    T_react_max = mpe * G                                    # pendulum horizontal
    rpm_shell = P.v_max_target / R * 60 / (2 * math.pi)
    # momentum-assisted: kinetic energy needed to cover the gravity deficit on the 0.8 ft ramp
    m_shell = sum(r_["mass_kg"] for r_ in rows if r_["body"] == "shell")
    I_shell_thin = (2.0 / 3.0) * m_shell * R ** 2            # thin-shell approximation (conservative)
    M_eff = M + I_shell_thin / R ** 2
    h = 0.8 * 0.3048
    avail = k * math.sin(math.radians(60))                  # available force / (M g) at phi = 60 deg
    mom_tbl = []
    for a in (15, 20, 25, 30, 35):
        ar = math.radians(a)
        need = math.sin(ar) + P.c_rr * math.cos(ar)
        L = h / math.sin(ar)
        v0 = 0.0 if need <= avail else math.sqrt(2 * M * G * (need - avail) * L / M_eff)
        mom_tbl.append(dict(alpha_deg=a, ramp_length_m=round(h / math.sin(ar), 3), approach_speed_mps=round(v0, 2)))
    # motor operating points (per motor, at the gearmotor output shaft, spur losses included)
    per = 1.0 / (2 * P.gear_ratio * P.gear_eff)
    to_rpm = lambda v: v / R * 60 / (2 * math.pi) * P.gear_ratio
    a_lim = math.radians(alpha_max["phi_60"])
    T_cruise = M * G * R * P.c_rr * per
    T_climb = M * G * R * (math.sin(a_lim) + P.c_rr * math.cos(a_lim)) * per
    T_peak = mpe * G * per
    v_climb = 0.5
    V_min, V_rated = 18.0, 24.0
    stall_rated = 4.0
    # linear DC-motor model, speed and stall torque both scale with voltage
    n0_needed_at_vmin = to_rpm(P.v_max_target) / (1 - T_cruise / (stall_rated * V_min / V_rated))
    n0_spec_rated = math.ceil(n0_needed_at_vmin * V_rated / V_min / 10) * 10
    ops = dict(
        cruise=dict(torque_Nm=round(T_cruise, 2), rpm=round(to_rpm(P.v_max_target), 0), note="flat, v_target"),
        climb=dict(torque_Nm=round(T_climb, 2), rpm=round(to_rpm(v_climb), 0),
                   note=f"steady climb at the 60 deg limit ({alpha_max['phi_60']} deg) at {v_climb} m/s (assumed)"),
        peak=dict(torque_Nm=round(T_peak, 2), note="pendulum horizontal; short-term only"),
        V_min=V_min, V_rated=V_rated, stall_rated_Nm=stall_rated,
        no_load_rpm_needed_at_Vmin=round(n0_needed_at_vmin, 0), no_load_rpm_spec_at_rated=n0_spec_rated,
        stall_at_Vmin_Nm=round(stall_rated * V_min / V_rated, 2),
        climb_speed_at_Vmin_rpm=round(n0_spec_rated * V_min / V_rated * (1 - T_climb / (stall_rated * V_min / V_rated)), 0),
    )
    F_launch = mpe * G * math.sin(math.radians(60)) / R - M * G * P.c_rr
    a_launch = F_launch / M_eff
    # lip / step (quasi-static)
    x_avail = mpe / M                                        # m, at phi = 90 deg
    h_lip = R - math.sqrt(max(R ** 2 - x_avail ** 2, 0))
    return dict(
        assumptions=dict(c_rr=P.c_rr, gear_ratio=P.gear_ratio, gear_eff=P.gear_eff, rolling_radius_m=R,
                         g=G, v_target_mps=P.v_max_target,
                         note="quasi-static; ignores pendulum dynamics, slip, ramp-entry transition and "
                              "shell deformation. Phase 2 replaces these with a dynamic model."),
        total_mass_kg=round(M, 3), pendulum_first_moment_kgm=round(mpe, 4), M_times_R_kgm=round(M * R, 4),
        climb_index_mpe_over_MR=round(k, 4), alpha_max_deg=alpha_max, alpha_max_no_rr_deg=alpha_max_no_rr,
        motor_operating_points=ops, launch_accel_mps2=round(a_launch, 2),
        max_reaction_torque_shell_Nm=round(T_react_max, 2),
        torque_table=tbl, shell_rpm_at_v_target=round(rpm_shell, 1),
        motor_output_rpm_at_v_target=round(rpm_shell * P.gear_ratio, 1),
        M_eff_kg=round(M_eff, 2), momentum_table_0p8ft_ramp=mom_tbl,
        quasi_static_lip_height_mm=round(h_lip * 1000, 1),
        stator_rest_pitch_deg=round(math.degrees(math.atan2(mom_p[0], -mom_p[2])), 2),
    )


def steering_authority(P: Params, betas=(-30, -20, -10, 0, 10, 20, 30)) -> dict:
    out = []
    for b in betas:
        parts = build_parts(P, beta_deg=b, include_envelopes=False)
        rows = mass_table(parts)
        _, _, mom = cg_of(rows)              # shell parts sit on the axle line -> no moment
        gamma = math.degrees(math.atan2(mom[1], -mom[2]))
        out.append(dict(beta_deg=b, lean_gamma_deg=round(gamma, 2)))
    return dict(table=out, note="static lean of axle/shell with the CG directly below the centre; "
                                "turning radius vs speed is a Phase 2 dynamic result")


def cg_envelope(P: Params) -> dict:
    pts = []
    for phi in (-30, 0, 30):
        for b in (-30, 0, 30):
            rows = mass_table(build_parts(P, phi_deg=phi, beta_deg=b, include_envelopes=False))
            _, cg, _ = cg_of(rows)
            pts.append(dict(phi_deg=phi, beta_deg=b, cg_mm=[round(c, 2) for c in cg]))
    return dict(points=pts)


def ballast_sweep(P: Params) -> list[dict]:
    out = []
    for n in (2, 3, 4, 5, 6):
        Q = Params(**{**P.__dict__, "n_ballast": n})
        rows = mass_table(build_parts(Q, include_envelopes=False))
        M, cg, mom = cg_of(rows)
        mpe = math.hypot(mom[0], mom[2]) / 1000
        R = (Q.R_o + Q.tape_t) / 1000
        k = mpe / (M * R)
        out.append(dict(n_plates=n, mass_kg=round(M, 2), cg_z_mm=round(cg[2], 1), mpe_kgm=round(mpe, 3),
                        alpha_max_phi60_deg=round(alpha_limit_deg(k, 60, Q.c_rr), 2),
                        alpha_max_phi90_deg=round(alpha_limit_deg(k, 90, Q.c_rr), 2)))
    return out


def json_dump(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=lambda o: o if not isinstance(o, np.generic) else o.item())
