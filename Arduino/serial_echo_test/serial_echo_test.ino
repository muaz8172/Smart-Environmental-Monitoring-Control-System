// Muhammad Muaz Bin Md Fazli, UniKL MFI, topic: Smart Environmental & Monitoring System
// Serial echo test: proves the Arduino RX pin receives data in Proteus.
// Sends "READY n" every 2 s; replies "ECHO:<text>" to every line it receives; pin 13 LED toggles per byte.
unsigned long last = 0, n = 0;
String buf;

void setup() { Serial.begin(9600); pinMode(13, OUTPUT); }

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    digitalWrite(13, !digitalRead(13));
    if (c == '\n') { buf.trim(); Serial.print("ECHO:"); Serial.println(buf); buf = ""; }
    else if (buf.length() < 32) buf += c;
  }
  if (millis() - last > 2000) { last = millis(); Serial.print("READY "); Serial.println(n++); }
}
