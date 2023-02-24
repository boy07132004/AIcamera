import cv2
from collections import deque
import threading


class VideoCaptureWithThread:
    def __init__(self, source, size=3):
        self.source = source
        self.capture = cv2.VideoCapture(source)
        self.queue = deque(maxlen=3)
        self.stopped = False
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while not self.stopped and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                self.queue.append(frame)

        self.stop()

    def read(self):
        while len(self.queue) == 0:
            pass
        return self.queue.popleft()

    def stop(self):
        self.stopped = True
        self.thread.join()

    def release(self):
        self.capture.release()
