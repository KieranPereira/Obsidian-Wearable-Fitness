#ifndef IMU_PROCESSING_H
#define IMU_PROCESSING_H

#include <Wire.h>
#include <MPU6050.h>

class IMUProcessor {
public:
    IMUProcessor(uint8_t device_id);  // Constructor with device ID
    bool begin();
    void update();
    float getRoll();
    float getPitch();
    uint8_t getDeviceID();  // ✅ Add this function to return device ID

private:
    MPU6050 mpu;
    uint8_t deviceID;  // Stores the ESP32 device ID
    float roll, pitch;
    float calculateAngle(float ax, float ay, float az);
};

#endif
