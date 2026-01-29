#include <Wire.h>
#include <AS5600.h>

// Analog Sensor 1
const int analogPin = A0;

// I2C sensor 2
AS5600 as5600;   

void setup() {
  Serial.begin(115200);
  
  // Initialize I2C
  Wire.begin();

  // Initialize the I2C Sensor
  // as5600 lib func .begin() is to check if found
  if (!as5600.begin()) {
    Serial.println("Error: I2C Sensor (Sensor 2) not found!");
  }
  // not necessary but great for controlling what you get 
  as5600.setDirection(AS5600_CLOCK_WISE); 
}

void loop() {

  int analogRaw = analogRead(analogPin);
  // Convert 0-1023 to 0-360
  float angle1 = analogRaw * (360.0 / 1023.0);

  // Convert 4096 to 0-350
  float angle2 = as5600.readAngle() * (360.0 / 4096.0);

  
  Serial.print(angle1, 1);
  
  Serial.print(","); // Spacer
  
  Serial.println(angle2, 2); // 2 decimal places

  delay(100);
}
