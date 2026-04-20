# 🌱 Smart Environmental Monitoring Control System

## 📌 Project Overview

This project is designed to monitor and control environmental conditions such as **temperature, humidity, air quality, light intensity, and distance detection** in real-time.

It integrates multiple sensors with a microcontroller and a visualization platform (Node-RED) to provide accurate monitoring and potential automation control.

This system is suitable for applications such as **smart homes, greenhouses, laboratories, and industrial environments**.

---

## ⚙️ System Features

* 🌡️ Temperature monitoring
* 💧 Humidity tracking
* 🌫️ Air quality / dust detection
* 📏 Distance measurement (object detection)
* 💡 Light intensity sensing
* 📊 Real-time data visualization (Node-RED)
* ⚡ Motor control using driver circuit

---

## 🧰 Components Used

### 🔌 Sensors

* **DHT11** → Temperature & Humidity sensor
* **BMP180** → Atmospheric pressure sensor
* **PPD42** → Dust / air quality sensor
* **HC-SR04 Ultrasonic** → Distance measurement
* **LDR** → Light intensity detection

### ⚙️ Actuator & Driver

* **L293D Motor Driver** → Controls DC motor direction and speed
* **DC Motor** → Used for control action (e.g., fan/ventilation system)

---

## 🧠 System Architecture

Sensor Data → Arduino → Data Processing → Node-RED → Dashboard Display → Motor Control

---

## 📂 Project Structure

* `/Arduino` → Microcontroller code
* `/Node-RED` → Flow configuration (.json)
* `/Report` → Project documentation
* `/Images` → Circuit diagrams and setup

---

## 🚀 How It Works

1. Sensors collect environmental data continuously
2. Arduino reads and processes sensor inputs
3. Data is transmitted to Node-RED
4. Node-RED dashboard displays real-time values
5. Motor can be activated based on conditions (e.g., high temperature or poor air quality)

---

## 📈 Example Output

* Temperature & humidity graph
* Air quality monitoring display
* Distance detection readings
* Light intensity indication
* Real-time dashboard interface

---

## 🔧 Future Improvements

* IoT integration (MQTT / cloud monitoring)
* Mobile application interface
* Automated decision-making system
* Data logging and analytics

---

## 👨‍💻 Author

**Muaz Fazli**
Mechatronics Engineering Student

---

## 📜 License

This project is for academic and educational purposes.
