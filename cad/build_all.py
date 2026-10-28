"""Rebuild every Phase 1 CAD output from the parameters.

usage (from the cad/ folder, with the project venv):
    ..\\.venv\\Scripts\\python.exe build_all.py            # everything
    ..\\.venv\\Scripts\\python.exe build_all.py checks     # analysis only
    ..\\.venv\\Scripts\\python.exe build_all.py export     # STEP / STL / GLB
    ..\\.venv\\Scripts\\python.exe build_all.py render     # 3D renders
    ..\\.venv\\Scripts\\python.exe build_all.py figures    # 2D drawings and charts
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time

import cadquery as cq

import wb700_analysis as A
from wb700_model import build_parts
from wb700_params import P

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
ROOT = os.path.dirname(HERE)
os.makedirs(OUT, exist_ok=True)
os.chdir(HERE)


def stage_checks():
    t0 = time.time()
    res = {"parameters": P.as_dict()}
    parts = build_parts(P)
    rows = A.mass_table(parts)
    with open(os.path.join(OUT, "mass_table.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    M, cg, mom = A.cg_of(rows)
    by_body = {}
    for b in ("shell", "stator", "bob"):
        m, c, _ = A.cg_of(rows, bodies=(b,))
        by_body[b] = dict(mass_kg=round(m, 3), cg_mm=[round(x, 2) for x in c])
    res["mass"] = dict(total_kg=round(M, 3), cg_mm=[round(x, 2) for x in cg], by_body=by_body,
                       n_parts=len(rows), n_placeholder=sum(1 for r in rows if r["placeholder"]),
                       placeholder_mass_kg=round(sum(r["mass_kg"] for r in rows if r["placeholder"]), 3))
    print(f"[mass] {M:.3f} kg  CG {cg}  ({time.time() - t0:.1f}s)")
    res["dimensions"] = A.dimensional_check(P, parts)
    print("[dims]", json.dumps(res["dimensions"]))
    res["drive_feasibility"] = A.drive_feasibility(P, rows)
    print("[drive] alpha_max", res["drive_feasibility"]["alpha_max_deg"])
    res["steering"] = A.steering_authority(P)
    print("[steer]", res["steering"]["table"])
    res["cg_envelope"] = A.cg_envelope(P)
    res["ballast_sweep"] = A.ballast_sweep(P)
    print("[ballast]", res["ballast_sweep"])
    res["max_radius_moving"] = A.max_radius_moving(P)
    print("[rmax]", res["max_radius_moving"])
    t1 = time.time()
    res["swept_clearance"] = A.swept_clearance(P)
    print("[swept]", json.dumps(res["swept_clearance"]["worst_margin"], default=str),
          "min frame/bob->skin", res["swept_clearance"]["min_frame_or_bob_to_skin_mm"],
          f"({time.time() - t1:.1f}s)")
    t1 = time.time()
    res["camera_fov"] = A.camera_fov_check(P, OUT)
    res["camera_pose_sweep"] = A.camera_pose_sweep(P, OUT)
    print("[camera] pose sweep max blocked %", res["camera_pose_sweep"]["max_blocked_pct"])
    print("[fov]", json.dumps(res["camera_fov"], default=str), f"({time.time() - t1:.1f}s)")
    t1 = time.time()
    res["envelopes"] = A.envelope_check(P)
    print("[env]", json.dumps(res["envelopes"], default=str), f"({time.time() - t1:.1f}s)")
    t1 = time.time()
    res["clash"] = A.clash_check(P)
    print("[clash]", len(res["clash"]["clashes"]), "clashes", json.dumps(res["clash"]["clashes"][:10], default=str),
          f"({time.time() - t1:.1f}s)")
    A.json_dump(res, os.path.join(OUT, "analysis_results.json"))
    print(f"[checks] done in {time.time() - t0:.1f}s")
    return res


def stage_export():
    t0 = time.time()
    parts = build_parts(P, include_envelopes=False)
    assy = cq.Assembly(name="WB700_Phase1")
    for p in parts:
        r, g, b = p.color
        assy.add(p.solid, name=p.pid.replace("-", "_"), color=cq.Color(r, g, b, max(p.opacity, 0.15)))
    step = os.path.join(OUT, "WB700_Phase1_Assembly.step")
    try:
        assy.export(step)
    except AttributeError:
        assy.save(step)
    stl_dir = os.path.join(OUT, "stl")
    os.makedirs(stl_dir, exist_ok=True)
    for p in parts:
        cq.exporters.export(p.solid, os.path.join(stl_dir, f"{p.pid}.stl"), tolerance=0.3, angularTolerance=0.25)
    # coloured GLB for quick viewing in any glTF viewer
    import trimesh
    scene = trimesh.Scene()
    for p in parts:
        m = A.to_mesh(p.solid, tol=0.4)
        rgba = [int(255 * c) for c in p.color] + [int(255 * max(p.opacity, 0.15))]
        m.visual.face_colors = rgba
        scene.add_geometry(m, node_name=p.pid, geom_name=p.pid)
    scene.export(os.path.join(OUT, "WB700_Phase1_Assembly.glb"))
    print(f"[export] STEP + {len(parts)} STL + GLB in {time.time() - t0:.1f}s")


def stage_render():
    import wb700_render
    wb700_render.render_all(P, OUT, os.path.join(ROOT, "figures"))


def stage_figures():
    import wb700_figures
    wb700_figures.make_all(P, OUT, os.path.join(ROOT, "figures"))


if __name__ == "__main__":
    which = sys.argv[1:] or ["checks", "export", "render", "figures"]
    for s in which:
        {"checks": stage_checks, "export": stage_export, "render": stage_render, "figures": stage_figures}[s]()
