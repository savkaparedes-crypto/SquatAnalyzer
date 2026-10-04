import cv2
import mediapipe as mp
import numpy as np

from .biomechanics import calculate_angle, interpolate_nan, smooth_signal

mp_pose = mp.solutions.pose

def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("No se pudo abrir el video.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    times, angles, visibility_values = [], [], []
    frame_number = 0

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            angle, visibility = np.nan, 0.0

            if result.pose_landmarks:
                lm = result.pose_landmarks.landmark
                hip = lm[mp_pose.PoseLandmark.RIGHT_HIP]
                knee = lm[mp_pose.PoseLandmark.RIGHT_KNEE]
                ankle = lm[mp_pose.PoseLandmark.RIGHT_ANKLE]
                visibility = min(hip.visibility, knee.visibility, ankle.visibility)

                if visibility > 0.5:
                    angle = calculate_angle(
                        [hip.x, hip.y],
                        [knee.x, knee.y],
                        [ankle.x, ankle.y],
                    )

            times.append(frame_number / fps)
            angles.append(angle)
            visibility_values.append(visibility)
            frame_number += 1

    cap.release()

    times = np.asarray(times, dtype=float)
    angles = np.asarray(angles, dtype=float)
    visibility_values = np.asarray(visibility_values, dtype=float)

    if np.sum(~np.isnan(angles)) >= 2:
        angles = smooth_signal(interpolate_nan(angles), 7)

    return times, angles, visibility_values, frame_count, fps
