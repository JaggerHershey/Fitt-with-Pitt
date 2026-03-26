# Tentative nutrition model, feel free to change, add, or remove anything

from models import db

class Nutrition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(80), unique=True)
    user_notes = db.Column(db.String(1000))  # Stores any details the user wants to store about the food
    serving_size = db.Column(db.Integer)
    num_calories = db.Column(db.Integer)
    grams_of_protein = db.Column(db.Integer)
    additional_details = db.Column(db.String(1000))