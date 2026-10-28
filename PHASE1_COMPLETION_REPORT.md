# Phase 1 Completion Report (2026-10-21)

**Status: technical package complete and checked. Submission still needs the team actions listed at the
end.** The quality gate (`docs_src/quality_gate.py`, output in `build/quality_gate.txt`) shows
**22 / 22 PASS**.

## Deliverables

| Deliverable | Path | Verification status | Outstanding issues |
|---|---|---|---|
| CAD abstract (main submission, mirrors the official Round 1 template field by field; template re-checked 2026-10-21, unchanged) | `Phase1_CAD_Abstract.pdf` (11 pp.), `.md`, `.docx` | PDF inspected page by page; numbers cross-checked against the CAD results by the gate; DOCX structure checked (template title lines, 16 fields + 11 sub-fields, 9 figures) | Team placeholders and two `[GOOGLE DRIVE LINK]` placeholders; DOCX not yet opened in Word or Google Docs; upload format unconfirmed (Q2) |
| Technical design document (21 sections + appendices) | `Phase1_Technical_Design_Document.pdf` (25 pp.), `.md` | Inspected page by page; landscape diagram pages verified; numbers cross-checked | Two partly empty pages before full-page figures (cosmetic) |
| Editable parametric CAD | `cad/wb700_params.py`, `cad/wb700_model.py`, `cad/build_all.py` | Rebuilds the 68-part assembly; STEP/STL/GLB exported | Built in CadQuery (OCCT) because OpenSCAD/FreeCAD were not installed; the STEP opens in FreeCAD |
| Complete assembly, packaging and envelopes | `cad/out/WB700_Phase1_Assembly.step`, `.glb`, `stl/` | Clash check: 0 clashes in 6 pitch/tilt states; frame/bob to shell ≥ 19.98 mm; battery removal path clear | Purchased parts are placeholder envelopes (27 items, 3.03 kg) |
| Dimensional compliance | `figures/Dimensioned_Views.png`, `cad/out/analysis_results.json` | Calipers 696.3-700.7 mm over 2562 directions, strictly inside 609.6-762.0 mm (also with ±7 mm tolerance); 0 external protrusions | How the organisers measure the diameter is unconfirmed (Q5) |
| Cutaway / cross-section, isometric, exploded renders | `figures/Cross_Section.png`, `Isometric_Render.png`, `Exploded_Assembly.png` | Generated from the CAD; inspected | Some label crowding in the exploded view (cosmetic) |
| Internal layout drawing | `figures/Internal_Layout.png` | Orthographic projections of the CAD solids; inspected | none |
| Centre of gravity + mass table | `figures/Center_of_Gravity.png`, `cad/out/mass_table.csv` | CG (+1.4, -0.4, -87.2) mm, 17.00 kg, reproducible from the table | Static estimate; dynamic validation is Phase 2, hardware CG is Phase 3 |
| Camera field of view | `figures/Camera_FOV.png` | Ray-cast: 0 % blocked, seam stripe 6.8 % (masked), floor visible from 181 mm ahead | Image quality through PC not tested (Phase 2/3) |
| Preliminary ramp / torque check | `figures/Ramp_Capability.png` | Quasi-static; 12.4° capability at baseline | Ramp angle not published (Q3); final sizing is Phase 2 |
| System, electronics, power, software diagrams | `figures/System_Architecture.png`, `Electronics_Architecture.png`, `Power_Distribution.png`, `Software_Flowchart.png`; sources `diagrams/build_diagrams.py`, `diagrams/svg/*.svg`, `diagrams/*.mmd` | Inspected; the safety path is visually distinct; no offboard processing | Mermaid files are logical exports (auto-layout); the SVG/PNG are the presentation versions |
| Component-interface table, one-page system explanation | TDD sections 11-12 | Included | none |
| Requirements traceability matrix | `Requirements_Compliance.csv` (40 rows) | 16 satisfied, 18 partially satisfied, 6 unresolved; quotes are verbatim | Unresolved rows are team or organiser actions |
| Preliminary BOM + mass budget | `Preliminary_BOM.csv` (49 lines) | Total equals CAD mass (17.003 kg) | No prices (none verified) |
| Organiser questions | `Open_Questions_for_Organizers.md` | 13 questions | Must be posted by the team |
| Research and source verification | `research/` | Official page and template read 2026-10-20; licences checked | none |
| README, standby list, progress log | `Phase1_README.md`, `FUTURE_PHASES_STANDBY.md`, `PROGRESS_LOG.md` | Written | none |

## Exact steps to submit

1. Register on techfest.org and obtain the Team ID.
2. Fill the team placeholders in `docs_src/abstract_template.md` and `docs_src/tdd_template.md`, then run
   `..\.venv\Scripts\python.exe build_docs.py` from `docs_src`, then `quality_gate.py`.
3. Post Q1 (AI-assisted documentation) and Q2 (submission format) in the Doubts section now. Review
   every decision so the team can defend it as its own work.
4. Put the design-document PDF, the STEP model and the figures in a view-only Google Drive folder and
   replace the two `[GOOGLE DRIVE LINK]` placeholders.
5. Submit before **October 25, 2026**, in whatever format the organisers specify:
   `Phase1_CAD_Abstract.pdf`, or the team's `wrecking_ball` Google Doc shared as Viewer. That doc is
   already filled with the same content in the template's layout; it still needs the 9 figures inserted
   at their `[Insert image: ...]` markers, the team details and the Drive link.
