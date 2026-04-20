from models import db
from datetime import datetime, timezone

class BodyWeight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(3), nullable=False, default='lbs')
    notes = db.Column(db.String(500))
    logged_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
