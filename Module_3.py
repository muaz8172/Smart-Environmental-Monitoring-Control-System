import serial #Communicate with arduino serial port (COM4)
from datetime import datetime #Date & Time
import csv #Save data into excel (CSV file)

#---------- SETUP SERIAL CONNECTION ----------
ser = serial.Serial('COM2', 9600, timeout = 1)
ser.flushInput()

#---------- OPEN CSV FILE ----------
with open("sensor_data.csv", "a", newline="") as file:
    writer = csv.writer(file)
    
    #---------- MAIN LOOP ----------
    while True:
        data = ser.readline()
        
        if(len(data)>0):
            strdata = data.decode("utf-8").strip()
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            print(timestamp, "-", strdata)
            
            writer.writerow([timestamp, strdata])
            