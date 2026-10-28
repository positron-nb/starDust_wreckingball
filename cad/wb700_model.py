"""WB-700 parametric assembly (CadQuery / OpenCASCADE B-rep).

build_parts(P, phi, beta, explode) -> list[Part]

Every part carries: a unique id, functional group, the rigid body it belongs to
('shell' rotates with the shell, 'stator' is the gravity-held pendulum frame, 'bob' is the
steering mass, 'envelope' is a non-physical check volume), material/density or an assigned
purchased-part mass, and a PLACEHOLDER flag for envelopes of hardware that is not yet selected.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cadquery as cq

from wb700_params import RHO, Params

V = cq.Vector


# --------------------------------------------------------------------------- primitives
def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p0, p1):
    a, b = V(*p0), V(*p1)
    d = b - a
    return cq.Solid.makeCylinder(r, d.Length, a, d.normalized())


def tube(ro, ri, p0, p1):
    return cyl(ro, p0, p1).cut(cyl(ri, p0, p1))


def ring_y(ro, ri, y0, y1):
    """Annulus about the Y axis between y0 and y1."""
    return tube(ro, ri, (0, y0, 0), (0, y1, 0)) if ri > 0 else cyl(ro, (0, y0, 0), (0, y1, 0))


def sphere(r, c=(0, 0, 0)):
    return cq.Solid.makeSphere(r, V(*c), V(0, 0, 1), -90, 90, 360)


def solid_of(shape):
    """Return a single Solid/Compound usable for booleans and export."""
    if isinstance(shape, cq.Workplane):
        shape = shape.val()
    return shape.clean() if hasattr(shape, "clean") else shape


def gear_xz(n, m, y0, y1, cx=0.0, cz=0.0, bore=0.0, phase=0.0):
    """Spur gear with simplified trapezoid teeth, axis parallel to Y."""
    ra, rf = m * (n / 2 + 1.0), m * (n / 2 - 1.25)
    pitch = 2 * math.pi / n
    pts = []
    for i in range(n):
        a = phase + i * pitch
        for r, da in ((rf, -0.27), (ra, -0.12), (ra, 0.12), (rf, 0.27)):
            pts.append((cx + r * math.cos(a + da * pitch), cz + r * math.sin(a + da * pitch)))
    g = cq.Workplane("XZ", origin=(0, y0, 0)).polyline(pts).close().extrude(-(y1 - y0)).val()
    if bore > 0:
        g = g.cut(cyl(bore, (cx, y0 - 1, cz), (cx, y1 + 1, cz)))
    return g


def annular_sector_x(rho_i, rho_o, half_deg, cz, x0, length):
    """Annular sector in the YZ plane centred on (y=0, z=cz), opening downward, extruded +X."""
    h = math.radians(half_deg)

    def pt(r, a):
        return (r * math.sin(a), cz - r * math.cos(a))

    wp = (cq.Workplane("YZ", origin=(x0, 0, 0))
          .moveTo(*pt(rho_i, -h)).lineTo(*pt(rho_o, -h))
          .threePointArc(pt(rho_o, 0.0), pt(rho_o, h))
          .lineTo(*pt(rho_i, h))
          .threePointArc(pt(rho_i, 0.0), pt(rho_i, -h))
          .close().extrude(length))
    return wp.val()


def trapezoid_yz(x0, length, z_top, half_top, z_bot, half_bot):
    pts = [(-half_top, z_top), (half_top, z_top), (half_bot, z_bot), (-half_bot, z_bot)]
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(length).val()


# --------------------------------------------------------------------------- part record
@dataclass
class Part:
    pid: str
    name: str
    group: str               # SHELL, POLAR, STATOR, DRIVE, STEERING, POWER, COMPUTE, SENSORS, SAFETY, HARNESS, ENVELOPE
    body: str                # shell | stator | bob | envelope
    solid: object
    color: tuple
    material: str = ""
    density: float | None = None     # kg/mm^3 -> mass from CAD volume
    mass: float | None = None        # assigned mass (purchased / estimated)
    placeholder: bool = False
    basis: str = ""                  # provenance of the mass value
    note: str = ""
    opacity: float = 1.0
    interface_with: tuple = field(default_factory=tuple)  # designed contacts (excluded from clash)

    @property
    def kg(self) -> float:
        if self.mass is not None:
            return self.mass
        if self.density is not None:
            return self.solid.Volume() * self.density
        return 0.0


# colour palette by function (kept consistent across every figure)
C = {
    "shell": (0.62, 0.78, 0.90), "band": (0.55, 0.85, 0.95), "tape": (0.80, 0.90, 0.95),
    "flange": (0.25, 0.25, 0.28), "gear": (0.93, 0.92, 0.86), "bearing": (0.70, 0.70, 0.72),
    "hub": (0.18, 0.20, 0.24), "axle": (0.80, 0.81, 0.83), "plate": (0.66, 0.69, 0.73),
    "motor": (0.20, 0.23, 0.28), "pinion": (0.55, 0.55, 0.58), "arm": (0.50, 0.53, 0.58),
    "battery": (0.95, 0.55, 0.12), "ballast": (0.45, 0.17, 0.15), "bobframe": (0.58, 0.60, 0.64),
    "compute": (0.10, 0.55, 0.33), "driver": (0.12, 0.38, 0.75), "power": (0.95, 0.75, 0.10),
    "safety": (0.85, 0.12, 0.12), "sensor": (0.55, 0.25, 0.75), "camera": (0.10, 0.10, 0.12),
    "harness": (0.30, 0.30, 0.30), "rubber": (0.12, 0.12, 0.12), "envelope": (0.20, 0.75, 0.35),
}


# --------------------------------------------------------------------------- builder
def build_parts(P: Params, phi_deg: float = 0.0, beta_deg: float = 0.0,
                explode: float = 0.0, include_envelopes: bool = True) -> list[Part]:
    R_o, R_i = P.R_o, P.R_i
    parts: list[Part] = []

    def add(**kw):
        parts.append(Part(**kw))

    # ======================= SHELL BODY (rotates with the ball) =======================
    hollow = sphere(R_o).cut(sphere(R_i))
    big = R_o + 10
    shell_L = hollow.intersect(box(-big, big, 0, big, -big, big))
    shell_L = shell_L.cut(cyl(P.r_pole_open, (0, 1, 0), (0, big, 0)))
    shell_R = hollow.intersect(box(-big, big, -big, 0, -big, big))
    shell_R = shell_R.cut(cyl(P.r_pole_open, (0, -1, 0), (0, -big, 0)))
    # anti-rotation notches in the right hemisphere rim (keys on the band engage them)
    key_w, key_d = 10.0, 8.0
    keys = []
    for k in range(P.n_keys):
        ang = 45.0 + k * 360.0 / P.n_keys
        notch = box(P.band_r_out - 0.5, R_o + 1, -key_d, 0.01, -key_w / 2, key_w / 2)
        notch = notch.rotate(V(0, 0, 0), V(0, 1, 0), ang)
        shell_R = shell_R.cut(notch)
        key = box(P.band_r_out - 0.5, R_o - 0.3, -key_d + 0.3, 0.0, -key_w / 2 + 0.3, key_w / 2 - 0.3)
        keys.append(key.rotate(V(0, 0, 0), V(0, 1, 0), ang))
    add(pid="SH-01", name="Shell hemisphere L (clear PC)", group="SHELL", body="shell",
        solid=shell_L, color=C["shell"], material="Polycarbonate, clear", density=RHO["PC"],
        basis="CAD volume x density", opacity=0.16,
        note=f"OD {P.D_shell:.0f} mm, wall {P.t_shell:.1f} mm nominal, thermoformed; camera views through it")
    add(pid="SH-02", name="Shell hemisphere R (clear PC)", group="SHELL", body="shell",
        solid=shell_R, color=C["shell"], material="Polycarbonate, clear", density=RHO["PC"],
        basis="CAD volume x density", opacity=0.16, note="removable half; 4 rim notches for key tabs")

    band = ring_y(P.band_r_out, P.band_r_out - P.band_t, -P.band_w / 2, P.band_w / 2)
    for k in keys:
        band = band.fuse(k)
    add(pid="SH-03", name="Equatorial spigot band + 4 key tabs (clear PC)", group="SHELL", body="shell",
        solid=band, color=C["band"], material="Polycarbonate, clear", density=RHO["PC"],
        basis="CAD volume x density", opacity=0.45,
        note="bonded in L hemisphere; R hemisphere slides over; held by axial preload through axle")

    tape = sphere(R_o + P.tape_t).cut(sphere(R_o)).intersect(
        box(-big, big, -P.tape_half_w, P.tape_half_w, -big, big))
    add(pid="SH-04", name="Clear PU protective tape band (3M 8671-class)", group="SHELL", body="shell",
        solid=tape, color=C["tape"], material="TPU film 0.35 mm", density=RHO["TPU"],
        basis="CAD volume x density", opacity=0.22,
        note="sacrificial, replaceable; protects rolling band / camera view, adds grip; counted in OD")

    for side, s in (("L", 1), ("R", -1)):
        web = ring_y(P.flange_r_out, P.brg_od / 2, s * P.y_brg, s * (P.y_brg + P.brg_w))
        sleeve = ring_y(P.flange_r_out, P.flange_r_out - P.flange_sleeve_t,
                        s * (P.y_brg + P.brg_w), s * (R_o - 2)).intersect(sphere(R_i))
        flange = web.fuse(sleeve)
        add(pid=f"SH-1{0 if s > 0 else 1}", name=f"Pole flange {side} (bearing seat)", group="POLAR",
            body="shell", solid=flange, color=C["flange"], material="PA12-CF print + Al bearing insert",
            density=RHO["PA12CF"], basis="CAD volume x density",
            note="bonded + screwed to shell around polar opening", interface_with=("bearing", "gear", "shell"))
        ring = gear_xz(P.ring_teeth, P.gear_m, min(s * (P.y_gear_out - P.gear_face), s * P.y_gear_out),
                       max(s * (P.y_gear_out - P.gear_face), s * P.y_gear_out), bore=33.0)
        add(pid=f"SH-2{0 if s > 0 else 1}", name=f"Ring gear {side} {P.ring_teeth}T m{P.gear_m}",
            group="DRIVE", body="shell", solid=ring, color=C["gear"], material="POM-C (acetal)",
            density=RHO["POM"], basis="CAD volume x density (simplified teeth)",
            note="bolted to flange web; slides axially out of mesh when hemisphere is removed",
            interface_with=("pinion", "flange"))
        brg = ring_y(P.brg_od / 2, P.brg_id / 2, s * P.y_brg, s * (P.y_brg + P.brg_w))
        add(pid=f"SH-3{0 if s > 0 else 1}", name=f"Pole bearing {side} 61908-2RS (40x62x12)", group="POLAR",
            body="shell", solid=brg, color=C["bearing"], material="steel (purchased)", mass=0.110,
            basis="estimate (catalogue-class)", note="interface stator/shell; axisymmetric",
            interface_with=("flange", "hub"))

    # ======================= STATOR BODY (gravity-held pendulum frame) =======================
    st: list[Part] = []

    def add_st(**kw):
        st.append(Part(**kw))

    add_st(pid="ST-01", name="Stationary axle 30x3 tube (hollow harness duct)", group="STATOR",
           body="stator", solid=tube(P.axle_od / 2, P.axle_id / 2, (0, -P.axle_half_len, 0),
                                       (0, P.axle_half_len, 0)),
           color=C["axle"], material="Al 6061-T6", density=RHO["AL6061"], basis="CAD volume x density",
           note="does not rotate with shell; carries hub harness inside (no slip ring)",
           interface_with=("hub", "clamp", "arm", "imu"))

    for side, s in (("L", 1), ("R", -1)):
        boss = ring_y(P.brg_id / 2, P.axle_od / 2, s * (P.y_brg - 2), s * (P.hub_cup_floor_y + 4))
        floor = ring_y(P.hub_cup_r, P.axle_od / 2, s * P.hub_cup_floor_y, s * (P.hub_cup_floor_y + 4))
        wall = ring_y(P.hub_cup_r, P.hub_cup_r - P.hub_cup_wall, s * (P.hub_cup_floor_y + 4),
                      s * P.hub_cap_inner_y)
        cap = cyl(P.hub_cap_r, (0, s * P.hub_cap_inner_y, 0), (0, s * (R_o + 2), 0)).intersect(
            sphere(R_o - P.hub_recess))
        hub = boss.fuse(floor).fuse(wall).fuse(cap)
        if s > 0:  # left hub: pockets for disconnect plug, charge port and LED
            hub = hub.cut(box(14, 36, 330, 352, -1.5, 21.5))   # arming plug pocket
            hub = hub.cut(box(-36, -24, 330, 352, 8, 26))      # charge port pocket
            hub = hub.cut(cyl(3.0, (-25, 330, -22), (-25, 352, -22)))  # LED
        else:      # right hub: recessed preload bolt head
            hub = hub.cut(cyl(11.0, (0, -332, 0), (0, -352, 0)))
        add_st(pid=f"ST-0{2 if s > 0 else 3}", name=f"Polar hub {side} (non-rotating, flush)",
               group="POLAR", body="stator", solid=hub, color=C["hub"],
               material="PA12-CF print, Al boss", density=RHO["PA12CF"], basis="CAD volume x density",
               note=("LEFT: manual external disconnect + charge port + status LED" if s > 0
                     else "RIGHT: M12 preload bolt clamps hemispheres through the axle"),
               interface_with=("bearing", "axle", "device"))

    # left-hub devices (purchased)
    add_st(pid="PW-04", name="Manual disconnect: anti-spark arming plug (XT90-S class)", group="POWER",
           body="stator", solid=box(15, 35, 331, 346, -0.5, 20.5), color=C["safety"],
           material="purchased", mass=0.030, placeholder=True, basis="estimate",
           note="recessed 2-3 mm below hub cap; pulling it isolates the battery", interface_with=("hub",))
    add_st(pid="PW-05", name="Charge port (BMS charge input)", group="POWER", body="stator",
           solid=box(-35, -25, 331, 345, 9, 25), color=C["power"], material="purchased", mass=0.006,
           placeholder=True, basis="estimate", interface_with=("hub",))
    add_st(pid="SA-03", name="Status LED (armed / e-stop / fault)", group="SAFETY", body="stator",
           solid=cyl(2.5, (-25, 331, -22), (-25, 346, -22)), color=C["safety"], material="purchased",
           mass=0.002, placeholder=True, basis="estimate", interface_with=("hub",))
    add_st(pid="ST-04", name="Preload bolt M12 + disc springs (right hub)", group="POLAR", body="stator",
           solid=cyl(6.0, (0, -300, 0), (0, -340, 0)).fuse(cyl(9.0, (0, -332, 0), (0, -340, 0))),
           color=C["pinion"], material="steel", density=RHO["STEEL"], basis="CAD volume x density",
           note="single fastener opens the ball", interface_with=("hub", "axle"))

    # box frame plates
    bx, by, zt, zb, t = P.box_x, P.box_y, P.box_z_top, P.box_z_bot, P.plate_t
    for side, s in (("L", 1), ("R", -1)):
        pl = box(-bx, bx, min(s * (by - t), s * by), max(s * (by - t), s * by), zb, zt)
        pl = pl.cut(cyl(P.axle_od / 2 + 0.5, (0, -by - 5, 0), (0, by + 5, 0)))
        for (hx, hz) in ((-70, -50), (70, -50), (-95, 5), (95, 5)):
            pl = pl.cut(cyl(13.0, (hx, -by - 5, hz), (hx, by + 5, hz)))
        add_st(pid=f"ST-1{0 if s > 0 else 1}", name=f"Stator side plate {side}", group="STATOR",
               body="stator", solid=pl, color=C["plate"], material="Al 6061 3 mm",
               density=RHO["AL6061"], basis="CAD volume x density", interface_with=("clamp", "plate"))
    for side, s in (("F", 1), ("A", -1)):
        pl = box(min(s * (bx - t), s * bx), max(s * (bx - t), s * bx), -(by - t), by - t, zb, zt)
        pl = pl.cut(cyl(10.5, (s * (bx + 5), 0, -P.pivot_depth), (s * (bx - 10), 0, -P.pivot_depth)))
        add_st(pid=f"ST-1{2 if s > 0 else 3}", name=f"Stator {'front' if s > 0 else 'rear'} plate",
               group="STATOR", body="stator", solid=pl, color=C["plate"], material="Al 6061 3 mm",
               density=RHO["AL6061"], basis="CAD volume x density",
               interface_with=("plate", "pivotbrg", "device"))
    for side, s in (("L", 1), ("R", -1)):
        cl = box(-20, 20, min(s * 70, s * (by - t)), max(s * 70, s * (by - t)), -22, 22)
        cl = cl.cut(cyl(P.axle_od / 2, (0, -by, 0), (0, by, 0)))
        add_st(pid=f"ST-1{4 if s > 0 else 5}", name=f"Axle clamp block {side}", group="STATOR",
               body="stator", solid=cl, color=C["arm"], material="Al 6061", density=RHO["AL6061"],
               basis="CAD volume x density", interface_with=("axle", "plate"))

    # twin drive: gearmotors (PLACEHOLDER envelopes), arms and pinions
    cd = P.gear_center_dist
    for side, s, sgn_x in (("L", 1, 1), ("R", -1, -1)):
        a = math.radians(P.motor_angle_deg)
        mx, mz = sgn_x * cd * math.sin(a), -cd * math.cos(a)
        yf = P.motor_face_y - P.motor_arm_t          # gearhead face bolts to arm inboard face
        y_face = s * yf
        y_end = s * (yf - P.motor_len)
        motor = cyl(P.motor_d / 2, (mx, y_face, mz), (mx, s * (yf - 50), mz))
        motor = motor.fuse(cyl(P.motor_d / 2, (mx, s * (yf - 50), mz), (mx, s * (yf - 125), mz)))
        motor = motor.fuse(cyl(18.0, (mx, s * (yf - 125), mz), (mx, y_end, mz)))
        motor = motor.fuse(cyl(4.0, (mx, y_face, mz), (mx, s * (P.y_gear_out - 2.0), mz)))
        add_st(pid=f"DR-0{1 if s > 0 else 2}", name=f"Drive gearmotor {side} (24 V planetary + encoder)",
               group="DRIVE", body="stator", solid=motor, color=C["motor"], material="purchased",
               mass=0.62, placeholder=True, basis="estimate for 42 mm planetary class",
               note="PLACEHOLDER envelope 42 x 145 mm; selection in Phase 2",
               interface_with=("arm", "pinion"))
        y0p = s * (P.y_gear_out - P.gear_face + 1.0)
        y1p = s * (P.y_gear_out - 2.0)
        pin = gear_xz(P.pinion_teeth, P.gear_m, min(y0p, y1p), max(y0p, y1p), cx=mx, cz=mz, bore=4.0,
                      phase=math.pi / P.pinion_teeth)
        add_st(pid=f"DR-0{3 if s > 0 else 4}", name=f"Pinion {side} {P.pinion_teeth}T m{P.gear_m}",
               group="DRIVE", body="stator", solid=pin, color=C["pinion"], material="steel",
               density=RHO["STEEL"], basis="CAD volume x density", interface_with=("gear", "motor"))
        # arm: plate from axle clamp to motor face (slotted for mesh adjustment)
        ya, yb = s * (P.motor_face_y - P.motor_arm_t), s * P.motor_face_y
        y_lo, y_hi = min(ya, yb), max(ya, yb)
        arm = cq.Workplane("XZ", origin=(0, y_lo, 0)).polyline(
            _stadium_pts((0.0, 0.0), (mx, mz), 27.0)).close().extrude(-(y_hi - y_lo)).val()
        arm = arm.cut(cyl(P.axle_od / 2, (0, y_lo - 1, 0), (0, y_hi + 1, 0)))
        arm = arm.cut(cyl(4.5, (mx, y_lo - 1, mz), (mx, y_hi + 1, mz)))
        add_st(pid=f"DR-0{5 if s > 0 else 6}", name=f"Motor arm {side} (clamped to axle)", group="DRIVE",
               body="stator", solid=arm, color=C["arm"], material="Al 6061 6 mm", density=RHO["AL6061"],
               basis="CAD volume x density", interface_with=("axle", "motor"))

    # steering pivot
    pz = -P.pivot_depth
    add_st(pid="SG-01", name="Steering pivot shaft 12 mm", group="STEERING", body="stator",
           solid=cyl(P.pivot_d / 2, (-140, 0, pz), (149, 0, pz)), color=C["pinion"], material="steel",
           density=RHO["STEEL"], basis="CAD volume x density",
           note="driven end at front; sensor magnet at rear", interface_with=("pivotbrg", "hanger", "steermotor", "sensor"))
    for side, s in (("F", 1), ("A", -1)):
        add_st(pid=f"SG-0{2 if s > 0 else 3}", name=f"Pivot bearing + housing {side} (6001-2RS)",
               group="STEERING", body="stator",
               solid=tube(18.0, P.pivot_d / 2, (s * 112, 0, pz), (s * (bx - t), 0, pz)),
               color=C["bearing"], material="steel/Al", mass=0.035, basis="estimate",
               interface_with=("pivotshaft", "plate"))
    add_st(pid="SG-04", name="Steering worm gearmotor (self-locking)", group="STEERING", body="stator",
           solid=box(bx, bx + 24, -23, 23, -75, -30).fuse(cyl(12.2, (bx + 12, 23, -62), (bx + 12, 58, -62))),
           color=C["motor"], material="purchased", mass=0.16, placeholder=True,
           basis="estimate (JGY-370 worm class)", note="PLACEHOLDER; holds bob angle unpowered (e-stop safe)",
           interface_with=("plate", "pivotshaft"))
    add_st(pid="SE-04", name="Steering angle sensor (AS5600-class magnetic)", group="SENSORS", body="stator",
           solid=box(-bx - 21, -bx - 17, -12, 12, pz - 12, pz + 12), color=C["sensor"],
           material="purchased", mass=0.004, placeholder=True, basis="estimate",
           interface_with=("pivotshaft", "plate"))
    for side, s in (("F", 1), ("A", -1)):
        for yy in (1, -1):
            bump = box(min(s * 110, s * (bx - t)), max(s * 110, s * (bx - t)),
                       min(yy * 44, yy * 56), max(yy * 44, yy * 56), zb, zb + 10)
            add_st(pid=f"SG-1{len([q for q in st if q.pid.startswith('SG-1')])}",
                   name=f"Tilt end-stop bumper {side}{'L' if yy > 0 else 'R'} (rubber)", group="STEERING",
                   body="stator", solid=bump, color=C["rubber"], material="NBR rubber",
                   density=RHO["RUBBER"], basis="CAD volume x density",
                   note="engages a stop tab on the hanger at ~32 deg (tab not modelled)",
                   interface_with=("plate",))

    # vision
    cx, cy, cz_ = P.cam_pos
    cam = box(cx - 12.4, cx, cy - 12.5, cy + 12.5, cz_ - 12, cz_ + 12)
    add_st(pid="SE-01", name="Camera Module 3 Wide (102 x 67 deg)", group="SENSORS", body="stator",
           solid=cam, color=C["camera"], material="purchased", mass=0.004, basis="datasheet dims; mass est.",
           note="25 x 24 x 12.4 mm (datasheet); lens front at cam_pos", interface_with=("servo",))
    add_st(pid="SE-02", name="Camera pitch-stabiliser servo (micro, metal gear)", group="SENSORS",
           body="stator", solid=box(bx + 2, bx + 25, cy + 13, cy + 25, 3, 31.5), color=C["sensor"],
           material="purchased", mass=0.014, placeholder=True, basis="estimate (MG90S class)",
           interface_with=("camera", "plate"))
    add_st(pid="SE-03", name="IMU 9-DoF (BNO085-class) on axle saddle", group="SENSORS", body="stator",
           solid=box(-12, 12, -10, 10, 16, 20).fuse(box(-15, 15, -12, 12, 14.5, 16)), color=C["sensor"],
           material="purchased", mass=0.006, placeholder=True, basis="estimate",
           note="22 mm from the pitch axis to limit tangential-acceleration error", interface_with=("axle",))
    add_st(pid="SE-05", name="Shell-angle index (Hall sensor on L arm, magnet on ring gear)", group="SENSORS",
           body="stator", solid=box(25, 36, 278, 280, -31, -20), color=C["sensor"], material="purchased",
           mass=0.002, placeholder=True, basis="estimate", interface_with=("arm",))

    # compute / control / power / safety electronics (PLACEHOLDER envelopes, purchased)
    def dev(pid, name, group, solid, color, mass, note="", basis="estimate"):
        add_st(pid=pid, name=name, group=group, body="stator", solid=solid, color=color,
               material="purchased", mass=mass, placeholder=True, basis=basis, note=note,
               interface_with=("plate", "device"))

    dev("CP-01", "Raspberry Pi 5 (8 GB) + active cooler", "COMPUTE", box(-bx - 23, -bx, -86, -1, -26, 30),
        C["compute"], 0.070, "85 x 56 mm board (official brief); vision + navigation")
    dev("CP-02", "Motor-control MCU carrier (Raspberry Pi Pico 2 class)", "COMPUTE",
        box(-bx - 15, -bx, 8, 78, -30, 20), C["compute"], 0.040, "real-time loops, encoders, watchdog I/O")
    dev("DV-01", "Dual drive motor driver (Cytron MDD20A class)", "POWER",
        box(20, 109, by, by + 25, -79, 0), C["driver"], 0.090, "6-30 V, 20 A cont./ch (retailer data)")
    dev("DV-02", "Steering motor driver (Cytron MD10C class)", "POWER",
        box(-105, -30, by, by + 20, -60, -17), C["driver"], 0.045, "5-30 V, 13 A cont. (retailer data)")
    dev("PW-01", "Power distribution board: fuse, INA228 monitor, bus bars", "POWER",
        box(25, 95, -by - 21, -by, -75, -20), C["power"], 0.080)
    dev("PW-02", "DC-DC 24 V -> 5.1 V / 5 A (Pi 5 rail)", "POWER", box(25, 70, -by - 15, -by, -12, 13),
        C["power"], 0.035)
    dev("PW-03", "DC-DC 24 V -> 6 V / 3 A (servo rail)", "POWER", box(-100, -70, by, by + 10, -10, 10),
        C["power"], 0.015)
    dev("SA-01", "Motor-power contactor (NO, 40 A) - e-stop channel A", "SAFETY",
        box(-100, -70, -by - 30, -by, -60, -30), C["safety"], 0.040)
    dev("SA-02", "Drive dynamic-brake relays + resistors (NC, fail-safe)", "SAFETY",
        box(-65, -30, -by - 25, -by, -60, -25), C["safety"], 0.060)
    dev("SA-04", "E-stop receiver + independent safety supervisor (ESP32-C3 class)", "SAFETY",
        box(bx, bx + 12, -80, -30, -15, 22).fuse(cyl(1.2, (bx + 6, -55, 22), (bx + 6, -55, 52))),
        C["safety"], 0.030, "heartbeat-based fail-safe link; drives channel A and B")

    # harness / cable-routing envelopes (mass of all wiring distributed here)
    harness = [
        ("HR-01", "Harness trunk L (inner face of L side plate)", box(-110, 110, by - t - 8, by - t, 22, 29), 0.06),
        ("HR-02", "Harness trunk R (inner face of R side plate)", box(-110, 110, -(by - t), -(by - t) + 8, 22, 29), 0.06),
        ("HR-03", "Axle-entry harness (into hollow axle to L hub)", box(-8, 8, 30, 70, 15.5, 22), 0.05),
        ("HR-04", "Bob service loop (battery + sensor leads)", box(84, 96, -16, 16, -205, -60), 0.08),
        ("HR-05", "Motor leads L/R", box(-8, 8, 95, 130, -40, -20).fuse(box(-8, 8, -130, -95, -40, -20)), 0.05),
    ]
    for pid, name, sol, m in harness:
        add_st(pid=pid, name=name, group="HARNESS", body="stator", solid=sol, color=C["harness"],
               material="wiring", mass=m, placeholder=True, basis="estimate",
               note="cable-routing space reservation", opacity=0.55, interface_with=("plate", "device", "axle"))
    add_st(pid="ST-20", name="Fasteners, brackets, standoffs (distributed)", group="STATOR", body="stator",
           solid=box(-bx + 5, bx - 5, -by + 5, by - 5, zt - 4, zt - 3), color=C["plate"], material="mixed",
           mass=0.25, placeholder=True, basis="estimate", note="lumped mass at frame top (conservative)",
           opacity=0.0, interface_with=("plate", "device", "clamp", "imu", "harness"))

    # ======================= STEERING BOB =======================
    bob: list[Part] = []

    def add_bob(**kw):
        bob.append(Part(**kw))

    hx, ht = P.hanger_x, P.hanger_t
    for side, s in (("F", 1), ("A", -1)):
        x0 = hx if s > 0 else -hx - ht
        hg = trapezoid_yz(x0, ht, pz + 12, 15.0, P.tray_z, P.tray_half_y)
        hg = hg.cut(cyl(P.pivot_d / 2, (x0 - 1, 0, pz), (x0 + ht + 1, 0, pz)))
        add_bob(pid=f"BB-0{1 if s > 0 else 2}", name=f"Bob hanger {side}", group="STEERING", body="bob",
                solid=hg, color=C["bobframe"], material="Al 6061 5 mm", density=RHO["AL6061"],
                basis="CAD volume x density", interface_with=("pivotshaft", "tray", "harness"))
    add_bob(pid="BB-03", name="Battery tray", group="STEERING", body="bob",
            solid=box(-hx - ht, hx + ht, -P.tray_half_y, P.tray_half_y, P.tray_z, P.tray_z + P.tray_t),
            color=C["bobframe"], material="Al 6061 4 mm", density=RHO["AL6061"], basis="CAD volume x density",
            interface_with=("hanger", "battery", "ballast"))
    zb0 = P.tray_z + P.tray_t
    add_bob(pid="PW-10", name="Battery 6S1P 21700 Li-ion (Molicel P45B) + BMS", group="POWER", body="bob",
            solid=box(-P.batt_l / 2, P.batt_l / 2, -P.batt_w / 2, P.batt_w / 2, zb0, zb0 + P.batt_h),
            color=C["battery"], material="purchased", mass=0.51, placeholder=True,
            basis="6 x 70 g cells (datasheet max) + BMS/wiring estimate",
            note="21.6 V nom, 4.5 Ah, ~97 Wh (<100 Wh); slides out along -Y", interface_with=("tray",))
    n = P.n_ballast
    xs = _ballast_x_positions(n, P.ballast_plate_t)
    for i, x0 in enumerate(xs):
        plate = annular_sector_x(P.ballast_rho_in, P.ballast_rho_out, P.ballast_half_deg, pz, x0,
                                 P.ballast_plate_t)
        add_bob(pid=f"BL-{i + 1:02d}", name=f"Ballast arc plate {i + 1} (laser-cut steel 8 mm)",
                group="STEERING", body="bob", solid=plate, color=C["ballast"], material="S275 steel",
                density=RHO["STEEL"], basis="CAD volume x density",
                note="arc centred on pivot axis -> constant clearance through tilt; count is the CG tuning knob",
                interface_with=("ballast", "tiebracket"))
    for side, grp in (("F", [x for x in xs if x > 0]), ("A", [x for x in xs if x < 0])):
        if not grp:
            continue
        g0, g1 = min(grp), max(grp) + P.ballast_plate_t
        add_bob(pid=f"BB-0{4 if side == 'F' else 5}", name=f"Ballast clamp bracket {side} (2 x M6 tie-rods)",
                group="STEERING", body="bob",
                solid=box(g0 - 3, g1 + 3, -25, 25, pz - P.ballast_rho_in + 0.5, P.tray_z),
                color=C["bobframe"], material="Al/steel", mass=0.06, basis="estimate",
                interface_with=("tray", "ballast"))

    # ======================= ENVELOPES (non-physical) =======================
    env: list[Part] = []
    if include_envelopes:
        env.append(Part(pid="EV-01", name="Battery removal path (after R hemisphere removed)",
                        group="ENVELOPE", body="envelope",
                        solid=box(-P.batt_l / 2 + 1, P.batt_l / 2 - 1, -R_o - 60, -P.batt_w / 2 - 0.5,
                                  zb0 + 1, zb0 + P.batt_h - 1),
                        color=C["envelope"], opacity=0.25))
        env.append(Part(pid="EV-02", name="Preload-bolt socket access (outside right hub)",
                        group="ENVELOPE", body="envelope",
                        solid=cyl(13.0, (0, -R_o + 6, 0), (0, -R_o - 80, 0)), color=C["envelope"], opacity=0.25))

    # ======================= apply state transforms =======================
    for p in bob:
        if beta_deg:
            p.solid = p.solid.rotate(V(0, 0, pz), V(1, 0, pz), beta_deg)
    stator_all = st + bob
    for p in stator_all:
        if phi_deg:
            p.solid = p.solid.rotate(V(0, 0, 0), V(0, 1, 0), phi_deg)
    for p in env:
        if p.pid == "EV-01" and phi_deg:
            p.solid = p.solid.rotate(V(0, 0, 0), V(0, 1, 0), phi_deg)

    allp = parts + stator_all + env
    if explode:
        _apply_explode(allp, explode)
    return allp


BALLAST_X0 = 70.0  # inner face of each ballast group: outside the battery (|x| <= 67.5) so the
                   # battery slides out along -Y without removing ballast; hangers sit at |x| >= 100


def _ballast_x_positions(n, t):
    """Front and rear groups at the ends of the bob (max 3 + 3 plates of 8 mm)."""
    nf = (n + 1) // 2
    nr = n - nf
    xs = [BALLAST_X0 + i * t for i in range(nf)]
    xs += [-BALLAST_X0 - (i + 1) * t for i in range(nr)]
    return sorted(xs)


def _stadium_pts(c0, c1, r, n=18):
    (x0, z0), (x1, z1) = c0, c1
    ang = math.atan2(z1 - z0, x1 - x0)
    pts = []
    for k in range(n + 1):
        a = ang + math.pi / 2 + math.pi * k / n
        pts.append((x0 + r * math.cos(a), z0 + r * math.sin(a)))
    for k in range(n + 1):
        a = ang - math.pi / 2 + math.pi * k / n
        pts.append((x1 + r * math.cos(a), z1 + r * math.sin(a)))
    return pts


EXPLODE_VECTORS = {
    # pid prefix -> direction (scaled by explode distance)
    "SH-02": (0, -1.6, 0), "SH-11": (0, -1.6, 0), "SH-21": (0, -1.6, 0), "SH-31": (0, -1.6, 0),
    "ST-03": (0, -1.6, 0), "ST-04": (0, -1.6, 0), "EV-02": (0, -1.6, 0),
    "SH-01": (0, 1.25, 0), "SH-10": (0, 1.25, 0), "SH-20": (0, 1.25, 0), "SH-30": (0, 1.25, 0),
    "SH-03": (0, 0.0, 0), "SH-04": (0, 0.0, 0),
    "ST-02": (0, 1.25, 0), "PW-04": (0, 1.25, 0), "PW-05": (0, 1.25, 0), "SA-03": (0, 1.25, 0),
    "BB": (0, 0, -0.55), "BL": (0, 0, -0.75), "PW-10": (0, -0.9, -0.42),
    "CP": (-0.35, 0, 0), "SE-04": (-0.35, 0, 0),
    "SE-01": (0.45, 0, 0.12), "SE-02": (0.45, 0, 0.12), "SA-04": (0.40, 0, 0),
    "SG-04": (0.40, 0, -0.08),
    "DV-01": (0, 0.30, 0), "PW-03": (0, 0.30, 0), "DV-02": (0, 0.30, 0),
    "PW-01": (0, -0.30, 0), "PW-02": (0, -0.30, 0), "SA-01": (0, -0.30, 0), "SA-02": (0, -0.30, 0),
    "DR-01": (0, 0.55, 0), "DR-03": (0, 0.55, 0), "DR-05": (0, 0.55, 0),
    "DR-02": (0, -0.55, 0), "DR-04": (0, -0.55, 0), "DR-06": (0, -0.55, 0),
    "SE-03": (0, 0, 0.35),
}


def _apply_explode(parts, dist):
    for p in parts:
        vec = None
        for key in sorted(EXPLODE_VECTORS, key=len, reverse=True):
            if p.pid.startswith(key):
                vec = EXPLODE_VECTORS[key]
                break
        if vec is None:
            continue
        p.solid = p.solid.translate(V(vec[0] * dist, vec[1] * dist, vec[2] * dist))
