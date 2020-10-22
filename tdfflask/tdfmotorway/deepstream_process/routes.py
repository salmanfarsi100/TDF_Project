from flask import render_template, request, Blueprint, redirect, url_for
from tdfmotorway import db
from tdfmotorway.models import Camera
from tdfmotorway.deepstream_records.routes import deepstreamrecordsbp
import os
import subprocess
from multiprocessing import Process

deepstreambp = Blueprint("deepstreambp", __name__, static_folder='static', template_folder='templates')

@deepstreambp.route("/", methods=['GET', 'POST'])
def deepstream_process():
	if request.form:
		if request.form["submit_button"] == "Add Vehicle Record":
			optimal_frame = Camera(tracking_id=request.form.get("tracking_id"))
			optimal_frame.frame_number = request.form.get("frame_number")
			optimal_frame.lane = request.form.get("lane")
			optimal_frame.datetime = request.form.get("datetime")
			optimal_frame.image_path = request.form.get("image_path")
			print(optimal_frame)
			db.session.add(optimal_frame)
			db.session.commit()
		if request.form["submit_button"] == "Start Application":
			# ~ os.system("unset DISPLAY")
			# ~ subprocess.call(['lxterminal -e python3 ofe_new.py file:///home/jetsonuser/Videos/vid301_cropped.264 frames'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask', shell=True)
			# ~ subprocess.call(['lxterminal -e python3 ofe_new.py file:///home/jetsonuser/Videos/vid301_cropped.264 frames'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/ofe', shell=True)
			
			subprocess.call(['lxterminal -e sudo python3 process.py'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes', shell=True)
			
			# ~ subprocess.call(['lxterminal -e python3 testspeed.py'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/radar', shell=True)
			# ~ subprocess.run("python3 /opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/radar/testspeed.py & python3 /opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/ofe/ofe_new.py file:///home/jetsonuser/Videos/vid301_cropped.264 frames", shell=True)
			# ~ subprocess.call(['lxterminal -e python3 unset DISPLAY'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/ofe', shell=True)
			# ~ subprocess.Popen('lxterminal; cd /opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/ofe; unset DISPLAY; python3 ofe_new.py file:///home/jetsonuser/Videos/vid301_cropped.264 frames', shell=True)
			# ~ os.system("gnome-terminal")
			# ~ process = Popen(['gnome-terminal', '/tmp/filename.swf', '-d'], stdout=PIPE, stderr=PIPE)
			# ~ stdout, stderr = process.communicate()
			# ~ os.system("sudo python3 /opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/ofe_new.py file:///home/jetsonuser/Videos/vid301_cropped.264 frames")		
			# ~ os.system("cd /opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/radar")		
			# ~ os.system("python3 ")				# recorded video h264 stream
			# ~ os.system("python3 testspeed.py")
			return redirect(url_for('deepstreamrecordsbp.deepstream_records'))
		if request.form["submit_button"] == "Stop Application":
			os.system("exit()")
			return redirect(url_for('deepstreamrecordsbp.deepstream_records'))
		if request.form["submit_button"] == "View OFE Records":
			return redirect(url_for('deepstreamrecordsbp.deepstream_records'))
		if request.form["submit_button"] == "Home":
			return redirect(url_for('home'))
	return render_template("deepstream.html")
