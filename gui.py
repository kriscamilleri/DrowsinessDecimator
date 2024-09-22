# gui.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from drowsiness_detector import DrowsinessDetector

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Drowsiness Detection')
        self.detector = DrowsinessDetector()

        # Video display label
        self.video_label = QLabel()
        self.video_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(1, 1)

        # Incident counter label
        self.incident_label = QLabel('Incidents: 0')
        self.incident_label.setFont(QFont('Arial', 16))
        self.incident_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.incident_label.setMinimumSize(1, 1)

        # Duration label
        self.duration_label = QLabel('Duration: 0.0s')
        self.duration_label.setFont(QFont('Arial', 16))
        self.duration_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.duration_label.setMinimumSize(1, 1)

        # Toggle button
        self.toggle_button = QPushButton('Toggle Outline')
        self.toggle_button.clicked.connect(self.detector.toggle_landmarks)
        self.toggle_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.toggle_button.setMinimumSize(1, 1)

        # Layouts
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add video label to the main layout
        main_layout.addWidget(self.video_label, stretch=1)

        # Create a horizontal layout for the labels
        labels_layout = QHBoxLayout()
        labels_layout.setSpacing(0)
        labels_layout.addWidget(self.incident_label)
        labels_layout.addWidget(self.duration_label)
        labels_layout.setAlignment(Qt.AlignCenter)
        # Add the labels layout to the main layout
        main_layout.addLayout(labels_layout)

        # Add the toggle button to the main layout, centered
        main_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        # Connect signals
        self.detector.update_frame.connect(self.update_image)
        self.detector.update_incidents.connect(self.update_incidents)
        self.detector.update_duration.connect(self.update_duration)

    def update_image(self, qt_image):
        self.latest_frame = qt_image  # Store the latest frame
        # Get the size of the video_label, ensuring minimum dimensions of 1 pixel
        label_width = max(1, self.video_label.width())
        label_height = max(1, self.video_label.height())
        # Scale the image to fit the label's size while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        pixmap = pixmap.scaled(label_width, label_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(pixmap)

    def update_incidents(self, count):
        self.incident_label.setText(f'Incidents: {count}')

    def update_duration(self, duration):
        self.duration_label.setText(f'Duration: {duration:.1f}s')

    def resizeEvent(self, event):
        # Force an update of the video label when the window is resized
        if hasattr(self, 'latest_frame'):
            self.update_image(self.latest_frame)
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.detector.cap.release()
        self.detector.thread.join()  # Ensure the detection thread has finished
        event.accept()
