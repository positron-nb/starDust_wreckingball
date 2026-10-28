"""WB-700 Phase 1 CAD -- single source of truth for every dimension and mass assumption.

Units: millimetres, kilograms, degrees.  Coordinate frame (used everywhere in the package):
    origin O = geometric centre of the spherical shell
    +X = direction of travel (forward), +Y = left (along the stationary axle), +Z = up.
Stator pitch PHI rotates stator+bob about +Y; bob tilt BETA rotates the bob about the
steering pivot axis (parallel to +X, through (y=0, z=-pivot_depth)).

Values marked RULE come from the official problem statement; everything else is a team
design choice or a labelled assumption and may be edited.  Re-run build_all.py after edits.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

FT = 304.8  # mm per foot

# Densities in kg/mm^3 (g/cm^3 * 1e-6)
RHO = {
    "PC": 1.20e-6,          # polycarbonate shell / band
    "TPU": 1.20e-6,         # clear PU protective tape (3M 8671-class)
    "AL6061": 2.70e-6,      # plates, axle, arms, hangers, tray
    "STEEL": 7.85e-6,       # ballast plates, shafts, pinions
    "POM": 1.41e-6,         # ring gears (acetal)
    "PA12CF": 1.15e-6,      # printed pole flanges / hub caps
    "RUBBER": 1.10e-6,      # tilt bumpers
}


@dataclass
class Params:
    # ---------------- official envelope (RULE) ----------------
    d_min_rule: float = 2.0 * FT            # 609.6 mm, diameter must be strictly greater
    d_max_rule: float = 2.5 * FT            # 762.0 mm, diameter must be strictly smaller
    protrusion_max_rule: float = 0.5 * FT   # 152.4 mm beyond outer shell surface

    # ---------------- shell (design parameter, NOT a rule) ----------------
    D_shell: float = 700.0          # nominal outer diameter of PC hemispheres
    t_shell: float = 3.0            # nominal wall (thermoformed PC; local thinning expected)
    shell_tol: float = 7.0          # assumed +/- diameter tolerance of thermoformed domes
    r_pole_open: float = 65.0       # polar opening radius
    band_w: float = 30.0            # equatorial spigot band axial width (clear PC)
    band_t: float = 5.0             # spigot band radial thickness
    n_keys: int = 4                 # anti-rotation key tabs on the band
    tape_t: float = 0.35            # 3M 8671-class clear PU tape total thickness (TDS: 0.014 in)
    tape_half_w: float = 100.0      # protective band covers |y| <= this
    hub_recess: float = 1.0         # hub caps sit this far below the spherical surface

    # ---------------- polar interface ----------------
    brg_id: float = 40.0            # 61908-2RS (6908) deep-groove bearing 40 x 62 x 12
    brg_od: float = 62.0
    brg_w: float = 12.0
    y_brg: float = 296.0            # inboard face of the pole bearing / flange web
    flange_r_out: float = 73.0      # pole flange web outer radius
    flange_sleeve_t: float = 3.0
    hub_cap_r: float = 63.0         # stationary hub cap radius (2 mm gap to opening)
    hub_cup_r: float = 61.0
    hub_cup_wall: float = 4.0
    hub_cup_floor_y: float = 312.0  # inner face of hub cup floor
    hub_cap_inner_y: float = 337.0

    # ---------------- stationary axle + stator frame ----------------
    axle_od: float = 30.0           # 6061-T6 tube, hollow core carries the hub harness
    axle_id: float = 24.0
    axle_half_len: float = 312.0
    box_x: float = 125.0            # stator box half-length (front/rear plate outer faces)
    box_y: float = 90.0             # stator box half-width (side plate outer faces)
    box_z_top: float = 30.0
    box_z_bot: float = -80.0
    plate_t: float = 3.0            # 6061 plate thickness

    # ---------------- twin spur-gear drive ----------------
    gear_m: float = 1.5             # module (preliminary)
    ring_teeth: int = 72            # POM ring gear on each pole flange (shell side)
    pinion_teeth: int = 18          # steel pinion on each gearmotor (stator side)
    gear_face: float = 12.0
    y_gear_out: float = 296.0       # outboard face of ring gear (bolted to flange web)
    motor_angle_deg: float = 50.0   # left motor front-down, right motor rear-down (anti-symmetric)
    motor_d: float = 42.0           # PLACEHOLDER 24 V planetary gearmotor envelope
    motor_len: float = 145.0        # gearhead + motor + encoder
    motor_face_y: float = 278.0
    motor_arm_t: float = 6.0

    # ---------------- steering bob ----------------
    pivot_depth: float = 45.0       # pivot axis below the axle centre line
    pivot_d: float = 12.0
    beta_max_deg: float = 30.0      # mechanical tilt range +/-; bumpers at ~32 deg
    hanger_x: float = 100.0         # inner face of the two hanger plates (|x|)
    hanger_t: float = 5.0
    tray_z: float = -250.0          # underside of battery tray
    tray_t: float = 4.0
    tray_half_y: float = 40.0
    batt_l: float = 135.0           # 6S1P 21700 pack envelope incl. BMS + wrap (PLACEHOLDER box)
    batt_w: float = 76.0
    batt_h: float = 34.0
    ballast_rho_in: float = 215.0   # arc-profile laser-cut steel plates (radius about pivot axis)
    ballast_rho_out: float = 265.0
    ballast_half_deg: float = 40.0
    ballast_plate_t: float = 8.0
    n_ballast: int = 4              # baseline; adjustable 2..6 in 8 mm steps

    # ---------------- vision ----------------
    cam_pos: tuple = (158.4, 50.0, 22.0)   # lens front centre (stator frame, PHI=0)
    cam_down_deg: float = 12.0             # nominal look-down angle held by pitch servo
    cam_hfov: float = 102.0                # Camera Module 3 Wide (datasheet)
    cam_vfov: float = 67.0

    # ---------------- clearances used by the checks ----------------
    min_moving_clearance: float = 8.0      # stator/bob vs shell-fixed parts
    min_static_gap: float = 1.0            # between parts on the same body

    # ---------------- assumptions for preliminary drive numbers ----------------
    c_rr: float = 0.03                     # rolling-resistance coefficient (ASSUMED)
    gear_eff: float = 0.95
    v_max_target: float = 2.0              # m/s design top speed (target, not a claim)

    # ------------- derived -------------
    @property
    def R_o(self) -> float:
        return self.D_shell / 2.0

    @property
    def R_i(self) -> float:
        return self.R_o - self.t_shell

    @property
    def band_r_out(self) -> float:
        return math.sqrt(self.R_i ** 2 - (self.band_w / 2.0) ** 2)

    @property
    def gear_center_dist(self) -> float:
        return self.gear_m * (self.ring_teeth + self.pinion_teeth) / 2.0

    @property
    def gear_ratio(self) -> float:
        return self.ring_teeth / self.pinion_teeth

    def as_dict(self) -> dict:
        d = asdict(self)
        d.update(R_o=self.R_o, R_i=self.R_i, band_r_out=self.band_r_out,
                 gear_center_dist=self.gear_center_dist, gear_ratio=self.gear_ratio)
        return d


P = Params()
