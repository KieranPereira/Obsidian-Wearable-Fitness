# main.py
"""
Purpose:
--------
This script integrates sensor data from two IMU devices (one for the upper arm and one for the forearm)
to provide both 2D and 3D motion tracking visualizations. It reads JSON-formatted data via serial communication,
applies smoothing to reduce noise using a moving average filter, and updates the visualizations in real time
using PyQt6 tabs. The 2D visualization is rendered using an elliptical representation of the arm,
while the 3D visualization uses Euler angles.
"""

import sys
import json
import serial
import threading
import time
import numpy as np

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

# Import the 2D and 3D visualization tab classes
from lateralraise2d import LateralRaise2DTab
from visualizer_3d import Visualizer3dTab

# Import the MovingAverageFilter for smoothing sensor data
from smoothing import MovingAverageFilter

# Global lock for thread-safe data access between sensor threads and the GUI
data_lock = threading.Lock()

# For 2D tracking, store angles as single-element lists (in degrees)
shoulder_angle = [0.0]  # Represents the upper arm angle for the 2D visualization
elbow_angle    = [0.0]  # Represents the forearm angle for the 2D visualization

# For 3D tracking using Euler angles, store each sensor's orientation as [roll, pitch, yaw] (in degrees)
# Here, the sensor's "angle" value is used as the pitch, while roll and yaw are initialized to 0
upper_arm_euler = [0.0, 0.0, 0.0]
forearm_euler   = [0.0, 0.0, 0.0]

# Serial port settings for the ESP32 devices
ESP32_UPPER_ARM = "COM7"
ESP32_FOREARM   = "COM10"
BAUD_RATE = 115200

# Create Moving Average Filters for smoothing sensor readings for the upper arm
upper_arm_roll_filter = MovingAverageFilter(window_size=5)
upper_arm_pitch_filter = MovingAverageFilter(window_size=5)
upper_arm_yaw_filter = MovingAverageFilter(window_size=5)

# Create Moving Average Filters for smoothing sensor readings for the forearm
forearm_roll_filter = MovingAverageFilter(window_size=5)
forearm_pitch_filter = MovingAverageFilter(window_size=5)
forearm_yaw_filter = MovingAverageFilter(window_size=5)

def read_imu(port, label):
    """
    Reads JSON data from the ESP32 over serial communication.
    
    Expects JSON lines with keys for orientation (e.g., 'roll', 'pitch', 'yaw').
    Applies a moving average filter to reduce noise, and updates both the 2D angle and 
    the corresponding Euler angles for 3D visualization.
    
    Parameters:
    - port: The serial port identifier (e.g., "COM7").
    - label: A string label to identify the sensor ("Upper Arm" or "Forearm").
    """
    try:
        # Open the serial port with the specified baud rate and a timeout
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        print(f"✅ Connected to {label} ({port})")
    except Exception as e:
        # Print error message if connection fails
        print(f"❌ Connection error ({label}): {e}")
        return

    while True:
        try:
            # Check if data is available in the serial buffer
            if ser.in_waiting:
                # Read and decode a line from the serial port, stripping any whitespace
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue  # Skip if the line is empty

                try:
                    # Parse the JSON data from the line
                    data = json.loads(line)
                    # Retrieve orientation data, defaulting to 0.0 if a key is missing
                    roll_value  = data.get("roll", 0.0)
                    pitch_value = data.get("pitch", 0.0)
                    yaw_value   = data.get("yaw", 0.0)
                    
                    # Apply moving average smoothing to the incoming sensor readings
                    if label == "Upper Arm":
                        smoothed_roll  = upper_arm_roll_filter.update(roll_value)
                        smoothed_pitch = upper_arm_pitch_filter.update(pitch_value)
                        smoothed_yaw   = upper_arm_yaw_filter.update(yaw_value)
                    elif label == "Forearm":
                        smoothed_roll  = forearm_roll_filter.update(roll_value)
                        smoothed_pitch = forearm_pitch_filter.update(pitch_value)
                        smoothed_yaw   = forearm_yaw_filter.update(yaw_value)
                    
                    # Safely update the global sensor data using the data_lock
                    with data_lock:
                        if label == "Upper Arm":
                            upper_arm_euler[0] = smoothed_roll
                            upper_arm_euler[1] = smoothed_pitch
                            upper_arm_euler[2] = smoothed_yaw
                            # Update the 2D angle (using pitch as the representative value)
                            shoulder_angle[0] = smoothed_pitch
                        elif label == "Forearm":
                            forearm_euler[0] = smoothed_roll
                            forearm_euler[1] = smoothed_pitch
                            forearm_euler[2] = smoothed_yaw
                            # Update the 2D angle (using pitch as the representative value)
                            elbow_angle[0] = smoothed_pitch

                except json.JSONDecodeError:
                    # Ignore JSON decode errors and continue reading data
                    pass

            else:
                # If no data is waiting, sleep briefly to yield control
                time.sleep(0.01)
        except Exception as e:
            # Print any error encountered during the data reading process
            print(f"❌ Error reading from {label}: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        """
        Main application window that integrates both 2D and 3D visualization tabs.
        """
        super().__init__()
        # Set the window title and geometry (position and size)
        self.setWindowTitle("Integrated 2D + 3D Motion Tracking")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create a QTabWidget to hold the multiple visualization tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create the 2D visualization tab using the LateralRaise2DTab class
        self.tab2d = LateralRaise2DTab(
            angle_lock=data_lock,
            shoulder_angle_ref=shoulder_angle,
            elbow_angle_ref=elbow_angle,
            upper_arm_length=0.5,
            forearm_length=0.5,
            update_interval_ms=50
        )
        # Create the 3D visualization tab using the Visualizer3dTab class
        self.tab3d = Visualizer3dTab(
            data_lock=data_lock,
            upper_arm_euler_ref=upper_arm_euler,
            forearm_euler_ref=forearm_euler,
            upper_arm_length=0.4,
            forearm_length=0.35,
            update_interval_ms=50
        )

        # Add both tabs to the QTabWidget with appropriate labels
        self.tabs.addTab(self.tab2d, "2D Elliptical Arm")
        self.tabs.addTab(self.tab3d, "3D Euler Tracking")

def main():
    """
    Main function to start sensor reading threads and launch the PyQt application.
    """
    # Start a background thread for reading the upper arm sensor data
    threading.Thread(target=read_imu, args=(ESP32_UPPER_ARM, "Upper Arm"), daemon=True).start()
    # Start a background thread for reading the forearm sensor data
    threading.Thread(target=read_imu, args=(ESP32_FOREARM, "Forearm"), daemon=True).start()

    # Create the PyQt application and main window
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Start the application's event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    # Entry point of the script
    main()
