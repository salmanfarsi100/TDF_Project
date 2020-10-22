from flask import render_template, request, Blueprint, redirect, url_for
from tdfmotorway import db
from tdfmotorway.models import Camera
from tdfmotorway.deepstream_records.routes import deepstreamrecordsbp
import os
import subprocess
from multiprocessing import Process

speedprocessbp = Blueprint("speedprocessbp", __name__, static_folder='static', template_folder='templates')

@speedprocessbp.route("/", methods=['GET', 'POST'])
def speed_process():
	if request.form:
		if request.form["submit_button"] == "Add Radar Record":
			speed_data = Radar(speed = request.form.get("speed"))
			speed_data.vehiclerange = request.form.get("vehiclerange")
			speed_data.datetime = request.form.get("datetime")
			print(speed_data)
			db.session.add(speed_data)
			db.session.commit()
		if request.form["submit_button"] == "Start Application":
			# ~ subprocess.call(['lxterminal -e python3 testspeed.py'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/radar', shell=True)
			subprocess.call(['lxterminal -e sudo python3 process.py'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes', shell=True)
			return redirect(url_for('speedrecordsbp.speed_records'))
		if request.form["submit_button"] == "Stop Application":
			os.system("exit()")
			return redirect(url_for('speedrecordsbp.speed_records'))
		if request.form["submit_button"] == "View Speed Records":
			return redirect(url_for('speedrecordsbp.speed_records'))
		if request.form["submit_button"] == "Home":
			return redirect(url_for('home'))
	return render_template("speed_process.html")
