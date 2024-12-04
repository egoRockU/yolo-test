from flask import Flask, render_template, request
from serial import Serial
import time
import threading
from threading import Lock

import cv2
import numpy as np
from ultralytics import YOLO
from picamera2 import Picamera2
from gpiozero import LED

# INITIAL SETUPS
SERIAL = "/dev/ttyACM0"
app = Flask(__name__)
ser = Serial()
ser.baudrate = 115200
ser.port = SERIAL
ser.timeout = 1

data_buffer = []
buffer_lock = Lock()
flash = LED(23)


@app.route('/')
def hello_world():
   with buffer_lock:
       print (data_buffer)

   return data_buffer


def serial_listen():
    time.sleep(5)
    try:
        ser.open()
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        return
   
    while True:
        if ser.in_waiting:
            data = ser.readline().decode('utf8').strip()
            if 'OBJECT DETECTED!' in data:
                image_arr = pi_capture_image()
                if image_arr is None:
                    data_buffer.append('Camera did not work properly')
                    res = "res: " + str(4) + "\n"
                    ser.write(res.encode())
                    print(data_buffer)
                else:
                    bottle_class = identify_bottle(image_arr)
                    if bottle_class is None:
                        print("Not bottle")
                        with buffer_lock:
                            data_buffer.append("Not Bottle")
                            res = "res: " + str(3) + "\n"
                            print(res)
                            ser.write(res.encode())
                            print(data_buffer)
                    else:
                        print("bottle class: ", bottle_class)
                        with buffer_lock:
                            data_buffer.append(bottle_class)
                            res = "res: " + str(bottle_class) + "\n"
                            ser.write(res.encode())
                            print(data_buffer)


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

def pi_capture_image():
    picam2 = Picamera2()
    camera_config = picam2.create_still_configuration(
        main={"size": (640, 640), "format": "RGB888"}, 
        )
    picam2.configure(camera_config)

    picam2.start()
    flash.on()
    time.sleep(2)
    frame = picam2.capture_array()
    flash.off()
    picam2.close()
    
    return frame

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
    listener_thread = threading.Thread(target=serial_listen, daemon=True)
    listener_thread.start()

    # Run the Flask app
    app.run(threaded=True)