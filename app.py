from flask import Flask, flash, render_template, redirect, url_for, request
from models import db
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models.user_model import User
from models.nutrition_model import Nutrition
from models.activity_model import Activity
from models.goal_model import Goal, ActivityGoal
from datetime import datetime, timedelta

# Initialize flask application and configure database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

# Initialize database and login manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    nutrition_entries = Nutrition.query.all()[:4]  # Need to order by creation time here too
    activity_entries = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).all()[:4]
    return render_template('dashboard.html', nutrition_entries=nutrition_entries, activity_entries=activity_entries)

@app.route('/nutrition', methods=['GET', 'POST'])
@login_required
def nutrition():
    if request.method == 'POST':
        food_name = request.form.get("food_name")
        serving_size = request.form.get('serving_size')
        num_calories = request.form.get('num_calories')
        grams_of_protein = request.form.get('grams_of_protein')
        grams_of_carb = request.form.get('grams_of_carb')
        grams_of_fat = request.form.get('grams_of_fat')
        user_notes = request.form.get('user_notes')

        new_meal = Nutrition(
            food_name=food_name,
            serving_size=serving_size,
            num_calories=num_calories,
            grams_of_protein=grams_of_protein,
            grams_of_carb=grams_of_carb,
            grams_of_fat=grams_of_fat,
            user_notes=user_notes
        )
        db.session.add(new_meal)
        db.session.commit()

        return redirect(url_for('nutrition'))
    else:
        entries = Nutrition.query.all()
        return render_template('nutrition.html', entries=entries)

@app.route('/activity', methods=['GET', 'POST'])
@login_required
def activity():
    if request.method == 'POST':
        workout_name = request.form.get('workout_name')
        muscle_group = request.form.get('muscle_group')
        num_set = request.form.get('num_set')
        num_reps = request.form.get('num_reps')
        calories_burned = request.form.get('calories_burned')
        user_notes = request.form.get('user_notes')

        new_activity = Activity(
            workout_name=workout_name,
            muscle_group=muscle_group,
            num_set=num_set,
            num_reps=num_reps,
            calories_burned=calories_burned,
            user_notes=user_notes,
            user_id=current_user.id
        )
        db.session.add(new_activity)
        db.session.commit()

        return redirect(url_for('activity'))
    else:
        # Get user's activities only
        entries = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).all()
        
        # Calculate weekly stats
        today = datetime.utcnow()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        weekly_workouts = Activity.query.filter(
            Activity.user_id == current_user.id,
            Activity.created_at >= start_of_week
        ).all()
        
        weekly_count = len(weekly_workouts)
        weekly_calories = sum(w.calories_burned or 0 for w in weekly_workouts)
        weekly_sets = sum(w.num_set or 0 for w in weekly_workouts)
        weekly_reps = sum(w.num_reps or 0 for w in weekly_workouts)
        
        # Get user's workout goal (default to 4)
        activity_goal = ActivityGoal.query.filter_by(user_id=current_user.id).first()
        weekly_goal = activity_goal.weekly_workouts if activity_goal else 4
        
        # Calculate ring progress
        ring_progress = min(100, int((weekly_count / weekly_goal) * 100)) if weekly_goal > 0 else 0
        
        return render_template('activity.html', 
            entries=entries,
            weekly_count=weekly_count,
            weekly_calories=weekly_calories,
            weekly_sets=weekly_sets,
            weekly_reps=weekly_reps,
            weekly_goal=weekly_goal,
            ring_progress=ring_progress
        )

@app.route('/set_workout_goal', methods=['POST'])
@login_required
def set_workout_goal():
    weekly_workouts = request.form.get('weekly_workouts', type=int)
    
    if weekly_workouts and weekly_workouts > 0:
        existing_goal = ActivityGoal.query.filter_by(user_id=current_user.id).first()
        
        if existing_goal:
            existing_goal.weekly_workouts = weekly_workouts
        else:
            new_goal = ActivityGoal(
                user_id=current_user.id,
                target_value=weekly_workouts,
                weekly_workouts=weekly_workouts
            )
            db.session.add(new_goal)
        
        db.session.commit()
        flash(f"Weekly workout goal set to {weekly_workouts}!", "success")
    
    return redirect(url_for('activity'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User does not exist, please make an account.", "info")
            return render_template('login.html', error='Invalid credentials')
        if user.check_password(password=password):
            login_user(user, remember=True)
            next = request.args.get('next')
            if next:
                return redirect(next)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_username = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email is already taken. Please choose another.", "info")
            return redirect(url_for('register'))
        elif existing_username:
            flash("Username is already taken. Please choose another.", "info")
            return redirect(url_for('register'))
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
        
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out of your account", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)