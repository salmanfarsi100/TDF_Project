from flask import render_template, request, Blueprint, jsonify, redirect, url_for
from tdfmotorway import db
from tdfmotorway.models import Camera
import os

camerabp = Blueprint("camerabp", __name__, static_folder='static', template_folder='templates')

@camerabp.route("/", methods=['GET', 'POST'])
def get_frame():
	content = request.json
	tracking_id = content['tracking_id']
	frame_number = content['frame_number']
	lane = content['lane']
	datetime = content['datetime']
	image_path = content['image_path']
	print(content)
	
	optimal_frame = Camera(tracking_id = tracking_id)
	optimal_frame.frame_number = frame_number
	optimal_frame.lane = lane
	optimal_frame.datetime = datetime
	optimal_frame.image_path = image_path
	db.session.add(optimal_frame)
	db.session.commit()

	return jsonify(202)
	# ~ return jsonify(content)
