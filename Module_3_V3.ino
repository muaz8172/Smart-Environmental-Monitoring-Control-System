//=============== INCLUDE LIBRARY ===============
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <DHT.h>

//=============== DEFINE SENSORS & DRIVERS ===============
#define redLED 2
#define greenLED 3
#define DHTPIN 4
#define PPDPin 5
#define DHTTYPE DHT11
#define trigPin 11
#define echoPin 12
#define LDRPin A1
#define buzzerPin 8
#define EN1 6
#define IN1 10
#define IN2 9

//=============== SENSORS DECLARATION ===============
LiquidCrystal_I2C lcd(0x20, 16, 2);
Adafruit_BMP085 bmp;
DHT dht(DHTPIN, DHTTYPE);

//=============== SET VALUE ===============
int ldrValue = 0;

//=============== VARIABLES ===============
float humidity,temperature;
float pressurePa, pressurehPa;
float duration, distance, dustValue;
bool fanState;

//=============== ULTRASONIC FUNCTION ===============
float getDistance() 
{
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  return distance = (duration * 0.0343) / 2; //cm
}

//=============== FAN CONTROL FUNCTION ===============
float fanControl()
{
  digitalWrite(EN1, HIGH);

  if(distance >= 100)
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    return false;
  }
  else
  {
    if(temperature >= 37 || humidity >= 60 || dustValue >= 55 || pressurehPa >=1050 || ldrValue <= 500)
    {
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      return true;
    }
    else
    {
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, LOW);
      return false;
    }
  }
  return fanState;
}

//=============== SETUP ===============
void setup() 
{
  //----- INPUT & OUTPUT -----
  pinMode(LDRPin, INPUT);
  pinMode(PPDPin, INPUT);
  pinMode(echoPin, INPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(EN1, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  //----- LCD & SERIAL MONITOR -----
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();

  //----- DHT & BMP -----
  dht.begin();
  bmp.begin();

  //----- WELCOME DISPLAY -----
  lcd.setCursor(0,0);
  lcd.print("ENVIRONMENT     ");
  lcd.setCursor(0,1);
  lcd.print("SYSTEM          ");
  delay(2000);
  lcd.clear();
}

//=============== LOOPING ===============
void loop() 
{
  //----- READ ALL SENSOR -----
  fanState = fanControl();
  distance = getDistance(); //function call ultrasonic sensor (distance)
  humidity = dht.readHumidity(); //read humidity sensor
  temperature = dht.readTemperature(); //read temperature sensor
  pressurePa = bmp.readPressure(); //read pressure sensor
  pressurehPa = pressurePa / 100.0; //convert Pa to hPa
  distance = (duration * 0.0343) / 2; //calculate distance in cm
  unsigned long duration = pulseIn(PPDPin, LOW);
  dustValue = duration/200;
  ldrValue = analogRead(LDRPin);

  //----- Rules 1 -----
  if(distance >= 100) //no person detected
  {
    digitalWrite(redLED, LOW);
    digitalWrite(greenLED, LOW);
    digitalWrite(buzzerPin, LOW);
    fanState;
    
    lcd.setCursor(0,0);
    lcd.print("NO OCCUPANCY    ");
    lcd.setCursor(0,1);
    lcd.print("                ");
  }

  //----- Rules 2 -----
  else //person detected
  {
      lcd.setCursor(0,0);
      lcd.print("MONITORING ON   ");

      //----- Rules 3 -----
      if(temperature >= 37) //high temperature
      {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
        digitalWrite(buzzerPin, HIGH);
        fanState;

        lcd.setCursor(0,1);
        lcd.print("HIGH TEMPERATURE");
      }

      //----- Rules 4 -----
      else if(dustValue >= 55) //bad air quality
      {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
        digitalWrite(buzzerPin, HIGH);
        fanState;

        lcd.setCursor(0,1);
        lcd.print("BAD AIR QUALITY ");
      }

      //----- Rules 5 -----
      else if(humidity >= 60) //high humidity
      {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
        digitalWrite(buzzerPin, HIGH);
        fanState;

        lcd.setCursor(0,1);
        lcd.print("HIGH HUMIDITY   ");
      }

      //----- Rules 6 -----
      else if(humidity <= 30) //low humidity
      {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
        digitalWrite(buzzerPin, HIGH);
        fanState;

        lcd.setCursor(0,1);
        lcd.print("LOW HUMIDITY    ");
      }

      //----- Rules 7 -----
      else if(ldrValue <= 500) //low light condition
      {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
        digitalWrite(buzzerPin, HIGH);
        fanState;

        lcd.setCursor(0,1);
        lcd.print("LOW LIGHT       ");
      }

      //----- Rules 8 -----
      else if(pressurehPa <= 980) //low pressure
      {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
        digitalWrite(buzzerPin, HIGH);
        fanState;

        lcd.setCursor(0,1);
        lcd.print("LOW PRESSURE    ");
      }

      //----- Rules 9 -----
      else if(pressurehPa >= 1050) //high pressure
      {
        digitalWrite(redLED, HIGH);
        digitalWrite(greenLED, LOW);
        digitalWrite(buzzerPin, HIGH);
        fanState;
  
        lcd.setCursor(0,1);
        lcd.print("HIGH PRESSURE   ");
      }

      //----- Rules 10 -----
      else //system normal
      {
        digitalWrite(redLED, LOW);
        digitalWrite(greenLED, HIGH);
        digitalWrite(buzzerPin, LOW);
        fanState;

        lcd.setCursor(0,1);
        lcd.print("SYSTEM NORMAL   ");
      }
  }

//=============== SERIAL MONITOR OUTPUT ===============
Serial.print(temperature);
Serial.print(",");
Serial.print(humidity);
Serial.print(",");
Serial.print(pressurehPa);
Serial.print(",");
Serial.print(dustValue);
Serial.print(",");
Serial.print(ldrValue);
Serial.print(",");
Serial.print(distance);
Serial.print(",");
Serial.println(fanState ? "ON" : "OFF");

delay(2000);
}