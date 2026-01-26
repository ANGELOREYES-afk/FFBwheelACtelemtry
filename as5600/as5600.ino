#include <Wire.h>
#include <AS5600.h>

AS5600 as5600;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  as5600.begin();   // I2C addr is fixed at 0x36 for AS5600 [page:1]
}

void loop() {
  double angle = as5600.readAngle();
  double conversion = 360.0/4096.0;
  Serial.println(angle * conversion);
  delay(200);
}
