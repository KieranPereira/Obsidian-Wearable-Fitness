# biometric_visualizer_3d.py
import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

# For 3D plotting
from mpl_toolkits.mplot3d import Axes3D  # needed for 3D support

class BiometricVisualizer3DTab(QWidget):
    """
    A QWidget-based class for 3D arm visualization using quaternions.
    """

    def __init__(
        self,
        data_lock,
        upper_arm_quat_ref,
        forearm_quat_ref,
        upper_arm_length=0.4,
        forearm_length=0.35,
        update_interval_ms=50
    ):
        """
        :param data_lock: threading.Lock shared by the main script
        :param upper_arm_quat_ref: reference to an array/list storing the upper arm quaternion
        :param forearm_quat_ref: reference to an array/list storing the forearm quaternion
        :param upper_arm_length: length of the upper arm in 3D
        :param forearm_length: length of the forearm in 3D
        :param update_interval_ms: refresh rate in ms
        """
        super().__init__()

        self.data_lock = data_lock
        self.upper_arm_quat_ref = upper_arm_quat_ref
        self.forearm_quat_ref   = forearm_quat_ref
        self.upper_arm_length   = upper_arm_length
        self.forearm_length     = forearm_length
        self.update_interval_ms = update_interval_ms

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 3D figure + canvas
        self.fig = plt.figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Hide tick labels
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_zticklabels([])

        # Create lines for upper arm + forearm
        self.shoulder_pos = np.array([0.0, 0.0, 0.0])
        self.upper_arm_line, = self.ax.plot([], [], [], 'o-', lw=6, markersize=12,
                                            color='#1a759f', alpha=0.8)
        self.forearm_line, = self.ax.plot([], [], [], 'o-', lw=6, markersize=12,
                                          color='#76c893', alpha=0.8)

        self.ax.set_xlim3d(-1, 1)
        self.ax.set_ylim3d(-1, 1)
        self.ax.set_zlim3d(-1, 1)
        self.ax.view_init(elev=20, azim=45)

        # QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(self.update_interval_ms)

    def quaternion_rotation_matrix(self, q):
        """Convert quaternion [w, x, y, z] into a 3x3 rotation matrix."""
        w, x, y, z = q
        return np.array([
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w,     2*x*z + 2*y*w],
            [2*x*y + 2*z*w,     1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
            [2*x*z - 2*y*w,     2*y*z + 2*x*w,     1 - 2*x*x - 2*y*y]
        ], dtype=float)

    def update_plot(self):
        with self.data_lock:
            q_upper = np.array(self.upper_arm_quat_ref)
            q_forearm = np.array(self.forearm_quat_ref)

        # Upper arm rotation matrix
        R_upper = self.quaternion_rotation_matrix(q_upper)
        # Assume local +Y is the arm direction
        upper_arm_end = R_upper @ np.array([0, self.upper_arm_length, 0], dtype=float)

        # Forearm orientation
        R_forearm = self.quaternion_rotation_matrix(q_forearm)
        forearm_end = upper_arm_end + R_forearm @ np.array([0, self.forearm_length, 0], dtype=float)

        # Update lines
        self.upper_arm_line.set_data_3d(
            [self.shoulder_pos[0], upper_arm_end[0]],
            [self.shoulder_pos[1], upper_arm_end[1]],
            [self.shoulder_pos[2], upper_arm_end[2]]
        )
        self.forearm_line.set_data_3d(
            [upper_arm_end[0], forearm_end[0]],
            [upper_arm_end[1], forearm_end[1]],
            [upper_arm_end[2], forearm_end[2]]
        )

        # Optional: adjust axes
        max_val = max(np.abs(forearm_end).max(), 1.0)
        self.ax.set_xlim3d(-max_val, max_val)
        self.ax.set_ylim3d(-max_val, max_val)
        self.ax.set_zlim3d(-max_val, max_val)

        self.canvas.draw_idle()
