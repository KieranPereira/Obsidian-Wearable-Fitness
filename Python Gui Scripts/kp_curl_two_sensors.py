# main.py
import sys
import json
import serial
import threading
import time
import numpy as np

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

# Import the 2D and 3D tab classes
from lateralraise2d import LateralRaise2DTab
from KP_biometric_visualizer_3d import BiometricVisualizer3DTab

# Global lock for thread-safe data access
data_lock = threading.Lock()

# For 2D tracking, we store angles as single-element lists (in degrees)
shoulder_angle = [0.0]  # Upper arm angle for 2D
elbow_angle    = [0.0]  # Forearm angle for 2D

# For 3D tracking using Euler angles, we store each sensor’s Euler angles as [roll, pitch, yaw] (in degrees).
# In this example, we use the sensor's "angle" value as the pitch; roll and yaw start at 0.
upper_arm_euler = [0.0, 0.0, 0.0]
forearm_euler   = [0.0, 0.0, 0.0]

ESP32_UPPER_ARM = "COM10"
ESP32_FOREARM   = "COM11"
BAUD_RATE = 115200

def read_imu(port, label):
    """
    Reads JSON data from the ESP32 over serial.
    Expects JSON lines with an "angle" key.
    Updates both the 2D angle and the corresponding Euler pitch for 3D.
    """
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        print(f"✅ Connected to {label} ({port})")
    except Exception as e:
        print(f"❌ Connection error ({label}): {e}")
        return

    while True:
        try:
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    angle_value = data.get("angle", None)
                    if angle_value is None:
                        continue
                    # Optional: validate the angle range if needed
                    if not (-180 <= angle_value <= 180):
                        continue

                    with data_lock:
                        if label == "Upper Arm":
                            shoulder_angle[0] = angle_value
                            # Update Euler pitch (we use the sensor angle as pitch)
                            upper_arm_euler[1] = angle_value
                        elif label == "Forearm":
                            elbow_angle[0] = angle_value
                            forearm_euler[1] = angle_value
                    # Uncomment for debugging:
                    # print(f"[DEBUG] {label} angle: {angle_value}")
                except json.JSONDecodeError:
                    pass
            else:
                time.sleep(0.01)
        except Exception as e:
            print(f"❌ Error reading from {label}: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated 2D + 3D Motion Tracking")
        self.setGeometry(100, 100, 1200, 800)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create the 2D tab
        self.tab2d = LateralRaise2DTab(
            angle_lock=data_lock,
            shoulder_angle_ref=shoulder_angle,
            elbow_angle_ref=elbow_angle,
            upper_arm_length=0.5,
            forearm_length=0.5,
            update_interval_ms=50
        )
        # Create the 3D tab (using Euler angles)
        self.tab3d = BiometricVisualizer3DTab(
            data_lock=data_lock,
            upper_arm_euler_ref=upper_arm_euler,
            forearm_euler_ref=forearm_euler,
            upper_arm_length=0.4,
            forearm_length=0.35,
            update_interval_ms=50
        )

        self.tabs.addTab(self.tab2d, "2D Elliptical Arm")
        self.tabs.addTab(self.tab3d, "3D Euler Tracking")

def main():
    # Start sensor-reading threads for each sensor
    threading.Thread(target=read_imu, args=(ESP32_UPPER_ARM, "Upper Arm"), daemon=True).start()
    threading.Thread(target=read_imu, args=(ESP32_FOREARM, "Forearm"), daemon=True).start()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
