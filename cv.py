import cv2
import numpy as np
from ultralytics import YOLO

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if cap.isOpened():
    frame_count = 0
    while frame_count < 100:
        ret, frame = cap.read()
        #frame = cv2.resize(frame, (640, 640))
        frame_array = np.array(frame)
        frame_count += 1
    cv2.imwrite('captured.jpg', frame)
    print("Captured Frame:", frame_array.shape)
    cap.release()
    cv2.destroyAllWindows()


model = YOLO("300ep.pt")
cls_list = ["Large", "Medium", "Small"]

results = model(source=frame_array, conf=0.4)

if (len(results[0]) == 0):
    raise Exception("No Detected Bottles")

result = results[0].boxes.cpu().numpy()

object_cls = int(result.cls[0])

print("Detected Object:", cls_list[object_cls])
