/**
 * @file mpu6050_controller.hpp
 * @brief Header file for the MPU6050Controller class.
 *
 * This file defines the MPU6050Controller class, which encapsulates the initialization,
 * data acquisition, and basic processing of sensor data from an MPU6050 inertial measurement unit (IMU).
 * The class handles reading acceleration, gyroscopic, and temperature data, as well as calculating an
 * orientation angle based on acceleration values. It also includes optional LED blinking functionality
 * for status indication.
 *
 * Dependencies:
 * - Arduino.h
 * - Wire.h
 * - Adafruit_MPU6050.h
 * - Adafruit_Sensor.h
 * - ArduinoJson.h
 *
 * @note Designed for use on an ESP32, with configurable I2C pins.
 */

#ifndef MPU6050_CONTROLLER_H
#define MPU6050_CONTROLLER_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ArduinoJson.h>

// Define I2C Pins for ESP32
#define I2C_SDA 21
#define I2C_SCL 22

// Define the LED Pin (optional)
#define LED_PIN 13

class MPU6050Controller {
public:
    MPU6050Controller();
    
    // Initializes the MPU6050 sensor.
    bool begin();
    
    // Updates sensor readings and processes data.
    void update();

private:
    // Adafruit sensor object for MPU6050
    Adafruit_MPU6050 mpu;
    
    // Sensor readings (as floats because the sensor returns floating point values)
    float accelX, accelY, accelZ;
    float gyroX, gyroY, gyroZ;
    float temp;
    
    // Calculated angle (if used for orientation estimation)
    float angle;
    
    // Timing variables for update and optional LED blinking.
    unsigned long lastUpdate;
    unsigned long lastBlink;
    bool ledState;
    
    // Intervals in milliseconds.
    const int updateInterval = 10;
    const int blinkInterval  = 1000;

    // Calculates an angle based on acceleration values.
    float calculateAngle(float ax, float ay, float az);
};

#endif // MPU6050_CONTROLLER_H
