// Name   : Muhammad Muaz Bin Md Fazli
// Uni    : UniKL MFI
// Topic  : Smart Environmental & Monitoring System
// I2C scanner: prints the address of the LCD backpack and the BMP180 (Serial Monitor, 9600 baud)
// Expect: 0x27 or 0x3F = LCD, 0x77 = BMP180

#include <Wire.h>

void setup()
{
  Serial.begin(9600);
  Wire.begin();
}

void loop()
{
  Serial.println("Scanning I2C...");
  for (byte a = 1; a < 127; a++)
  {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0)
    {
      Serial.print("Found device at 0x");
      Serial.println(a, HEX);
    }
  }
  delay(3000);
}
