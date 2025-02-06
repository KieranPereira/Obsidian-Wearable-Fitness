#include "mpu6050_controller.hpp"

MPU6050Controller controller;

void setup() {
    Serial.begin(115200);
}

void loop() {
    controller.update();
}