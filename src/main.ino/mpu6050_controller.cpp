/**
 * @file mpu6050_controller.cpp
 * @brief Implementation of the MPU6050Controller class.
 *
 * This file implements the methods of the MPU6050Controller class, which is responsible for:
 * - Initializing the MPU6050 sensor over I2C using defined SDA and SCL pins.
 * - Reading sensor data (acceleration, gyroscope, and temperature) from the MPU6050.
 * - Calculating an orientation angle based on acceleration values.
 * - Packaging the sensor data into a JSON document and transmitting it over Bluetooth,
 *   as well as outputting it to the USB Serial Monitor.
 * - Blinking an LED at regular intervals to indicate active sensor updates.
 *
 * @note The Bluetooth serial instance 'serialBT' must be defined externally.
 */

#include "mpu6050_controller.hpp"
#include <BluetoothSerial.h>
extern BluetoothSerial serialBT;  // Reference the Bluetooth serial instance



// Constructor: do not initialize the sensor here.
MPU6050Controller::MPU6050Controller() : mpu() {
    // Constructor left intentionally empty.
}

// New begin() method to initialize the sensor and I2C.
bool MPU6050Controller::begin() {
    // Initialize I2C with the defined SDA and SCL pins.
    Wire.begin(I2C_SDA, I2C_SCL);

    // Attempt to initialize the MPU6050 sensor at I2C address 0x68.
    if (!mpu.begin(0x68)) {
        Serial.println("Failed to find MPU6050 sensor!");
        return false;
    }

    // Set up the LED pin and timing.
    pinMode(LED_PIN, OUTPUT);
    ledState = false;
    lastUpdate = millis();
    lastBlink  = millis();

    return true;
}

void MPU6050Controller::update() {
    unsigned long currentMillis = millis();

    // Update sensor reading at the defined interval.
    if (currentMillis - lastUpdate >= updateInterval) {
        lastUpdate = currentMillis;

        // Retrieve sensor events for acceleration, gyroscope, and temperature.
        sensors_event_t a, g, tempEvent;
        mpu.getEvent(&a, &g, &tempEvent);

        // Save the sensor readings.
        accelX = a.acceleration.x;
        accelY = a.acceleration.y;
        accelZ = a.acceleration.z;
        gyroX  = g.gyro.x;
        gyroY  = g.gyro.y;
        gyroZ  = g.gyro.z;
        temp   = tempEvent.temperature;

        // Calculate roll, pitch, and yaw angles from the acceleration values.
        // (You may choose to rename these variables or make them class members.)
        float pitch_angle = calculateAngle(accelX, accelY, accelZ);
        float roll_angle  = atan2(accelY, accelZ) * (180.0 / PI);
        float yaw_angle   = 0;  // Placeholder: Implement sensor fusion for a proper yaw.

        // Create a JSON document.
        StaticJsonDocument<256> doc;
        doc["roll"]  = roll_angle;
        doc["pitch"] = pitch_angle;
        doc["yaw"]   = yaw_angle;
        doc["accel_x"] = accelX;
        doc["accel_y"] = accelY;
        doc["accel_z"] = accelZ;
        doc["gyro_x"]  = gyroX;
        doc["gyro_y"]  = gyroY;
        doc["gyro_z"]  = gyroZ;
        doc["temp"]    = temp;
        doc["status"]  = (pitch_angle >= 85 && pitch_angle <= 95) ? "Done" : "In Progress";

        // Transmit the JSON data over Bluetooth.
        serializeJson(doc, serialBT);
        serialBT.println();

        // Optionally, also output to the USB Serial Monitor.
        serializeJson(doc, Serial);
        Serial.println();
    }

    // Blink the LED as before.
    if (currentMillis - lastBlink >= blinkInterval) {
        lastBlink = currentMillis;
        ledState = !ledState;
        digitalWrite(LED_PIN, ledState);
    }
}

float MPU6050Controller::calculateAngle(float ax, float ay, float az) {
    // Calculate an angle (in degrees) from the acceleration data.
    return atan2(az, sqrt(sq(ax) + sq(ay))) * (180.0 / PI);
}