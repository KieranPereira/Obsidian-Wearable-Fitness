/**
 * @file main.ino
 * @brief Main application for controlling the MPU6050 sensor and communicating over Bluetooth.
 *
 * This application is designed for the ESP32 platform. It performs the following tasks:
 * - Initializes a Bluetooth serial connection with the device name "Feather-BT".
 * - Sets up the MPU6050 sensor using an instance of MPU6050Controller.
 * - Transmits sensor readings (acceleration, gyroscope, temperature, and a calculated angle)
 *   as JSON data over both Bluetooth and USB Serial.
 * - Listens for incoming Bluetooth commands to control an LED:
 *     - '1' turns the LED on.
 *     - '0' turns the LED off.
 *
 * @note If the sensor initialization fails, the application halts in an infinite loop.
 */

#include <BluetoothSerial.h>
#include "mpu6050_controller.hpp"

// Create a BluetoothSerial object.
BluetoothSerial serialBT;

// Create an instance of the MPU6050 controller.
MPU6050Controller controller;

// Variable to store incoming Bluetooth commands.
char cmd;

void setup() {
  // Start USB Serial for debugging.
  Serial.begin(115200);

  // Initialize Bluetooth with the device name "Feather-BT".
  serialBT.begin("WROOM-ESP-BT");
  
  // Initialize the MPU6050 sensor.
  if (!controller.begin()) {
    Serial.println("Sensor initialization failed!");
    while (1) {
      delay(100);
    }
  }
}

void loop() {
  // Check if there is any Bluetooth data available.
  if (serialBT.available()) {
    cmd = serialBT.read();

    // Process commands received over Bluetooth.
    // '1' turns the LED on, and '0' turns it off.
    if (cmd == '1') {
      digitalWrite(LED_PIN, HIGH);
    } else if (cmd == '0') {
      digitalWrite(LED_PIN, LOW);
    }
  }
  
  // Update the sensor readings and output the JSON data over USB Serial and Bluetooth.
  controller.update();

  delay(2);
}
