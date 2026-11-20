// Name   : Muhammad Muaz Bin Md Fazli
// Uni    : UniKL MFI
// Topic  : Smart Environmental & Monitoring System
// IR 7.0 firmware (AI commands over serial + 10 s watchdog fallback to local rules)
// Serial in : FAN:ON | FAN:OFF | AUTO
// Serial out: T,H,P,dust,light,distance,ON|OFF,AI|LOCAL

#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <DHT.h>

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

LiquidCrystal_I2C lcd(0x20, 16, 2);
Adafruit_BMP085 bmp;
DHT dht(DHTPIN, DHTTYPE);

int ldrValue = 0;
float humidity, temperature, pressurehPa, distance, dustValue;
bool fanState, remote = false, remoteFan = false;
unsigned long lastCmd = 0;
String buf;

float getDistance()
{
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  return pulseIn(echoPin, HIGH) * 0.0343 / 2;  // cm
}

void readCommands()
{
  while (Serial.available())
  {
    char c = Serial.read();
    if (c != '\n') { if (buf.length() < 16) buf += c; continue; }
    buf.trim();
    if (buf == "FAN:ON" || buf == "FAN:OFF") { remote = true; remoteFan = (buf == "FAN:ON"); lastCmd = millis(); }
    else if (buf == "AUTO") remote = false;
    buf = "";
  }
  if (remote && millis() - lastCmd > 10000) remote = false;  // watchdog: AI lost -> local rules
}

bool fanControl()
{
  bool on;
  if (remote) on = remoteFan;
  else on = distance < 100 && (temperature >= 37 || humidity >= 60 || dustValue >= 55 || pressurehPa >= 1050 || ldrValue <= 500);
  digitalWrite(EN1, HIGH);
  digitalWrite(IN1, on ? HIGH : LOW);
  digitalWrite(IN2, LOW);
  return on;
}

void show(bool alarm, const char *msg)
{
  digitalWrite(redLED, alarm);
  digitalWrite(greenLED, !alarm);
  digitalWrite(buzzerPin, alarm);
  lcd.setCursor(0, 1);
  lcd.print(msg);
}

void setup()
{
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

  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  dht.begin();
  bmp.begin();

  lcd.setCursor(0, 0);
  lcd.print("IR 7.0 SMART    ");
  lcd.setCursor(0, 1);
  lcd.print("ENVIRONMENT     ");
  delay(2000);
  lcd.clear();
}

void loop()
{
  readCommands();
  distance = getDistance();
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  pressurehPa = bmp.readPressure() / 100.0;
  dustValue = pulseIn(PPDPin, LOW) / 200;
  ldrValue = analogRead(LDRPin);
  fanState = fanControl();  // after the reads, so it uses fresh values

  if (distance >= 100)
  {
    digitalWrite(redLED, LOW);
    digitalWrite(greenLED, LOW);
    digitalWrite(buzzerPin, LOW);
    lcd.setCursor(0, 0);
    lcd.print("NO OCCUPANCY    ");
    lcd.setCursor(0, 1);
    lcd.print(remote ? "AI CONTROL      " : "                ");
  }
  else
  {
    lcd.setCursor(0, 0);
    lcd.print(remote ? "AI CONTROL      " : "LOCAL CONTROL   ");
    if (temperature >= 37)        show(true, "HIGH TEMPERATURE");
    else if (dustValue >= 55)     show(true, "BAD AIR QUALITY ");
    else if (humidity >= 60)      show(true, "HIGH HUMIDITY   ");
    else if (humidity <= 30)      show(true, "LOW HUMIDITY    ");
    else if (ldrValue <= 500)     show(true, "LOW LIGHT       ");
    else if (pressurehPa <= 980)  show(true, "LOW PRESSURE    ");
    else if (pressurehPa >= 1050) show(true, "HIGH PRESSURE   ");
    else                          show(false, "SYSTEM NORMAL   ");
  }

  Serial.print(temperature); Serial.print(",");
  Serial.print(humidity);    Serial.print(",");
  Serial.print(pressurehPa); Serial.print(",");
  Serial.print(dustValue);   Serial.print(",");
  Serial.print(ldrValue);    Serial.print(",");
  Serial.print(distance);    Serial.print(",");
  Serial.print(fanState ? "ON" : "OFF");
  Serial.println(remote ? ",AI" : ",LOCAL");

  for (int i = 0; i < 100; i++) { readCommands(); delay(20); }  // 2 s, still listening for commands
}
