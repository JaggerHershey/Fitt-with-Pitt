from models import db

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
