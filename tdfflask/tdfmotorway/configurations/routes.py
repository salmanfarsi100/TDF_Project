from flask import render_template, request, Blueprint, redirect, url_for

configbp = Blueprint("configbp", __name__, static_folder='static', template_folder='templates')

@configbp.route("/", methods=['GET', 'POST'])
def config():
	if request.form:
		if request.form["submit_button"] == "Submit":

			with open('tdfmotorway/road.ini', 'r') as file:   # config file of the frame extractor application
				data = file.readlines()
			data[2] = str('x11 ') + str(request.form.get("x11")) + str('\n')
			data[4] = str('x12 ') + str(request.form.get("x12")) + str('\n')
			data[6] = str('x13 ') + str(request.form.get("x13")) + str('\n')
			data[8] = str('x14 ') + str(request.form.get("x14")) + str('\n')
			data[10] = str('x21 ') + str(request.form.get("x21")) + str('\n')
			data[12] = str('x22 ') + str(request.form.get("x22")) + str('\n')
			data[14] = str('x23 ') + str(request.form.get("x23")) + str('\n')
			data[16] = str('x24 ') + str(request.form.get("x24")) + str('\n')
			data[18] = str('y11 ') + str(request.form.get("y11")) + str('\n')
			data[20] = str('y22 ') + str(request.form.get("y22")) + str('\n')
			data[24] = str('y1 ') + str(request.form.get("y1")) + str('\n')
			data[26] = str('y2 ') + str(request.form.get("y2"))
			with open('tdfmotorway/road.ini', 'w') as file:
				file.writelines(data)
				
			with open('tdfmotorway/camera.ini', 'r') as file:   # login credentials of the camera
				data = file.readlines()
			data[2] = str('username ') + str(request.form.get("username")) + str('\n')
			data[4] = str('password ') + str(request.form.get("password")) + str('\n')
			data[6] = str('ipaddress ') + str(request.form.get("ipaddress"))
			with open('tdfmotorway/camera.ini', 'w') as file:
				file.writelines(data)

			with open('tdfmotorway/config.ini', 'r') as file:   # config file of the radar
				data = file.readlines()
			data[2] = str('BRate = ') + str(request.form.get("baudrate")) + str('\n')
			data[4] = str('SampleFreq = ') + str(request.form.get("samplefrequency")) + str('\n')
			data[6] = str('SpeedUnit = ') + str(request.form.get("speedunit")) + str('\n')
			data[8] = str('Direction = ') + str(request.form.get("direction")) + str('\n')
			data[10] = str('FFTMode = ') + str(request.form.get("fftmode")) + str('\n')
			data[12] = str('JSMode = ') + str(request.form.get("jsonmode")) + str('\n')
			data[14] = str('RAWData = ') + str(request.form.get("rawdata")) + str('\n')
			data[16] = str('NReports = ') + str(request.form.get("numberreport")) + str('\n')
			data[18] = str('RReports = ') + str(request.form.get("rangereport")) + str('\n')
			data[20] = str('SReports = ') + str(request.form.get("speedreport")) + str('\n')
			data[22] = str('uReports = ') + str(request.form.get("reportunit")) + str('\n')
			with open('tdfmotorway/config.ini', 'w') as file:
				file.writelines(data)

			return redirect(url_for('home'))

		if request.form["submit_button"] == "Use Defaults":
			return redirect(url_for('home'))

	return render_template("config.html")