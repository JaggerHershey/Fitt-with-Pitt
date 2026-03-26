from models import db
class Goal(db.Model):
    __tablename__ = 'goal'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable = False)
    target_value = db.Column(db.Float, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    __mapper_args__ = {
        'polymorphic_identity': 'goal',
        'polymorphic_on': type
    }

class WeightGoal(Goal):
    current_weight = db.Column(db.Float)
    target_weight = db.Column(db.Float)
    
    __mapper_args__ = {
        'polymorphic_identity': 'weight_goal'
    }

class NutritionGoal(Goal):
    daily_cal = db.Column(db.Integer)
    # all in grams v v
    daily_protein = db.Column(db.Integer)
    daily_carbs = db.Column(db.Integer)
    daily_fats = db.Column(db.Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'nutrition'
    }

class ActivityGoal(Goal):
    weekly_workouts = db.Column(db.Integer) # target num of workouts per week

    __mapper_args__ = {
        'polymorphic_identity': 'activity'
    }

