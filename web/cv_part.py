import cv2


def get_current_image(toJPG=False, demo=False):
    src = "rtsp://rtsp_server:8554/"
    src += "test" if demo else "webcam"

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print("Error opening the camera")
        return None

    # Buffer
    for _ in range(10):
        ret, frame = cap.read()

    # Check if the frame was successfully captured
    if not ret:
        print("Error capturing the frame")
        return None

    if toJPG:
        ret, frame = cv2.imencode('.jpg', frame)
        if not ret:
            print("Error encode to jpg")
            return None

    cap.release()
    return frame
