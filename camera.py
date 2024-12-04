from ultralytics import YOLO

model = YOLO("models/300ep.pt")

results = model(source="0", show=True, conf=0.4)

