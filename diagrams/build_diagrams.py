"""WB-700 Phase 1 diagrams: single editable source for the system, electronics, power and software
diagrams.  Writes figures/<name>.png (rendered), diagrams/svg/<name>.svg (editable vector) and
diagrams/<name>.mmd (Mermaid logical export of the same nodes and edges).

usage (from this folder):  ..\\.venv\\Scripts\\python.exe build_diagrams.py
"""
from __future__ import annotations

import pathlib

from diagram_kit import Diagram

HERE = pathlib.Path(__file__).resolve().parent
FIG = HERE.parent / "figures"
SVG = HERE / "svg"
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]


# =============================================================================== 1. system
def system_architecture():
    D = Diagram("System_Architecture", 1810, 1160, "WB-700 - system block diagram (Phase 1)",
                "Camera -> image processing -> navigation + state machine -> motion commands -> motor-control MCU -> drivers -> "
                "internal drive actuators.\nThe red safety path is hardware and independent of the autonomy software. "
                "No offboard processing or remote driving during a run.")
    yS0, yS1 = 165, 255
    yA0, yA1 = 325, 455
    yB0, yB1 = 525, 615
    yC0, yC1 = 705, 805
    yD0, yD1 = 905, 1015
    D.group(1025, 125, 1545, 272, "SUPPLEMENTARY INTERNAL SENSORS (stabilisation)", "#7b4bc4", "#f8f4fd")
    D.group(25, 290, 240, 478, "PRIMARY SENSOR", "#7b4bc4", "#f8f4fd")
    D.group(265, 290, 1012, 640, "ONBOARD COMPUTER: Raspberry Pi 5 (all navigation, no offboard processing)",
            "#1f8a4c", "#f3fbf6")
    D.group(1330, 290, 1785, 478, "DRIVERS + INTERNAL DRIVE ACTUATORS", "#2b5cb8", "#f3f6fd")
    D.group(25, 665, 1300, 822, "ONBOARD POWER (battery only, no tether)", "#c98a00", "#fffaf0")
    D.group(25, 862, 1785, 1042, "INDEPENDENT SAFETY PATH (hardware, outside the autonomy software)", "#c62828",
            "#fff6f6", dash="9 6")
    D.box("DEV", 40, 135, 420, 235, "Development laptop", ["parameters + logs BEFORE the run only;", "no link during the run"], "dev")
    D.box("IMU", 1040, yS0, 1190, yS1, "IMU 9-DoF", ["stator pitch, roll,", "yaw rate"], "sense")
    D.box("ENC", 1210, yS0, 1360, yS1, "Encoders", ["2 drive motors", "+ shell index"], "sense")
    D.box("ANG", 1380, yS0, 1530, yS1, "Steering angle", ["magnetic sensor", "on bob pivot"], "sense")
    D.box("CAM", 40, yA0, 225, yA1, "Camera Module 3", ["Wide, 102 x 67 deg", "PRIMARY sensor:", "path tracking +", "gate identification"], "sense")
    D.box("VIS", 285, yA0, 500, yA1, "Image processing", ["cone + gate detection", "(yellow left / red right)", "seam mask, ground", "projection"], "comp")
    D.box("NAV", 535, yA0, 750, yA1, "Autonomous", ["navigation +", "course state machine,", "sector speed profiles,", "pendulum timing"], "comp")
    D.box("CMD", 785, yA0, 995, yA1, "Motion + steering", ["commands", "v_ref, lean_ref,", "camera pitch_ref"], "comp")
    D.box("MCU", 1060, yA0, 1285, yA1, "Motor-control MCU", ["RP2350 class, 500 Hz:", "speed + pendulum damping,", "steering angle, camera", "stabiliser, cmd time-out"], "mcu")
    D.box("DRV", 1345, yA0, 1545, yA1, "Motor drivers", ["dual drive 20 A/ch", "+ steering driver", "(PWM/DIR inputs only)"], "act")
    D.box("ACT", 1580, yA0, 1772, yA1, "Drive actuators", ["2 gearmotors -> ring", "gears -> SHELL ROLLS;", "worm motor tilts bob;", "camera pitch servo"], "act")
    D.box("EST", 420, yB0, 680, yB1, "State estimation (EKF)", ["distance, lateral offset,", "heading, speed, pitch"], "comp")
    D.box("BAT", 40, yC0, 235, yC1, "Battery 6S1P Li-ion", ["21.6 V nom., ~97 Wh", "BMS: LVC, OC, SC, temp"], "pwr")
    D.box("DISC", 285, yC0, 480, yC1, "MANUAL DISCONNECT", ["arming plug in left", "hub (external, flush)"], "safe")
    D.box("BUS", 530, yC0, 720, yC1, "Main bus", ["40 A fuse at pack,", "V / I monitor"], "pwr")
    D.box("REG", 775, yC0, 995, yC1, "Voltage regulation", ["5.1 V / 5 A: Pi 5", "3.3-5 V: MCU, sensors,", "safety supervisor"], "pwr")
    D.box("KC", 1060, yC0, 1285, yC1, "Motor-power contactor", ["NO, e-stop channel A;", "6 V servo DC-DC after it"], "safe")
    D.box("TX", 40, yD0, 270, yD1, "Handheld wireless e-stop", ["latching mushroom switch,", "2.4 GHz heartbeat 20 Hz"], "safe")
    D.box("RX", 420, yD0, 720, yD1, "E-stop receiver +", ["safety supervisor (own MCU)", "fail-safe: no heartbeat = STOP,", "latched until manual re-arm"], "safe")
    D.box("WD", 785, yD0, 995, yD1, "Hardware watchdog", ["MCU heartbeat", "-> WD_OK"], "safe")
    D.box("BRK", 1345, yD0, 1545, yD1, "Brake relays (changeover)", ["break-before-make: driver", "cut, motor shorted"], "safe")

    D.edge("CAM", "VIS", "info", "CSI-2\n50 fps", lab=(255, 360))
    D.edge("VIS", "NAV", "info", "cones,\ngates", lab=(517, 360))
    D.edge("NAV", "CMD", "info")
    D.edge("CMD", "MCU", "info", "UART\n50 Hz", lab=(1027, 360))
    D.edge("MCU", "DRV", "info", "PWM /\nDIR", lab=(1315, 360))
    D.edge("DRV", "ACT", "power")
    D.edge("VIS", "EST", "info", s="b", d="t", sf=0.5, df=0.25, via=[(392.5, 490), (485, 490)])
    D.edge("EST", "NAV", "info", s="t", d="b", sf=0.75, df=0.5, via=[(615, 490), (642.5, 490)])
    D.edge("MCU", "EST", "info", "attitude + odometry 100 Hz", s="b", d="r", sf=0.2, via=[(1105, 570)], lab=(880, 570))
    D.edge("IMU", "MCU", "info", "I2C", s="b", d="t", df=0.2, via=[(1115, 300), (1105, 300)], lab=(1150, 290))
    D.edge("ENC", "MCU", "info", "quad.", s="b", d="t", df=0.5, via=[(1285, 290), (1172.5, 290)], lab=(1250, 278))
    D.edge("ANG", "MCU", "info", "I2C", s="b", d="t", df=0.8, via=[(1455, 280), (1240, 280)], lab=(1420, 268))
    D.edge("BAT", "DISC", "power")
    D.edge("DISC", "BUS", "power")
    D.edge("BUS", "REG", "power")
    D.edge("REG", (885, 640), "logic", "5.1 V", s="t", sf=0.5, lab=(918, 668))
    D.edge("REG", "MCU", "logic", "3.3-5 V", s="r", d="b", sf=0.3, df=0.1, via=[(1022, 735), (1022, 478), (1082.5, 478)],
           lab=(1052, 700))
    D.edge("BUS", "KC", "power", "motor feed", s="b", d="b", sf=0.5, df=0.4, via=[(625, 838), (1150, 838)], lab=(890, 838))
    D.edge("KC", "DRV", "power", "motor bus", s="r", d="b", sf=0.5, df=0.5, via=[(1445, 755)], lab=(1380, 735))
    D.edge("TX", "RX", "status", "2.4 GHz\nheartbeat", lab=(345, 960))
    D.edge("MCU", "WD", "status", "heartbeat", s="b", d="t", sf=0.6, df=0.6,
           via=[(1195, 650), (1040, 650), (1040, 875), (911, 875)], lab=(1110, 650))
    D.edge("WD", "RX", "safety", "WD_OK", s="l", d="r", lab=(752, 960))
    D.edge("RX", "KC", "safety", "contactor coil (A)", s="b", d="b", sf=0.5, df=0.8,
           via=[(570, 1030), (1240, 1030)], lab=(905, 1030))
    D.edge("RX", "BRK", "safety", "brake relays (B)", s="t", d="t", sf=0.85, df=0.5, via=[(675, 884), (1445, 884)],
           lab=(1180, 884))
    D.edge("RX", "DRV", "safety", "PWM gated off (C)", s="t", d="b", sf=0.3, df=0.15,
           via=[(510, 852), (1315, 852), (1315, 490), (1375, 490)], lab=(1250, 600))
    D.edge("BRK", "ACT", "safety", "motors\nshorted", s="r", d="b", sf=0.5, df=0.5, via=[(1676, 960)], lab=(1676, 600))
    D.edge("RX", (505, 640), "status", "e-stop state", s="t", sf=0.283, lab=(438, 842))
    D.edge("DEV", (300, 290), "dev", "pre-run only", s="b", sf=0.684, lab=(370, 262))
    D.set_legend([("info", "information / control"), ("power", "motor power"), ("logic", "logic power"),
                  ("safety", "safety path (hardware)"), ("status", "heartbeat / status"), ("dev", "pre-run link only")],
                 40, 1090, dx=290)
    D.text(40, 1135, "Source: diagrams/build_diagrams.py (also exported as svg/System_Architecture.svg and "
                     "System_Architecture.mmd). PH parts and numbers are Phase 1 placeholders.", 14)
    return D


# =============================================================================== 2. electronics
def electronics_architecture():
    D = Diagram("Electronics_Architecture", 1810, 1130, "WB-700 - preliminary electronics architecture (boards + interfaces)",
                "PH = placeholder part class (final selection in Phase 2). Buses: CSI-2 camera, UART/USB Pi-to-MCU, "
                "I2C/SPI sensors, PIO quadrature encoders, PWM/DIR drivers.")
    D.group(25, 120, 1785, 690, "COMPUTE, SENSING AND ACTUATION", "#3d4654", "#fafbfc")
    D.group(25, 715, 1785, 1060, "SAFETY CHAIN (independent of the Pi 5 software)", "#c62828", "#fff6f6", dash="9 6")
    D.box("CAM", 45, 165, 265, 265, "Camera Module 3 Wide", ["IMX708 12 MP", "102 x 67 deg (datasheet)"], "sense")
    D.box("PI", 345, 150, 645, 290, "Raspberry Pi 5, 8 GB", ["Raspberry Pi OS 64-bit", "vision, EKF, state machine",
                                                          "5.1 V / 5 A input", "2 x CSI-2, USB, UART, GPIO"], "comp")
    D.box("MCU", 780, 150, 1080, 330, "Motor-control MCU (PH)", ["RP2350 class (Pico 2)", "PIO quadrature x2",
                                                               "PWM x4, I2C, SPI, ADC", "UART to Pi 5", "WDI out, e-stop input"], "mcu")
    D.box("IMU", 640, 360, 890, 430, "IMU 9-DoF (PH)", ["BNO085 class, 400 Hz"], "sense")
    D.box("ENC", 640, 450, 890, 520, "Drive encoders L+R", ["Hall quadrature, A/B x2"], "sense")
    D.box("IDX", 640, 540, 890, 610, "Shell index Hall", ["magnet on ring gear"], "sense")
    D.box("ANG", 960, 360, 1190, 430, "Steering angle (PH)", ["AS5600 class, I2C"], "sense")
    D.box("INA", 960, 450, 1190, 520, "Bus V/I monitor (PH)", ["INA228 class, I2C"], "pwr")
    D.box("BMS", 960, 540, 1190, 610, "6S BMS", ["fault flag (if exposed)"], "pwr")
    D.box("DD", 1300, 150, 1530, 260, "Dual drive driver (PH)", ["Cytron MDD20A class", "6-30 V, 20 A per ch."], "act")
    D.box("SD", 1300, 300, 1530, 400, "Steering driver (PH)", ["Cytron MD10C class", "5-30 V, 13 A"], "act")
    D.box("SVD", 1300, 440, 1530, 520, "Servo PWM out", ["6 V rail after contactor"], "act")
    D.box("ML", 1590, 140, 1770, 195, "Gearmotor L", [], "act")
    D.box("MR", 1590, 215, 1770, 270, "Gearmotor R", [], "act")
    D.box("SM", 1590, 315, 1770, 385, "Steering worm motor", ["self-locking"], "act")
    D.box("SV", 1590, 445, 1770, 515, "Camera pitch servo", ["metal gear, 6 V"], "act")
    D.box("TX", 45, 810, 285, 920, "Handheld e-stop TX", ["latching mushroom switch,", "heartbeat 20 Hz"], "safe")
    D.box("SUP", 420, 790, 760, 950, "Safety supervisor (PH)", ["independent MCU + 2.4 GHz RX", "(ESP32-C3 class, ESP-NOW)",
                                                              "RUN only if heartbeat valid", "AND WD_OK AND not latched"], "safe")
    D.box("WD", 860, 780, 1080, 860, "Watchdog IC (PH)", ["TPS3823 class"], "safe")
    D.box("LED", 860, 930, 1080, 1000, "Status LED", ["left hub"], "safe")
    D.box("K", 1300, 780, 1530, 860, "Contactor, NO", ["24 V coil, 40 A"], "safe")
    D.box("BRK", 1300, 930, 1530, 1010, "Brake relays, changeover", ["break-before-make + resistors"], "safe")

    D.edge("CAM", "PI", "info", "CSI-2", lab=(305, 202))
    D.edge("PI", "MCU", "info", "UART / USB", s="r", d="l", sf=0.45, df=0.35, bi=True, lab=(712, 190))
    D.edge((925, 575), "MCU", "info", None, s="b", d="b", df=0.4833)
    for sid, y in (("IMU", 395), ("ENC", 485), ("IDX", 575)):
        D.edge(sid, (921, y), "info", None, s="r")
    for sid, y in (("ANG", 395), ("INA", 485), ("BMS", 575)):
        D.edge(sid, (929, y), "info", None, s="l")
    D.text(925, 640, "shared sensor bus into the MCU", 14, "#3d4654", anchor="middle")
    D.edge("MCU", "DD", "info", "PWM+DIR x2", s="r", d="l", sf=0.2, df=0.33, lab=(1190, 172))
    D.edge("MCU", "SD", "info", "PWM+DIR", s="r", d="l", sf=0.55, df=0.5, via=[(1255, 249), (1255, 350)], lab=(1170, 249))
    D.edge("MCU", "SVD", "info", "PWM 50 Hz", s="r", d="l", sf=0.85, df=0.5, via=[(1240, 303), (1240, 480)], lab=(1160, 303))
    D.edge("DD", "ML", "power", s="r", d="l", sf=0.25)
    D.edge("DD", "MR", "power", s="r", d="l", sf=0.7)
    D.edge("SD", "SM", "power")
    D.edge("SVD", "SV", "power")
    D.edge("MCU", "WD", "status", "WDI pulses", s="r", d="r", sf=0.97, df=0.5, via=[(1215, 325), (1215, 820)], lab=(1215, 660))
    D.edge("WD", "SUP", "safety", "WD_OK", s="l", d="r", sf=0.5, df=0.3, lab=(812, 795))
    D.edge("TX", "SUP", "status", "2.4 GHz\nheartbeat", lab=(352, 865))
    D.edge("SUP", "K", "safety", "contactor coil", s="r", d="l", sf=0.1, df=0.5,
           via=[(790, 806), (790, 750), (1280, 750), (1280, 820)], lab=(1040, 750))
    D.edge("SUP", "BRK", "safety", "brake coil", s="b", d="l", sf=0.5, df=0.5,
           via=[(590, 1025), (1280, 1025), (1280, 970)], lab=(940, 1025))
    D.edge("SUP", "DD", "safety", "PWM gate off on STOP", s="b", d="b", sf=0.8, df=0.8,
           via=[(692, 1042), (1560, 1042), (1560, 280), (1484, 280)], lab=(1560, 620))
    D.edge("SUP", "SD", "safety", None, s="b", d="b", sf=0.8, df=0.8,
           via=[(692, 1042), (1560, 1042), (1560, 420), (1484, 420)])
    D.edge("SUP", "MCU", "status", "ESTOP_STATE", s="t", d="b", sf=0.65, df=0.4333, via=[(641, 728), (910, 728)],
           lab=(760, 728))
    D.edge("SUP", "PI", "status", "ESTOP_STATE (GPIO)", s="t", d="b", sf=0.12, df=0.3,
           via=[(461, 705), (300, 705), (300, 330), (435, 330)], lab=(300, 520))
    D.edge("SUP", "LED", "info", None, s="r", d="l", sf=0.8, df=0.5, via=[(810, 918), (810, 965)])
    D.set_legend([("info", "signal / data"), ("power", "motor power"), ("safety", "safety output"),
                  ("status", "heartbeat / status")], 40, 1100, dx=320)
    return D


# =============================================================================== 3. power
def power_distribution():
    D = Diagram("Power_Distribution", 1810, 1000, "WB-700 - preliminary power distribution",
                "Strictly onboard battery power. Every actuator (drive, steering, camera servo) is downstream of the e-stop "
                "contactor; the logic rail stays\nalive so the robot can report and log the stop. Values are Phase 1 "
                "design targets; fuse and wire sizes are confirmed in Phase 2.")
    D.group(25, 130, 400, 935, "SOURCE + ISOLATION", "#c98a00", "#fffaf0")
    D.group(430, 130, 1785, 470, "LOGIC BRANCH (always on while armed)", "#1f8a4c", "#f3fbf6")
    D.group(430, 495, 1785, 935, "ACTUATOR BRANCH (cut by the e-stop)", "#c62828", "#fff6f6", dash="9 6")
    D.box("CELL", 50, 175, 375, 285, "Battery 6S1P Li-ion 21700", ["Molicel P45B cells (datasheet)", "21.6 V nom., 18.0-25.2 V",
                                                                 "4.5 Ah, ~97 Wh (< 100 Wh)"], "pwr")
    D.box("BMS", 50, 325, 375, 435, "6S BMS", ["under-voltage cut-off (LVC),", "over-voltage, over-current,", "short-circuit, temperature, balance"], "pwr")
    D.box("F1", 50, 475, 375, 545, "Main fuse 40 A", ["at the pack terminals"], "pwr")
    D.box("ARM", 50, 585, 375, 695, "MANUAL DISCONNECT", ["anti-spark arming plug", "(XT90-S class), left polar hub"], "safe")
    D.box("BUS", 50, 735, 375, 835, "Main bus 18-25.2 V", ["INA228-class V/I monitor", "software LVC warning to MCU"], "pwr")
    D.box("CHG", 50, 860, 375, 925, "Charge port, left hub", ["CC/CV 25.2 V, plug removed"], "pwr")
    D.box("F4", 470, 260, 640, 340, "Fuse 5 A", ["logic branch"], "pwr")
    D.box("B5", 700, 250, 960, 350, "DC-DC 24 V -> 5.1 V", ["5 A (Pi 5 needs 5 A)"], "pwr")
    D.box("PI", 1030, 165, 1320, 235, "Raspberry Pi 5 + camera", ["~8-12 W (estimate)"], "comp")
    D.box("MCU", 1030, 265, 1320, 335, "MCU + sensors", ["3.3 V on-board LDO"], "comp")
    D.box("SUP", 1030, 365, 1320, 445, "Safety supervisor + RX", ["+ watchdog + status LED"], "safe")
    D.box("NOTE", 1380, 175, 1765, 445, "Logic power notes", ["Pi 5 needs a stable 5.1 V / 5 A rail.", "Separate regulated branches", "reduce electrical coupling;",
                                                             "logic-rail stability during motor", "start, stall and braking needs verification.",
                                                             "Common ground; motor return", "kept short and star-pointed."], "note")
    D.box("F2", 470, 640, 640, 720, "Fuse 30 A", ["actuator branch"], "pwr")
    D.box("K", 700, 630, 960, 730, "Contactor, NO", ["e-stop channel A", "coil from supervisor"], "safe")
    D.box("MB", 1030, 630, 1290, 730, "Motor bus", ["TVS + bulk capacitor", "(regeneration clamp)"], "pwr")
    D.box("DD", 1360, 530, 1560, 600, "Dual drive driver", ["20 A per channel"], "act")
    D.box("BRK", 1360, 625, 1560, 705, "Brake relays (C/O)", ["driver cut, motor shorted"], "safe")
    D.box("ML", 1600, 535, 1765, 595, "Gearmotor L", [], "act")
    D.box("MR", 1600, 635, 1765, 695, "Gearmotor R", [], "act")
    D.box("F3", 1030, 790, 1180, 860, "Fuse 5 A", [], "pwr")
    D.box("SD", 1230, 790, 1420, 860, "Steering driver", [], "act")
    D.box("SM", 1470, 790, 1765, 860, "Steering worm gearmotor", ["self-locking when unpowered"], "act")
    D.box("B6", 1030, 878, 1180, 925, "DC-DC 6 V / 3 A", [], "pwr")
    D.box("SV", 1230, 878, 1420, 925, "Camera servo", [], "act")
    D.edge("CELL", "BMS", "power", s="b", d="t")
    D.edge("BMS", "F1", "power", s="b", d="t")
    D.edge("F1", "ARM", "power", s="b", d="t")
    D.edge("ARM", "BUS", "power", s="b", d="t")
    D.edge("CHG", "BMS", "charge", "charge", s="l", d="l", sf=0.5, df=0.5, via=[(36, 892), (36, 380)], lab=(36, 620))
    D.edge("BUS", "F4", "logic", s="r", d="l", sf=0.3, df=0.5, via=[(420, 765), (420, 300)])
    D.edge("F4", "B5", "logic")
    D.edge("B5", "PI", "logic", s="r", d="l", sf=0.3, df=0.5, via=[(995, 280), (995, 200)])
    D.edge("B5", "MCU", "logic", s="r", d="l", sf=0.5, df=0.5)
    D.edge("B5", "SUP", "logic", s="r", d="l", sf=0.7, df=0.5, via=[(995, 320), (995, 405)])
    D.edge("BUS", "F2", "power", s="r", d="l", sf=0.7, df=0.5, via=[(440, 805), (440, 680)])
    D.edge("F2", "K", "power")
    D.edge("K", "MB", "power")
    D.edge("MB", "DD", "power", s="r", d="l", sf=0.3, df=0.5, via=[(1325, 660), (1325, 565)])
    D.edge("DD", "BRK", "power", s="b", d="t")
    D.edge("BRK", "ML", "power", s="r", d="l", sf=0.3, df=0.5, via=[(1580, 649), (1580, 565)])
    D.edge("BRK", "MR", "power", s="r", d="l", sf=0.7)
    D.edge("MB", "F3", "power", s="b", d="t", sf=0.3, df=0.5, via=[(1108, 760), (1105, 760)])
    D.edge("F3", "SD", "power")
    D.edge("SD", "SM", "power")
    D.edge("MB", "B6", "power", s="b", d="l", sf=0.15, df=0.5, via=[(1069, 760), (1010, 760), (1010, 901)])
    D.edge("B6", "SV", "power")
    D.set_legend([("power", "battery / motor power"), ("logic", "logic power"), ("charge", "charging (plug removed)")],
                 40, 970, dx=330)
    return D


# =============================================================================== 4. software
def software_flowchart():
    D = Diagram("Software_Flowchart", 1810, 1230, "WB-700 - software flowchart: vision / AI stack and course state machine",
                "Concept level for Phase 1. Everything runs on the Raspberry Pi 5; the MCU closes the 500 Hz loops. "
                "Algorithms are developed and validated in Phase 2.")
    D.group(25, 125, 830, 1150, "VISION + AI STACK (per frame, 50 fps target)", "#1f8a4c", "#f3fbf6")
    D.group(860, 125, 1785, 1150, "COURSE STATE MACHINE", "#3d4654", "#fafbfc")
    D.box("A", 230, 165, 625, 245, "Capture", ["Camera Module 3 Wide, 1280 x 720 @ 50 fps"], "comp")
    D.box("B", 230, 275, 625, 365, "Rectify", ["undistort (calibrated through the shell),", "apply static seam-band mask"], "comp")
    D.box("C", 230, 395, 625, 475, "Geometry", ["IMU attitude + servo angle -> ground homography"], "comp")
    D.box("Dk", 45, 520, 405, 620, "Colour segmentation", ["red / yellow cones, adaptive HSV", "tuned on Sector 1 chevron gates"], "comp")
    D.box("F", 450, 520, 810, 620, "Optional CNN detector", ["YOLO-nano class: cones + pendulum", "(CPU, or AI HAT+ if added)"], "dev")
    D.box("E", 45, 660, 405, 750, "Cone map", ["blob filter + ground projection", "-> cone positions"], "comp")
    D.box("G", 45, 790, 405, 890, "Track model", ["yellow = left, red = right (RANSAC)", "-> lane centre, heading error, gates"], "comp")
    D.box("H", 450, 680, 810, 790, "Pendulum tracker (Sector 4)", ["bob position x(t) in a ROI;", "fit period, amplitude, phase"], "comp")
    D.box("I", 45, 930, 405, 1010, "EKF fusion", ["vision + IMU + encoders"], "comp")
    D.box("J", 450, 830, 810, 920, "Crossing-window predictor", ["time-to-cross vs. pendulum clearance"], "comp")
    D.box("K", 230, 1050, 625, 1130, "Controllers + state machine", ["speed profile, lean command, stop / go"], "mcu")
    D.edge("A", "B", "info", s="b", d="t")
    D.edge("B", "C", "info", s="b", d="t")
    D.edge("C", "Dk", "info", s="b", d="t", sf=0.25, df=0.6)
    D.edge("C", "F", "info2", s="b", d="t", sf=0.75, df=0.4)
    D.edge("Dk", "E", "info", s="b", d="t")
    D.edge("F", "E", "info2", s="l", d="r", sf=0.8, df=0.5, via=[(425, 600), (425, 705)])
    D.edge("C", "H", "info", s="r", d="r", sf=0.5, df=0.5, via=[(815, 435), (815, 735)])
    D.edge("E", "G", "info", s="b", d="t")
    D.edge("G", "I", "info", s="b", d="t")
    D.edge("H", "J", "info", s="b", d="t")
    D.edge("I", "K", "info", s="b", d="l", sf=0.5, df=0.5, via=[(225, 1090)])
    D.edge("J", "K", "info", s="b", d="r", sf=0.5, df=0.5, via=[(630, 1090)])
    # state machine: column 1 down, column 2 up
    xs1, xs2 = (935, 1235), (1450, 1750)
    rows = [165, 265, 365, 465, 565, 665, 765]
    h = 62
    st1 = [("S0", "SAFE_IDLE"), ("S1", "ARMED"), ("S2", "CALIBRATE"), ("S3", "RUNWAY"), ("S4", "RAMP_APPROACH"),
           ("S5", "RAMP_CLIMB"), ("S6", "RAMP_EXIT")]
    st2 = [("S12", "FINISH"), ("S11", "CROSS"), ("S10", "COMMIT"), ("S9", "OBSERVE"), ("S8", "PENDULUM_HOLD"),
           ("S7", "WRECKING_ZONE")]
    for (sid, nm), y in zip(st1, rows):
        D.box(sid, xs1[0], y, xs1[1], y + h, nm, [], "state", rx=26)
    for (sid, nm), y in zip(st2, rows[1:]):
        D.box(sid, xs2[0], y, xs2[1], y + h, nm, [], "state", rx=26)
    lab1 = ["arming plug in, e-stop RUN,\nself-test OK", "start trigger\n(method: organisers)", "thresholds locked\non chevron gates",
            "odometry ~13 m\nor ramp detected", "aligned in gate,\nspeed >= v_ramp", "IMU pitch back\nnear level"]
    for k in range(6):
        a, b = st1[k][0], st1[k + 1][0]
        D.edge(a, b, "info", lab1[k], s="b", d="t", lab=(1342, rows[k] + h + 19), lab_anchor="middle")
    D.edge("S6", "S4", "info", "repeat\nx 3", s="l", d="l", sf=0.5, df=0.5, via=[(897, 796), (897, 596)], lab=(897, 696))
    D.edge("S6", "S7", "info", "3 ramps done (~35 m)", s="r", d="l", lab=(1342, 818))
    lab2 = ["~53 m or pendulum seen", "stopped before swing plane", "safe window predicted", "go", "~75 m / finish seen"]
    order2 = ["S7", "S8", "S9", "S10", "S11", "S12"]
    for k in range(5):
        a, b = order2[k], order2[k + 1]
        ya = rows[6 - k]
        D.edge(a, b, "info", lab2[k], s="t", d="b", lab=(1595 if k % 2 else 1595, ya - 19))
    D.box("SAFE", 935, 880, 1750, 960, "SAFE_STOP  (from ANY state)",
          ["watchdog time-out, lane lost > 0.5 s, low battery, excessive tilt -> controlled stop"], "state_hot", rx=16)
    D.box("ESTOP", 935, 985, 1750, 1065, "E-STOP  (hardware, latching)",
          ["contactor open + changeover brake relays + PWM gated off; overrides software; re-arm only"], "state_hot", rx=16)
    D.box("NOTE", 1440, 165, 1750, 230, "Wrecking zone strategy", ["gyro heading hold + border cones"], "note", rx=8)
    D.edge("S7", "SAFE", "status", s="b", d="t", sf=0.5, df=0.75)
    D.text(935, 1105, "Distances are odometry cues from the published sector map (0-15-35-55-75 m); vision cues take priority.", 15)
    D.set_legend([("info", "data / transition"), ("info2", "optional path"), ("status", "fault transition")], 40, 1195, dx=300)
    return D


if __name__ == "__main__":
    exe = next(b for b in BROWSERS if pathlib.Path(b).exists())
    for fn in (system_architecture, electronics_architecture, power_distribution, software_flowchart):
        d = fn()
        png, size = d.write(SVG, HERE, FIG, exe)
        print(f"{d.name}: {png.name} {size[0]}x{size[1]} px")
