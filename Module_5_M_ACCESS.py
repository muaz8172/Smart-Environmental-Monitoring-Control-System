import serial
import pyodbc
from datetime import datetime

# =========================
# ARDUINO SERIAL SETTINGS
# =========================
ser = serial.Serial('COM2', 9600, timeout=1)
ser.flushInput()

# =========================
# MICROSOFT ACCESS CONNECTION
# =========================
conn = pyodbc.connect(
    "DSN=SensorDB;"
    "Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
)

# Cursor to execute SQL commands
cursor = conn.cursor() 

# Display connection status to the serial monitor
print("Connected to Microsoft Access database")
print("Waiting for Arduino data...")

# =========================
# MAIN LOOP
# =========================
while True:
    data = ser.readline()

    if len(data) > 0:
        try:
            # Convert from bytes to string
            strdata = data.decode("utf-8").strip()
            print("Raw Data:", strdata)

            # Split data by comma
            data_array = strdata.split(",")

            # Check data is received: 7 data
            if len(data_array) == 7:
                temperature = float(data_array[0]) #Temperature
                humidity = float(data_array[1]) #Humidity
                pressure = float(data_array[2]) #Pressure
                dust = float(data_array[3]) #Dust
                LDR = float(data_array[4]) #Light 
                distance = float(data_array[5]) #Distance
                fan_status = data_array[6] #Fan Status

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Insert into Microsoft Access table
                cursor.execute("""
                INSERT INTO Sensor_data
                ([Timestamp], [Temperature], [Humidity], [Pressure], [Dust], [LDR], [Distance], [Fan_Status])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, temperature, humidity, pressure, dust, LDR, distance, fan_status))

                conn.commit()

                print("Data successfully inserted into Microsoft Access database")
                print("Timestamp:", timestamp)
                print("Temperature:", temperature)
                print("Humidity:", humidity)
                print("Pressure:", pressure)
                print("Dust:", dust)
                print("LDR:", LDR)
                print("Distance:", distance)
                print("Fan Status:", fan_status)
                print("-" * 50)

            else:
                print("Invalid data format. Expected 7 values.")

        except Exception as e:
            print("Error:", e)
