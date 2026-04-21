# Tentative nutrition model, feel free to change, add, or remove anything

from datetime import datetime, timezone

from models import db

class Nutrition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(80), nullable=False)
    user_notes = db.Column(db.String(1000))  # Stores any details the user wants to store about the food
    serving_size = db.Column(db.Integer)
    num_calories = db.Column(db.Integer)
    grams_of_protein = db.Column(db.Integer)
    grams_of_carb = db.Column(db.Integer)
    grams_of_fat = db.Column(db.Integer)
    additional_details = db.Column(db.String(1000))

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)