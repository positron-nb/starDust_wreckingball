# Mechanism Research and Architecture Selection (STEPS 3–4)

Scope: just enough research to make a defensible Phase 1 decision. Detailed dynamics and actuator
sizing are Phase 2 work (see `FUTURE_PHASES_STANDBY.md`).

## 1. Reference projects reviewed

| Project | What it really is (from its repository) | CAD present | Licence | What we took / did not take |
|---|---|---|---|---|
| **SphBot** — <https://github.com/alirezaahmadi/SphBot> | Pendulum-driven spherical robot (AUT). README: three units: shell (two halves), inside drive unit and pendulum mechanism. M1 drives the sphere forward and M2 applies a leaning torque that turns it. Gear drive. Android-app control, wireless camera for remote monitoring. Paper: Kolbari, Ahmadi, Bahrami, Janati, *Impedance estimation and motion control of a pendulum-driven spherical robot*, IcRoM 2018, pp. 6–11. | No CAD files in the repo (only `Code/`, `PCB -final/`). | **MIT**, © 2019 Alireza Ahmadi | Confirms that a split shell, gear-driven drive axis and lean steering are a proven pairing. No files reused. |
| **Rollie** — <https://github.com/dformoso/rollie> | 120 mm gravity-stabilised ball. A weighted **stator** hangs as a pendulum. Two Pololu 50:1 micro gearmotors on the stator drive the shell halves through 75 mm printed slewing bearings. Camera Module 3 Wide and BNO055 on the stator look out through an **equatorial gap**. Pi Zero 2 W + Pico 2 W. v0.1 is remote-controlled and its IMU loop is a stub. | Yes: OpenSCAD sources (`cad/*.scad`) + STL. | **MIT**, © 2025 Daniel Martinez Formoso | Confirms the "stator inside a rotating shell" idea and Camera Module 3 Wide on the pendulum. A 120 mm toy-scale part set does not scale to a 15 kg, 700 mm robot. No files reused. |
| **Spherical-Robot** — <https://github.com/Integral-Robotics-Lab/Spherical-Robot> | Pendulum-based ball. Two DC motors for forward/back, a third DC motor swings a pendulum for heading. NodeMCU + ESP32-CAM, Wi-Fi control. README numbers lack context (e.g. torque quoted in kg·m; kinematics written for a differential-drive vehicle). | No CAD files listed. | **None found** (all rights reserved by default) | Background only. Nothing reused. |

Other precedent: Rotundus **GroundBot**, a commercial 60 cm, 25 kg, hermetically sealed ball
"driven via a patented pendulum-based mechanism" with a pair of cameras (New Atlas, 24 Oct 2011,
<https://newatlas.com/rotundus-groundbot/20259/>). Literature: Chase & Pandya (2012) classify
spherical-robot drives as barycentre offset, shell transformation and conservation of angular
momentum. Halme et al. (1996) introduced the inside-drive-unit (IDU) ball. Ylikorpi, Halme &
Forsman (2017) model obstacle crossing of pendulum-driven balls. Full references are in the
Technical Design Document.

**Originality statement.** The WB-700 layout described here (a stationary through-axle stator,
twin belt drives into both shell poles, a steering bob of laser-cut arc ballast plates, and flush
non-rotating polar hubs carrying the manual disconnect) is our own integration for this track. No
CAD, code or text from the repositories above is copied.

## 2. Candidate drive principles

* **A. Two-axis pendulum (barycentre offset).** A transverse axle carries an internal pendulum.
  Rotating the shell relative to the pendulum lifts the pendulum and offsets the centre of mass,
  which rolls the ball. A second actuator tilts a mass sideways to lean and steer.
* **B. Internal drive unit (IDU / "hamster wheel").** A differential-drive cart rolls on the inside
  of the shell (optionally pinned by sprung top idlers). Turning the cart steers the ball.
* **C. Twin hemisphere differential (Rollie-type).** Two shell halves driven independently about a
  common axle, with a stationary equatorial band. Steering comes from the speed difference.

### Physics used for the comparison (quasi-static, flat-shell idealisation)

* Pendulum reaction limit on an incline α (any barycentre-offset drive):
  `sin α_max = (m_p · e / (M · R)) · sin φ_max`, where `m_p·e` is the first moment of all
  internally moving mass about the shell centre, `M` the total mass, `R` the rolling radius and `φ`
  the pendulum swing angle. The drive torque needed is `T ≈ M g R (sin α + c_rr cos α)`. The
  pendulum (or cart) must be able to react this torque by gravity, so **extra motor torque
  beyond `m_p·e·g` cannot be used**.
* Step or lip of height h (quasi-static): the centre of mass must move horizontally by
  `√(2Rh − h²)` to roll over the edge (20 mm lip at R = 350 mm → 117 mm). Momentum reduces this.
* IDU traction: the cart wheels must not slip on the inside of the shell, so `μ_inner ≥ tan φ_cart`
  at the operating cart angle (≈0.84 at 40°). This is unreliable on clean or dusty polycarbonate.
* Lean steering with a bob pivoting at depth `d_p` under the axle (small angles):
  `γ/β ≈ m_b L_b / (m_f e_f + m_b e_b)`, where `L_b = e_b − d_p`. A pivot close to the centre and
  a heavy, low bob give the most lean per degree of bob tilt.

## 3. Comparison (score 1 = poor … 5 = good, for THIS track)

| Criterion | A. Two-axis pendulum | B. Internal wheel / IDU | C. Twin-hemisphere differential |
|---|---|---|---|
| Mechanical plausibility at 700 mm / ~15 kg | **5** — positive belt/gear drive into the shell; widely built | 3 — needs sprung idlers to keep the cart seated at this size | 3 — large-diameter bearings carry all loads; equatorial gap at ground contact |
| Steering authority | 3 — lean steering; no turn-in-place, but adequate for gate-to-gate corrections on a linear track | **5** — turns in place | **5** — differential yaw |
| Traction / torque path | **5** — no internal slip; torque limited only by `m_p·e` | 2 — wheel-to-shell slip on ramps and impacts; dust degrades μ | 4 — positive drive, but two edge contacts at the gap |
| Mass distribution / CG | 4 — battery and ballast can sit within ~30 mm of the shell | **5** — whole cart sits on the shell bottom | 3 — stator mass straddles the gap |
| Packaging | 4 — swing envelope is a sphere about the centre (easy to prove clearance) | 3 — cart, mast and idlers; camera looks through the band the wheels scuff | 3 — band, bearings and two drives crowd the equator |
| Repairability | 4 — single hemisphere removal (see §5) | 3 | 3 |
| Manufacturing complexity | 4 — plates, tube, standard bearings, stock pulleys | 3 | 2 — two precision large bearings |
| Barrier impacts (Sector 3) | **5** — pendulum cannot derail | 2 — cart can climb or derail on impact | 3 — debris can enter the equatorial gap |
| Ramps (Sector 2) | 4 — capability set by `m_p·e/(M·R)`; tunable with ballast | 3 — limited by inner-shell friction | 4 |
| Pendulum timing (Sector 4) | 3 — needs pitch-damped stop-and-hold control | 4 | 4 |
| Vision | 4 — camera on the pitch-stabilised stator looks through clear PC | 3 — view through the band the drive wheels scuff | 4 — open gap, but debris |
| **Total (/55)** | **44** | 36 | 38 |

*Scores are engineering judgement for this specific track and envelope, not measured data.*

## 4. Selected preliminary architecture — WB-700

**Two-axis pendulum drive with a stationary through-axle stator** (barycentre offset):

1. **Shell:** two clear polycarbonate hemispheres (OD 700 mm, wall 3 mm nominal) joined on the
   equator by a clear PC spigot band, clamped axially through the axle. A clear polyurethane
   protective tape band covers the rolling band and the seam.
2. **Stator:** a hollow 30 mm aluminium axle is supported in the shell by a 61908 bearing at each
   pole. The axle carries the frame, both drive motors, the electronics and the camera, and it
   does **not** rotate with the shell.
3. **Drive:** **twin** 24 V planetary gearmotors (anti-symmetric front-left and rear-right),
   each driving an HTD-5M 72T pulley bolted to that hemisphere's pole flange through an 18T pulley
   and a 500 mm belt. Twin drive gives lateral mass balance without dead ballast and redundancy,
   and it puts torque into both hemispheres so the equatorial joint carries little torque.
4. **Steering:** a heavy **bob** (6S Li-ion pack plus laser-cut steel arc ballast plates) hangs
   from a longitudinal pivot 45 mm below the axle. A self-locking worm gearmotor tilts it ±30°,
   which leans the ball and turns it.
5. **Polar hubs:** flush, non-rotating caps on the axle ends. The **left hub carries the manual
   external power disconnect** (anti-spark arming plug), the charge port and the status LED.
   Cables run inside the hollow axle, so **no slip ring** is needed.
6. **Vision:** Camera Module 3 Wide on a 1-DOF servo mount that holds a constant downward look
   angle as the stator pitches. It is offset 50 mm left of the seam plane so the clear joint band
   images as a fixed, maskable stripe right of centre.

### Why A over B for this competition

* Ramps and barriers reward a **slip-free** torque path and a mechanism that cannot derail. The
  IDU's main advantage, turning in place, is not needed on a 75 m linear course of sequential
  sectors (track shape to be confirmed: Q-T1).
* The template's emphasis on **centre-of-gravity placement** fits a barycentre-offset design,
  whose climbing capability is set directly by the CG first moment `m_p·e`.
* Pendulum drawbacks are known and mitigated: (i) pitch oscillation is damped in the motor loop
  using IMU pitch rate; (ii) camera pitch is servo-stabilised; (iii) moderate steering authority
  comes from putting most internal mass in the bob and pivoting it close to the centre.

## 5. Unresolved assumptions carried forward

* Ramp angle, length, entry lip and exit (run-out or drop) are **unknown**. Capability is shown
  as a function of α and ballast.
* Track width, cone dimensions, surface friction and lighting are unknown.
* Shell sourcing (700 mm PC hemispheres, wall uniformity after thermoforming) is not yet confirmed.
* All masses of purchased parts are datasheet or estimated placeholders (see `Preliminary_BOM.csv`).
