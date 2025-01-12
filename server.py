from flask import Flask, render_template, request
from serial import Serial
import time
import threading
from threading import Lock

import cv2
import numpy as np
from ultralytics import YOLO

# INITIAL SETUPS
VENDO_SERIAL = "COM13"
FILTER_SERIAL = "COM3"

app = Flask(__name__)

# VENDO SERIAL CONNECTION
vendo_ser = Serial()
vendo_ser.baudrate = 115200
vendo_ser.port = VENDO_SERIAL
vendo_ser.timeout = 1

# FILTER SERIAL CONNECTION
filter_ser = Serial()
filter_ser.baudrate = 115200
filter_ser.port = FILTER_SERIAL
filter_ser.timeout = 1

data_buffer = []
buffer_lock = Lock()



@app.route('/')
def hello_world():
   with buffer_lock:
       print (data_buffer)

   return data_buffer


def vendo_serial_listen():
    time.sleep(5)
    try:
        vendo_ser.open()
        filter_ser.open()
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        return
   
    print("here")
    while True:
        if vendo_ser.in_waiting:
            data = vendo_ser.readline().decode('utf8').strip()
            # for detected objects for yolo to process
            if 'OBJECT DETECTED!' in data:
                image_arr = capture_image()
                if image_arr is None:
                    data_buffer.append('Camera did not work properly')
                    res = "res: " + str(4) + "\n"
                    vendo_ser.write(res.encode())
                    print(data_buffer)
                else:
                    bottle_class = identify_bottle(image_arr)
                    if bottle_class is None:
                        print("Not bottle")
                        with buffer_lock:
                            data_buffer.append("Not Bottle")
                            res = "res: " + str(3) + "\n"
                            print(res)
                            vendo_ser.write(res.encode())
                            print(data_buffer)
                    else:
                        print("bottle class: ", bottle_class)
                        with buffer_lock:
                            data_buffer.append(bottle_class)
                            res = "res: " + str(bottle_class) + "\n"
                            vendo_ser.write(res.encode())
                            print(data_buffer)
            
            # when liters are send, send a response to microcontroller to open pumpers.
            if 'TOTAL LITERS:' in data:
                liters = int(data.split(':')[-1].strip())
                res = "res: " + str(liters) + "\n"
                filter_ser.write(res.encode())


def capture_image():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if cap.isOpened():
        frame_count = 0
        while frame_count < 100:
            ret, frame = cap.read()
            frame_array = np.array(frame)
            frame_count += 1
    else:
        return None

    cap.release()
    cv2.destroyAllWindows()

    return frame_array

def identify_bottle(image_array):
    yolo_model = "models/300ep.pt"
    cls_list = ["Large", "Medium", "Small"]

    model = YOLO(yolo_model)

    results = model(source=image_array, conf=0.4)

    if (len(results[0]) == 0):
        return None

    result = results[0].boxes.cpu().numpy()
    print("Result: ", result.cls[0])
    object_cls = int(result.cls[0])

    return object_cls       



if __name__ == '__main__':
    # Start the serial listener thread
    listener_thread = threading.Thread(target=vendo_serial_listen, daemon=True)
    listener_thread.start()

    # Run the Flask app
    app.run(debug=True, threaded=True)