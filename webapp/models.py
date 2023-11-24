from datetime import datetime

from flask_login import UserMixin

from webapp import db, manager


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    user_login = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    admin = db.Column(db.Integer, default=0)

    fullname = db.Column(db.String, nullable=False)
    school_class = db.Column(db.String, nullable=False)
    birth_date = db.Column(db.String, nullable=False)
    sum_of_record = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<User %r>' % self.id


class Record(db.Model):
    __tablename__ = 'record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    users = db.relationship('User',
                            backref=db.backref('user', lazy='joined'),
                            lazy=True)

    title = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String, nullable=False)
    text = db.Column(db.Text, nullable=False)
    sum_of_files = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Record %r>' % self.id


class Files(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('record.id'), nullable=False)
    records = db.relationship('Record',
                              backref=db.backref('record', lazy='joined'),
                              lazy=True)
    filename = db.Column(db.String, nullable=False)
    path_to_explorer = db.Column(db.String, nullable=False)
    format = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Files %r>' % self.id


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

