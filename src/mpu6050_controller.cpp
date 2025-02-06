#include "mpu6050_controller.hpp"

// Constructor: just initializes the mpu object.
// Actual sensor and I2C initialization is done in begin().
MPU6050Controller::MPU6050Controller() : mpu() {
    // Empty constructor body; initialization happens in begin().
}

// Initializes I2C, the sensor, and other peripherals.
bool MPU6050Controller::begin() {
    Wire.begin(I2C_SDA, I2C_SCL); // Initialize I2C with defined pins

    // Initialize the MPU6050 sensor with the I2C address 0x68.
    if (!mpu.begin(0x68)) {
        Serial.println("Failed to find MPU6050 sensor!");
        return false;
    }

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

        // Obtain sensor events for acceleration, gyroscope, and temperature.
        sensors_event_t a, g, tempEvent;
        mpu.getEvent(&a, &g, &tempEvent);

        // Store the sensor values.
        accelX = a.acceleration.x;
        accelY = a.acceleration.y;
        accelZ = a.acceleration.z;

        gyroX = g.gyro.x;
        gyroY = g.gyro.y;
        gyroZ = g.gyro.z;

        temp = tempEvent.temperature;

        // Calculate the angle (for example, pitch or roll) based on acceleration.
        angle = calculateAngle(accelX, accelY, accelZ);

        // Prepare a JSON document to output the data.
        StaticJsonDocument<256> doc;
        doc["accel_x"] = accelX;
        doc["accel_y"] = accelY;
        doc["accel_z"] = accelZ;
        doc["gyro_x"]  = gyroX;
        doc["gyro_y"]  = gyroY;
        doc["gyro_z"]  = gyroZ;
        doc["temp"]    = temp;
        doc["angle"]   = angle;
        doc["status"]  = (angle >= 85 && angle <= 95) ? "Done" : "In Progress";

        // Serialize JSON to Serial.
        serializeJson(doc, Serial);
        Serial.println();
    }

    // Blink the LED at the defined interval.
    if (currentMillis - lastBlink >= blinkInterval) {
        lastBlink = currentMillis;
        ledState = !ledState;
        digitalWrite(LED_PIN, ledState);
    }
}

float MPU6050Controller::calculateAngle(float ax, float ay, float az) {
    // Calculate angle using the arctangent of az over the horizontal magnitude.
    return atan2(az, sqrt(sq(ax) + sq(ay))) * (180.0 / PI);
}
