import json
import redis
import requests
from flask import render_template, request, make_response, jsonify, Blueprint
from flask_login import login_required


PERSON = Blueprint('person', __name__)
POOL = redis.ConnectionPool(host="aicamera_redis_1",
                            port=6379, decode_responses=True)
REDIS = redis.Redis(connection_pool=POOL)
WIDTH = 640
HEIGHT = 480


@PERSON.route('/person_box_setting', methods=['GET'])
@PERSON.route('/get_box_info', methods=['GET'])
def box_setting():
    rule = request.url_rule
    boxInfo = REDIS.get("boxInfo") or "{}"
    areaMap = json.loads(boxInfo)
    if rule.rule == "/get_box_info":
        return areaMap

    return render_template("main.html", historyArea=areaMap)


@PERSON.route('/update_box_info', methods=["POST"])
@login_required
def update_box_info():
    boxJson = request.json
    boxInfo = {}

    for name, info in boxJson.items():
        if len(info["newName"]) > 0:
            name = info["newName"]

        boxInfo[name] = {
            "x": info["x"],
            "y": info["y"],
            "w": max(1, info["w"]),
            "h": max(1, info["h"])
        }

    REDIS.set("boxInfo", json.dumps(boxInfo))
    requests.get("http://person_tracking:5555/refresh")

    return jsonify(status="OK"), 200
