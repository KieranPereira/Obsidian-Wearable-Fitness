#include "mpu6050_controller.hpp"  // Use the .h extension as in your files

MPU6050Controller controller;

void setup() {
    Serial.begin(115200);
    
    // Initialize the MPU6050 sensor
    if (!controller.begin()) {
        Serial.println("Sensor initialization failed!");
        while (1) { 
            delay(100); 
        }
    }
}

void loop() {
    controller.update();
}
