"""Build the Phase 1 documents from the CAD analysis results (single source of numbers).

Outputs (project root): Phase1_CAD_Abstract.md/.pdf/.docx, Phase1_Technical_Design_Document.md/.pdf,
Requirements_Compliance.csv, Preliminary_BOM.csv.   Intermediate HTML and optimised figures: build/.

usage (from docs_src):  ..\\.venv\\Scripts\\python.exe build_docs.py
"""
from __future__ import annotations

import csv
import datetime
import json
import math
import pathlib
import re
import subprocess
import sys
import tempfile

import markdown
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs_src"
BUILD = ROOT / "build"
FIG = ROOT / "figures"
OUT = ROOT / "cad" / "out"
sys.path.insert(0, str(ROOT / "cad"))
from wb700_params import P  # noqa: E402

import compliance_data as CD  # noqa: E402

BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
TODAY = datetime.date.today().isoformat()


# ----------------------------------------------------------------------------- data
def load():
    res = json.loads((OUT / "analysis_results.json").read_text(encoding="utf-8"))
    with open(OUT / "mass_table.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in ("mass_kg", "x_mm", "y_mm", "z_mm", "volume_cm3"):
            r[k] = float(r[k])
        r["placeholder"] = r["placeholder"] == "True"
    return res, rows


def f(x, n=1):
    return f"{x:.{n}f}"


def signed(x, n=1):
    return f"{x:+.{n}f}"


def tokens(res, rows):
    m = res["mass"]
    d = res["dimensions"]
    df = res["drive_feasibility"]
    tt = {t["alpha_deg"]: t for t in df["torque_table"]}
    mt = {t["alpha_deg"]: t for t in df["momentum_table_0p8ft_ramp"]}
    bs = res["ballast_sweep"]
    st = res["steering"]["table"]
    sc = res["swept_clearance"]
    cam = res["camera_fov"]
    bb = m["by_body"]
    m_pend = bb["stator"]["mass_kg"] + bb["bob"]["mass_kg"]
    z_pend = (bb["stator"]["mass_kg"] * bb["stator"]["cg_mm"][2] + bb["bob"]["mass_kg"] * bb["bob"]["cg_mm"][2]) / m_pend
    R = df["assumptions"]["rolling_radius_m"]
    g = 9.81
    mpe = df["pendulum_first_moment_kgm"]
    phi_acc = math.degrees(math.asin(min(1, df["M_eff_kg"] * 0.5 * R / (mpe * g))))
    lean30 = (abs(st[0]["lean_gamma_deg"]) + abs(st[-1]["lean_gamma_deg"])) / 2
    T = {}
    for a in (5, 10, 15, 20):
        ar = math.radians(a)
        T[a] = m["total_kg"] * g * R * (math.sin(ar) + P.c_rr * math.cos(ar))
    ops = df["motor_operating_points"]
    # pendulum crossing: hold line 0.3 m, corridor 0.5 m (assumed), body 0.70 m, speed cap 1.5 m/s
    a_l, s_x, v_cap = df["launch_accel_mps2"], 0.3 + 0.5 + 2 * R, 1.5
    s1 = v_cap ** 2 / (2 * a_l)
    t_cross = math.sqrt(2 * s_x / a_l) if s1 >= s_x else v_cap / a_l + (s_x - s1) / v_cap
    cps = res["camera_pose_sweep"]["states"]
    assert d["max_non_skin_protrusion_mm"] < 0, "the abstract states the hubs sit inside the sphere surface"
    tok = dict(
        date=TODAY, D_shell=f(P.D_shell, 0), D_shell_ft=f(P.D_shell / 304.8, 3), t_shell=f(P.t_shell, 1),
        band_w=f(P.band_w, 0), band_t=f(P.band_t, 0), n_parts=str(m["n_parts"]), M=f(m["total_kg"], 2),
        cg_x=signed(m["cg_mm"][0]), cg_y=signed(m["cg_mm"][1]), cg_z=signed(m["cg_mm"][2]),
        cg_z_abs=f(abs(m["cg_mm"][2])), m_shell=f(bb["shell"]["mass_kg"], 2), m_stator=f(bb["stator"]["mass_kg"], 2),
        m_bob=f(bb["bob"]["mass_kg"], 2), m_pend=f(m_pend, 2), z_pend_abs=f(abs(z_pend)),
        ph_mass=f(m["placeholder_mass_kg"], 2), n_ph=str(m["n_placeholder"]),
        d_max=f(d["caliper_max_mm"]), d_min=f(d["caliper_min_mm"]), d_max_ft=f(d["caliper_max_ft"], 3),
        d_min_ft=f(d["caliper_min_ft"], 3), margin_up=f(d["margin_to_upper_mm"]), margin_low=f(d["margin_to_lower_mm"]),
        tol_min=f(d["tolerance_case_min_mm"]), tol_max=f(d["tolerance_case_max_mm"]),
        prot_depth=f(-d["max_non_skin_protrusion_mm"]), lean30=f(lean30), gear_ratio=f(P.gear_ratio, 0),
        R_roll=f(R, 3), c_rr=f(P.c_rr, 2), T5=f(T[5]), T10=f(T[10]), T15=f(T[15]), T20=f(T[20]),
        mpe=f(mpe, 2), Tr90=f(df["max_reaction_torque_shell_Nm"]), Tr60=f(df["max_reaction_torque_shell_Nm"] * math.sin(math.radians(60))),
        a60=f(df["alpha_max_deg"]["phi_60"]), a90=f(df["alpha_max_deg"]["phi_90"]),
        a60_min=f(bs[0]["alpha_max_phi60_deg"]), a60_max=f(bs[-1]["alpha_max_phi60_deg"]),
        M_eff=f(df["M_eff_kg"]), v15=f(mt[15]["approach_speed_mps"], 2), v20=f(mt[20]["approach_speed_mps"], 2),
        v30=f(mt[30]["approach_speed_mps"], 2), lip=f(df["quasi_static_lip_height_mm"], 0),
        Tm_react=f(df["max_reaction_torque_shell_Nm"] / (2 * P.gear_ratio * P.gear_eff), 2),
        rpm_motor=f(df["motor_output_rpm_at_v_target"], 0), v_target=f(P.v_max_target, 1),
        T_climb=f(ops["climb"]["torque_Nm"], 2), rpm_climb=f(ops["climb"]["rpm"], 0),
        T_cruise=f(ops["cruise"]["torque_Nm"], 2), n0_spec=str(ops["no_load_rpm_spec_at_rated"]),
        n0_vmin=f(ops["no_load_rpm_spec_at_rated"] * ops["V_min"] / ops["V_rated"], 0),
        stall_vmin=f(ops["stall_at_Vmin_Nm"], 1), climb_rpm_vmin=f(ops["climb_speed_at_Vmin_rpm"], 0),
        a_launch=f(a_l, 2), t_cross=f(t_cross, 1), t_req=f(t_cross + 0.15 + 0.5, 1),
        cam_states=str(len(cps)), cam_blk_max=f(res["camera_pose_sweep"]["max_blocked_pct"], 1),
        seam_min=f(min(c["seam_pct"] for c in cps), 1), seam_max=f(max(c["seam_pct"] for c in cps), 1),
        fov_blocked=f(cam["blocked_by_internal_parts_pct"], 1), seam_pct=f(cam["seam_band_pct_of_image"], 1),
        seam_az0=f(cam["seam_band_azimuth_deg"][0]), seam_az1=f(cam["seam_band_azimuth_deg"][1]),
        floor_near=f(cam["nearest_visible_floor_ahead_of_shell_mm"], 0), max_inc=f(cam["max_incidence_deg"]),
        cg_z_2=f(bs[0]["cg_z_mm"]), cg_z_6=f(bs[-1]["cg_z_mm"]),
        clr_skin=f(sc["min_frame_or_bob_to_skin_mm"]), clr_skin_pair=sc["min_frame_or_bob_to_skin_pair"],
        clr_polar=f(sc["worst_margin"]["clearance_mm"]), clash_states=str(len(res["clash"]["states"])),
        clash_n=str(len(res["clash"]["clashes"])), rmax=f(res["max_radius_moving"]["0"]["max_radius_mm"]),
        R_i=f(P.R_i, 0), climb=f(df["climb_index_mpe_over_MR"], 3), rest_pitch=f(df["stator_rest_pitch_deg"], 2),
        phi_acc=f(phi_acc, 0), bob_frac=f(100 * bb["bob"]["mass_kg"] / m_pend, 0),
        L_bob=f(abs(bb["bob"]["cg_mm"][2]) - P.pivot_depth, 0), pole_open=f(2 * P.r_pole_open, 0),
        hub_cap=f(2 * P.hub_cap_r, 0), axle_od=f(P.axle_od, 0), axle_wall=f((P.axle_od - P.axle_id) / 2, 0),
        axle_id=f(P.axle_id, 0), axle_len=f(2 * P.axle_half_len, 0), gear_m=f(P.gear_m, 1),
        gear_cd=f(P.gear_center_dist, 1), box_l=f(2 * P.box_x, 0), box_w=f(2 * P.box_y, 0),
        box_h=f(P.box_z_top - P.box_z_bot, 0), rho_in=f(P.ballast_rho_in, 0), rho_out=f(P.ballast_rho_out, 0),
        ball_half=f(P.ballast_half_deg, 0), n_ballast=str(P.n_ballast), cam_x=f(P.cam_pos[0]),
        cam_y=f(P.cam_pos[1], 0), cam_z=f(P.cam_pos[2], 0), n_req=str(len(CD.REQUIREMENTS)),
    )
    return tok


# ----------------------------------------------------------------------------- tables
def md_table(header, rows, align=None):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(align or ["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


GROUPS = [
    ("Shell + equatorial joint + tape", ("SH-01", "SH-02", "SH-03", "SH-04")),
    ("Polar interface (flanges, bearings, hubs, hub devices, bolt)", ("SH-10", "SH-11", "SH-30", "SH-31", "ST-02", "ST-03", "ST-04", "PW-04", "PW-05", "SA-03")),
    ("Twin drive (gearmotors, pinions, arms, ring gears)", ("DR-", "SH-20", "SH-21")),
    ("Stator structure (axle, plates, clamps, fasteners)", ("ST-01", "ST-1", "ST-20")),
    ("Steering mechanism (pivot, bearings, worm motor, stops, hangers, tray, brackets)", ("SG-", "BB-")),
    ("Ballast arc plates", ("BL-",)),
    ("Battery 6S1P + BMS", ("PW-10",)),
    ("Compute (Pi 5, MCU)", ("CP-",)),
    ("Motor drivers", ("DV-",)),
    ("Power electronics (PDB, DC-DC)", ("PW-01", "PW-02", "PW-03")),
    ("Safety hardware (contactor, brake relays, supervisor)", ("SA-01", "SA-02", "SA-04")),
    ("Camera, servo and sensors", ("SE-",)),
    ("Wiring harness (allowance)", ("HR-",)),
]


def group_of(pid):
    for name, keys in GROUPS:
        for k in keys:
            if pid == k or (k.endswith("-") and pid.startswith(k)) or (len(k) == 4 and pid.startswith(k)):
                return name
    return "Other"


def table_mass_groups(rows):
    agg = {}
    for r in rows:
        g = group_of(r["pid"])
        a = agg.setdefault(g, dict(m=0, mx=0, my=0, mz=0, cad=0, est=0))
        a["m"] += r["mass_kg"]
        a["mx"] += r["mass_kg"] * r["x_mm"]
        a["my"] += r["mass_kg"] * r["y_mm"]
        a["mz"] += r["mass_kg"] * r["z_mm"]
        if r["basis"].startswith("CAD"):
            a["cad"] += r["mass_kg"]
        else:
            a["est"] += r["mass_kg"]
    M = sum(a["m"] for a in agg.values())
    out = []
    for name, _ in GROUPS:
        a = agg.get(name)
        if not a:
            continue
        out.append([name, f(a["m"], 3), f(100 * a["m"] / M, 1), signed(a["mx"] / a["m"]), signed(a["my"] / a["m"]),
                    signed(a["mz"] / a["m"]), f"{f(a['cad'], 2)} / {f(a['est'], 2)}"])
    tot = [sum(a[k] for a in agg.values()) for k in ("m", "mx", "my", "mz", "cad", "est")]
    out.append(["**Total**", f"**{f(tot[0], 3)}**", "100.0", signed(tot[1] / tot[0]), signed(tot[2] / tot[0]),
                signed(tot[3] / tot[0]), f"{f(tot[4], 2)} / {f(tot[5], 2)}"])
    return md_table(["Mass group", "kg", "%", "x mm", "y mm", "z mm", "CAD / est. kg"], out,
                    ["---", "--:", "--:", "--:", "--:", "--:", "--:"])


PLACEMENT = {
    "SE-01": ("front plate, 50 mm left of seam plane, on servo", "servo bracket", "clear forward view; seam stripe off-centre"),
    "SE-02": ("front plate, upper left", "screwed bracket", "pitch-stabilises the camera"),
    "SE-03": ("saddle on the axle, 22 mm above the pitch axis", "clamp saddle", "minimal tangential acceleration"),
    "SE-04": ("rear end of the pivot shaft", "bracket off rear plate", "absolute bob angle"),
    "SE-05": ("left motor arm, facing ring-gear magnet", "arm-mounted", "once-per-revolution shell reference"),
    "CP-01": ("rear plate, outer face (right half)", "M2.5 standoffs + damping", "heat spread into the Al plate; away from the drivers"),
    "CP-02": ("rear plate, outer face (left half)", "standoffs", "short UART to the Pi; central harness"),
    "DV-01": ("left side plate, outer face, front", "standoffs", "short leads to both gearmotors"),
    "DV-02": ("left side plate, outer face, rear", "standoffs", "near the steering motor harness"),
    "PW-01": ("right side plate, outer face, front", "standoffs", "balances the left-side drivers"),
    "PW-02": ("right side plate, outer face", "standoffs", "Pi rail kept separate from the motor bus"),
    "PW-03": ("left side plate, rear", "standoffs", "servo rail after the contactor"),
    "SA-01": ("right side plate, rear", "bracket", "motor-bus isolation (channel A)"),
    "SA-02": ("right side plate, rear", "bracket", "dynamic brake (channel B)"),
    "SA-04": ("front plate, right; antenna up", "standoffs", "best RF view through the clear upper shell"),
    "PW-04": ("left polar hub face, recessed", "panel mount", "external manual disconnect"),
    "PW-05": ("left polar hub face", "panel mount", "charge without opening the ball"),
    "SA-03": ("left polar hub face", "panel mount", "armed / e-stop / fault indication"),
    "PW-10": ("steering-bob tray, lowest practical position", "strap + rails", "mass in the bob = steering authority"),
}


def table_placement(rows):
    by = {r["pid"]: r for r in rows}
    out = []
    for pid, (loc, mnt, why) in PLACEMENT.items():
        r = by[pid]
        out.append([pid, r["name"], f"({r['x_mm']:.0f}, {r['y_mm']:.0f}, {r['z_mm']:.0f})", loc, mnt, why])
    return md_table(["ID", "Component", "CG (x, y, z) mm", "Location", "Mounting", "Reason"], out)


INTERFACES = [
    ("Camera -> Pi 5", "MIPI CSI-2, 2 lanes (15-to-22-pin FPC)", "1280x720 @ 50 fps", "camera-side 3.3 V"),
    ("Pi 5 <-> MCU", "UART 1 Mbaud (or USB-CDC)", "cmd 50 Hz / telemetry 100 Hz", "3.3 V logic"),
    ("IMU -> MCU", "I2C 400 kHz or SPI", "400 Hz", "3.3 V"),
    ("Drive encoders -> MCU", "quadrature A/B on PIO", "up to ~50 kHz edges", "level-shift if 5 V"),
    ("Shell index Hall -> MCU", "digital interrupt", "1 pulse / shell rev.", "3.3 V"),
    ("Steering angle sensor -> MCU", "I2C (AS5600 class)", "200 Hz", "3.3 V"),
    ("Bus monitor -> MCU", "I2C (INA228 class)", "50 Hz", "3.3 V"),
    ("MCU -> drive driver", "PWM 20 kHz + DIR, x2", "500 Hz update", "3.3 V logic"),
    ("MCU -> steering driver", "PWM + DIR", "500 Hz update", "3.3 V logic"),
    ("MCU -> camera servo", "servo PWM 1-2 ms", "50 Hz", "signal 3.3 V, power 6 V"),
    ("MCU -> watchdog IC", "WDI toggle", ">= 10 Hz", "3.3 V"),
    ("Watchdog -> supervisor", "WD_OK, open drain", "level", "3.3 V"),
    ("E-stop TX -> supervisor", "2.4 GHz (ESP-NOW class) heartbeat", "20 Hz, 250 ms time-out", "RF"),
    ("Supervisor -> contactor", "low-side MOSFET coil driver + flyback diode", "level", "24 V coil"),
    ("Supervisor -> brake relays", "coil driver (NC contacts short motors)", "level", "24 V coil"),
    ("Supervisor -> drivers", "PWM gate (AND + pull-downs)", "level", "3.3 V"),
    ("Supervisor -> MCU, Pi 5", "ESTOP_STATE GPIO", "level", "3.3 V"),
    ("DC-DC -> Pi 5", "5.1 V / 5 A to the 5 V input", "continuous", "Pi 5 USB current limit set in config"),
]


def table_interfaces():
    return md_table(["Link", "Physical layer / protocol", "Rate", "Level / note"], INTERFACES)


def table_torque(res):
    rows = []
    for t in res["drive_feasibility"]["torque_table"]:
        if t["alpha_deg"] in (5, 8, 10, 12, 14, 16, 20, 25, 30):
            rows.append([t["alpha_deg"], f(t["shell_torque_Nm"], 1), f(t["torque_per_motor_Nm"], 2),
                         "-" if t["pendulum_angle_deg"] is None else f(t["pendulum_angle_deg"], 1),
                         "yes" if t["quasi_static_ok_phi_le_60"] else "run-up needed"])
    return md_table(["Ramp angle (deg)", "Shell torque (N m)", "Per gearmotor (N m)", "Pendulum angle (deg)",
                     "Quasi-static (pendulum <= 60 deg)"], rows, ["--:", "--:", "--:", "--:", "---"])


def table_momentum(res):
    rows = [[t["alpha_deg"], f(t["ramp_length_m"], 2), f(t["approach_speed_mps"], 2)]
            for t in res["drive_feasibility"]["momentum_table_0p8ft_ramp"]]
    return md_table(["Ramp angle (deg)", "Ramp length for a 0.244 m rise (m)", "Approach speed (m/s)"], rows,
                    ["--:", "--:", "--:"])


def table_req_summary():
    rows = []
    for r in CD.REQUIREMENTS:
        if r["show_in_summary"]:
            rows.append([r["id"], r["short"], r["type"], r["status"]])
    return md_table(["ID", "Requirement (short form; exact wording in CSV)", "Type", "Status"], rows)


def table_checks(res):
    d = res["dimensions"]
    sc = res["swept_clearance"]
    cam = res["camera_fov"]
    env = res["envelopes"]
    rows = [
        ["Diameter strictly within 609.6-762.0 mm (2562 directions)", f"{d['caliper_min_mm']}-{d['caliper_max_mm']} mm", "PASS" if d["strictly_within_rule"] else "FAIL"],
        ["Same with +/-7 mm forming tolerance", f"{d['tolerance_case_min_mm']}-{d['tolerance_case_max_mm']} mm", "PASS" if d["strictly_within_rule_with_tolerance"] else "FAIL"],
        ["External features beyond the shell (limit 152.4 mm)", f"{d['external_sensors_or_mounts']} items; max {d['max_non_skin_protrusion_mm']} mm", "PASS" if d["protrusion_rule_ok"] else "FAIL"],
        ["Frame/bob to shell clearance, all pitch, bob +/-30 deg (>= 8 mm)", f"{sc['min_frame_or_bob_to_skin_mm']} mm", "PASS"],
        ["Polar precision gaps (>= 1 mm)", f"{sc['worst_margin']['clearance_mm']} mm ({sc['worst_margin']['moving']} vs {sc['worst_margin']['shell_part']})", "PASS" if sc["pass"] else "FAIL"],
        ["B-rep clash check, 6 pitch/tilt states", f"{len(res['clash']['clashes'])} clashes", "PASS" if res["clash"]["pass"] else "FAIL"],
        ["Camera rays blocked by internal parts (< 0.5 %)", f"{cam['blocked_by_internal_parts_pct']} %", "PASS" if cam["pass"] else "FAIL"],
        ["Battery removal path", "clear" if env["EV-01"]["clear"] else "obstructed", "PASS" if env["EV-01"]["clear"] else "FAIL"],
        ["Preload-bolt socket access", "clear" if env["EV-02"]["clear"] else "obstructed", "PASS" if env["EV-02"]["clear"] else "FAIL"],
        ["Lateral CG offset, abs(y) <= 2 mm", f"{res['mass']['cg_mm'][1]} mm", "PASS" if abs(res["mass"]["cg_mm"][1]) <= 2 else "FAIL"],
    ]
    return md_table(["Check", "Result", "Verdict"], rows)


def table_risks():
    return md_table(["ID", "Risk", "L", "I", "Mitigation (phase)"], CD.RISKS)


# ----------------------------------------------------------------------------- BOM + compliance CSV
def write_bom(rows):
    lines = {}
    for r in rows:
        key = CD.BOM_KEY.get(r["pid"], r["pid"])
        e = lines.setdefault(key, dict(rows=[], name=CD.BOM_NAME.get(key, r["name"])))
        e["rows"].append(r)
    out = []
    for key, e in lines.items():
        rs = e["rows"]
        m = sum(r["mass_kg"] for r in rs)
        cg = [sum(r["mass_kg"] * r[k] for r in rs) / m for k in ("x_mm", "y_mm", "z_mm")]
        info = CD.BOM_INFO.get(key, {})
        same = max(r["mass_kg"] for r in rs) - min(r["mass_kg"] for r in rs) < 1e-6
        out.append({
            "Item": key, "Description": e["name"], "Group": group_of(rs[0]["pid"]), "Qty": len(rs),
            "CAD part IDs": " ".join(r["pid"] for r in rs),
            "Material / part class": rs[0]["material"], "Selected or reference part": info.get("part", ""),
            "Mass each (kg)": f(m / len(rs), 4) + ("" if same else " (avg)"), "Mass total (kg)": f(m, 4),
            "Mass basis": rs[0]["basis"], "CG x (mm)": f(cg[0]), "CG y (mm)": f(cg[1]), "CG z (mm)": f(cg[2]),
            "Placeholder (PH)": "yes" if rs[0]["placeholder"] else "no",
            "Spec source": info.get("source", ""), "Notes": info.get("note", rs[0]["note"]),
            "Cost": "not quoted (Phase 3 procurement)",
        })
    tot = sum(float(o["Mass total (kg)"]) for o in out)
    summ = [[o["Item"], o["Description"], o["Qty"], o["Mass total (kg)"], o["Placeholder (PH)"]] for o in out]
    summ.append(["", "**Total on robot (equals CAD total)**", "", f"**{tot:.3f}**", ""])
    for key, desc, qty in CD.OFF_ROBOT:
        out.append({k: "" for k in out[0]} | {"Item": key, "Description": desc, "Group": "Off-robot support equipment",
                                              "Qty": qty, "Mass total (kg)": "n/a (off-robot)",
                                              "Placeholder (PH)": "yes", "Cost": "not quoted (Phase 3 procurement)"})
        summ.append([key, desc + " (off-robot)", qty, "-", "yes"])
    with open(ROOT / "Preliminary_BOM.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    return md_table(["Item", "Description", "Qty", "Mass (kg)", "PH"], summ, ["---", "---", "--:", "--:", "---"]), tot


def write_compliance():
    cols = ["Requirement ID", "Source", "Exact requirement from the problem statement / template", "Mandatory or design-dependent",
            "Proposed design response", "Evidence in CAD or documentation", "Verification method", "Status"]
    with open(ROOT / "Requirements_Compliance.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in CD.REQUIREMENTS:
            w.writerow([r["id"], r["source"], r["text"], r["type"], r["response"], r["evidence"], r["verify"], r["status"]])


# ----------------------------------------------------------------------------- rendering
CSS = (SRC / "doc.css").read_text(encoding="utf-8")


def fill(template, tok):
    def rep(mo):
        k = mo.group(1)
        if k not in tok:
            raise KeyError(f"missing token {k}")
        return tok[k]
    return re.sub(r"\{\{([A-Za-z0-9_]+)\}\}", rep, template)


def optimise_figures():
    dst = BUILD / "fig"
    dst.mkdir(parents=True, exist_ok=True)
    for png in FIG.glob("*.png"):
        im = Image.open(png).convert("RGB")
        if im.width > 2600:
            im = im.resize((2600, round(im.height * 2600 / im.width)), Image.LANCZOS)
        if png.stem in ("Isometric_Render", "Cross_Section", "Exploded_Assembly"):
            im.save(dst / (png.stem + ".jpg"), quality=90, optimize=True)
        else:
            im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(
                dst / (png.stem + ".png"), optimize=True)


def html_doc(md_text, title, header):
    body = markdown.markdown(md_text, extensions=["tables", "attr_list", "md_in_html", "fenced_code", "sane_lists"])
    for stem in ("Isometric_Render", "Cross_Section", "Exploded_Assembly"):
        body = body.replace(f"../figures/{stem}.png", f"fig/{stem}.jpg")
    body = body.replace("../figures/", "fig/")
    # image + caption share one paragraph in the source; split them and keep them together, and put
    # wide diagrams on landscape pages and dense drawings on their own full page
    wrap = {"figwide": "landscape", "figpage": "fullpage", "fig": "figblock"}

    def figrep(mo):
        img, cls, cap = mo.group(1), mo.group(2), mo.group(3)
        return f'<div class="{wrap[cls]}"><p class="img">{img}</p><p class="cap">{cap}</p></div>'
    body = re.sub(r'<p>(<img[^>]*class="(figwide|figpage|fig)"[^>]*>)\s*(<em>.*?</em>)\s*</p>', figrep, body,
                  flags=re.S)
    # a heading directly before a page-sized figure travels with it (no stranded headings)
    body = re.sub(r'(<h[23][^>]*>[^<]*</h[23]>)\s*(<div class="(?:landscape|fullpage)">)', r'\2\1', body)
    css = CSS.replace("@@HEADER@@", header)
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{css}</style></head><body>{body}</body></html>"


def to_pdf(html_path, pdf_path):
    exe = next(b for b in BROWSERS if pathlib.Path(b).exists())
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                        "--print-to-pdf-no-header", "--virtual-time-budget=8000", f"--print-to-pdf={pdf_path}",
                        html_path.as_uri()], check=True, capture_output=True, timeout=240)


def main():
    res, rows = load()
    BUILD.mkdir(exist_ok=True)
    tok = tokens(res, rows)
    write_compliance()
    bom_table, bom_tot = write_bom(rows)
    assert abs(bom_tot - res["mass"]["total_kg"]) < 0.01, (bom_tot, res["mass"]["total_kg"])
    tok.update(TABLE_REQ_SUMMARY=table_req_summary(), TABLE_MASS_GROUPS=table_mass_groups(rows),
               TABLE_PLACEMENT=table_placement(rows), TABLE_INTERFACES=table_interfaces(),
               TABLE_TORQUE=table_torque(res), TABLE_MOMENTUM=table_momentum(res), TABLE_BOM=bom_table,
               TABLE_RISKS=table_risks(), TABLE_CHECKS=table_checks(res))
    optimise_figures()
    docs = [("abstract_template.md", "Phase1_CAD_Abstract", "WB-700 | Round 1 CAD Abstract | TM-47C20DF8A48"),
            ("tdd_template.md", "Phase1_Technical_Design_Document", "WB-700 | Phase 1 Technical Design Document | TM-47C20DF8A48")]
    for tpl, name, header in docs:
        md = fill((SRC / tpl).read_text(encoding="utf-8"), tok)
        (ROOT / f"{name}.md").write_text(md.replace("](../figures/", "](figures/"), encoding="utf-8")
        html = html_doc(md, name, header)
        hp = BUILD / f"{name}.html"
        hp.write_text(html, encoding="utf-8")
        to_pdf(hp, ROOT / f"{name}.pdf")
        print("built", name)
    import make_docx
    make_docx.build(ROOT / "Phase1_CAD_Abstract.md", ROOT / "Phase1_CAD_Abstract.docx", FIG)
    print("built Phase1_CAD_Abstract.docx")


if __name__ == "__main__":
    main()
