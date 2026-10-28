<p class="t1">Techfest 2026-27</p>
<p class="t2">The Wrecking Ball Challenge</p>
<p class="t3">Round 1: Submission Template</p>

## TEAM IDENTIFICATION

- **Team ID & Name:** TM-47C20DF8A48 \| StarDust
- **Institution:** Madan Mohan Malaviya University of Technology, Gorakhpur
- **Team Lead Contact:** Abhishek Kumar Singh \| abhishekkrsingh2345@gmail.com \| 8429339626

## 1. Mechanical Architecture & Enclosure Design (CAD Evidence)

- **CAD Renders Provided:**
    - *Isometric View Render:* Figure 1 below (full-resolution files and STEP model: [GOOGLE DRIVE LINK])
    - *Cross-Sectional View Render:* Figure 2 below (true section of the CAD solids on the mid-plane)

![Isometric view render](figures/Isometric_Render.png){: .fig}
*Figure 1 - Isometric view render of the WB-700 CAD assembly (68 parts; shell drawn translucent).*

![Cross-sectional view render](figures/Cross_Section.png){: .fig}
*Figure 2 - Cross-sectional view render on the mid-plane y = 0. Dark, black-outlined faces are true section faces.*

- **Shell Integrity:**
    - *Material:* **Polycarbonate**: two clear thermoformed PC hemispheres, 3.0 mm nominal wall, joined
      on the equator by a clear PC spigot band and clamped by a single M12 bolt through the axle. A
      replaceable clear polyurethane protective tape band (0.35 mm, 3M 8671 class) covers the rolling band
      and seam. PC is chosen for impact toughness and optical clarity, because the camera looks out
      through the shell.
    - *Exact Outer Diameter:* **700 mm = 2.297 ft** (shell); **700.7 mm = 2.299 ft**
      over the tape band. Measured on the CAD in every direction, all calipers are
      696.3-700.7 mm (2.284-2.299 ft), strictly inside 2.0-2.5 ft, with
      86.7 mm and 61.3 mm margin. The rule still holds with ±7 mm forming tolerance.
- **The 0.5-Foot Limit Rule:** **No external sensor mounts or camera pods. Protrusion beyond the outer
  shell: 0 mm, against the 152.4 mm (0.5 ft) limit.** The camera, computer, actuators, battery and
  electronics are all inside the shell. The two polar hubs are flush and recessed 1.0 mm below the
  sphere surface, so the largest non-shell feature sits 1.0 mm *inside* the surface (Figure 3).

![Dimensioned views](figures/Dimensioned_Views.png){: .fig}
*Figure 3 - External dimensions and envelope check, computed from the CAD meshes.*

- **CoG & Drive Mechanism:** a **two-axis pendulum (barycentre-offset) drive**. A gravity-held internal
  frame, the *stator*, hangs on a stationary hollow axle; the shell turns around it on two 61908 pole
  bearings. **Drive:** two 24 V gearmotors on the stator turn 72-tooth ring gears bolted to the
  hemisphere poles (4:1). The reaction swings the stator forward, the CG moves ahead of the
  contact point, and the ball rolls. **Steering:** a self-locking worm gearmotor tilts a heavy *steering
  bob* (6S battery + laser-cut steel ballast arcs, 5.34 kg) ±30° about a pivot 45 mm below the axle.
  This leans the ball about ±22.9° and it turns (Figure 5). The lean is a static estimate; turning
  radius and gate navigation are Phase 2 results. At both ±30° extremes the frame and bob stay at least
  20.0 mm from the shell, with no clashes. **Axle and shell joint:** the right hub's M12 bolt, with
  disc springs, threads into the stationary axle and draws the two hubs together. Each hub's boss carries a
  61908 bearing inner race, and the outer races sit in pole flanges bonded and screwed to the hemispheres.
  The light, spring-limited axial preload therefore runs hub → bearing → flange → hemisphere and closes the
  equatorial spigot joint, while the shell still turns freely on the bearings. The ring gears bolt to the
  flanges, so gear alignment follows the bearing axis. Bearing shoulders, spacers and circlips are detailed
  in Phase 2. **Balance:** the stator and bob (10.15 kg) hang
  146.2 mm below the axle as one pendulum, which gives a strong restoring moment; the MCU adds
  active pitch damping, and a servo keeps the camera at a constant look-down angle.
  **Initial calculated CoG relative to the geometric centre (X forward, Y left, Z up):
  (x, y, z) = (+1.4, -0.4, -87.2) mm, total mass 17.00 kg.** This comes from the CAD mass table
  (Figure 4). 3.03 kg of the total is placeholder hardware, and the ballast (2-6 plates) tunes
  the CG from -61.9 to -107.0 mm.

![Centre of gravity](figures/Center_of_Gravity.png){: .fig}
*Figure 4 - Component CGs (marker area proportional to mass), system CG and pendulum CG from the CAD mass table.*

![Steering mechanism](figures/Steering_Mechanism.png){: .figwide}
*Figure 5 - Steering by bob tilt at -30°, 0° and +30°: pivot, sideways CG shift, static lean and clearance to the shell.*

- **Ramp-Climbing Capability:** *preliminary and conditional. Techfest gives the ramp heights (0.2, 0.4
  and 0.8 ft = 60.96, 121.92 and 243.84 mm) but not their slopes or entry geometry, so torque is given
  against angle.* Required shell torque **T = M g R (sin a + c_rr cos a)**, with M = 17.00 kg,
  R = 0.350 m and c_rr = 0.03 (assumed): **11.9 N m at 10°, 16.8 N m at 15°, 21.6 N m at
  20°.** A pendulum drive can react at most **m_p e g sin(phi)** = 14.6 N m (pendulum horizontal) or
  12.6 N m at the 60° working limit. Setting the two equal, including rolling resistance, gives a
  **steady climbing limit of about 10.7°** with 4 ballast plates (7.1-13.6° with 2-6
  plates). For a steeper ramp, the energy needed for the 0.8 ft rise corresponds to a run-up of about
  **1.31 m/s at 20° and 1.53 m/s at 30°** (Figure 6). These are energy estimates only: they do not
  show that the robot keeps traction, survives the ramp entry or stays controllable at the crest, which
  Phase 2 checks.
  **Motor operating points** (per motor, at the gearmotor output; 18T/72T m1.5 spur stage, 4:1, 95 %
  efficient): steady climb at the 10.7° limit needs **1.66 N m continuous at 55 rpm**
  (0.5 m/s, assumed); cruising at 2.0 m/s needs 0.23 N m at 218 rpm; holding the
  pendulum horizontal needs 1.91 N m for a short time.
  **Selection:** 2 × 24 V brushed DC planetary gearmotors (42 mm class) with Hall encoders. **Targets per
  motor at 24 V: rated (continuous) ≥ 2 N m, stall ≥ 4 N m, no-load ≥ 320 rpm.** At the 18.0 V
  minimum pack voltage this still gives about 3.0 N m stall, 240 rpm unloaded (enough for
  218 rpm at cruise load) and about 107 rpm at the climb torque. Software caps
  the current. The exact part is fixed in Phase 2 once the ramp geometry is confirmed.

![Ramp capability](figures/Ramp_Capability.png){: .fig}
*Figure 6 - Required vs. available shell torque, and run-up speed for the 0.8 ft (0.244 m) rise. Preliminary and quasi-static; run-up values are energy estimates only.*

## 2. Electrical & Power System Architecture

- **Electrical Block Diagram:** Figure 7 (system block diagram), Figure 8 (power distribution) and
  Figure 9 (microcontroller, sensor interfaces and motor drivers).

![System block diagram](figures/System_Architecture.png){: .figwide}
*Figure 7 - System block diagram: information flow, power and the independent hardware safety path (red).*

![Power distribution](figures/Power_Distribution.png){: .figwide}
*Figure 8 - Power distribution: every actuator is downstream of the e-stop contactor.*

![Electronics architecture](figures/Electronics_Architecture.png){: .figwide}
*Figure 9 - Microcontroller, sensor interfaces, motor drivers and safety chain (PH = placeholder part class).*

- **Power Source & BMS:**
    - *Confirmation:* Strictly battery-powered: **YES.** No tether, external power line or remote power
      feed. Charging uses a hub port between runs, with the arming plug removed.
    - *Chemistry, Voltage & Capacity:* **Lithium-ion 21700 (Molicel P45B), 6S1P: 21.6 V nominal
      (18.0-25.2 V), 4.5 Ah, ≈97 Wh.** The pack is kept under 100 Wh for transport.
    - *Safeguards:* the 6S BMS provides cell-level **low-voltage cut-off (LVC)**, over-voltage,
      over-current, short-circuit and temperature protection, and balancing. There is a 40 A main fuse plus
      branch fuses (30 A actuators, 5 A logic, 5 A steering). A bus voltage/current monitor lets the MCU
      make a controlled stop at a software LVC threshold *above* the BMS cut-off.
- **Actuation & Motor Control:**
    - *Motor Specs:* drive: 2 × 24 V planetary gearmotors, **≥ 320 rpm no-load, ≥ 2 N m rated (continuous),
      ≥ 4 N m stall** at 24 V; operating point 1.66 N m at 55 rpm. Steering: self-locking worm gearmotor (JGY-370 class), **≥ 30 rpm, ≥ 4 N m**. Camera: 6 V
      metal-gear micro servo. These are target specifications; parts are confirmed in Phase 2.
    - *Driver Boards:* propulsion: **Cytron MDD20A class** (dual channel, 6-30 V, 20 A continuous / 60 A
      peak per channel), one channel per drive motor. Steering: **Cytron MD10C class** (5-30 V, 13 A
      continuous). Both take PWM/DIR from an RP2350-class motor MCU. The 25.2 V maximum is inside the
      30 V rating, and a TVS diode with bulk capacitance clamps regenerative spikes.
- **Safety Fail-Safes:**
    - *Wireless Kill-Switch:* a handheld transmitter with a **latching mushroom button** sends a 2.4 GHz
      heartbeat at 20 Hz. An **independent safety supervisor** (its own MCU and receiver) allows motion
      only while valid heartbeats arrive *and* a hardware watchdog confirms the motor MCU is alive. A STOP
      press, heartbeat loss (> 250 ms), watchdog trip or supervisor fault does three fail-safe things:
      **(A) opens the normally-open motor-power contactor**, removing power from every driver and actuator;
      **(B) gates the PWM inputs of both Cytron drivers to zero** through a supervisor-controlled gate with
      pull-downs, so the drivers cannot command the motors even if the MCU misbehaves (the MDD20A and
      MD10C have PWM/DIR inputs only, with no enable pin); **(C) releases changeover brake relays.** Each
      relay's normally-open side connects a drive motor to its driver and its normally-closed side shorts
      the motor through a braking resistor. Break-before-make means a motor is never connected to the
      driver and to the short at the same time. The stop latches until a manual re-arm, and the link carries
      no driving commands. **This stops all motor actuation immediately; it does not stop the sphere
      instantly.** The ball coasts, slowed by rolling resistance and the shorted motors, and on a slope it
      can still roll. Phase 2 quantifies the stopping distance.
    - *Manual Disconnect:* an **anti-spark arming plug (XT90-S class) recessed in the LEFT polar hub**.
      The hub does not rotate and is flush with the sphere, so it can be reached from outside whenever
      the ball is stationary. Pulling the plug isolates the battery from all loads (Figure 3, left view).

## 3. Software & Vision-Based Navigation Pipeline

- **Software Flowchart:** Figure 10 (vision / AI stack and course state machine).

![Software flowchart](figures/Software_Flowchart.png){: .figwide}
*Figure 10 - Vision / AI stack and course state machine (concept; algorithms are validated in Phase 2).*

- **Primary Vision Processing:** a Raspberry Pi Camera Module 3 Wide (102° × 67°) on the stator, at
  1280 × 720 and 50 fps, is calibrated through the installed shell. A ray-cast over the CAD shows
  **0.0 % of the view blocked** by internal parts in all 9 checked poses (bob at -30°,
  0° and +30°, camera servo at 0°, 12° and 24° down). The stator only pitches about the axle, the same
  axis the shell turns about, so the clear seam band stays in a fixed image stripe (6.7-7.1 %
  of the image) that is masked in software. These are CAD sightlines only: image quality through curved,
  scuffed polycarbonate is untested and is checked in Phases 2 and 3. IMU attitude plus the servo angle give
  a ground-plane homography. Adaptive HSV segmentation finds **yellow (left) and red (right) cones**, with
  thresholds tuned on the Sector 1 chevron gates. RANSAC boundary fits give the lane centre, heading
  error and gates. An optional lightweight CNN (YOLO-nano class) cross-checks under poor lighting.
- **State Estimation & Control:** an EKF fuses the vision lane measurements, the IMU (stator pitch,
  roll and yaw rate) and both drive encoders (shell rotation relative to the stator, plus a
  once-per-revolution shell index). It estimates distance, lateral offset, heading, speed and pendulum
  pitch. The MCU closes 500 Hz loops for drive speed with pendulum-pitch damping, the steering-bob angle
  and camera stabilisation. The Pi 5 runs lane-centring (a lean command) and the sector speed profiles.
  In the wrecking zone the robot holds heading on the gyro and border cones and keeps its momentum.
- **Obstacle Handling Logic (Sector 4):** the robot **stops at a hold line before the swing plane**. On a
  level floor, holding needs almost no drive torque, so the encoder and IMU loop can keep station. It
  tracks the pendulum bob in a region of interest over 2-3 swings and fits x(t) = A sin(2πt/T + φ) to get
  period, amplitude and phase with a confidence estimate. **Crossing policy:** it commits only if the
  predicted clear interval is at least t_req = t_delay + t_cross + t_margin, where t_cross is the time for
  the whole 0.70 m sphere to leave the hold line and clear the swing corridor. With the CAD-based launch
  acceleration of about 1.44 m/s² (pendulum at 60°), a 0.3 m hold distance, a 0.5 m corridor
  (assumed; the pendulum size is not yet published) and a 1.5 m/s speed cap, t_cross ≈ 1.5 s. With
  0.15 s sensing delay and a 0.5 s margin, it needs a clear window of about 2.2 s. If confidence drops
  before the commit point, it stays at the hold line and re-tracks for another cycle. After committing it
  does not stop or reverse inside the corridor, because continuing clears it sooner than backing out.
  The crossing policy never overrides emergency stop or a detected safety fault; safety shutdown remains
  active in every operating state.

*Supporting material (optional): Phase 1 Technical Design Document, CAD model (STEP) and full-resolution
figures at [GOOGLE DRIVE LINK]. All values are CAD-based design estimates or preliminary calculations;
no physical testing has been carried out yet.*
