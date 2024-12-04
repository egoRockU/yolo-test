from ultralytics import YOLO

model = YOLO("300ep.pt")

model.export(format="onnx")