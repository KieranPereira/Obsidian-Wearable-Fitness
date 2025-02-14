# lateralraise2d.py
"""
Purpose:
--------
This script creates a PyQt6 widget for 2D elliptical arm tracking visualization.
It models the arm using two ellipses (representing the upper arm and forearm) and a circle (representing the hand).
The arm's motion is updated in real time based on the shoulder and forearm angles (in degrees) provided via external references.
This widget is typically used as part of a motion tracking system that processes data from IMU sensors.
"""

import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Ellipse, Circle

# Global constants for the dimensions of the arm parts
UPPER_ARM_WIDTH = 0.15  # Width of the upper arm ellipse
FOREARM_WIDTH   = 0.10  # Width of the forearm ellipse
HAND_RADIUS     = 0.05  # Radius of the hand circle

class LateralRaise2DTab(QWidget):
    """
    2D elliptical arm visualization widget.
    
    Expects a lock and two 1-element lists holding the 2D angles (in degrees)
    for the upper arm and forearm. The widget uses these angles to update
    the arm's position in a 2D plot.
    """
    def __init__(
        self,
        angle_lock,
        shoulder_angle_ref,
        elbow_angle_ref,
        upper_arm_length=0.5,
        forearm_length=0.5,
        update_interval_ms=50
    ):
        super().__init__()
        # Store the provided references and configuration parameters
        self.angle_lock = angle_lock
        self.shoulder_angle_ref = shoulder_angle_ref
        self.elbow_angle_ref = elbow_angle_ref
        self.upper_arm_length = upper_arm_length
        self.forearm_length   = forearm_length
        self.update_interval_ms = update_interval_ms
        
        # Initialize the user interface components
        self.initUI()

    def initUI(self):
        # Create a vertical layout for the widget
        layout = QVBoxLayout()
        
        # Create a matplotlib figure and axis for drawing the arm
        self.figure, self.ax = plt.subplots()
        # Create a canvas widget to embed the matplotlib figure in the PyQt app
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Set the axis limits to ensure the arm stays within the view
        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        # Remove the tick marks for a cleaner visualization
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        # Set the title of the plot
        self.ax.set_title("2D Elliptical Arm Tracking")

        # Initialize fixed shoulder position at the origin
        self.shoulder = np.array([0.0, 0.0])
        # Initialize elbow and hand positions (will be updated dynamically)
        self.elbow = np.array([0.0, 0.0])
        self.hand  = np.array([0.0, 0.0])

        # Create an ellipse to represent the upper arm
        self.upper_arm_ellipse = Ellipse(
            xy=(0, 0),                   # Initial center position (updated later)
            width=self.upper_arm_length, # Initial length of the upper arm
            height=UPPER_ARM_WIDTH,        # Constant width of the ellipse
            angle=0.0,                   # Initial rotation angle
            color="#ffcc99",
            zorder=2                     # Drawing order (above background elements)
        )
        # Create an ellipse to represent the forearm
        self.forearm_ellipse = Ellipse(
            xy=(0, 0),                   # Initial center position (updated later)
            width=self.forearm_length,   # Initial length of the forearm
            height=FOREARM_WIDTH,        # Constant width of the ellipse
            angle=0.0,                   # Initial rotation angle
            color="#ffcc99",
            zorder=2                     # Drawing order
        )
        # Create a circle to represent the hand
        self.hand_circle = Circle(
            xy=(0, 0),                   # Initial center position (updated later)
            radius=HAND_RADIUS,
            color="#ffcc99",
            zorder=3                     # Drawn above the arm ellipses
        )

        # Add the patches (upper arm, forearm, and hand) to the axis
        self.ax.add_patch(self.upper_arm_ellipse)
        self.ax.add_patch(self.forearm_ellipse)
        self.ax.add_patch(self.hand_circle)

        # Set up a QTimer to periodically update the visualization
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(self.update_interval_ms)

    def update_plot(self):
        # Safely retrieve the 2D angles (in degrees) using the lock
        with self.angle_lock:
            shoulder_deg = self.shoulder_angle_ref[0]
            forearm_deg  = self.elbow_angle_ref[0]

        # Convert the angles from degrees to radians for trigonometric calculations
        shoulder_rad = np.radians(shoulder_deg)
        forearm_rad  = np.radians(forearm_deg)
        # The total rotation for the forearm is the sum of the shoulder and forearm angles
        total_forearm_rad = shoulder_rad + forearm_rad

        # Compute the elbow position based on the shoulder angle and upper arm length
        self.elbow = self.shoulder + np.array([
            self.upper_arm_length * np.cos(shoulder_rad),
            self.upper_arm_length * np.sin(shoulder_rad)
        ])

        # Compute the hand position based on the elbow position and forearm length
        self.hand = self.elbow + np.array([
            self.forearm_length * np.cos(total_forearm_rad),
            self.forearm_length * np.sin(total_forearm_rad)
        ])

        # Update properties of the upper arm ellipse
        # The center of the ellipse is the midpoint between the shoulder and elbow
        upper_arm_center = (self.shoulder + self.elbow) / 2.0
        # The length of the ellipse is the distance between the shoulder and elbow
        upper_arm_length = np.linalg.norm(self.elbow - self.shoulder)
        # Calculate the angle of the upper arm in degrees for correct ellipse rotation
        upper_arm_angle_deg = np.degrees(np.arctan2(
            self.elbow[1] - self.shoulder[1],
            self.elbow[0] - self.shoulder[0]
        ))
        # Update the ellipse's center, width (length), and angle
        self.upper_arm_ellipse.set_center(upper_arm_center)
        self.upper_arm_ellipse.width = upper_arm_length
        self.upper_arm_ellipse.angle = upper_arm_angle_deg

        # Update properties of the forearm ellipse
        # The center is the midpoint between the elbow and hand
        forearm_center = (self.elbow + self.hand) / 2.0
        # The length is the distance between the elbow and hand
        forearm_length = np.linalg.norm(self.hand - self.elbow)
        # Calculate the angle for the forearm in degrees
        forearm_angle_deg = np.degrees(np.arctan2(
            self.hand[1] - self.elbow[1],
            self.hand[0] - self.elbow[0]
        ))
        # Update the forearm ellipse's center, width, and angle
        self.forearm_ellipse.set_center(forearm_center)
        self.forearm_ellipse.width = forearm_length
        self.forearm_ellipse.angle = forearm_angle_deg

        # Update the hand circle's position to the new hand coordinates
        self.hand_circle.center = (self.hand[0], self.hand[1])

        # Request the canvas to redraw with the updated arm positions
        self.canvas.draw_idle()
