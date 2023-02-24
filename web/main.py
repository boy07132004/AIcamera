import json
import redis
import cv_part
import requests
from flasgger import Swagger
from flask import Flask, render_template, Response, redirect, url_for, request, make_response, jsonify


WIDTH = 640
HEIGHT = 480
HOST = "aicamera_redis_1"
POOL = redis.ConnectionPool(host=HOST, port=6379, decode_responses=True)
REDIS = redis.Redis(connection_pool=POOL)
FUNCTION = {"person_tracking": False}
APP = Flask(__name__)


@APP.route('/', methods=['GET'])
@APP.route('/get_box_info', methods=['GET'])
def index():
    rule = request.url_rule
    boxInfo = REDIS.get("boxInfo") or "{}"
    areaMap = json.loads(boxInfo)
    if rule.rule == "/get_box_info":
        return areaMap

    return render_template("main.html", historyArea=areaMap)


@APP.route('/get_image')
def get_image():
    jpeg = cv_part.get_current_image(True)
    if jpeg is not None:

        return Response(jpeg.tobytes(), content_type='image/jpeg')

    return redirect(url_for('index'))


def reset_box():
    REDIS.set("boxInfo", "")

    return make_response("OK", 200)


@APP.route('/get_info', methods=["GET"])
def get_info():

    return jsonify('{"frameWidth":640, "frameHeight":480}')


@APP.route('/update_box_info', methods=["POST"])
def update_box_info():
    boxJson = request.json
    boxInfo = {}

    for name, info in boxJson.items():
        if len(info["newName"]) > 0:
            name = info["newName"]

        boxInfo[name] = {}
        for attr in ["x", "y", "w", "h"]:
            if info[attr] <= 0:
                return make_response("The values of x, y, w, and h cannot be less than 0.", 400)
            boxInfo[str(name)][attr] = info[attr]

    REDIS.set("boxInfo", json.dumps(boxInfo))
    requests.get("http://person_tracking:5555/refresh")

    return make_response("OK", 200)


@APP.route('/service/<service>', methods=["GET"])
def service_set(service):
    cmd = request.args["cmd"]
    if service not in FUNCTION:

        return make_response("The service \"{service}\" is not available", 400)

    if cmd == "status":
        if FUNCTION[service]:
            status = "running"
        else:
            status = "idle"

        return make_response(f"{service} service is {status} now", 200)

    elif cmd == "start":
        FUNCTION[service] = True

    elif cmd == "stop":
        FUNCTION[service] = False

    else:

        return make_response(f"The command \"{cmd}\" is not available", 400)

    return make_response("Successed.", 200)


if __name__ == "__main__":
    APP.config['SWAGGER'] = {
        "title": "AI Camera",
        "description": "My API",
        "version": "1.0.0",
        "termsOfService": "",
        "hide_top_bar": True
    }
    Swagger(APP, template_file='swagger.yml')
    APP.run("0.0.0.0", debug=True)
