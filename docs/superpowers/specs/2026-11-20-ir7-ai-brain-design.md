# IR 7.0 Upgrade — "AI Brain" for the Smart Environmental & Monitoring System

Author: Muhammad Muaz Bin Md Fazli, UniKL MFI · Design date: 2026-11-20

## Context
Muaz is presenting this mini project at a university in Indonesia as a **live demo on one laptop**.
The demo runs Proteus (simulated Arduino Uno), the Python bridge, Mosquitto and the Node-RED dashboard.
Today the system is IR 4.0-level. The Arduino reads the sensors and decides the fan itself with fixed
thresholds. Data flows one way only: Arduino → COM2 → `Module_4_MQTT_Mosquitto.py` → Mosquitto
`muaz/iot/mfi` → Node-RED (System V1 tab) → SQLite. Nothing upstream ever decides or acts.
The goal is a version the audience can *watch* behave like an IR 7.0 system.

**Working definition of IR 7.0** (there is no official one; this is our call, stated on a slide):
IR 4.0 connectivity + IR 5.0 human-centric/sustainable, plus:
1. **Autonomous intelligence**: the system predicts and decides.
2. **Closed-loop, self-healing control**: decisions flow back to the device, and the device falls back safely if the AI disappears.
3. **Human–machine collaboration**: it explains *why* it acted, and a person can override it.
4. **Sustainability**: it measures fan energy and the CO₂ saved compared with the old fixed rule.

## Goals / non-goals / anti-goals
- **Goals:** all four pillars above visible live in the dashboard within a 10–15 min demo. Runs fully offline. Code is short, with few comments and the name/UniKL MFI/topic header on top (Muaz's style preference).
- **Non-goals:** cloud/LLM chatbot (approach B, rejected: venue internet risk); real hardware; redesigning the existing V1/V2 dashboards; editing the slides (separate task).
- **Anti-goals:** a demo that breaks when the Python AI or Mosquitto stops. The Arduino must keep working on its local rules. "AI" that is just the same thresholds renamed.

## Approaches considered
- **A. AI brain in Python + two-way control + new Node-RED panel — CHOSEN.** The only option where the system visibly decides, acts, explains itself and accepts an override, all offline.
- B. Digital twin + Claude chatbot: biggest wow factor, but needs internet and an API key at the venue. Rejected.
- C. Node-RED-only forecast/KPIs: control stays one-way, so the IR 7.0 story is weak. Rejected.

## Design

### Architecture (new parts marked ★)
```
Proteus Arduino ──CSV(8 fields)──► Module_4 bridge ──► muaz/iot/mfi ──► Node-RED V1 (existing) + SQLite
      ▲  ★ reads FAN:ON / FAN:OFF / AUTO              │
      └──────── ★ bridge writes muaz/iot/mfi/cmd ◄────┤
                                                       ▼
                         ★ Module_7_AI_Brain.py (subscribes muaz/iot/mfi + muaz/iot/mfi/override)
                           ├─ publishes muaz/iot/mfi/ai   (JSON: score, forecast, anomaly, decision, reason, energy)
                           ├─ publishes muaz/iot/mfi/cmd  (the only writer of commands)
                           └─ inserts into SQLite AI_Events
                         ★ Node-RED "IR 7.0 AI Brain" group ← muaz/iot/mfi/ai ; override switch → muaz/iot/mfi/override
```

### 0. Proteus wiring check (Muaz, in Proteus — first step)
Muaz reports the COMPIM is wired **TX → TX**, which carries Arduino → PC data. Commands need the other direction: **COMPIM RXD → Arduino RX (D0)**. In Proteus's COMPIM the pins are usually wired straight across (RXD–RX, TXD–TX). Step: check that the RXD–RX wire exists and add it if not (`Circuit/MODULE 3 CIRCUIT.pdsprj`). Then verify with a tiny echo sketch or the new firmware: send `FAN:ON` from Python and confirm the LCD shows `AI CONTROL`.

### 1. Arduino firmware (`Arduino/Module_3_V3/Module_3_V3.ino` → new `Arduino/Module_7_IR7/Module_7_IR7.ino`)
- Copy V3 so the working version stays untouched. Add the name header comment.
- Read `Serial` lines each loop (non-blocking): `FAN:ON`, `FAN:OFF` → remote mode; `AUTO` → local mode.
- **Watchdog:** in remote mode, revert to local rules if no command arrives for 10 s (the self-healing demo moment).
- Fix the existing order bug: `fanControl()` runs before the sensors are read, so it uses last loop's values. Move it after the reads.
- The CSV gets an 8th field: `AI` or `LOCAL` (the mode the fan is actually under). LCD line 0 shows `AI CONTROL` or `LOCAL CONTROL`.
- Keep `delay(2000)`, but poll serial in short slices so commands aren't missed (builder's call how).

### 2. Bridge (`Python/Module_4_MQTT_Mosquitto.py`)
- Accept 7 or 8 fields; add `"mode"` to the JSON payload (default `"LOCAL"` when there are 7 fields).
- Subscribe to `muaz/iot/mfi/cmd` and write each payload + `\n` to the open serial port. A serial write needs the port shared between the reader generator and the MQTT callback; a simple module-level reference + lock is fine.
- `--simulate` gains the mode field and honours commands (fake fan follows `FAN:*`, reverts after 10 s). This makes the backup demo work without Proteus.

### 3. AI brain (new `Python/Module_7_AI_Brain.py`, short style, header comment)
Pure functions (unit-tested) + a small MQTT loop. Uses only the stdlib + `paho-mqtt`; numpy is optional.
- **Environmental Health Score 0–100:** weighted distance of each reading from its comfort band (bands = existing thresholds: T<37, 30<H<60, dust<55, 980<P<1050, light>500).
- **Forecast:** least-squares slope over the last 30 readings (~60 s) for temperature, humidity and dust. Report "reaches threshold in N min" if the trend is upward and the threshold falls inside 10 min.
- **Anomaly / sensor-health:** a jump bigger than a fixed per-sensor step (e.g. T>5 °C, H>15 %, dust>30 in one reading) → "sudden spike". A z-score is not used, because Proteus values sit flat and have near-zero variance, so every click would flag. Out of physical range or `nan` → "sensor fault". A "stuck sensor" check exists but is **off by default** (`STUCK_CHECK = False`), because Proteus sensors only change when clicked *(our call)*.
- **Decision (only acts when occupied, distance<100):** *Muaz's decision: fan-fixable triggers only.* Fan ON if temperature ≥37, humidity ≥60 or dust ≥55 **or** a forecast says one of those will be crossed within 3 min (*pre-emptive*). Low light, low/high pressure and low humidity → alert + "why" text only, no fan. That is the honest energy saving compared with the old rule, which also ran the fan for light ≤500 and pressure ≥1050. The Arduino's LOCAL fallback keeps the old rule unchanged. Fan OFF only after all are back inside the bands with a 2-reading hysteresis (stops on/off flapping). Unoccupied → OFF.
- **Explanation:** one plain sentence built from the triggering facts, e.g. *"Fan ON: humidity 58 % rising 1.2 %/min, will exceed 60 % in ~2 min, so cooling early."*
- **Human override:** `muaz/iot/mfi/override` payload `AUTO` | `ON` | `OFF`. While ON/OFF, the AI sends that command and labels its decision "HUMAN OVERRIDE" but still shows what it *would* do.
- **Heartbeat:** publish `cmd` on every reading (≤2 s) so the Arduino watchdog stays satisfied. If the brain stops, the Arduino reverts to LOCAL within 10 s.
- **Energy & CO₂:** integrate the fan's ON time × `FAN_POWER_W` (constant, default 5 W) for the AI decisions vs a shadow run of the *old fixed rule* on the same readings. Show kWh used, kWh saved (can be negative) and CO₂ = kWh × `GRID_KG_PER_KWH` (constant; builder sets a cited value for the Malaysia grid and notes it on a slide).
- **Logging:** insert into a new SQLite table `AI_Events(ID, Timestamp DEFAULT local time, Type, Message)`, created if missing, only on state changes (decision flips, anomaly start/end, override changes), not every 2 s. Use `Database/Sensor_database.db` (the same file the Node-RED V1 SQLite node uses).
- CLI: `--broker`, `--topic`; no other flags.

### 4. Node-RED custom HTML dashboard (Muaz's choice: an HTML page served by Node-RED on the local PC, not `node-red-dashboard` ui_* widgets)
Delivered as an importable flow `Node-RED/IR7_HTML_Dashboard.json` (new tab "IR 7.0 Dashboard"). Muaz imports it with Ctrl+I → Deploy; we don't edit `~/.node-red/flows.json` directly (Node-RED overwrites it while running).
- **Page:** `http in GET /ir7` → `template` (one self-contained HTML/CSS/JS page) → `http response`. Opened at `http://localhost:1880/ir7`.
- **Live data:** `mqtt in` `muaz/iot/mfi` + `muaz/iot/mfi/ai` → small function that tags `{type:"sensor"|"ai", data}` → `websocket out` at `/ws/ir7`. The page connects with `new WebSocket("ws://" + location.host + "/ws/ir7")`. No Mosquitto websocket listener is needed.
- **Override:** page buttons AUTO / ON / OFF → `websocket in /ws/ir7` → `mqtt out muaz/iot/mfi/override`.
- **AI Events log:** on page load and every 10 s, the page fetches `GET /ir7/events` → `sqlite` (`SELECT * FROM AI_Events ORDER BY ID DESC LIMIT 20`, same DB config node `50a196d0c453da90`) → JSON response.
- **Fully offline:** no CDN libraries; charts are drawn with inline SVG/canvas so the demo works without internet.
- **Contents:** sensor tiles (T, H, P, dust, light, distance, occupancy), Health Score ring, control-mode badge (AI / LOCAL / HUMAN), "why" sentence, forecast line, anomaly alert, live temperature/humidity trend (last ~60 points held in the page), energy/CO₂ card, override buttons, AI Events table, a connection indicator, and the name/UniKL MFI/topic header in the page title bar.
- The existing V1/V2 dashboards stay as they are. Import notes also include the one-line fix to the existing "Sql Insert" fan bug (`Number(data.fan_state) === 1 ? "ON" : "OFF"`).
- The HTML source is also kept as `Node-RED/ir7_dashboard.html` so it can be edited and diffed. A tiny build step isn't needed; the builder pastes it into the template node in the JSON.

### Demo script (what the audience sees)
1. Normal room → score high, AI CONTROL, fan off.
2. Raise DHT11 humidity step by step in Proteus → forecast appears → the fan turns ON **before** 60 %, with the "why" sentence.
3. Flip the override switch to OFF → HUMAN badge; the AI shows what it disagrees with.
4. Stop `Module_7_AI_Brain.py` → within 10 s the LCD shows LOCAL CONTROL and the fan follows the old rules (self-healing).
5. Point at the energy/CO₂ panel and the AI Events log.

### Left to the builder
Exact score weights, the dashboard layout/colours, the serial-polling technique on the Arduino, and how the bridge shares the serial port.

## Files
- New: `Arduino/Module_7_IR7/Module_7_IR7.ino`, `Python/Module_7_AI_Brain.py`, `Python/test_ai_brain.py`, `Node-RED/IR7_HTML_Dashboard.json`, `Node-RED/ir7_dashboard.html`, `docs/superpowers/specs/2026-11-20-ir7-ai-brain-design.md` (this design, committed)
- Modified: `Python/Module_4_MQTT_Mosquitto.py`, `README.md` (an IR 7.0 section), `Circuit/MODULE 3 CIRCUIT.pdsprj` (by Muaz, only if the RXD–RX wire is missing)
- Untouched: V1/V2 flows, `Module_3_V3.ino`, existing DB data (only the new `AI_Events` table is added)

## Verification
1. `python -m pytest Python/test_ai_brain.py`: score, forecast (synthetic rising series → correct ETA), anomaly (spike / stuck), decision hysteresis, override, energy shadow comparison.
2. Mosquitto running (`C:\Program Files\mosquitto`), then `python Module_4_MQTT_Mosquitto.py --simulate` + `python Module_7_AI_Brain.py`. Watch with `mosquitto_sub -t "muaz/iot/#" -v` that `ai` and `cmd` messages flow, then that the fake fan follows commands and reverts to LOCAL ~10 s after the brain is killed.
3. Compile the firmware in the Arduino IDE (no arduino-cli installed), load the .hex in Proteus, and run the full demo script above on COM2.
4. Import `IR7_HTML_Dashboard.json`, Deploy, open `http://localhost:1880/ir7`. Check that the tiles and AI panel update every 2 s, the override buttons change the mode badge and the fan, the events table fills, and the page still works with Wi-Fi off.

## Next step after approval
Commit this design to `docs/superpowers/specs/`, then invoke `superpowers:writing-plans` to turn it into a step-by-step implementation plan.
