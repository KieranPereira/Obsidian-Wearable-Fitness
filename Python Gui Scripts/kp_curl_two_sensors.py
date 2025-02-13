# main.py
import sys
import json
import serial
import threading
import time
import numpy as np

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import QTimer

from lateralraise2d import LateralRaise2DTab

# ========== GLOBALS ==========
data_lock = threading.Lock()

# We can store angles in lists so they're mutable references:
shoulder_angle = [0.0]
elbow_angle    = [0.0]

ESP32_UPPER_ARM = "COM10"
ESP32_FOREARM   = "COM11"
BAUD_RATE       = 115200
UPDATE_INTERVAL_MS = 50  # If needed

def read_imu(port, label):
    """
    Read JSON data from an ESP32 over USB Serial and update the corresponding angle.
    """
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        print(f"✅ Connected to {label} ({port})")
    except Exception as e:
        print(f"❌ Connection error ({label}): {str(e)}")
        return

    while True:
        try:
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                # print(f"{label} Raw: {line}")  # Debug

                try:
                    data = json.loads(line)
                    angle_value = data.get("angle", None)
                    if angle_value is None:
                        continue
                    # Optional: validate angle range
                    if not (-180 <= angle_value <= 180):
                        continue

                    with data_lock:
                        # Update the relevant angle
                        if label == "Upper Arm":
                            shoulder_angle[0] = angle_value
                        elif label == "Forearm":
                            elbow_angle[0] = angle_value

                except json.JSONDecodeError as je:
                    print(f"❌ JSON parse error in {label}: {je}")
            else:
                time.sleep(0.01)
        except Exception as e:
            print(f"❌ Error reading from {label}: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated Motion Tracking")
        self.setGeometry(100, 100, 1200, 800)

        # Create your tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create the 2D tab from your external class
        self.tab2d = LateralRaise2DTab(
            angle_lock=data_lock,
            shoulder_angle_ref=shoulder_angle,
            elbow_angle_ref=elbow_angle
        )

        # If you have a second tab (3D or anything else), you can define it here.
        # For demonstration, we'll just add the single 2D tab.
        self.tabs.addTab(self.tab2d, "2D Elliptical Arm")


if __name__ == "__main__":
    # Start sensor threads
    threading.Thread(target=read_imu, args=(ESP32_UPPER_ARM, "Upper Arm"), daemon=True).start()
    threading.Thread(target=read_imu, args=(ESP32_FOREARM, "Forearm"), daemon=True).start()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())