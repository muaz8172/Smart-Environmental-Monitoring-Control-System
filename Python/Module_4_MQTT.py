import serial
import paho.mqtt.publish as publish

ser = serial.Serial('COM2', 9600, timeout = 1)
ser.flushInput()

channel_ID = "3324542"
mqtt_broker = "mqtt3.thingspeak.com"

mqtt_client_ID = "HRgLMhklBS4tFiMCOQ8uFAM"
mqtt_username = "HRgLMhklBS4tFiMCOQ8uFAM"
mqtt_password = "bVl9UDRbWvZ0H1qGTuAx2oOH"

t_transport = "tcp"
t_port = 1883

topic = "channels/" + channel_ID + "/publish"

while True:
    data = ser.readline()
    if len(data) > 0:
        print("===============================================================================")
        print("UPLOAD LIVE DATA TO THINGSPEAK USING MQTT")
        print("Raw data:", data)
        
        strdata = data.decode("utf-8").strip()
        strdata_arry = strdata.split(",")
        
        if len(strdata_arry) == 7:
            strfield1 = "field1=" + strdata_arry[0]   #Temperature
            strfield2 = "&field2=" + strdata_arry[1]  #Humidity
            strfield3 = "&field3=" + strdata_arry[2]  #Pressure
            strfield4 = "&field4=" + strdata_arry[3]  #Dust
            strfield5 = "&field5=" + strdata_arry[4]  #Light
            strfield6 = "&field6=" + strdata_arry[5]  #Distance
            strfield7 = "&field7=" + strdata_arry[6]  #Fan State
            
            status = "&status=MQTTPUBLISH"
            payload = strfield1 + strfield2 + strfield3 + strfield4 + strfield5 + strfield6 + strfield7
            
            try:
                print("Publishing:", payload)
                publish.single(topic,
                               payload,
                               hostname = mqtt_broker,
                               transport = t_transport,
                               port = t_port,
                               client_id = mqtt_client_ID,
                               auth = {'username' : mqtt_username, 'password': mqtt_password})
                print("MQTT publish successful")
                print("===============================================================================")
            
            except Exception as e:
                print("Publish failed:", e)
        else:
            print("Invalid data format")
