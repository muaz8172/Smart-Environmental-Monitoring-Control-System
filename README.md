# 🌱 Smart Environmental Monitoring Control System

## 📌 Project Overview

This project is a **multi-module environmental monitoring and control system** that collects, processes, and visualizes real-time data such as temperature, humidity, air quality, light intensity, and distance.

The system integrates **Arduino, Python, Node-RED, and database systems** to provide a complete monitoring solution with control capability.

---

## 📂 Project Structure

```
/Arduino      → Microcontroller programs (sensor reading & control)
/Python       → Data processing, communication (HTTP/MQTT), database handling
/Node-RED     → Dashboard visualization
/Database     → Stored sensor data (Access, SQLite, CSV)
/Circuit      → Proteus circuit design
README.md
```

---

## ⚙️ System Features

* 🌡️ Temperature & humidity monitoring (DHT11)
* 🌫️ Air quality detection (PPD42)
* 📏 Distance measurement (HC-SR04)
* 💡 Light intensity sensing (LDR)
* 📊 Real-time dashboard (Node-RED)
* 🔄 Data storage (SQLite / Access / CSV)
* ⚡ Motor control using L293D

---

## 🧰 Components Used

**Sensors:**

* DHT11 → Temperature & Humidity
* BMP180 → Pressure
* PPD42 → Dust / Air Quality
* HC-SR04 → Distance
* LDR → Light

**Actuator:**

* L293D Motor Driver + DC Motor

---

## 🧠 System Architecture

Sensors → Arduino → Python Processing → Database → Node-RED Dashboard → Control Action

---

## 📘 Module Explanation

### 🔹 Module 3 – Sensor Integration (Arduino + Python)

This module focuses on **reading sensor data and basic processing**.

**Files:**

* `Module_3.ino`, `Module_3_V2.ino`, `Module_3_V3.ino`
* `Module_3.py`, `Module_3V2.py`

**Function:**

* Collect data from sensors (DHT11, LDR, Ultrasonic, etc.)
* Send data to computer via serial communication
* Python reads and formats the data

👉 This is the **core data acquisition stage**

---

### 🔹 Module 4 – Communication Protocol (HTTP & MQTT)

This module handles **data transmission between systems**.

**Files:**

* `Module_4_HTTP.py`
* `Module_4_MQTT.py`

**Function:**

* Send sensor data using **HTTP requests**
* Send real-time data using **MQTT protocol**
* Connect system to Node-RED or external platforms

👉 This enables **real-time IoT communication**

---

### 🔹 Module 5 – Database Management

This module manages **data storage and retrieval**.

**Files:**

* `Module_5_M_ACCESS.py`
* `Module_5_SQLITE.py`
* `Sensor_database.accdb`
* `Sensor_database.db`
* `sensor_data.csv`

**Function:**

* Store sensor data into databases
* Support multiple formats:

  * Microsoft Access
  * SQLite
  * CSV
* Retrieve and manage stored data

👉 This provides **data logging and history tracking**

---

### 🔹 IR 7.0 AI Brain (closed-loop, self-healing, human-in-the-loop)

The system moves from *monitoring* to *autonomous control*:

| IR 7.0 pillar | What the demo shows |
|---|---|
| Autonomous intelligence | Health score 0–100, trend forecast ("humidity will exceed 60 % in ~2 min"), anomaly / sensor-fault detection |
| Closed-loop, self-healing control | AI sends `FAN:ON` / `FAN:OFF` back to the Arduino; if the AI stops, the Arduino returns to its own rules within 10 s |
| Human–machine collaboration | Every action comes with a one-line "why"; the dashboard override (Auto / On / Off) always wins |
| Sustainability | Fan energy (Wh) and CO₂ compared with the old fixed rule; the AI only runs the fan for what a fan can fix (temperature, humidity, dust) |

```
Proteus Arduino ⇄ COM2 ⇄ serial_mqtt_bridge ⇄ Mosquitto ⇄ ai_brain
                                              ⇅
                       Node-RED http://localhost:1880/ir7  (+ SQLite AI_Events)
```

**Firmware safety (IEC 60730-1 Annex H / IEC 61508-3 principles):** 8 s hardware watchdog, I2C timeout, sensor plausibility checks (DHT11 `nan`, missing or implausible BMP180, no ultrasonic echo). On a sensor fault the LCD shows **SENSOR FAULT**, the red LED and buzzer turn on, the fan goes to its safe state (OFF), and the faulty value is sent as `nan` so the dashboard never shows it as live. If the PC stops sending commands for 10 s the Arduino returns to its local rules.

**Files:** `Arduino/smart_env_firmware/smart_env_firmware.ino`, `Python/serial_mqtt_bridge.py`, `Python/ai_brain.py`, `Python/serial_link_check.py`, `Node-RED/IR7_HTML_Dashboard.json` (built from `ir7_dashboard.html` by `build_ir7_flow.py`)

**Setup (once)**
1. Proteus: COMPIM **TXD → Arduino TX** (data out) and **RXD → Arduino RX / D0** (commands in). Load `Arduino/smart_env_firmware/build/smart_env_firmware.ino.hex`. Check the link with `python serial_link_check.py` (it must say OK).
2. Node-RED: Ctrl+I → select `Node-RED/IR7_HTML_Dashboard.json` → Import → Deploy. It reuses your existing *Mosquitto* broker and *Sensor_database* SQLite config nodes.
3. Optional fix in the System V1 "Sql Insert" node: `let fan = Number(data.fan_state) === 1 ? "ON" : "OFF";`

**Run order:** Mosquitto → Node-RED → Proteus → `python serial_mqtt_bridge.py` (or `--simulate` without Proteus) → `python ai_brain.py` → open `http://localhost:1880/ir7` (add `?demo` to rehearse with fake data). Everything runs offline.

**Demo script**
1. Normal room → score high, *AI control*, fan off.
2. Raise DHT11 humidity step by step → forecast appears → fan turns ON **before** 60 % with the reason.
3. Press *Fan off* → *Human override*; the AI shows what it would do instead.
4. Stop `ai_brain.py` → within 10 s the LCD shows *LOCAL CONTROL* (self-healing).
5. Show the energy/CO₂ card and the AI event log.

**Tests:** `python -m pytest Python -q`

**Alarm limits (IEC 62682 rationalization; same values in `Python/ai_brain.py` and the dashboard)**

| Sensor | Low alarm | Low warning | High warning | High alarm | Deadband | Operator action |
|---|---|---|---|---|---|---|
| Temperature (°C) | – | – | 35 | 37 | 0.5 | Fan on (AI does this automatically) |
| Humidity (%) | 30 | 35 | 55 | 60 | 1 | High: fan on · Low: check room, no fan |
| Pressure (hPa) | 980 | 985 | 1045 | 1050 | 1 | Check sensor / weather; no fan |
| Dust (index) | – | – | 50 | 55 | 2 | Fan on, check air quality |
| Light (ADC 0–1023) | 500 | 550 | – | – | 10 | Turn on lighting; no fan |

Priorities: **Alarm** (past alarm limit, red, flashes until acknowledged) and **Warning** (past warning limit, yellow). An alarm clears only after the value moves back past its limit by the deadband; a cleared alarm stays listed until acknowledged. Alarm state and acknowledgement are kept by `ai_brain.py`, so they survive a page reload and match on every screen. While the room is empty, the comfort alarms (temperature, humidity, dust, light) are shown as **Suppressed** instead of alarming; pressure alarms stay active. If no sensor data arrives for more than 6 s (3 missed readings), every value is greyed out and marked **Stale**, and the header shows **No sensor data**, so old values are never shown as live. Normal readings show no badge (ISA-101: no news is good news). The header shows an alarm chip on every tab (click it to jump to the alarm list), the current time with the time of the last reading, and a yellow **Manual · mm:ss left** chip during a human override; the override returns to AI control automatically after 15 min (`OVERRIDE_MAX_S` in `ai_brain.py`). Colours follow ISA-101 / IEC 63303 high-performance HMI: normal readings are grey, and colour appears only for abnormal states using the IEC 60073 meanings (yellow warning, red alarm).

> CO₂ uses `GRID_KG_PER_KWH = 0.758` (Peninsular Malaysia grid factor) — verify the latest Suruhanjaya Tenaga figure before quoting it on a slide.

---

## 📊 Visualization (Node-RED)

**File:**

* `Dashboard_V2.json`

**Function:**

* Display real-time sensor data
* Plot graphs (temperature, humidity, etc.)
* Provide monitoring dashboard interface

---

## 🔌 Circuit Design

**File:**

* `MODULE 3 CIRCUIT.pdsprj`

**Function:**

* Simulated using Proteus
* Shows full hardware connection of sensors and Arduino

---

## 🚀 How the System Works

1. Sensors collect environmental data
2. Arduino reads and sends data
3. Python processes and transmits data
4. Data is stored in database
5. Node-RED displays real-time dashboard
6. System can trigger control actions (motor)

---

## 🔧 Future Improvements

* Cloud integration (Firebase / IoT platform)
* Mobile monitoring application
* AI-based prediction system
* Fully automated control system

---

## 👨‍💻 Author

**Muaz Fazli**
Mechatronics Engineering Student

---

## 📜 License

This project is for academic and educational purposes.
