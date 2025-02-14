# visualizer_3d.py
"""
Purpose:
--------
This script creates a PyQt6 widget for 3D arm visualization using Euler angles.
It converts Euler angles into rotation matrices (using the ZYX convention) and uses these
matrices to compute the positions of the upper arm and forearm segments. The 3D visualization
is rendered with Matplotlib's 3D plotting capabilities, and the widget is designed to work
with sensor data from IMUs.
"""

import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from mpl_toolkits.mplot3d import Axes3D  # Enables 3D support

def euler_to_rotation_matrix(roll, pitch, yaw):
    """
    Convert Euler angles (in radians) to a rotation matrix using the ZYX convention:
    R = Rz(yaw) * Ry(pitch) * Rx(roll)
    
    Parameters:
    - roll: Rotation angle around the x-axis (in radians)
    - pitch: Rotation angle around the y-axis (in radians)
    - yaw: Rotation angle around the z-axis (in radians)
    
    Returns:
    - A 3x3 rotation matrix.
    """
    # Rotation matrix about the z-axis (yaw)
    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw),  np.cos(yaw), 0],
        [0, 0, 1]
    ])
    # Rotation matrix about the y-axis (pitch)
    Ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])
    # Rotation matrix about the x-axis (roll)
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll),  np.cos(roll)]
    ])
    # Compose the rotation matrices: R = Rz * Ry * Rx
    return Rz @ Ry @ Rx

class Visualizer3dTab(QWidget):
    """
    3D arm visualization using Euler angles.
    
    Expects references to a data lock and to two 3-element lists holding Euler angles (in degrees)
    for the upper arm and forearm. In this example, the sensor's "angle" is used as the pitch,
    with roll and yaw set to 0.
    """
    def __init__(
        self,
        data_lock,
        upper_arm_euler_ref,  # e.g., [roll, pitch, yaw]
        forearm_euler_ref,
        upper_arm_length=0.4,
        forearm_length=0.35,
        update_interval_ms=50
    ):
        super().__init__()
        # Store provided references and configuration parameters
        self.data_lock = data_lock
        self.upper_arm_euler_ref = upper_arm_euler_ref
        self.forearm_euler_ref   = forearm_euler_ref
        self.upper_arm_length = upper_arm_length
        self.forearm_length   = forearm_length
        self.update_interval_ms = update_interval_ms
        
        # Initialize the user interface components
        self.initUI()

    def initUI(self):
        # Create a vertical layout for the widget
        layout = QVBoxLayout()
        # Create a Matplotlib figure for the 3D plot
        self.fig = plt.figure(figsize=(6, 5))
        # Create a canvas widget to embed the figure into the PyQt application
        self.canvas = FigureCanvas(self.fig)
        # Create a 3D subplot in the figure
        self.ax = self.fig.add_subplot(111, projection='3d')
        # Add a navigation toolbar for the 3D plot
        self.toolbar = NavigationToolbar(self.canvas, self)
        # Add the toolbar and canvas to the layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Remove tick labels for a cleaner 3D visualization
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_zticklabels([])

        # Define the fixed shoulder position at the origin
        self.shoulder_pos = np.array([0.0, 0.0, 0.0])
        # Create line objects to represent the upper arm and forearm segments
        self.upper_arm_line, = self.ax.plot([], [], [], 'o-', lw=6, markersize=12,
                                             color='#1a759f', alpha=0.8)
        self.forearm_line, = self.ax.plot([], [], [], 'o-', lw=6, markersize=12,
                                           color='#76c893', alpha=0.8)

        # Set initial 3D axes limits and the view angle
        self.ax.set_xlim3d(-1, 1)
        self.ax.set_ylim3d(-1, 1)
        self.ax.set_zlim3d(-1, 1)
        self.ax.view_init(elev=20, azim=45)

        # Create a QTimer to periodically update the 3D visualization
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(self.update_interval_ms)

    def update_plot(self):
        """
        Update the 3D visualization based on the current Euler angles.
        
        Steps:
        1. Safely retrieve the Euler angles (in degrees) for the upper arm and forearm.
        2. Convert the Euler angles from degrees to radians.
        3. Compute the corresponding rotation matrices.
        4. Compute the endpoints of the upper arm and forearm based on these rotation matrices.
        5. Update the 3D line objects to reflect the new arm positions.
        """
        # Retrieve Euler angles safely using the data lock
        with self.data_lock:
            # Get copies of the Euler angles for the upper arm and forearm
            upper_euler_deg = self.upper_arm_euler_ref[:]  # Expected format: [roll, pitch, yaw]
            forearm_euler_deg = self.forearm_euler_ref[:]

        # Convert the Euler angles from degrees to radians for computation
        upper_euler_rad = np.radians(upper_euler_deg)
        forearm_euler_rad = np.radians(forearm_euler_deg)

        # Compute rotation matrices from Euler angles using the helper function
        R_upper = euler_to_rotation_matrix(*upper_euler_rad)
        R_forearm = euler_to_rotation_matrix(*forearm_euler_rad)

        # Compute the endpoint of the upper arm:
        # The upper arm extends along the local x-axis, rotated by R_upper.
        upper_arm_end = R_upper @ np.array([self.upper_arm_length, 0, 0], dtype=float)
        # Compute the endpoint of the forearm:
        # The forearm extends along its local x-axis relative to the upper arm's orientation.
        forearm_end = upper_arm_end + R_forearm @ np.array([self.forearm_length, 0, 0], dtype=float)

        # Update the data for the upper arm line: from the shoulder to the upper arm endpoint.
        self.upper_arm_line.set_data_3d(
            [self.shoulder_pos[0], upper_arm_end[0]],
            [self.shoulder_pos[1], upper_arm_end[1]],
            [self.shoulder_pos[2], upper_arm_end[2]]
        )
        # Update the data for the forearm line: from the upper arm endpoint to the forearm endpoint.
        self.forearm_line.set_data_3d(
            [upper_arm_end[0], forearm_end[0]],
            [upper_arm_end[1], forearm_end[1]],
            [upper_arm_end[2], forearm_end[2]]
        )

        # Dynamically adjust the axes limits based on the forearm endpoint to ensure full visibility
        max_val = max(np.abs(forearm_end).max(), 1.0)
        self.ax.set_xlim3d(-max_val, max_val)
        self.ax.set_ylim3d(-max_val, max_val)
        self.ax.set_zlim3d(-max_val, max_val)

        # Redraw the canvas with the updated line data
        self.canvas.draw_idle()
