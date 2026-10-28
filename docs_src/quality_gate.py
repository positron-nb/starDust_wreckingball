"""Phase 1 quality gate: file presence, cross-document consistency and wording checks.
usage (from docs_src): ..\\.venv\\Scripts\\python.exe quality_gate.py"""
from __future__ import annotations

import csv
import json
import pathlib
import re

import pymupdf

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED = ["Phase1_CAD_Abstract.pdf", "Phase1_Technical_Design_Document.pdf", "Phase1_CAD_Abstract.md",
            "Phase1_CAD_Abstract.docx", "cad/wb700_params.py", "cad/wb700_model.py", "cad/build_all.py",
            "cad/out/WB700_Phase1_Assembly.step", "cad/out/WB700_Phase1_Assembly.glb", "cad/out/mass_table.csv",
            "cad/out/analysis_results.json", "figures/System_Architecture.png", "figures/Electronics_Architecture.png",
            "figures/Power_Distribution.png", "figures/Software_Flowchart.png", "figures/Internal_Layout.png",
            "figures/Exploded_Assembly.png", "figures/Dimensioned_Views.png", "figures/Center_of_Gravity.png",
            "figures/Isometric_Render.png", "figures/Cross_Section.png", "figures/Camera_FOV.png",
            "figures/Ramp_Capability.png", "diagrams/build_diagrams.py", "diagrams/svg/System_Architecture.svg",
            "diagrams/System_Architecture.mmd", "Preliminary_BOM.csv", "Requirements_Compliance.csv",
            "Open_Questions_for_Organizers.md", "Phase1_README.md", "FUTURE_PHASES_STANDBY.md", "PROGRESS_LOG.md"]


def main():
    res = json.loads((ROOT / "cad/out/analysis_results.json").read_text(encoding="utf-8"))
    out = []

    def check(name, ok, detail=""):
        out.append((name, "PASS" if ok else "FAIL", detail))

    missing = [f for f in REQUIRED if not (ROOT / f).exists()]
    check("All required files exist", not missing, ", ".join(missing) or f"{len(REQUIRED)} files")
    d = res["dimensions"]
    check("Diameter strictly inside 609.6-762.0 mm", d["strictly_within_rule"], f"{d['caliper_min_mm']}-{d['caliper_max_mm']} mm")
    check("No external protrusion beyond the 152.4 mm allowance", d["protrusion_rule_ok"] and d["external_sensors_or_mounts"] == 0,
          f"max non-skin {d['max_non_skin_protrusion_mm']} mm")
    check("No clashes in modelled states", res["clash"]["pass"], f"{len(res['clash']['states'])} states")
    check("Moving parts keep >= 8 mm to the shell", res["swept_clearance"]["min_frame_or_bob_to_skin_mm"] >= 8,
          f"{res['swept_clearance']['min_frame_or_bob_to_skin_mm']} mm")
    check("Camera view unobstructed", res["camera_fov"]["pass"], f"{res['camera_fov']['blocked_by_internal_parts_pct']} % blocked")
    cg = res["mass"]["cg_mm"]
    cg_s = f"({cg[0]:+.1f}, {cg[1]:+.1f}, {cg[2]:+.1f})"
    for doc in ("Phase1_CAD_Abstract.md", "Phase1_Technical_Design_Document.md"):
        s = (ROOT / doc).read_text(encoding="utf-8")
        check(f"{doc}: CG matches CAD {cg_s}", cg_s.replace("(", "").replace(")", "") in s.replace("(", "").replace(")", ""))
        check(f"{doc}: mass {res['mass']['total_kg']:.2f} kg present", f"{res['mass']['total_kg']:.2f} kg" in s)
        check(f"{doc}: calipers present", f"{d['caliper_min_mm']}" in s and f"{d['caliper_max_mm']}" in s)
        figs = re.findall(r"\]\((figures/[^)]+)\)", s)
        bad = [x for x in figs if not (ROOT / x).exists()]
        check(f"{doc}: {len(figs)} referenced figures exist", not bad, ", ".join(bad))
        check(f"{doc}: no unfilled tokens or mojibake", not any(t in s for t in ("{{", "Ã", "�")))
        claims = [m.group(0) for m in re.finditer(r"[^.\n]*\b(tested|proven|guarantee[sd]?|validated|verified)\b[^.\n]*", s, re.I)]
        risky = [c.strip() for c in claims if not re.search(r"\b(no|not|will|be|Phase 2|Phase 3|to be|until|once|later|"
                                                           r"accessed|checked|datasheet|dynamic|only)\b", c, re.I)]
        check(f"{doc}: no unqualified test/validation claims", not risky, " | ".join(risky)[:200])
    statuses = {r["Status"] for r in csv.DictReader(open(ROOT / "Requirements_Compliance.csv", encoding="utf-8"))}
    check("Compliance statuses limited to Satisfied / Partially satisfied / Unresolved",
          statuses <= {"Satisfied", "Partially satisfied", "Unresolved"}, ", ".join(sorted(statuses)))
    bom = list(csv.DictReader(open(ROOT / "Preliminary_BOM.csv", encoding="utf-8")))
    tot = sum(float(r["Mass total (kg)"]) for r in bom if r["Mass total (kg)"][:1].isdigit())
    check("BOM mass equals CAD mass", abs(tot - res["mass"]["total_kg"]) < 0.01, f"{tot:.3f} vs {res['mass']['total_kg']:.3f} kg")
    for pdf in ("Phase1_CAD_Abstract.pdf", "Phase1_Technical_Design_Document.pdf"):
        doc = pymupdf.open(ROOT / pdf)
        imgs = sum(len(p.get_images()) for p in doc)
        land = sum(1 for p in doc if p.rect.width > p.rect.height)
        check(f"{pdf}: renders, pages={doc.page_count}, images={imgs}, landscape={land}", doc.page_count > 0 and imgs > 0)
    width = max(len(n) for n, _, _ in out)
    lines = [f"{v:4s}  {n.ljust(width)}  {det}" for n, v, det in out]
    print("\n".join(lines))
    (ROOT / "build" / "quality_gate.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\nFAILED" if any(v == "FAIL" for _, v, _ in out) else "\nALL PASS")


if __name__ == "__main__":
    main()
