from flask import Flask, request, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy

from tdfmotorway.config import Config


db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from tdfmotorway.numberplate.routes import numberplate
    from tdfmotorway.configurations.routes import configbp
    from tdfmotorway.deepstream_listen.routes import deepstreamlistenbp
    from tdfmotorway.deepstream_monitor.routes import camerabp
    from tdfmotorway.deepstream_process.routes import deepstreambp
    from tdfmotorway.deepstream_records.routes import deepstreamrecordsbp
    from tdfmotorway.speed_listen.routes import speedlistenbp
    from tdfmotorway.speed_monitor.routes import speedbp
    from tdfmotorway.speed_process.routes import speedprocessbp
    from tdfmotorway.speed_records.routes import speedrecordsbp

    @app.route("/", methods=["GET", "POST"])
    def home():
        if request.form:
            if request.form["submit_button"] == "Go to Configurations":
                return redirect(url_for('configbp.config'))
            if request.form["submit_button"] == "Go to Camera API":
                return redirect(url_for('deepstreambp.deepstream_process'))
            if request.form["submit_button"] == "Go to Camera Records":
                return redirect(url_for('deepstreamrecordsbp.deepstream_records'))
            if request.form["submit_button"] == "Go to Radar API":
                return redirect(url_for('speedprocessbp.speed_process'))
            if request.form["submit_button"] == "Go to Radar Records":
                return redirect(url_for('speedrecordsbp.speed_records'))
        return render_template("home.html")

    app.register_blueprint(numberplate)
    app.register_blueprint(configbp, url_prefix="/config")
    app.register_blueprint(deepstreamlistenbp, url_prefix="/deepstream_listen")
    app.register_blueprint(camerabp, url_prefix="/camera")
    app.register_blueprint(deepstreambp, url_prefix="/deepstream_process")
    app.register_blueprint(deepstreamrecordsbp, url_prefix="/deepstream_records")
    app.register_blueprint(speedlistenbp, url_prefix="/speed_listen")
    app.register_blueprint(speedbp, url_prefix="/speed")
    app.register_blueprint(speedprocessbp, url_prefix="/speed_process")
    app.register_blueprint(speedrecordsbp, url_prefix="/speed_records")

    return app
