# WB-700: Techfest 2026-27 Wrecking Ball Challenge, Phase 1 package

Phase 1 = **Registration & CAD Abstract Submission, due October 25, 2026** (problem statement and
techfest.org agree; checked 2026-10-20). Phases 2 and 3 are on standby (`FUTURE_PHASES_STANDBY.md`).

## What to submit

1. **`Phase1_CAD_Abstract.pdf`** (11 pages) is the main submission. It reproduces the official
   [Round 1 template](https://docs.google.com/document/d/1d9hi3iQEn4ySm097KdtqvR12Imkbawf7IRolQd3GMWo/edit?tab=t.0)
   exactly: same title lines, the same field labels in the same order, each filled in, with the figures
   placed under the fields that ask for them. `Phase1_CAD_Abstract.docx` has the same content. To hand it
   in as a Google Doc, upload the DOCX to Google Drive and choose *Open with → Google Docs*, or paste it
   into your own copy of the template (*File → Make a copy*). Then share it as **Viewer**. If a PDF is
   requested, use the PDF here or *File → Download → PDF*. Replace the two `[GOOGLE DRIVE LINK]`
   placeholders with a view-only Drive folder containing the design-document PDF, the STEP model and the
   figures.
2. **`Phase1_Technical_Design_Document.pdf`** (25 pages) is the supporting design document, in case
   supplementary material is accepted.
3. Supporting data: `Requirements_Compliance.csv`, `Preliminary_BOM.csv`, `figures/`,
   `cad/out/WB700_Phase1_Assembly.step`.

**Before submitting, the team must:**

- Register on techfest.org and get the Team ID.
- Replace every `[TEAM ...]`, `[NAME]` and `[EMAIL]` placeholder in `docs_src/*_template.md`, then rebuild.
- Post the questions in `Open_Questions_for_Organizers.md` in the Doubts section. Q1 and Q2 are urgent.
- Review and own every design decision (see the compliance note below).

## Folder map

| Path | Contents |
|---|---|
| `reference/` | Copy of the official 5-page problem statement |
| `research/` | Official-source verification (incl. the Round 1 template), mechanism research and drive selection |
| `cad/wb700_params.py` | **Every dimension and mass assumption** (edit here) |
| `cad/wb700_model.py` | Parametric CadQuery assembly (68 parts; shell, stator, bob, envelopes) |
| `cad/wb700_analysis.py` | Mass/CG, diameter and protrusion checks, swept clearance, B-rep clash checks, camera ray-cast, preliminary drive numbers |
| `cad/wb700_render.py`, `cad/wb700_figures.py` | 3D renders and 2D drawings, all generated from the model |
| `cad/out/` | `WB700_Phase1_Assembly.step` (FreeCAD, Fusion, SolidWorks), `stl/` per part, `.glb`, `analysis_results.json`, `mass_table.csv` |
| `diagrams/build_diagrams.py` | Single source for the system, electronics, power and software diagrams: writes PNG, editable SVG (`diagrams/svg/`) and Mermaid (`diagrams/*.mmd`) |
| `figures/` | All figures used in the documents |
| `docs_src/` | Document templates, compliance and risk data, document builder |
| `build/` | Intermediate HTML and optimised figures (regenerated) |

## Rebuild everything (Windows, from the project folder)

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install cadquery pyvista trimesh manifold3d matplotlib markdown numpy scipy pymupdf python-docx shapely rtree
cd cad        & ..\.venv\Scripts\python.exe build_all.py
cd ..\diagrams & ..\.venv\Scripts\python.exe build_diagrams.py
cd ..\docs_src & ..\.venv\Scripts\python.exe build_docs.py
```

The `.venv` already exists in this folder. Documents and PDFs are rendered with the installed Microsoft
Edge in headless mode. Change a parameter, such as `D_shell` or `n_ballast`, and rebuild: every number
in the documents comes from the CAD results, so the documents stay consistent with the model.

## Honest status of the content

- The CAD is a **concept model**. Purchased parts that are not yet selected are **placeholder (PH)
  envelopes**: 27 items, 3.03 kg of the 17.00 kg total.
- All masses, the CG and the torque numbers are **design estimates or quasi-static calculations. No
  hardware has been built or tested**, and no prices have been quoted.
- The ramp angle is not published, so ramp capability is given as a function of angle.

## Compliance note: originality and AI tools

Rule 3 of the problem statement: *"Submissions must represent the team's original work. Using external
AI tools during live rounds is strictly prohibited unless judges explicitly authorize it."* This package
was drafted with an AI assistant. The team should understand and be able to defend every element, adapt
it as its own work, and ask the organizers (Q1) whether AI-assisted Round 1 documentation is acceptable
and whether it must be disclosed.
