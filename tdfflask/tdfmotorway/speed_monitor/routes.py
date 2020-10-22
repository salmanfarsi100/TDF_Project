from flask import render_template, request, Blueprint, jsonify, redirect, url_for

path = "tdfmotorway/config.ini"
from tdfmotorway import db
from tdfmotorway.models import Radar
import os

speedbp = Blueprint("speedbp", __name__, static_folder='static', template_folder='templates')

@speedbp.route("/", methods=['GET', 'POST'])
def get_speed():
    content = request.json
    speed = content['speed']
    _range = content['range']
    datetime = content['date_time']
    print(content)
    speed_data = Radar(speed = speed)
    speed_data.datetime = datetime
    speed_data.vehiclerange = _range
    db.session.add(speed_data)
    db.session.commit()
    
    return jsonify(202)
