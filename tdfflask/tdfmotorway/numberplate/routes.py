from flask import render_template, request, Blueprint
from tdfmotorway.models import Radar

numberplate = Blueprint('numberplate', __name__)


@numberplate.route("/")
@numberplate.route("/home")
def home():
    #page = request.args.get('page', 1, type=int)
    #posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return "home"#render_template('home.html', posts=posts)


@numberplate.route("/about")
def about():
    return "hello about"#render_template('about.html', title='About')
