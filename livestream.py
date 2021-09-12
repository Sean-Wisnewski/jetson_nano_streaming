import cv2
import time, threading
from flask import Response, Flask

global video_frame
video_frame = None

global thread_lock
thread_lock = threading.Lock()

GSTREAMER_PIPELINE = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=3280, height=2464, format=(string)NV12, framerate=21/1 ! nvvidconv flip-method=0 ! video/x-raw, width=960, height=616, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink wait-on-eos=false max-buffers=1 drop=True'

app = Flask(__name__)

def capture_frames():
    global video_frame, thread_lock

    cap = cv2.VideoCapture(GSTREAMER_PIPELINE, cv2.CAP_GSTREAMER)

    while True and cap.isOpened():
        return_key, frame = cap.read()
        if not return_key:
            break

        with thread_lock:
            video_frame = frame.copy()

        key = cv2.waitKey(30) & 0xff
        if key == 27:
            break

    cap.release()

def encode_frame():
    global thread_lock
    while True:
        with thread_lock:
            global video_frame
            if video_frame is None:
                continue
            return_key, encoded_image = cv2.imencode(".jpg", video_frame)

            yield('--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

@app.route('/')
def stream_frames():
    return Response(encode_frame(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__=="__main__":
    process_thread = threading.Thread(target=capture_frames)
    process_thread.daemon = True

    process_thread.start()
    app.run("0.0.0.0", port="8000")