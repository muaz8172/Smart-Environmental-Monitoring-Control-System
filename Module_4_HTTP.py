import serial
#Import urllib for HTTP communication with ThingSpeak
import urllib.request 
import urllib.parse

ser = serial.Serial('COM2', 9600, timeout = 1)
ser.flushInput()

while True:
    data = ser.readline()
    if(len(data) > 0):
        print(data)
        strdata = data.decode("utf-8").strip()
        strdata = strdata.rstrip("\r\n")
        
        strdata_arry = strdata.split(",")
        
        #ThingSpeak HTTP API URL
        url = "https://api.thingspeak.com/update?api_key=RGQ2UR6NGOHPEQ4H"
        
        #Map for each sensor value to ThingSpeak
        strfield1 = "&field1=" + strdata_arry[0]	#Temperature
        strfield2 = "&field2=" + strdata_arry[1]	#Humidity
        strfield3 = "&field3=" + strdata_arry[2]	#Pressure
        strfield4 = "&field4=" + strdata_arry[3]	#Dust
        strfield5 = "&field5=" + strdata_arry[4]	#Light
        strfield6 = "&field6=" + strdata_arry[5]	#Distance
        strfield7 = "&field7=" + strdata_arry[6]	#Fan State
        
        #Combine all fields into one URL
        url = url + strfield1 + strfield2 + strfield3 + strfield4 + strfield5 + strfield5 + strfield6 + strfield7
        
        #Send HTTP request to ThingSpeak
        f = urllib.request.urlopen(url)
        
        #Print successfull Message
        print("Data Uploaded to ThingSpeak")