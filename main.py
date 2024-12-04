from ultralytics import YOLO

model = YOLO("models/300ep.pt")
cls_list = ["Large", "Medium", "Small"]
#results = model(source="0", show=True, conf=0.4, save=True)

# onnx_model = YOLO("300ep.onnx")

results = model(source="profilePic.PNG", conf=0.4)

if (len(results[0]) == 0):
    raise Exception("No Detected Bottles")

result = results[0].boxes.cpu().numpy()

object_cls = int(result.cls[0])

print("Detected Object:", cls_list[object_cls])