import os
import cv2
import time
import logging
import requests
import threading
from region_timer import RegionTimer
from centroid_tracker import CentroidTracker
from collections import deque
from http.server import HTTPServer
from aicam_logging import aicam_log_init
from frame_process import VideoCaptureWithThread
from influxdb_client import InfluxDBClient

import yolo_part
from stream_part import CamHandler

RTSP_INPUT_URL = "rtsp://rtsp_server:8554/webcam"
USER = os.environ['INFLUXDB_ADMIN_USER']
PASSWORD = os.environ['INFLUXDB_ADMIN_PASSWORD']
DATABASE = os.environ['INFLUXDB_DB']
DATABASEHOST = "database"
FLAG = {"REFRESH": False}


def main(rtGroup):
    src = VideoCaptureWithThread(RTSP_INPUT_URL)
    ct = CentroidTracker(10)

    clear_frame = 0

    while True:
        if FLAG['REFRESH']:
            update_box_info(rtGroup)
            FLAG['REFRESH'] = False

        img = src.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        fpsTime = time.perf_counter()
        img, bboxList = yolo_part.detect(img)

        for rt in rtGroup:
            x1, y1, x2, y2 = list(map(int, rt.region))
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 3)

        if len(bboxList) == 0:
            if clear_frame <= 50:
                clear_frame += 1
            else:
                cv2.putText(img, "Clear", (500, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 0, 0), 2)
                ct.reset()
                for rt in rtGroup:
                    rt.reset()
        else:
            clear_frame = 0

        objects = ct.update(bboxList)
        for rt in rtGroup:
            rt.update(objects, CLIENT)

        for (objectID, centroid) in objects.items():
            text = "ID {}".format(objectID)
            cv2.putText(img, text, (centroid[0] - 10, centroid[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.circle(img, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

        if img is not None:
            fps = round(1/(time.perf_counter()-fpsTime), 2)
            # logging.info(str(fps))
            cv2.putText(img, "FPS: {}".format(round(fps, 4)), (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)

            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            queue.append(img)


def update_box_info(rtGroup: list):
    rtGroup.clear()
    boxInfo = requests.get("http://web:5000/get_box_info").json()
    for name, xywh in boxInfo.items():
        rtGroup.append(
            RegionTimer(name,
                        [xywh['x'],
                         xywh['y'],
                            xywh['x']+xywh['w'],
                            xywh['y']+xywh['h']]
                        )
        )


if __name__ == "__main__":
    aicam_log_init("/main_log.txt")
    CLIENT = InfluxDBClient(
        url=f'http://{DATABASEHOST}:8086', token=f'{USER}:{PASSWORD}', org='-')

    while not CLIENT.ping():
        time.sleep(5)
        logging.warning("Connection failed. Retry in 5 seconds....")

    queue = deque(maxlen=5)

    rtGroup = []
    update_box_info(rtGroup)

    server = HTTPServer(('0.0.0.0', 5555),
                        lambda *args, **kwargs: CamHandler(queue, FLAG, *args, **kwargs))
    print("Server started")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    main(rtGroup)
    server.shutdown()
