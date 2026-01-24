#include <Wire.h>
#include <AS5600.h>

AS5600 as5600;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  as5600.begin();   // I2C addr is fixed at 0x36 for AS5600 [page:1]
}

void loop() {
  double angle = as5600.rawAngle();
  Serial.println("Angle: " + String(angle));
  delay(200);
}
