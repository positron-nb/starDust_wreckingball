# Official Sources — Verification Record (STEP 1)

Verified on **2026-10-20** (local date of this workspace). Everything below was read from the
sources named; nothing is inferred unless marked *[interpretation]*.

## 1. Primary authority — supplied problem statement

| Item | Value |
|---|---|
| File (original) | `Downloads\Ultraviollete_PS_2_compressed.pdf` (129,976 bytes) |
| Project copy | `reference/Techfest2026_WreckingBall_ProblemStatement.pdf` |
| Pages | 5 (all read: objective, constraints, deliverables, track, format, scoring, eligibility, timeline, rules, certificates, prizes, prize T&C) |
| Phase 1 deadline in PDF | **October 25, 2026** — "Registration & CAD Abstract Submission" |

## 2. Official competition page

URL: <https://techfest.org/competitions/wrecking-ball-challenge> (JavaScript-rendered; read in a
real browser on 2026-10-20).

| Item on website | Agrees with PDF? | Note |
|---|---|---|
| Timeline: Oct 25 / Nov 15 / Nov 20 / Dec 16 / Dec 17, 2026 | **Yes — identical** | No date conflict found. |
| Round structure (R1 abstract & design audit; R2 virtual simulation audit; R3 on-site) | Yes | |
| Registration on techfest.org for an official Team ID | Yes | |
| Originality / AI-tool rule | Yes (shortened wording) | Website: "Submissions must represent original work. External AI tools during live rounds are prohibited unless authorized by judges." See §4. |
| Sensor rule | **Minor wording difference** | PDF: "Supplementary **internal** sensors (IMUs, encoders, distance sensors) are permitted for stabilization." Website omits "internal". Our design uses internal sensors only, so it complies with both readings. |
| Diameter FAQ | Yes | "The robot must be spherical with a diameter between 2.0 and 2.5 feet." |
| Doubts / queries | Website has a "Doubts" section (requires registration) | Matches PDF rule 4. |

## 3. Official Round 1 Submission Template (found on the official page)

Link published on the official page:
<https://docs.google.com/document/d/1d9hi3iQEn4ySm097KdtqvR12Imkbawf7IRolQd3GMWo/edit?usp=sharing>
(read via the public `mobilebasic` view on 2026-10-20; nothing was downloaded or edited).

Template structure (headings and prompts, transcribed):

- **TEAM IDENTIFICATION** — Team ID & Name; Institution; Team Lead Contact (Name | Email | Phone).
- **1. Mechanical Architecture & Enclosure Design (CAD Evidence)**
  - CAD Renders Provided: *Isometric View Render*; *Cross-Sectional View Render*.
  - Shell Integrity: Material; Exact Outer Diameter; *The 0.5-Foot Limit Rule* — "Dimension and confirm that all external sensor mounts or camera pods extend [≤ 0.5 ft] beyond the outer shell diameter" *[the comparison symbol did not render in the public view; interpretation based on the rule in the PDF]*.
  - CoG & Drive Mechanism: explain how the internal drive/pendulum moves and balances the robot; **provide initial calculated CoG coordinates relative to the geometric centre**.
  - **Ramp-Climbing Capability: "Detail motor torque calculations and selection chosen to conquer the hardest ramp".**
- **2. Electrical & Power System Architecture**
  - Electrical Block Diagram (power distribution, microcontroller, sensor interfaces, motor drivers).
  - Power Source & BMS: battery-only confirmation (Yes/No); chemistry, voltage, capacity; BMS and **low-voltage cut-off (LVC)** safeguards.
  - Actuation & Motor Control: **Motor specs (RPM, stall torque)**; driver boards (model and specs for propulsion and steering drivers).
  - Safety Fail-Safes: **Wireless kill-switch** mechanism; **Manual Disconnect — "manual external power disconnect switch location"**.
- **3. Software & Vision-Based Navigation Pipeline**
  - **Software Flowchart** — architecture flowchart showing the state-machine diagram and vision AI stack.
  - Primary Vision Processing; State Estimation & Control (sensor fusion); Obstacle Handling Logic (Sector 4 pendulum).

### Consequences for our Phase 1 scope

1. The template asks for **preliminary motor-torque calculations and a motor selection** in Round 1.
   We therefore include a *preliminary, assumption-labelled* torque estimate and a motor
   *specification class*. Final sizing stays in Phase 2.
2. The template expects a **manual external power disconnect**. The design puts it on the
   non-rotating left polar hub (see TDD §16).
3. The template asks for a **software flowchart with a state-machine diagram**. One was added
   (`figures/Software_Flowchart.png`).
4. No file-format, page-limit or word-limit rule was found in any official source. The upload
   format (Google Doc copy, PDF or DOCX) and channel are **not stated**. PDF rule 2 says round
   instructions arrive by registered e-mail. We supply PDF, DOCX and MD versions that follow
   the template headings exactly.

## 4. Compliance note — originality and AI tools

PDF rule 3 / website: *"Submissions must represent the team's original work. Using external AI
tools during live rounds is strictly prohibited unless judges explicitly authorize it."*

This package was prepared with an AI assistant. *[Interpretation]* "Live rounds" most naturally
means the on-site rounds, but the originality requirement applies to all submissions. Before
submitting, the team should:

- review, understand and own every design decision and number, and be able to defend it without assistance;
- ask the organisers through the official **Doubts** section whether AI-assisted documentation is acceptable for Round 1 and whether it must be disclosed (see `Open_Questions_for_Organizers.md`, Q1).

## 5. Not verifiable from official sources (left open)

Ramp geometry (angle, length, lip, run-out or drop), track width, cone size, pendulum geometry and
period, surface material, lighting, weight limit (none stated — **no limit is assumed**), the
definition of "electrical isolation" at inspection, and the submission file format. All are listed
in `Open_Questions_for_Organizers.md`.
