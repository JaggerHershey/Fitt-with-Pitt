from models import db
from datetime import datetime, timezone

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_name = db.Column(db.String(80), nullable=False)
    user_notes = db.Column(db.String(1000))
    num_set = db.Column(db.Integer)
    num_reps = db.Column(db.Integer)
    workout_weight = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    muscle_group = db.Column(db.String(50), nullable=False)
    
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)