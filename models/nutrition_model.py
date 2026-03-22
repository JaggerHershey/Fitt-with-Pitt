from models import db

class Nutrition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
