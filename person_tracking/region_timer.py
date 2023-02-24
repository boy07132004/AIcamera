import os
import time
from collections import OrderedDict
from datetime import datetime
from influxdb_client import Point
from influxdb_client .client.write_api import SYNCHRONOUS


RETENTIONPOLICY = 'autogen'
DATABASE = os.environ['INFLUXDB_DB']
BUCKET = f'{DATABASE}/{RETENTIONPOLICY}'


class RegionTimer():
    def __init__(self, regionName, region):
        self.location = regionName
        self.staytime = OrderedDict()
        self.starttime = OrderedDict()
        self.status = OrderedDict()

        xList = [region[0], region[2]]
        yList = [region[1], region[3]]
        self.region = min(xList), min(yList), max(xList), max(yList)

    def register(self, ID):
        self.status[ID] = 0
        self.staytime[ID] = 0

    def enter(self, ID):
        self.starttime[ID] = time.perf_counter()
        self.status[ID] += 1

    def leave(self, ID):
        self.staytime[ID] += time.perf_counter() - self.starttime[ID]
        self.starttime.pop(ID)
        self.status[ID] = 0

    def reset(self):
        self.status.clear()

    def is_in_matrix(self, centroid, matrix):

        if len(centroid) != 2 or len(matrix) != 4:
            raise ValueError("centroid or matrix size error.")
        x, y = centroid
        if x <= matrix[0] or x >= matrix[2] or y <= matrix[1] or y >= matrix[3]:

            return False

        return True

    def detect(self, ID, centroid):
        if self.status[ID] == 0:
            if self.is_in_matrix(centroid, self.region):
                self.enter(ID)

        elif self.status[ID] == 1:
            if not (self.is_in_matrix(centroid, self.region)):
                self.leave(ID)

    def update(self, objects, dbclient):
        recentObjects = set(self.staytime.keys())

        for (objectID, centroid) in objects.items():

            if objectID in recentObjects:
                recentObjects.remove(objectID)

            if objectID in self.status:
                self.detect(objectID, centroid)
            else:
                self.register(objectID)

        for key in list(recentObjects):
            if self.status[key] > 0:
                self.leave(key)
            stayTime = self.staytime.pop(key)

            self.record(dbclient, stayTime)

    def record(self, dbclient, stayTime):
        if stayTime < 1:
            return

        p = Point("person_stay_time").tag("location", self.location)
        p.field("stay", float(stayTime))
        p.time(datetime.utcnow())
        dbclient.write_api(write_options=SYNCHRONOUS).write(
            bucket=BUCKET, record=p.to_line_protocol())
