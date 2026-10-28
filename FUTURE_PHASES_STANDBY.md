# Future phases: STANDBY (not started; requires explicit authorisation)

These workstreams are recorded only. None is active until the team authorises the next phase.

## PHASE 2: target November 15, 2026 (Virtual Design & Simulation Audit)

- [ ] Final actuator torque and gear-ratio sizing (0.8 ft ramp worst case; select the gearmotor part number)
- [ ] Ramp feasibility and stability analysis (with organiser-confirmed ramp geometry)
- [ ] Detailed battery and runtime validation
- [ ] Dynamics and full-track simulation
- [ ] Camera-based cone-detection implementation
- [ ] Complete autonomous state machine
- [ ] Pendulum motion estimation and safe-crossing validation
- [ ] Detailed emergency-stop verification (latency and fail-safe bench tests)
- [ ] Technical simulation report

## PHASE 3: December 16-17, 2026 (IIT Bombay)

- [ ] Hardware procurement and fabrication
- [ ] Assembly and electrical integration
- [ ] Physical ramp tests
- [ ] Vision and lighting calibration
- [ ] Barrier-contact tests
- [ ] Pendulum-gate trials
- [ ] Emergency-stop and safety inspections
- [ ] Full-course timed runs
- [ ] Repairability and competition-day preparation

## Design dependencies recorded in Phase 1 (to be resolved later; none blocks Phase 1)

| Dependency | Needed by | Source |
|---|---|---|
| Ramp angle, length, entry lip and exit geometry | Phase 2 motor sizing | Organiser Q3 |
| Track/gate width, cone size, track shape | Phase 2 steering and lane model | Organiser Q4 |
| Pendulum size, period, amplitude, position | Phase 2 crossing algorithm | Organiser Q6 |
| Definition of "electrical isolation"; kill-switch requirements | Phase 2 safety design | Q8, Q9 |
| Gearmotor, steering motor, BMS and driver part selection (replace PH envelopes) | Phase 2 | TDD sections 14, 16, 17 |
| 700 mm PC hemisphere supplier, tolerance and lead time | Phase 3 (start enquiries early) | Risk R9 |
| Measured masses and CG (suspension test) | Phase 3 | TDD section 10 |
| Pi 5 thermal behaviour in the sealed shell | Phase 2 estimate, Phase 3 test | Risk R11 |
