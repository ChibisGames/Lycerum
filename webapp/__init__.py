from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAXIMUM_QUANTITY = 10
MAX_CONTENT_LENGTH = 32 * 1024 * 1024

app = Flask(__name__)
app.secret_key = 'LycerumTheBestSchoolForumEVER'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.sqlite3'
# app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

db = SQLAlchemy(app)
manager = LoginManager(app)

from webapp import models, routs

with app.app_context():
    db.create_all()
    db.session.commit()
