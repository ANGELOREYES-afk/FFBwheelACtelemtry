#include <Wire.h>
#include <AS5600.h>

AS5600 as5600;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  as5600.begin();   // I2C addr is fixed at 0x36 for AS5600 [page:1]
}

void loop() {
  if (!as5600.detectMagnet()) Serial.println("Magnet: NOT detected");
  else if (as5600.magnetTooWeak()) Serial.println("Magnet: detected, TOO WEAK");
  else if (as5600.magnetTooStrong()) Serial.println("Magnet: detected, TOO STRONG");
  else Serial.println("Magnet: detected, OK");
  delay(200);
}
