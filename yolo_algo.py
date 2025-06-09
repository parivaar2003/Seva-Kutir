import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
import matplotlib.pyplot as plt

# Load models
yolo_model = YOLO("yolo11n.pt")  # or yolov8s.pt for better accuracy
mp_pose = mp.solutions.pose.Pose(static_image_mode=True)

def preprocess_image(image_path):
    image = cv2.imread(image_path)
    image = cv2.resize(image, (640, 640))

    # Light normalization
    yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
    image_norm = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

    # Denoise
    image_denoised = cv2.fastNlMeansDenoisingColored(image_norm, None, 10, 10, 7, 21)
    return image_denoised

def detect_people(image):
    results = yolo_model(image)
    person_boxes = []
    for box in results[0].boxes.data:
        x1, y1, x2, y2, conf, cls = box
        if int(cls) == 0:
            person_boxes.append((int(x1), int(y1), int(x2), int(y2)))
    return person_boxes

def estimate_poses(image, boxes):
    pose_count = 0
    for x1, y1, x2, y2 in boxes:
        cropped = image[y1:y2, x1:x2]
        rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        results = mp_pose.process(rgb)
        if results.pose_landmarks:
            pose_count += 1
    return pose_count

def count_density(image, boxes):
    height, width = image.shape[:2]
    density_map = np.zeros((height, width), dtype=np.float32)
    for x1, y1, x2, y2 in boxes:
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.circle(density_map, (cx, cy), 20, 1, -1)
    estimated_count = np.sum(density_map) / (np.pi * 20 * 20)
    return int(estimated_count)

def pipeline(image_path):
    image = preprocess_image(image_path)
    boxes = detect_people(image)
    pose_count = estimate_poses(image, boxes)
    density_estimate = count_density(image, boxes)

    print(f"YOLO Detected Bodies: {len(boxes)}")
    print(f"MediaPipe Pose Estimates: {pose_count}")
    print(f"Density Estimated Count: {density_estimate}")

    for (x1, y1, x2, y2) in boxes:
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Detected Students")
    plt.axis("off")
    plt.show()

# Example usage
pipeline("images/IMG-20211007-WA0150.jpg")
