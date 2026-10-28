# Open Questions for the Organizers (post in the official "Doubts" section)

Prepared 2026-10-21 for the Techfest 2026-27 Wrecking Ball Challenge. Ask Q1-Q2 first, because they
affect the Round 1 submission due **October 25, 2026**.

| # | Topic | Question | Why it matters to our design |
|---|---|---|---|
| Q1 | Originality / AI | Rule 3 prohibits external AI tools "during live rounds". Is AI-assisted preparation of the Round 1 CAD abstract allowed, and must it be disclosed? | Our documents were drafted with AI assistance; the team must review and own every decision. |
| Q2 | Submission | In what format and through what channel is Round 1 submitted (copy of the Google Doc template, PDF or DOCX upload)? Are there page or file-size limits? | Determines the final export. |
| Q3 | Ramps | For the 0.2 / 0.4 / 0.8 ft ramps: incline angle or length, surface material, entry lip, and what is beyond the top (down-ramp, platform or drop)? | Pendulum-drive capability depends on the angle (12.4° quasi-static baseline); a lip over ~11 mm needs momentum. |
| Q4 | Track | Track width, gate widths, cone size and spacing; is the 75 m course straight or curved? Floor material? | Cone-contact penalties, steering needs, FOV checks. |
| Q5 | Diameter check | Is the 2.0-2.5 ft diameter measured over the shell only or over every exterior feature? Are the limits exclusive? Is there a weight limit (inspection lists "weight")? | Our caliper is 696.3-700.7 mm; no weight limit is assumed. |
| Q6 | Pendulum | Bob size, mass and height above the floor; swing amplitude and period; exact position; is contact a penalty or DNF? | Timing algorithm and safety margin. |
| Q7 | Low-density obstacles | Size, mass and arrangement; fixed or loose; is pushing them aside allowed without penalty? | Momentum and heading-hold strategy. |
| Q8 | Electrical isolation | What exactly is checked under "electrical isolation" at inspection? | We provide an external anti-spark arming plug (left hub). |
| Q9 | Kill switch | Any required frequency band, range, latency or fail-safe behaviour? Are organizer-supplied kill switches used? Is a team-built 2.4 GHz heartbeat e-stop acceptable? | Safety-supervisor design. |
| Q10 | Start | How is a run started (timer, onboard trigger or wireless start signal)? Is calibration time allowed before the clock starts? | State machine ARMED to CALIBRATE. |
| Q11 | Sensors | The PDF says "supplementary **internal** sensors"; the website omits "internal". Are external distance sensors allowed? | We use internal sensors only; clarification for completeness. |
| Q12 | Battery | Any chemistry, voltage or capacity limits, or rules for charging at the venue? | Our 6S1P Li-ion pack is about 97 Wh. |
| Q13 | Restarts | Can the robot be adjusted or charged between the 3 restart attempts? | Service procedure. |
