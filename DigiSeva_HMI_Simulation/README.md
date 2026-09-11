# EcoDrive Intelligence — Live HMI Simulation
**Team DigiSeva** · Schneider Electric HMI Hackathon 2026 · Round 1/2 prototype

A self-contained, **offline** interactive HMI + energy-optimization simulation of the 30 kW
variable-demand water pumping station from our proposal. No installation, no internet, no
dependencies — it is a single `index.html` file that runs in any modern browser.

---

## ▶ How to run
1. Double-click **`index.html`** → it opens in your default browser (Chrome/Edge/Firefox).
2. It auto-starts running. Use the right-hand **control panel** and **Demo Scenarios** to drive it.
3. That's it — works with the Wi-Fi off, on any laptop, even at the venue.

## 📎 How to attach it to the PowerPoint
- **Best:** zip this whole folder (`DigiSeva_HMI_Simulation.zip`) and upload/attach it alongside the PPTX, or
- **Link it:** put the zip on Google Drive and paste the link on a slide, or
- **Embed proof:** drop `Screenshot_1_Overview.png`, `Screenshot_2_Energy.png`, and
  `Screenshot_3_SystemCurve.png` onto **Slide 3** — this directly strengthens Objective 2
  (intuitive HMI screens), which is the highest-value gap for an HMI-focused jury.

---

## 🎬 5-minute live demo script (for Round 2 / to narrate over the screenshots)
1. **Baseline vs VFD** — click **DRIVE → FIXED+VALVE**: watch active power jump (~21 kW) and the
   "instant saving" show what VFD recovers. Switch back to **VFD** → power drops (~10 kW). *"Same
   water delivered, ~50% less energy — that's the affinity law, P ∝ N³."*
2. **System curve** — open the **System Curve** tab: show the red operating point sliding down the
   green (reduced-speed) pump curve as demand falls. *"We only save on the friction component —
   the static head is honest overhead. This is calibrated, not the ideal cube law."*
3. **Sleep Mode** — let demand fall (or set Demand → MANUAL, low). VFD Sleep activates and stops the
   pump; the fixed-speed shadow still burns ~6 kW. Cumulative saving climbs.
4. **Alarms (ISA-18.2)** — click **Trigger Dry-Run**: a P1 flashing banner appears, the alarm table
   logs it with priority/timestamp, press **ACK**. Then **Comm Loss** → safe-state P2.
5. **Energy dashboard** — show SEC (0.31 vs 0.58 baseline), power-factor colour band, cumulative
   kWh, ₹ cost avoided and CO₂ — updating live.

---

## 🔬 The model (why the numbers are defensible)
- **Pump affinity laws**: flow ∝ N, head ∝ N², power ∝ N³ (friction component).
- **System curve**: `H_total = H_static + H_friction` (static 8 m + friction k·Q²) — so savings are
  *calibrated to the static/friction split*, exactly as in the proposal. Raise the setpoint and you
  can **watch the savings shrink** (static-dominated) — a live proof of our §8.1a argument.
- **PID pressure control** adjusts VFD speed to hold the header-pressure setpoint.
- **Baseline shadow**: a fixed-speed + throttle-valve pump delivering the *same* water is computed
  every tick, so VFD-vs-baseline energy is a fair, continuous comparison.
- At the default **3.0 bar** setpoint over a diurnal demand cycle the model produces
  **SEC ≈ 0.31 (VFD) vs 0.58 (fixed-speed), ~46–50 % energy saved, peak ~26 kW** — matching the
  headline figures in the deck. These were validated numerically, not asserted.

## ✅ Which hackathon objectives it demonstrates
| # | Objective | In the sim |
|---|-----------|-----------|
| 1 | Comms architecture (PLC-HMI-VFD-Meter) | Mimic shows M241 ↔ ATV630 ↔ PM5300 ↔ HMI with live tags |
| 2 | **Intuitive HMI screens** | Overview mimic, Energy dashboard, Alarms, Trends, System-Curve (ISA-101 styling) |
| 3 | PLC control logic | PID pressure loop, AUTO/MANUAL, soft states, interlocks |
| 4 | Energy monitoring dashboards | Full energy tab: power, SEC, PF, THD, kWh, ₹, CO₂ |
| 5 | Alarm & event management | ISA-18.2 priorities P1–P4, ACK, event log, banner |
| 6 | Data analysis & optimization | Live SEC, VFD-vs-baseline savings, recommendations, sleep/energy-adapt |
| 7 | Remote monitoring (IoT) | Browser-based HMI = the remote/web client concept |

## Notes
- All values are a physics-based *simulation* for demonstration; real deployment uses the Schneider
  stack (Modicon M241, Altivar ATV630, PowerLogic PM5300, Harmony GTU, EcoStruxure Machine Advisor).
- `#overview` / `#energy` / `#alarms` / `#trends` / `#curve` can be appended to the file URL to
  deep-link a specific screen.
