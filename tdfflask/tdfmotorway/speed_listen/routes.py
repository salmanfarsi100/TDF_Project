from flask import render_template, request, Blueprint, jsonify, redirect, url_for
from tdfmotorway import db
from tdfmotorway.models import Radar
from datetime import date
import json

speedlistenbp = Blueprint("speedlistenbp", __name__, static_folder='static', template_folder='templates')

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d

@speedlistenbp.route("/<key_time>", methods=['GET', 'POST'])
def listen_speed(key_time):
	yymmdd = str(date.today())
	date_today = yymmdd[8:10] + '/' + yymmdd[5:7] + '/' + yymmdd[0:4] 
	key_datetime = str(date_today) + ' ' + str(key_time)
	print(key_datetime)
	result = Radar.query.filter(Radar.datetime >= key_datetime)
	d = 'no entries found' 
	if result:
		new_d = []
		for i in result:
			new_d.append(row2dict(i))
		d = new_d
		
	print(json.dumps(d))
	return json.dumps(d)
