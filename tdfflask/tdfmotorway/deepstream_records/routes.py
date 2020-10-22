from flask import render_template, request, Blueprint, redirect, url_for
from tdfmotorway import db
from tdfmotorway.models import Camera
import os

deepstreamrecordsbp = Blueprint("deepstreamrecordsbp", __name__, static_folder='static', template_folder='templates')

@deepstreamrecordsbp.route("/", methods=['GET', 'POST'])
def deepstream_records():
	if request.form:
		if request.form["submit_button"] == "Home":
			return redirect(url_for('home'))
		if request.form["submit_button"] == "Delete Records":
			Camera.query.delete()
			db.session.commit()
			return redirect(url_for('home'))
	optimal_frames = Camera.query.all()
	return render_template("deepstream_records.html", optimal_frames = optimal_frames)
