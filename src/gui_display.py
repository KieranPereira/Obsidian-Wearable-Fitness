import serial
import json
import tkinter as tk
from tkinter import ttk
import math

# Serial Port Configuration
SERIAL_PORT = 'COM6'  # Update this to match your COM port
BAUD_RATE = 115200

# Initialize Serial Communication
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# GUI Setup
root = tk.Tk()
root.title("ESP32 MPU6050 Arm Orientation")
root.geometry("500x600")

# Labels for Displaying Sensor Data
labels = {
    "accel_x": ttk.Label(root, text="Accel X: "),
    "accel_y": ttk.Label(root, text="Accel Y: "),
    "accel_z": ttk.Label(root, text="Accel Z: "),
    "gyro_x": ttk.Label(root, text="Gyro X: "),
    "gyro_y": ttk.Label(root, text="Gyro Y: "),
    "gyro_z": ttk.Label(root, text="Gyro Z: "),
    "temp": ttk.Label(root, text="Temp: "),
    "angle": ttk.Label(root, text="Angle: "),
    "status": ttk.Label(root, text="Status: ")
}

# Grid Placement
for i, (key, label) in enumerate(labels.items()):
    label.grid(row=i, column=0, sticky="W", padx=10, pady=5)

# Status Label Formatting
labels["status"].config(font=("Arial", 16, "bold"))

# Arm Line Display
canvas = tk.Canvas(root, width=300, height=300, bg='white')
canvas.grid(row=11, column=0, columnspan=2, pady=20)

# Initial Line Parameters
line = canvas.create_line(150, 150, 150, 50, width=5, fill='blue')

# Update Function
def update_data():
    try:
        line_data = ser.readline().decode('utf-8').strip()
        if line_data:
            try:
                data = json.loads(line_data)
                labels["accel_x"].config(text=f"Accel X: {data.get('accel_x', 0):.2f} m/s^2")
                labels["accel_y"].config(text=f"Accel Y: {data.get('accel_y', 0):.2f} m/s^2")
                labels["accel_z"].config(text=f"Accel Z: {data.get('accel_z', 0):.2f} m/s^2")
                labels["gyro_x"].config(text=f"Gyro X: {data.get('gyro_x', 0):.2f} rad/s")
                labels["gyro_y"].config(text=f"Gyro Y: {data.get('gyro_y', 0):.2f} rad/s")
                labels["gyro_z"].config(text=f"Gyro Z: {data.get('gyro_z', 0):.2f} rad/s")
                labels["temp"].config(text=f"Temp: {data.get('temp', 0):.2f} °C")
                labels["angle"].config(text=f"Angle: {data.get('angle', 0):.2f}°")
                status = data.get("status", "Unknown")
                labels["status"].config(text=f"Status: {status}", foreground="green" if status == "Done" else "red")

                # Update Line Orientation based on Angle
                angle = data.get('angle', 0)
                radians = math.radians(-angle)
                end_x = 150 + 100 * math.sin(radians)
                end_y = 150 - 100 * math.cos(radians)
                canvas.coords(line, 150, 150, end_x, end_y)
            
            except json.JSONDecodeError:
                print("Invalid JSON received:", line_data)
        else:
            print("Empty line received, skipping...")
    except (UnicodeDecodeError, serial.SerialException) as e:
        print("Error:", e)
    
    root.after(1, update_data)  # Schedule next update

# Start Updating GUI
update_data()
root.mainloop()
