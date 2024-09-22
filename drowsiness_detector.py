# drowsiness_detector.py
import cv2
import mediapipe as mp
import numpy as np
import threading
import time
import pygame
import json
import datetime
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QImage

class DrowsinessDetector(QObject):
    # Signals to communicate with the GUI
    update_frame = pyqtSignal(QImage)
    update_incidents = pyqtSignal(int)
    update_duration = pyqtSignal(float)
    toggle_visualization = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        # Initialize MediaPipe Face Mesh and webcam
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)
        self.cap = cv2.VideoCapture(0)  # Use 0 for the default camera

        # Define eye landmark indices
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]

        # Thresholds
        self.EAR_THRESHOLD = 0.25

        # Initialize variables for drowsiness detection
        self.drowsiness_incident_count = 0
        self.is_drowsy = False
        self.drowsiness_start_time = None
        self.drowsiness_duration = 0
        self.eyes_closed_start_time = None
        self.eyes_open_start_time = None

        # Visualization toggle
        self.visualize_landmarks = True

        # Initialize pygame mixer for sound playback
        pygame.mixer.init()
        # Load the alarm sound
        self.alarm_sound = pygame.mixer.Sound('alarm.mp3')
        # Initialize a specific channel for the alarm sound
        self.alarm_channel = pygame.mixer.Channel(0)

        # Start the detection thread
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def start_alarm(self):
        if not self.alarm_channel.get_busy():
            self.alarm_channel.play(self.alarm_sound, loops=-1)  # Play the sound indefinitely
            print("Alarm started")

    def stop_alarm(self):
        if self.alarm_channel.get_busy():
            self.alarm_channel.fadeout(5000)  # Fade out over 5000 milliseconds (5 seconds)
            print("Alarm stopped with fadeout")

    def log_incident(self, incident_start_time, incident_end_time, duration):
        incident = {
            'createdDateTime': datetime.datetime.now().isoformat(),
            'incidentStartDateTime': datetime.datetime.fromtimestamp(incident_start_time).isoformat(),
            'incidentStopDateTime': datetime.datetime.fromtimestamp(incident_end_time).isoformat(),
            'incidentDurationInSeconds': round(duration, 2)
        }

        # Read existing incidents from the file
        try:
            with open('drowsiness_log.json', 'r') as f:
                incidents = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            incidents = []

        # Append the new incident
        incidents.append(incident)

        # Write the updated incidents back to the file
        with open('drowsiness_log.json', 'w') as f:
            json.dump(incidents, f, indent=4)

        print("Drowsiness incident logged")

    def calculate_EAR(self, landmarks, indices):
        # Extract the coordinates of the eye landmarks
        eye = np.array([[landmarks[idx].x, landmarks[idx].y] for idx in indices])
        # Compute distances between the horizontal and vertical eye landmarks
        horizontal = np.linalg.norm(eye[0] - eye[3])
        vertical1 = np.linalg.norm(eye[1] - eye[5])
        vertical2 = np.linalg.norm(eye[2] - eye[4])
        EAR = (vertical1 + vertical2) / (2.0 * horizontal)
        return EAR

    def run(self):
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip the frame horizontally for a later selfie-view display
            frame = cv2.flip(frame, 1)
            # Convert the BGR frame to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Process the frame to find face landmarks
            results = self.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Calculate EAR for both eyes
                    left_EAR = self.calculate_EAR(face_landmarks.landmark, self.LEFT_EYE)
                    right_EAR = self.calculate_EAR(face_landmarks.landmark, self.RIGHT_EYE)
                    avg_EAR = (left_EAR + right_EAR) / 2.0

                    # Visualize landmarks if enabled
                    if self.visualize_landmarks:
                        mp.solutions.drawing_utils.draw_landmarks(
                            rgb_frame, face_landmarks, self.mp_face_mesh.FACEMESH_TESSELATION,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=1)
                        )

                    # Check if EAR is below the threshold (eyes closed)
                    if avg_EAR < self.EAR_THRESHOLD:
                        if self.eyes_closed_start_time is None:
                            self.eyes_closed_start_time = time.time()
                        else:
                            eyes_closed_duration = time.time() - self.eyes_closed_start_time
                            if eyes_closed_duration >= 3 and not self.is_drowsy:
                                # Eyes have been closed for more than 3 seconds, start drowsiness incident
                                self.is_drowsy = True
                                self.drowsiness_start_time = self.eyes_closed_start_time
                                self.drowsiness_incident_count += 1
                                # Start alarm
                                self.start_alarm()
                    else:
                        # Eyes are open
                        if self.eyes_open_start_time is None:
                            self.eyes_open_start_time = time.time()
                        else:
                            eyes_open_duration = time.time() - self.eyes_open_start_time
                            if eyes_open_duration >= 3 and self.is_drowsy:
                                # Eyes have been open for more than 3 seconds, end drowsiness incident
                                self.is_drowsy = False
                                self.drowsiness_duration = time.time() - self.drowsiness_start_time
                                # Stop alarm with fadeout
                                self.stop_alarm()
                                # Log the incident
                                incident_end_time = time.time()
                                self.log_incident(self.drowsiness_start_time, incident_end_time, self.drowsiness_duration)
                        # Reset eyes_closed_start_time
                        self.eyes_closed_start_time = None

                    # If currently in drowsy state, update drowsiness_duration
                    if self.is_drowsy:
                        self.drowsiness_duration = time.time() - self.drowsiness_start_time
                    else:
                        # Keep the last drowsiness_duration value
                        pass

                    # Emit signals to update GUI
                    self.update_incidents.emit(self.drowsiness_incident_count)
                    self.update_duration.emit(self.drowsiness_duration)

            else:
                # No face detected, reset variables
                self.eyes_closed_start_time = None
                self.eyes_open_start_time = None
                if self.is_drowsy:
                    self.is_drowsy = False
                    self.drowsiness_duration = time.time() - self.drowsiness_start_time
                    # Stop alarm with fadeout
                    self.stop_alarm()
                    # Log the incident
                    incident_end_time = time.time()
                    self.log_incident(self.drowsiness_start_time, incident_end_time, self.drowsiness_duration)

            # Convert frame to QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # Emit signal to update frame
            self.update_frame.emit(qt_image)

        self.cap.release()
        pygame.mixer.quit()

    def toggle_landmarks(self):
        self.visualize_landmarks = not self.visualize_landmarks
