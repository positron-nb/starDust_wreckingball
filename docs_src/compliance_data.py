"""Hand-authored content for the traceability matrix, risk register and BOM metadata.

Requirement text is quoted verbatim from the supplied problem statement (PS, page numbers given) or the
official Round 1 submission template (TPL). Status is one of: Satisfied / Partially satisfied / Unresolved.
"""

S, PS_, U = "Satisfied", "Partially satisfied", "Unresolved"
M, DD = "Mandatory", "Design-dependent"


def R(id_, source, text, short, type_, response, evidence, verify, status, summary=True):
    return dict(id=id_, source=source, text=text, short=short, type=type_, response=response, evidence=evidence,
                verify=verify, status=status, show_in_summary=summary)


REQUIREMENTS = [
    R("R-01", "PS p.1, Hardware & Mechanical Constraints",
      "Robot Structure: Must be a spherical robot (ball-shaped) with a strict diameter between 2.0 feet and 2.5 feet.",
      "Spherical, diameter strictly 2.0-2.5 ft", M,
      "700 mm (2.30 ft) PC sphere; max caliper 700.7 mm over tape band, min 696.3 mm across recessed hubs.",
      "Dimensioned_Views.png; cad/out/analysis_results.json (dimensions); wb700_params.py D_shell",
      "CAD caliper check over 2562 directions incl. all exterior parts (done); +/-7 mm tolerance case (done); "
      "physical go/no-go gauge check in Phase 3", S),
    R("R-02", "PS p.1", "Internal Housing: All core computing hardware, power sources, actuators, and electronics must fit "
      "completely inside the spherical body.", "All compute, power, actuators, electronics inside", M,
      "Every electronic/power/actuator part is inside the shell; hub devices recessed in flush polar hubs.",
      "Internal_Layout.png; Cross_Section.png; max non-skin radius 349.0 mm (recessed 1.0 mm)",
      "CAD radius/envelope check (done); inspection in Phase 3", S),
    R("R-03", "PS p.1", "Peripheral Limits: External sensors, mounts, or camera lenses cannot extend more than 0.5 feet beyond "
      "the surface of the outer shell.", "External sensors/mounts <= 0.5 ft beyond shell", M,
      "No external sensors, mounts or camera pods; camera internal behind clear PC.",
      "Dimensioned_Views.png envelope panel; analysis_results.json external_sensors_or_mounts = 0",
      "CAD protrusion check (done)", S),
    R("R-04", "PS p.1", "Power Supply: Must be strictly onboard battery-powered. No tethered cables, external power lines, or "
      "remote power feeds are allowed.", "Strictly onboard battery power", M,
      "6S1P Li-ion 21700 pack (about 97 Wh) on the steering bob; charge port used only between runs with the arming plug removed.",
      "Power_Distribution.png; Preliminary_BOM.csv (BATTERY)", "Design review (done); inspection in Phase 3", S),
    R("R-05", "PS p.1, Deliverables", "Phase 1 CAD & System Document: Complete CAD assembly illustrating internal electronic "
      "layout, center-of-gravity placement, and system architecture schematic.", "Phase 1 CAD + system document", M,
      "Parametric CadQuery assembly (STEP/STL/GLB) with labelled electronics, CG figure and architecture diagrams.",
      "cad/; figures/; Phase1_Technical_Design_Document.pdf; Phase1_CAD_Abstract.pdf",
      "Package review against this matrix (done); organiser screening", S),
    R("R-06", "PS p.2, Format", "Round 1 (Abstract & Design Audit): Online screening based on CAD models, system schematics, "
      "and dimension compliance.", "Round 1 screening content", M,
      "Abstract follows the official template; CAD renders, schematics and dimension compliance included.",
      "Phase1_CAD_Abstract.pdf/.docx/.md", "Submission by the team (pending format confirmation, Q2)", PS_),
    R("R-07", "PS p.1, Deliverables", "Phase 2 Technical Simulation Report: Mathematical analysis validating actuator torque "
      "across inclined planes, balance stability, and safety kill-switch mechanism implementation.",
      "Phase 2 simulation report (future)", M,
      "Preliminary quasi-static torque check only; full analysis is a Phase 2 standby workstream.",
      "Ramp_Capability.png; FUTURE_PHASES_STANDBY.md", "Phase 2 dynamic model and report", PS_),
    R("R-08", "PS p.2, Format", "Round 2 (Virtual Simulation Audit): Virtual evaluation of motor sizing calculations, torque "
      "requirements for the 0.8 ft ramp, and wireless kill-switch mechanics.", "Round 2 audit content (future)", M,
      "Ramp torque relation and pendulum limit established; motor class and kill-switch architecture defined.",
      "TDD sections 14 and 16; Ramp_Capability.png", "Phase 2 report", PS_),
    R("R-09", "PS p.2, Deliverables", "Phase 3 Physical Prototype: Fully operational ball bot fielded live on-campus at IIT "
      "Bombay for technical evaluation and track trials.", "Phase 3 prototype (future)", M,
      "On standby; manufacturing and assembly approach defined.", "TDD section 18; FUTURE_PHASES_STANDBY.md",
      "Phase 3 build and trials", U, summary=False),
    R("R-10", "PS p.2, Round 3 Day 1", "Day 1: Technical inspection (size check, weight, electrical isolation, emergency "
      "kill-switch validation) and preliminary practice runs.", "Inspection: size, weight, isolation, kill switch", M,
      "Diameter margins; mass estimate 17.0 kg; external arming plug for isolation; 3-channel e-stop with self-test.",
      "Dimensioned_Views.png; Center_of_Gravity.png; Power_Distribution.png",
      "Phase 3 inspection; 'electrical isolation' definition requested (Q8)", PS_),
    R("R-11", "PS p.2, Track", "Visual Guidance: Track boundaries are defined by color-coded cone barriers: Red Cones: Located "
      "on the right side of the track. Yellow Cones: Located on the left side of the track.",
      "Red cones right, yellow cones left", DD,
      "HSV segmentation of red/yellow cones; boundary model yellow = left, red = right.",
      "Software_Flowchart.png; Camera_FOV.png", "Phase 2 dataset tests; Phase 3 calibration", PS_),
    R("R-12", "PS p.2, Sector 1", "Sector 1: The Gate Runway (0m - 15m) Straight acceleration stretch featuring wide "
      "chevron-patterned cone gates to allow onboard vision calibration.", "S1 gate runway, vision calibration", DD,
      "CALIBRATE state locks colour thresholds and exposure on the chevron gates while rolling slowly.",
      "Software_Flowchart.png", "Phase 2 simulation; Phase 3 runs", PS_),
    R("R-13", "PS p.2, Sector 2", "Sector 2: The Step-Up Ramps (15m - 35m) Three consecutive incline ramps with heights of "
      "0.2 ft, 0.4 ft, and 0.8 ft, funneled through cone gates to test traction and motor torque.",
      "S2 ramps 0.2 / 0.4 / 0.8 ft", DD,
      "Pendulum capability 10.7 deg steady climb incl. rolling resistance (7.1-13.6 deg with 2-6 ballast plates); run-up energy estimate for steeper ramps (unverified); PU tape for grip.",
      "Ramp_Capability.png; TDD section 14", "Phase 2 dynamic model once ramp geometry is known (Q3)", PS_),
    R("R-14", "PS p.2, Sector 3", "Sector 3: The Wrecking Zone (35m - 55m) Sector populated with low-density obstacles (foam, "
      "thermocol, cardboard). The robot must maintain course alignment using border cones while plowing through obstacles.",
      "S3 low-density obstacles, keep alignment", DD,
      "Heavy low pendulum (cannot derail), PC shell, gyro heading hold + border cones, momentum of 1-1.5 m/s.",
      "TDD sections 10 and 14", "Phase 2 impact analysis; Phase 3 barrier tests", PS_),
    R("R-15", "PS p.2, Sector 4", "Sector 4: The Pendulum Gauntlet (55m - 75m) Final hazard sector featuring a continuously "
      "swinging mechanical pendulum across the track before the finish line.", "S4 swinging pendulum", DD,
      "Stop before swing plane, observe 2-3 swings, fit period/phase, commit and cross in the predicted window.",
      "Software_Flowchart.png; TDD section 15", "Phase 2 Monte-Carlo timing; Phase 3 test pendulum", PS_),
    R("R-16", "PS p.3, Scoring", "Each participating team is granted 3 restart attempts within their designated operational "
      "window, with only their top performance logged for official scoring.", "3 restart attempts", DD,
      "Charging through the hub port and a single-bolt service procedure support quick turnarounds.",
      "TDD section 8.8", "Phase 3 rehearsal", PS_, summary=False),
    R("R-17", "PS p.3, Scoring", "FinalScore(Seconds) = RawRunTime + Penalties", "Score = run time + penalties", DD,
      "Reliability first, then a speed profile per sector; target top speed 2 m/s (design target, not a claim).",
      "TDD sections 11 and 14", "Phase 2 simulation", PS_, summary=False),
    R("R-18", "PS p.3, Team", "Team Size: Maximum of 6 members per team.", "Max 6 members", M,
      "Team placeholders provided for up to 6 members.", "TDD section 1", "Team to confirm", U, summary=False),
    R("R-19", "PS p.3, Timeline", "Phase 1 Registration & CAD Abstract Submission October 25, 2026",
      "Phase 1 deadline 25 Oct 2026", M, "Package prepared; date confirmed on techfest.org on 2026-10-20.",
      "research/Official_Sources_Verification.md", "Team submits before the deadline", PS_),
    R("R-20", "PS p.3, General Rules 1", "All teams must register on techfest.org to receive an official Team ID for tracking "
      "and submissions.", "Register for Team ID", M, "Team ID placeholders in all documents.", "Phase1_README.md",
      "Team action", U),
    R("R-21", "PS p.4, General Rules 2", "Instructions for specific rounds would be communicated on time via registered mail IDs",
      "Round instructions by e-mail", M, "Team to monitor the registered mailbox; format question Q2 prepared.",
      "Open_Questions_for_Organizers.md", "Team action", U, summary=False),
    R("R-22", "PS p.4, General Rules 3", "Submissions must represent the team's original work. Using external AI tools during "
      "live rounds is strictly prohibited unless judges explicitly authorize it.", "Original work; AI-tool rule", M,
      "Package drafted with AI assistance; team must review and own every decision; disclosure question Q1 prepared.",
      "Open_Questions_for_Organizers.md (Q1); Phase1_README.md", "Team review + organiser answer", U),
    R("R-23", "PS p.4, General Rules 4", "Official announcements will be posted on techfest.org. All contest queries must be "
      "submitted through the official portal's Doubt section.", "Queries via the Doubts section", M,
      "13 questions prepared for the Doubts section.", "Open_Questions_for_Organizers.md", "Team action", PS_, summary=False),
    R("R-24", "PS p.4, General Rules 6", "Autonomy: The robot must operate with 100% autonomy during its run. No manual remote "
      "control, external human intervention, or external processing offloads are allowed once the run begins.",
      "100 % autonomy, no offboard processing", M,
      "All perception, estimation and planning on the Pi 5; control on the MCU; the only RF link is the inhibit-only e-stop; "
      "development laptop disconnected during runs.", "System_Architecture.png", "Addressed in design; verification pending (Phase 3 demonstration)", PS_),
    R("R-25", "PS p.4, General Rules 7", "Sensor Restrictions: Onboard cameras must serve as the primary sensor for path "
      "tracking and gate identification. Supplementary internal sensors (IMUs, encoders, distance sensors) are permitted for "
      "stabilization.", "Camera primary; internal supplementary sensors", M,
      "Camera Module 3 Wide is the primary sensor; IMU, encoders, shell-index and steering-angle sensors are internal.",
      "System_Architecture.png; Electronics_Architecture.png", "Design review (done)", S),
    R("R-26", "PS p.4, General Rules 8", "Cone Contact Penalties: Touching, knocking over, or running over any track cone incurs "
      "a +5 second penalty per instance added to the total run time.", "+5 s per cone contact", DD,
      "Lane-centring on both boundaries with margin; lean steering +/-22.9 deg static authority.",
      "TDD sections 10 and 13", "Phase 2 simulation once track/gate width is known (Q4)", PS_),
    R("R-27", "PS p.4, General Rules 9", "Emergency Stop: Every robot must have an operational wireless emergency kill switch "
      "that can immediately stop all motor actuation during a run.", "Wireless kill switch stops all actuation", M,
      "Heartbeat e-stop with independent supervisor: contactor open + driver PWM inputs gated to zero + changeover brake relays (break-before-make); latched; all "
      "actuators downstream of the contactor.", "Power_Distribution.png; Electronics_Architecture.png; TDD section 16",
      "Addressed in design; verification pending (Phase 2 bench latency/fail-safe tests, Phase 3 inspection)", PS_),
    R("R-28", "PS p.4, General Rules 10", "Did Not Finish (DNF): A run is marked as DNF if the robot fails to move, loses "
      "complete control, suffers total power failure, or cannot clear an obstacle.", "Avoid DNF conditions", DD,
      "Fail-safe stops, torque headroom management, ballast tuning, fused branches, BMS; risks tracked.",
      "TDD section 19", "Phase 2/3", PS_, summary=False),
    R("T-01", "TPL Team identification", "Team ID & Name: [Enter Team ID and Team Name] Institution: [Enter College / "
      "University Name] Team Lead Contact: [Name | Email | Phone Number]", "Team identification", M,
      "Placeholders present; never invented.", "Phase1_CAD_Abstract", "Team to fill", U),
    R("T-02", "TPL 1", "CAD Renders Provided: [Insert Isometric View Render Link/Image] [Insert Cross-Sectional View Render "
      "Link/Image]", "Isometric + cross-section renders", M, "Both renders generated from the CAD.",
      "Isometric_Render.png; Cross_Section.png", "Visual inspection (done)", S),
    R("T-03", "TPL 1", "Shell Integrity: Material: [e.g., Polycarbonate / Carbon Fiber / Fiberglass] Exact Outer Diameter: "
      "[e.g., 2.2 feet]", "Shell material and exact OD", M, "Clear PC, 3 mm; OD 700.0 mm (2.297 ft); 700.7 mm over tape.",
      "Dimensioned_Views.png", "CAD (done)", S),
    R("T-04", "TPL 1", "The 0.5-Foot Limit Rule: [Dimension and confirm that all external sensor mounts or camera pods extend "
      " beyond the outer shell diameter]", "0.5 ft rule confirmation", M, "No external mounts or pods (0 mm).",
      "Dimensioned_Views.png", "CAD (done)", S),
    R("T-05", "TPL 1", "CoG & Drive Mechanism: [Explain how the internal drive/pendulum mechanism moves and balances the robot. "
      "Provide initial calculated CoG coordinates relative to the geometric center]", "CoG coordinates + drive explanation", M,
      "CG (+1.4, -0.4, -87.2) mm from the CAD mass table; mechanism explained.", "Center_of_Gravity.png; mass_table.csv",
      "Reproducible calculation (done); hardware CG measurement in Phase 3", S),
    R("T-06", "TPL 1", "Ramp-Climbing Capability: [Detail motor torque calculations and selection chosen to conquer the hardest "
      " ramp]", "Motor torque calculation + selection", M,
      "Quasi-static torque table, pendulum reaction limit, run-up speeds, motor class and selection targets.",
      "Ramp_Capability.png; abstract section 1", "Phase 2 final sizing after ramp geometry (Q3)", PS_),
    R("T-07", "TPL 2", "Electrical Block Diagram: [Insert schematic / block diagram showing power distribution, microcontroller, "
      "sensor interfaces, and motor drivers]", "Electrical block diagram", M, "System, electronics and power diagrams.",
      "System_Architecture.png; Electronics_Architecture.png; Power_Distribution.png", "Visual inspection (done)", S),
    R("T-08", "TPL 2", "Power Source & BMS: Confirmation: Strictly battery-powered (Yes/No) Chemistry, Voltage & Capacity: "
      "[e.g., Lithium Polymer, 24V, 5000mAh] Safeguards: [Detail onboard BMS and low-voltage cutoff (LVC) safeguards]",
      "Battery, BMS and LVC", M, "Yes; Li-ion 6S1P 21.6 V 4.5 Ah; BMS with LVC + software LVC stop + fuses.",
      "Power_Distribution.png", "Design review (done); thresholds with the selected BMS in Phase 2", S),
    R("T-09", "TPL 2", "Actuation & Motor Control: Motor Specs: [RPM, Stall Torque] Driver Boards: [Model and specs for "
      "propulsion and steering drivers]", "Motor specs + driver boards", M,
      "Target specs per drive motor at 24 V: >= 320 rpm no-load, >= 2 N m rated continuous, >= 4 N m stall (operating point 1.66 N m at 55 rpm, checked at 18 V); MDD20A / MD10C class drivers.",
      "Abstract section 2; Electronics_Architecture.png", "Phase 2 part selection", PS_),
    R("T-10", "TPL 2", "Safety Fail-Safes: Wireless Kill-Switch: [Outline wireless emergency kill-switch mechanism] Manual "
      "Disconnect: [Outline manual external power disconnect switch location]", "Kill switch + external manual disconnect", M,
      "Heartbeat e-stop (3 channels); anti-spark arming plug in the non-rotating left polar hub.",
      "Dimensioned_Views.png (left view); Power_Distribution.png", "Design review (done)", S),
    R("T-11", "TPL 3", "Software Flowchart: [Insert architecture flowchart showing state machine diagram and vision AI stack]",
      "Software flowchart (state machine + vision stack)", M, "Concept-level flowchart.", "Software_Flowchart.png",
      "Visual inspection (done)", S),
    R("T-12", "TPL 3", "Primary Vision Processing / State Estimation & Control / Obstacle Handling Logic (Sector 4)",
      "Vision, estimation, Sector 4 logic", M, "Concept descriptions in abstract section 3 and TDD sections 13-15.",
      "Phase1_CAD_Abstract; TDD", "Algorithms validated in Phase 2", PS_),
]


RISKS = [
    ["R1", "Ramp steeper than the pendulum limit (10.7 deg baseline)", "M", "H",
     "Ballast to 6 plates (13.6 deg incl. rolling resistance), run-up energy strategy (estimate only), tape grip; ramp geometry asked (Q3); Phase 2 dynamic model"],
    ["R2", "Entry lip or drop at the ramp ends stalls or shocks the robot", "M", "H",
     "Approach speed, software torque limit, compliant gear mounts; question Q3; drop test in Phase 3"],
    ["R3", "Image quality through scratched/dirty PC, glare", "M", "M",
     "Replaceable PU tape band, seam mask, adaptive thresholds + optional CNN, spare hemisphere; gyro/odometry bridging"],
    ["R4", "Pendulum pitch oscillation on accel/brake", "H", "M",
     "Pitch-stabilised camera, active damping in the 500 Hz loop, speed ramps; Phase 2 model"],
    ["R5", "Lean steering too weak at low speed -> cone contacts", "M", "M",
     "+/-22.9 deg static lean authority, early lateral corrections, speed planning; Phase 2 turning-radius model"],
    ["R6", "Barrier impact causes heading loss or damage", "M", "M",
     "Heavy low CG, gyro heading hold, robust axle and bearings, torque limiting; Phase 2 impact loads"],
    ["R7", "Station-keeping before the pendulum (pendulum robots rock)", "M", "H",
     "Encoder + IMU hold loop, hold line set back from the swing plane; Phase 2 validation"],
    ["R8", "E-stop link range or interference in the arena", "L", "H",
     "Heartbeat fail-safe (loss = stop), internal antenna placed high behind the clear upper shell (no external mount), range test; sub-GHz fallback"],
    ["R9", "700 mm PC hemispheres: sourcing, wall uniformity, lead time", "M", "H",
     "Early supplier enquiries; diameter is a parameter (re-run CAD); acrylic/PETG fallback"],
    ["R10", "Real masses/CG differ from estimates (3.0 kg placeholders)", "M", "M",
     "Adjustable ballast, CG suspension test, parametric CAD update"],
    ["R11", "Pi 5 thermal throttling in a sealed shell", "M", "M",
     "Active cooler + Al plate heat spreader, temperature monitoring; Phase 2 thermal estimate"],
    ["R12", "Gear mesh misalignment from flange compliance", "L", "M",
     "Bearing-referenced flanges, slotted motor arms, POM ring gear; inspection at assembly"],
    ["R13", "Rule interpretation (diameter measurement, isolation, AI use)", "M", "H",
     "Doubts-section questions Q1, Q5, Q8 before submission"],
    ["R14", "Li-ion pack safety under impact", "L", "H",
     "Cylindrical cells in a rigid padded tray, BMS, 40 A fuse, fire-safe charging bag"],
]


BOM_KEY = {
    "SH-01": "SHELL-HEMI", "SH-02": "SHELL-HEMI", "SH-03": "SPIGOT-BAND", "SH-04": "PU-TAPE",
    "SH-10": "POLE-FLANGE", "SH-11": "POLE-FLANGE", "SH-20": "RING-GEAR", "SH-21": "RING-GEAR",
    "SH-30": "POLE-BEARING", "SH-31": "POLE-BEARING", "ST-01": "AXLE", "ST-02": "HUB-LEFT", "ST-03": "HUB-RIGHT",
    "ST-04": "PRELOAD-BOLT", "PW-04": "ARMING-PLUG", "PW-05": "CHARGE-PORT", "SA-03": "STATUS-LED",
    "ST-10": "SIDE-PLATE", "ST-11": "SIDE-PLATE", "ST-12": "END-PLATE", "ST-13": "END-PLATE",
    "ST-14": "AXLE-CLAMP", "ST-15": "AXLE-CLAMP", "ST-20": "FASTENERS",
    "DR-01": "GEARMOTOR", "DR-02": "GEARMOTOR", "DR-03": "PINION", "DR-04": "PINION", "DR-05": "MOTOR-ARM",
    "DR-06": "MOTOR-ARM", "SG-01": "PIVOT-SHAFT", "SG-02": "PIVOT-BEARING", "SG-03": "PIVOT-BEARING",
    "SG-04": "STEER-MOTOR", "SG-10": "TILT-STOP", "SG-11": "TILT-STOP", "SG-12": "TILT-STOP", "SG-13": "TILT-STOP",
    "SE-01": "CAMERA", "SE-02": "CAM-SERVO", "SE-03": "IMU", "SE-04": "STEER-ANGLE", "SE-05": "HALL-INDEX",
    "CP-01": "PI5", "CP-02": "MCU-BOARD", "DV-01": "DRIVE-DRIVER", "DV-02": "STEER-DRIVER", "PW-01": "PDB",
    "PW-02": "DCDC-5V", "PW-03": "DCDC-6V", "SA-01": "CONTACTOR", "SA-02": "BRAKE-RELAYS", "SA-04": "ESTOP-SUPERVISOR",
    "HR-01": "HARNESS", "HR-02": "HARNESS", "HR-03": "HARNESS", "HR-04": "HARNESS", "HR-05": "HARNESS",
    "BB-01": "BOB-HANGER", "BB-02": "BOB-HANGER", "BB-03": "BOB-TRAY", "BB-04": "BALLAST-BRACKET",
    "BB-05": "BALLAST-BRACKET", "PW-10": "BATTERY", "BL-01": "BALLAST-PLATE", "BL-02": "BALLAST-PLATE",
    "BL-03": "BALLAST-PLATE", "BL-04": "BALLAST-PLATE",
}

BOM_NAME = {
    "SHELL-HEMI": "Clear polycarbonate hemisphere, OD 700 mm, 3 mm wall (R has 4 rim notches)",
    "SPIGOT-BAND": "Equatorial spigot band + 4 key tabs, clear PC 5 mm",
    "PU-TAPE": "Clear PU protective tape band, 0.35 mm (applied in narrow strips)",
    "POLE-FLANGE": "Pole flange with bearing seat (PA12-CF print + Al insert)",
    "RING-GEAR": "Ring gear 72T m1.5, face 12 mm (POM-C), bored",
    "POLE-BEARING": "Deep-groove bearing 61908-2RS (6908), 40 x 62 x 12 mm",
    "AXLE": "Stationary axle tube 30 x 3 mm, 6061-T6, 624 mm",
    "HUB-LEFT": "Left polar hub (non-rotating, flush): cap, cup, boss",
    "HUB-RIGHT": "Right polar hub (non-rotating, flush)",
    "PRELOAD-BOLT": "M12 preload bolt + disc-spring stack + axle end plug",
    "ARMING-PLUG": "Anti-spark arming plug + receptacle (XT90-S class) - manual disconnect",
    "CHARGE-PORT": "Charge port receptacle (BMS charge input)",
    "STATUS-LED": "Status LED (RGB, panel)",
    "SIDE-PLATE": "Stator side plate, 6061 3 mm, laser-cut",
    "END-PLATE": "Stator front/rear plate, 6061 3 mm, laser-cut",
    "AXLE-CLAMP": "Split axle clamp block, 6061",
    "FASTENERS": "Fasteners, angle brackets, standoffs (allowance)",
    "GEARMOTOR": "24 V brushed DC planetary gearmotor with Hall encoder, 42 mm class",
    "PINION": "Pinion 18T m1.5, steel",
    "MOTOR-ARM": "Motor arm clamped to axle, 6061 6 mm (slotted)",
    "PIVOT-SHAFT": "Steering pivot shaft, 12 mm steel",
    "PIVOT-BEARING": "Pivot bearing 6001-2RS + housing",
    "STEER-MOTOR": "Self-locking worm gearmotor (steering)",
    "TILT-STOP": "Rubber tilt end-stop",
    "CAMERA": "Raspberry Pi Camera Module 3 Wide",
    "CAM-SERVO": "Metal-gear micro servo (camera pitch)",
    "IMU": "9-DoF IMU breakout",
    "STEER-ANGLE": "Magnetic angle sensor + magnet (steering pivot)",
    "HALL-INDEX": "Hall sensor + magnet (shell index)",
    "PI5": "Raspberry Pi 5, 8 GB + active cooler",
    "MCU-BOARD": "Motor-control MCU carrier board (RP2350 class)",
    "DRIVE-DRIVER": "Dual-channel brushed DC motor driver, 20 A/ch",
    "STEER-DRIVER": "Single-channel brushed DC motor driver, 13 A",
    "PDB": "Power distribution board: fuses, bus monitor, bus bars",
    "DCDC-5V": "DC-DC converter 24 V -> 5.1 V / 5 A",
    "DCDC-6V": "DC-DC converter 24 V -> 6 V / 3 A",
    "CONTACTOR": "Motor-power contactor / relay, NO, 24 V coil, 40 A",
    "BRAKE-RELAYS": "Dynamic-brake relays (NC) + braking resistors",
    "ESTOP-SUPERVISOR": "E-stop receiver + safety supervisor board + watchdog IC",
    "HARNESS": "Wiring harness and cable-routing allowance",
    "BOB-HANGER": "Steering-bob hanger plate, 6061 5 mm",
    "BOB-TRAY": "Battery tray, 6061 4 mm",
    "BALLAST-BRACKET": "Ballast clamp bracket + 2 x M6 tie-rods",
    "BATTERY": "Battery 6S1P 21700 Li-ion + 6S BMS + wrap",
    "BALLAST-PLATE": "Ballast arc plate, laser-cut 8 mm steel, R215-R265 about the pivot axis",
}

BOM_INFO = {
    "SHELL-HEMI": dict(part="to be sourced (thermoformed PC dome)", source="design parameter",
                       note="supplier, tolerance and wall uniformity to be confirmed (risk R9)"),
    "PU-TAPE": dict(part="3M 8671 / 8671HS class", source="3M TDS: transparent TPU, 0.014 in"),
    "POLE-BEARING": dict(part="61908-2RS (6908-2RS)", source="ISO 15 standard dimensions; mass estimated"),
    "GEARMOTOR": dict(part="TBD in Phase 2", source="targets: >= 320 rpm no-load @ 24 V, >= 2 N m rated continuous, >= 4 N m stall",
                      note="PLACEHOLDER envelope 42 x 145 mm"),
    "STEER-MOTOR": dict(part="JGY-370 worm class (TBD)", source="target >= 4 N m, >= 30 rpm", note="PLACEHOLDER"),
    "CAMERA": dict(part="Raspberry Pi Camera Module 3 Wide", source="RPi product brief (2024): 25 x 24 x 12.4 mm, 102 x 67 deg",
                   note="mass estimated"),
    "PI5": dict(part="Raspberry Pi 5 (8 GB)", source="RPi product brief: 85 x 56 mm, 5 V / 5 A", note="mass estimated"),
    "MCU-BOARD": dict(part="Raspberry Pi Pico 2 (RP2350) on custom carrier (reference)", source="class-level PH"),
    "DRIVE-DRIVER": dict(part="Cytron MDD20A class", source="retailer listing: 6-30 V, 20 A cont./ch, 60 A peak"),
    "STEER-DRIVER": dict(part="Cytron MD10C class", source="retailer listing: 5-30 V, 13 A cont."),
    "IMU": dict(part="BNO085 class (reference)", source="class-level PH"),
    "STEER-ANGLE": dict(part="AS5600 class (reference)", source="class-level PH"),
    "ESTOP-SUPERVISOR": dict(part="ESP32-C3 class + TPS3823 class watchdog (reference)", source="class-level PH"),
    "BATTERY": dict(part="6 x Molicel INR-21700-P45B + 6S BMS (>= 40 A)",
                    source="Molicel datasheet: 4.5 Ah, 45 A cont., <= 70 g, 21.4 x 70.0 mm",
                    note="21.6 V nom., ~97 Wh (< 100 Wh)"),
    "ARMING-PLUG": dict(part="XT90-S anti-spark class", source="class-level PH"),
    "RING-GEAR": dict(part="stock m1.5 72T POM spur gear, re-bored", source="CAD volume (simplified teeth)"),
    "PINION": dict(part="stock m1.5 18T steel spur gear", source="CAD volume (simplified teeth)"),
}

OFF_ROBOT = [
    ("ESTOP-TX", "Handheld wireless e-stop transmitter (latching mushroom switch, ESP32 class)", 1),
    ("CHARGER", "6S Li-ion CC/CV charger, 25.2 V, <= 4.5 A", 1),
    ("SERVICE-STAND", "Service stand (holds the ball left-hub-down for opening)", 1),
    ("GAUGES", "Go/no-go ring gauges 2.0 ft and 2.5 ft (QC)", 2),
]
