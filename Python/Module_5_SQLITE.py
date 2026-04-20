import serial
import sqlite3
from datetime import datetime

# =========================
# ARDUINO SERIAL SETTINGS
# =========================
ser = serial.Serial('COM2', 9600, timeout=1)
ser.flushInput()

# =========================
# SQLLITE CONNECTION
# =========================
conn = sqlite3.connect("Sensor_database.db")
cursor = conn.cursor()

print("Connected to SQLite database")
print("Waiting for Arduino data...")

# =========================
# MAIN LOOP
# =========================
while True:
    data = ser.readline()

    if len(data) > 0:
        try:
            # Convert data to string
            strdata = data.decode("utf-8").strip()
            print("Raw Data:", strdata)

            # Split data by comma
            data_array = strdata.split(",")

            # Make sure exactly 6 values are received
            if len(data_array) == 7:
                temperature = float(data_array[0]) # Temperature
                humidity = float(data_array[1]) # Humidity
                pressure = float(data_array[2]) # Pressure
                dust = float(data_array[3]) # Dust
                light = float(data_array[4]) # Light
                distance = float(data_array[5]) # Distance
                fan_status = data_array[6] #Fan Status

                # Generate timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Insert into SQLite table
                cursor.execute("""
                INSERT INTO Sensor_data
                (Timestamp, Temperature, Humidity, Pressure, Dust, Light, Distance, Fan_Status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, temperature, humidity, pressure, dust, light, distance, fan_status))

                conn.commit()

                print("Data inserted into SQLite database")
                print("Timestamp:", timestamp)
                print("Temperature:", temperature)
                print("Humidity:", humidity)
                print("Pressure:", pressure)
                print("Dust:", dust)
                print("light:", light)
                print("Distance:", distance)
                print("Fan Status:", fan_status)
                print("-" * 50)

            else:
                print("Invalid data format. Expected 8 values.")

        except Exception as e:
            print("Error:", e)