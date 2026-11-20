# Physical Build: Real Arduino Uno (UniKL x ITS, Surabaya)

Everything needed to run the system on real hardware. It uses the same logic as the Proteus version; the only firmware change is the real LCD I2C address.

```
Physical_Build/
├── arduino/smart_env_physical/smart_env_physical.ino   ← upload this to the Arduino Uno
├── arduino/i2c_scanner/i2c_scanner.ino                 ← use only if the LCD stays blank
├── python/serial_mqtt_bridge.py                        ← Arduino ⇄ Mosquitto
├── python/ai_brain.py                                  ← AI decisions, alarms, forecast
├── python/find_port.py                                 ← shows which COM port is the Arduino
├── python/requirements.txt
└── start_demo.bat                                      ← starts bridge + AI brain + dashboard
```

## 1. Wiring

| Part | Pin(s) | Arduino |
|---|---|---|
| DHT11 module | DATA | **D4** |
| PPD42NS | OUT (pin 4) | **D5** |
| HC-SR04 | TRIG / ECHO | **D11 / D12** |
| LDR (bare) | 5V → LDR → **A1** → 10 kΩ → GND | **A1** |
| BMP180 (GY-68) | SDA / SCL | **A4 / A5** |
| 16×2 LCD (I2C) | SDA / SCL | **A4 / A5** (shared with BMP180) |
| Red LED + 330 Ω | anode | **D2** |
| Green LED + 330 Ω | anode | **D3** |
| Active buzzer (2-pin, 5V) | + | **D8** |
| L298N | ENA (**remove the jumper cap**) / IN1 / IN2 | **D6 / D10 / D9** |
| L298N | OUT1 / OUT2 | 12V fan |
| L298N | 12V / GND | 12V 2A adapter |

- All sensors, the LCD and the buzzer run on the Arduino **5V** pin (about 320 mA in total; a laptop USB port supplies 500 mA).
- **Connect all GNDs together**: Arduino, L298N and the 12V adapter.
- Do **not** connect the L298N 5V pin to the Arduino 5V pin.
- The Arduino is powered and talks to the laptop through the **USB cable** (this replaces COMPIM / com0com).

## 2. Upload the firmware (Arduino IDE)

1. Install the libraries (Sketch → Include Library → Manage Libraries):
   - **LiquidCrystal I2C** (Frank de Brabander)
   - **Adafruit BMP085 Library** (works for the BMP180)
   - **DHT sensor library** (Adafruit) and **Adafruit Unified Sensor**
2. Open `arduino/smart_env_physical/smart_env_physical.ino`.
3. Tools → Board → **Arduino Uno**; Tools → Port → the Arduino's COM port.
4. Click **Upload**.
5. Test: open Serial Monitor at **9600 baud**. Every 2 s you should see a line like
   `31.40,52.00,1010.89,0.00,612,45.20,OFF,LOCAL`
6. **Close the Serial Monitor** before starting the Python bridge; only one program can use the COM port.

The LCD shows `IR 7.0 SMART / ENVIRONMENT`, then the room status. If it stays blank, upload `i2c_scanner`, read the address in the Serial Monitor, and change `LCD_ADDR` at the top of the firmware (usually `0x27` or `0x3F`). The contrast screw on the back of the LCD backpack can also make the text invisible, so turn it slowly.

## 3. Laptop software (once)

```
py -m pip install -r python\requirements.txt
```
You also need Mosquitto (running as a Windows service) and Node-RED, with `Node-RED/Smart_Env_SQLite_Flows.json` imported (see the main README).

## 4. Run the demo

1. Start **Mosquitto** and **Node-RED** (`node-red`).
2. Plug in the Arduino USB cable and the 12V adapter.
3. Double-click **`start_demo.bat`**. It lists the COM ports; type the one marked `<- Arduino` (e.g. `COM3`), or run `start_demo.bat COM3`.
4. The bridge and AI brain open in two windows, and the dashboard opens at http://localhost:1880/ir7.

Manual commands (from the `python` folder):
```
py find_port.py
py serial_mqtt_bridge.py --port COM3
py ai_brain.py
```

Opening the COM port resets the Arduino, so the first reading arrives about 3 s after the bridge starts. This is normal.

## 5. Real hardware notes

- **PPD42NS:** keep it upright and let it warm up for about 1 minute; dust reads 0 in clean air.
- **DHT11:** reads every 2 s (its minimum is 1 s), so this is fine.
- **Surabaya climate:** room humidity is often 65–80 %, above the 60 % humidity alarm, so the fan may run all the time. If so, raise the humidity limits in **all four** places: `LIMITS` in `ai_brain.py`, the local rule in the firmware (`humidity >= 60`), the dashboard limit table, and `Alarm_Limit` in `Database/schema.sql`.
- **Self-healing demo:** close the AI brain window. Within 10 s the LCD shows `LOCAL CONTROL` and the Arduino uses its own rules.
- **Sensor fault demo:** unplug the DHT11 data wire. The LCD shows `SENSOR FAULT`, the red LED and buzzer turn on, and the fan stops (safe state).

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `could not open port` | Close the Serial Monitor or any other program using the port; check `py find_port.py` |
| LCD blank or showing blocks | Turn the contrast screw; run `i2c_scanner` and set `LCD_ADDR` |
| `FAULT: BMP180` on the LCD | Check SDA→A4, SCL→A5, VCC 5V; the scanner should show `0x77` |
| `FAULT: HC-SR04` | Check TRIG D11 / ECHO D12 and 5V; something must be within about 4 m |
| Fan never turns | Remove the ENA jumper and wire ENA→D6; check that the 12V adapter is plugged in and grounds are shared |
| Dashboard shows `No sensor data` | Is the bridge window printing readings? Is Mosquitto running? |
