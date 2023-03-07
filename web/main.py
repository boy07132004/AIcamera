import os
import cv_part
from flasgger import Swagger
from flask import Flask, render_template, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from person_tracking import PERSON


FUNCTION = {"person_tracking": False}
APP = Flask(__name__)
LOGIN_MANAGER = LoginManager(APP)


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@LOGIN_MANAGER.user_loader
def user_loader(name):
    if name not in users:
        return jsonify(status="User not found or password error."), 403

    user = User(name)
    return user


@APP.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":
        parameter = request.get_json()
        userID = parameter.get("user_id")
        passwd = parameter.get("password")

        if passwd and users.get(userID) == passwd:
            user = User(userID)
            login_user(user)
            return jsonify(status=f"Welcome back {user.id}.")
        else:
            return jsonify(errors="user or password error"), 400

    return render_template('login_page.html')


@APP.route('/logout')
def logout():
    logout_user()
    return jsonify(status="Logout success.")


@APP.route('/get_image')
def get_image():
    jpeg = cv_part.get_current_image(True)
    if jpeg is not None:

        return Response(jpeg.tobytes(), content_type='image/jpeg')

    return jsonify(status="Can't capture image."), 500


@APP.route('/get_info', methods=["GET"])
@login_required
def get_info():
    info = {
        "camera": {
            "width": os.environ("CAMERA_WIDTH"),
            "height": os.environ("CAMERA_HEIGHT")
        }
    }
    return jsonify(info)


@APP.route('/service/<service>', methods=["GET", "POST"])
@login_required
def manage_service(service):
    if service not in FUNCTION:
        return jsonify(errors="Service not found")

    if request.method == "GET":
        status = "Running"
        return jsonify(service=service, status=status)

    elif request.method == "POST":
        command = request.json.get("command")
        status = f"{command} {service}....."

        if command == "start":
            status = command
            """
            TO-DO
            """
        elif command == "stop":
            status = command
            """
            TO-DO
            """
        else:
            return jsonify(service=service, errors=f"Invalid command: {command}")

        status = f"{service} {command} finished."
        return jsonify(service=service, status=status)


if __name__ == "__main__":
    APP.config['SWAGGER'] = {
        "title": "AI Camera",
        "description": "My API",
        "version": "1.0.0",
        "termsOfService": "",
        "hide_top_bar": True,
        "ui_params": {"tagsSorter": "alpha"}
    }

    Swagger(APP, template_file='swagger.yml')
    APP.register_blueprint(PERSON)
    APP.config['SECRET_KEY'] = 'my_secret_key'

    LOGIN_MANAGER.login_view = 'login'
    LOGIN_MANAGER.session_protection = 'strong'
    users = {"user": '0000'}
    APP.run("0.0.0.0", debug=True)
