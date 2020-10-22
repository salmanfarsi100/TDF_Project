from flask import render_template, request, Blueprint, redirect, url_for
from tdfmotorway import db
from tdfmotorway.models import Radar
import os

speedrecordsbp = Blueprint("speedrecordsbp", __name__, static_folder='static', template_folder='templates')

@speedrecordsbp.route("/", methods=['GET', 'POST'])
def speed_records():
	if request.form:
		if request.form["submit_button"] == "Home":
			return redirect(url_for('home'))
		if request.form["submit_button"] == "Delete Records":
			Radar.query.delete()
			db.session.commit()
			return redirect(url_for('home'))
	radar_values = Radar.query.all()
	return render_template("speed_records.html", radar_values = radar_values)
