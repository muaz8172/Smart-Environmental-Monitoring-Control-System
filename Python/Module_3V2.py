import serial
import time
import csv
import os
import re

# =========================
# SETTINGS
# =========================
PORT = 'COM2'
BAUD = 9600
CSV_FILE = 'SERIALDATAFINALLOG.csv'
PRINT_INTERVAL = 30  # save to CSV every 30 seconds

HEADERS = [
    'Timestamp',
    'Distance (cm)',
    'Temp(DHT) (C)',
    'Humidity (%)',
    'Pressure (hPa)',
    'Light (lx)',
    'Dust (ug/m3)',
    'Fan State'
]

# =========================
# CREATE CSV FILE IF NOT EXIST
# =========================
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(HEADERS)
    print("CSV file created.")

# =========================
# CONNECT TO SERIAL PORT
# =========================
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print("Connected to serial port.")
except serial.SerialException as e:
    print("Serial connection error:", e)
    exit()

# =========================
# FUNCTION TO EXTRACT VALUE
# =========================
def parse_data(line):
    match = re.search(r':\s*([0-9.]+)|:\s*(ON|OFF)', line)

    if match:
        if match.group(1):
            return match.group(1)
        elif match.group(2):
            return match.group(2)

    return None

# =========================
# FUNCTION TO SAVE CSV
# =========================
def save_to_csv(row):
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(row)
    except IOError as e:
        print("CSV write error:", e)

# =========================
# MAIN PROGRAM
# =========================
print("Start logging data... Press Ctrl+C to stop.")

data_set = []
last_save_time = time.time()

try:
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        if line == "":
            continue

        # Start of new sensor block
        if "Sensor Readings:" in line:

            # Save previous full data to CSV every 30 seconds
            if len(data_set) == len(HEADERS):
                current_time = time.time()

                if current_time - last_save_time >= PRINT_INTERVAL:
                    save_to_csv(data_set)
                    print("Saved to CSV.")
                    last_save_time = current_time

            # Start new row with timestamp
            data_set = [time.strftime('%Y-%m-%d %H:%M:%S')]
            continue

        # Skip separator lines
        if "-----" in line or "=====" in line:
            continue

        # Extract sensor value
        value = parse_data(line)

        if value is not None:
            data_set.append(value)

            # When full data is ready, show in Thonny
            if len(data_set) == len(HEADERS):
                ts, dist, dht, bmp, hum, pres, light, dust, fan = data_set

                print(
                    f"[{ts}] "
                    f"Dist:{dist}cm | "
                    f"DHT:{dht}C | BMP:{bmp}C | "
                    f"Hum:{hum}% | Pres:{pres}hPa | "
                    f"Light:{light}lx | Dust:{dust}ug/m3 | "
                    f"Fan:{fan}"
                )

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nLogging stopped by user.")

finally:
    ser.close()
    print("Serial port closed.")