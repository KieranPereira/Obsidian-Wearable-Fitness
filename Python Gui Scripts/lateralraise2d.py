# lateralraise2d.py
import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Ellipse, Circle

# Ellipse and circle dimensions for the 2D arm
UPPER_ARM_WIDTH = 0.15
FOREARM_WIDTH   = 0.10
HAND_RADIUS     = 0.05

class LateralRaise2DTab(QWidget):
    """
    2D elliptical arm visualization.
    Expects references to a lock and two 1-element lists holding the 2D angles
    (in degrees) for the upper arm and forearm.
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
        self.angle_lock = angle_lock
        self.shoulder_angle_ref = shoulder_angle_ref
        self.elbow_angle_ref = elbow_angle_ref
        self.upper_arm_length = upper_arm_length
        self.forearm_length   = forearm_length
        self.update_interval_ms = update_interval_ms
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-0.2, 1.2)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_title("2D Elliptical Arm Tracking")

        # Fixed shoulder at origin; initialize elbow and hand positions
        self.shoulder = np.array([0.0, 0.0])
        self.elbow = np.array([0.0, 0.0])
        self.hand  = np.array([0.0, 0.0])

        # Create ellipse patches for the upper arm and forearm, and a circle for the hand.
        self.upper_arm_ellipse = Ellipse(
            xy=(0, 0),
            width=self.upper_arm_length,
            height=UPPER_ARM_WIDTH,
            angle=0.0,
            color="#ffcc99",
            zorder=2
        )
        self.forearm_ellipse = Ellipse(
            xy=(0, 0),
            width=self.forearm_length,
            height=FOREARM_WIDTH,
            angle=0.0,
            color="#ffcc99",
            zorder=2
        )
        self.hand_circle = Circle(
            xy=(0, 0),
            radius=HAND_RADIUS,
            color="#ffcc99",
            zorder=3
        )

        self.ax.add_patch(self.upper_arm_ellipse)
        self.ax.add_patch(self.forearm_ellipse)
        self.ax.add_patch(self.hand_circle)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(self.update_interval_ms)

    def update_plot(self):
        # Retrieve the 2D angles (in degrees) safely
        with self.angle_lock:
            shoulder_deg = self.shoulder_angle_ref[0]
            forearm_deg  = self.elbow_angle_ref[0]

        # Convert degrees to radians
        shoulder_rad = np.radians(shoulder_deg)
        forearm_rad  = np.radians(forearm_deg)
        total_forearm_rad = shoulder_rad + forearm_rad

        # Compute elbow position
        self.elbow = self.shoulder + np.array([
            self.upper_arm_length * np.cos(shoulder_rad),
            self.upper_arm_length * np.sin(shoulder_rad)
        ])

        # Compute hand position
        self.hand = self.elbow + np.array([
            self.forearm_length * np.cos(total_forearm_rad),
            self.forearm_length * np.sin(total_forearm_rad)
        ])

        # Update upper arm ellipse properties
        upper_arm_center = (self.shoulder + self.elbow) / 2.0
        upper_arm_length = np.linalg.norm(self.elbow - self.shoulder)
        upper_arm_angle_deg = np.degrees(np.arctan2(
            self.elbow[1] - self.shoulder[1],
            self.elbow[0] - self.shoulder[0]
        ))
        self.upper_arm_ellipse.set_center(upper_arm_center)
        self.upper_arm_ellipse.width = upper_arm_length
        self.upper_arm_ellipse.angle = upper_arm_angle_deg

        # Update forearm ellipse properties
        forearm_center = (self.elbow + self.hand) / 2.0
        forearm_length = np.linalg.norm(self.hand - self.elbow)
        forearm_angle_deg = np.degrees(np.arctan2(
            self.hand[1] - self.elbow[1],
            self.hand[0] - self.elbow[0]
        ))
        self.forearm_ellipse.set_center(forearm_center)
        self.forearm_ellipse.width = forearm_length
        self.forearm_ellipse.angle = forearm_angle_deg

        # Update hand circle
        self.hand_circle.center = (self.hand[0], self.hand[1])

        self.canvas.draw_idle()
