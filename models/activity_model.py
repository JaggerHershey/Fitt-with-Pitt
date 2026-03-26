from models import db

class Activity(db.Model):
    entry_id = db.Column(db.Integer, primary_key=True)
