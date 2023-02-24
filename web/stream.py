import cv2
from flask import Flask, render_template, Response

# Initialize Flask and OpenCV
app = Flask(__name__)
cap = cv2.VideoCapture(r"rtsp://rtsp_server:8554/webcam")


def gen():
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n\r\n')


@app.route('/')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
