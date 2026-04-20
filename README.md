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
