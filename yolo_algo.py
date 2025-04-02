from ultralytics import YOLO
import os

model = YOLO("yolo11n.pt")  
images = [os.path.join('images', img) for img in os.listdir('images')]
results = model(images)


# Process results list
for result in results:
    path = result.path
    image_name = path.split('\\')[-1]
    boxes = result.boxes
    result.save(filename=f"{os.path.join('results',image_name)}")