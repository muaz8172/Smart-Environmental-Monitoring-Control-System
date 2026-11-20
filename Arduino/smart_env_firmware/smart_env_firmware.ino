// Name   : Muhammad Muaz Bin Md Fazli
// Uni    : UniKL MFI
// Topic  : Smart Environmental & Monitoring System
// IR 7.0 firmware (AI commands over serial + 10 s command timeout back to local rules)
// Serial in : FAN:ON | FAN:OFF | AUTO
// Serial out: T,H,P,dust,light,distance,ON|OFF,AI|LOCAL   (a faulty sensor is sent as "nan")
// IEC 60730-1 Annex H / IEC 61508-3 principles: hardware watchdog, I2C timeout, sensor plausibility, fan OFF on fault

#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <DHT.h>
#include <avr/wdt.h>

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
#define ECHO_TIMEOUT_US 40000UL  // HC-SR04 gives ~38 ms with no obstacle; 0 = no echo at all = sensor fault

LiquidCrystal_I2C lcd(0x20, 16, 2);
Adafruit_BMP085 bmp;
DHT dht(DHTPIN, DHTTYPE);

int ldrValue = 0;
float humidity, temperature, pressurehPa, distance, dustValue;
bool fanState, remote = false, remoteFan = false, bmpOk = false;
unsigned long lastCmd = 0;
String buf;

float getDistance()
{
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  return pulseIn(echoPin, HIGH, ECHO_TIMEOUT_US) * 0.0343 / 2;  // cm, 0 = no echo
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
  if (remote && millis() - lastCmd > 10000) remote = false;  // command timeout: AI lost -> local rules
}

bool fanControl(bool fault)
{
  bool on;
  if (fault) on = false;  // defined safe state: fan OFF while any sensor is faulty
  else if (remote) on = remoteFan;
  else on = distance < 100 && (temperature >= 37 || humidity >= 60 || dustValue >= 55 || pressurehPa >= 1050 || ldrValue <= 500);
  digitalWrite(EN1, HIGH);
  digitalWrite(IN1, on ? HIGH : LOW);
  digitalWrite(IN2, LOW);
  return on;
}

void show(bool alarm, const char *msg, bool buzz = true)
{
  digitalWrite(redLED, alarm);
  digitalWrite(greenLED, !alarm);
  digitalWrite(buzzerPin, alarm && buzz);
  lcd.setCursor(0, 1);
  lcd.print(msg);
}

void printValue(float v)
{
  if (isnan(v)) Serial.print("nan"); else Serial.print(v);
}

void setup()
{
  MCUSR = 0;
  wdt_disable();  // a watchdog reset leaves the WDT running; switch it off until setup is done

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
  Wire.begin();
  Wire.setWireTimeout(25000, true);  // a stuck I2C bus (LCD/BMP180) times out instead of freezing
  lcd.init();
  lcd.backlight();
  dht.begin();
  bmpOk = bmp.begin();

  lcd.setCursor(0, 0);
  lcd.print("IR 7.0 SMART    ");
  lcd.setCursor(0, 1);
  lcd.print("ENVIRONMENT     ");
  delay(2000);
  lcd.clear();
  wdt_enable(WDTO_8S);  // hardware watchdog: resets the board if the loop stops for 8 s
}

void loop()
{
  wdt_reset();
  readCommands();
  distance = getDistance();
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  pressurehPa = bmpOk ? bmp.readPressure() / 100.0 : NAN;
  if (!(pressurehPa >= 300 && pressurehPa <= 1100)) pressurehPa = NAN;  // implausible or missing BMP180
  dustValue = pulseIn(PPDPin, LOW) / 200;
  ldrValue = analogRead(LDRPin);
  wdt_reset();

  const char *fault = isnan(temperature) || isnan(humidity) ? "FAULT: DHT11    "
                    : isnan(pressurehPa)                    ? "FAULT: BMP180   "
                    : distance <= 0                         ? "FAULT: HC-SR04  " : NULL;
  fanState = fanControl(fault != NULL);  // after the reads, so it uses fresh values

  if (fault)
  {
    lcd.setCursor(0, 0);
    lcd.print("SENSOR FAULT    ");
    show(true, fault);
  }
  else if (distance >= 100)
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
    else if (ldrValue <= 500)     show(true, "LOW LIGHT       ", false);  // red lamp only, no buzzer
    else if (pressurehPa <= 980)  show(true, "LOW PRESSURE    ");
    else if (pressurehPa >= 1050) show(true, "HIGH PRESSURE   ");
    else                          show(false, "SYSTEM NORMAL   ");
  }

  printValue(temperature); Serial.print(",");
  printValue(humidity);    Serial.print(",");
  printValue(pressurehPa); Serial.print(",");
  Serial.print(dustValue); Serial.print(",");
  Serial.print(ldrValue);  Serial.print(",");
  printValue(distance > 0 ? distance : NAN); Serial.print(",");
  Serial.print(fanState ? "ON" : "OFF");
  Serial.println(remote ? ",AI" : ",LOCAL");

  for (int i = 0; i < 100; i++) { wdt_reset(); readCommands(); delay(20); }  // 2 s, still listening for commands
}
