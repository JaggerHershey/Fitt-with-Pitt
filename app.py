from flask import Flask, flash, render_template, redirect, url_for, request
from models import db
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models.user_model import User
from models.nutrition_model import Nutrition
from models.activity_model import Activity
from models.goal_model import Goal, ActivityGoal, NutritionGoal, WeightGoal
from models.bodyweight_model import BodyWeight
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime, timedelta
import requests
import os
import json


def calculate_progress(current, goal):
    if not goal or goal <= 0:
        return 0
    return min(100, int((current / goal) * 100))


def get_or_create_activity_goal(user_id):
    activity_goal = ActivityGoal.query.filter_by(user_id=user_id).first()
    if activity_goal:
        return activity_goal

    activity_goal = ActivityGoal(
        user_id=user_id,
        target_value=4,
        weekly_workouts=4
    )
    db.session.add(activity_goal)
    db.session.commit()
    return activity_goal


def get_dashboard_metrics(user_id):
    today = datetime.now().date()
    current_week_start = today - timedelta(days=today.weekday())

    nutrition_entries = Nutrition.query.filter_by(user_id=user_id).all()
    activity_entries = Activity.query.filter_by(user_id=user_id).all()
    activity_goal = get_or_create_activity_goal(user_id)
    nutrition_goal = NutritionGoal.query.filter_by(user_id=user_id).first()
    weight_goal = WeightGoal.query.filter_by(user_id=user_id).first()

    calories_today = sum(
        entry.num_calories or 0
        for entry in nutrition_entries
        if entry.created_at and entry.created_at.date() == today
    )
    protein_today = sum(
        entry.grams_of_protein or 0
        for entry in nutrition_entries
        if entry.created_at and entry.created_at.date() == today
    )
    carbs_today = sum(
        entry.grams_of_carb or 0
        for entry in nutrition_entries
        if entry.created_at and entry.created_at.date() == today
    )
    fat_today = sum(
        entry.grams_of_fat or 0
        for entry in nutrition_entries
        if entry.created_at and entry.created_at.date() == today
    )
    workouts_this_week = sum(
        1
        for entry in activity_entries
        if entry.created_at and entry.created_at.date() >= current_week_start
    )

    calorie_goal = nutrition_goal.daily_cal if nutrition_goal and nutrition_goal.daily_cal else None
    protein_goal = nutrition_goal.daily_protein if nutrition_goal and nutrition_goal.daily_protein else None
    workout_goal = activity_goal.weekly_workouts if activity_goal and activity_goal.weekly_workouts else None

    latest_weight = BodyWeight.query.filter_by(user_id=user_id).order_by(BodyWeight.logged_at.asc()).all()
    latest_weight_entry = latest_weight[-1] if latest_weight else None

    weight_goal_progress = 0
    weight_goal_remaining = None
    if weight_goal and latest_weight_entry and weight_goal.current_weight and weight_goal.target_weight:
        starting_delta = abs(weight_goal.target_weight - weight_goal.current_weight)
        current_delta = abs(weight_goal.target_weight - latest_weight_entry.weight)
        if starting_delta == 0:
            weight_goal_progress = 100
        else:
            weight_goal_progress = min(100, int(((starting_delta - current_delta) / starting_delta) * 100))
        weight_goal_remaining = round(current_delta, 1)

    return {
        'today': today,
        'calories_today': calories_today,
        'protein_today': protein_today,
        'carbs_today': carbs_today,
        'fat_today': fat_today,
        'workouts_this_week': workouts_this_week,
        'nutrition_goal': nutrition_goal,
        'activity_goal': activity_goal,
        'weight_goal': weight_goal,
        'calorie_goal': calorie_goal,
        'protein_goal': protein_goal,
        'workout_goal': workout_goal,
        'calorie_progress': calculate_progress(calories_today, calorie_goal),
        'protein_progress': calculate_progress(protein_today, protein_goal),
        'workout_progress': calculate_progress(workouts_this_week, workout_goal),
        'latest_weight_entry': latest_weight_entry,
        'weight_goal_progress': weight_goal_progress,
        'weight_goal_remaining': weight_goal_remaining,
    }

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

mail_api_key = os.getenv("MAIL_API_KEY")
auth_api_key = os.getenv("AUTH_API_KEY")

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
    metrics = get_dashboard_metrics(current_user.id)
    nutrition_entries = Nutrition.query.filter_by(user_id=current_user.id).order_by(Nutrition.created_at.desc()).limit(4).all()
    activity_entries = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).limit(4).all()
    weight_entries = BodyWeight.query.filter_by(user_id=current_user.id).order_by(BodyWeight.logged_at.asc()).all()
    weight_chart_data = [
        {'date': e.logged_at.strftime('%Y-%m-%d'), 'weight': e.weight, 'unit': e.unit}
        for e in weight_entries
    ]
    latest_weight = weight_entries[-1] if weight_entries else None
    return render_template('dashboard.html',
        nutrition_entries=nutrition_entries,
        activity_entries=activity_entries,
        calories_today=metrics['calories_today'],
        protein_today=metrics['protein_today'],
        workouts_this_week=metrics['workouts_this_week'],
        calorie_goal=metrics['calorie_goal'],
        protein_goal=metrics['protein_goal'],
        workout_goal=metrics['workout_goal'],
        calorie_progress=metrics['calorie_progress'],
        protein_progress=metrics['protein_progress'],
        workout_progress=metrics['workout_progress'],
        weight_goal=metrics['weight_goal'],
        weight_goal_progress=metrics['weight_goal_progress'],
        weight_goal_remaining=metrics['weight_goal_remaining'],
        weight_chart_data=weight_chart_data,
        latest_weight=latest_weight,
    )

@app.route('/log_weight', methods=['POST'])
@login_required
def log_weight():
    weight = request.form.get('weight', type=float)
    unit = request.form.get('unit', 'lbs')
    notes = request.form.get('notes') or None
    if weight:
        db.session.add(BodyWeight(weight=weight, unit=unit, notes=notes, user_id=current_user.id))
        db.session.commit()
        flash('Weight logged!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/nutrition', methods=['GET', 'POST'])
@login_required
def nutrition():
    if request.method == 'POST':
        food_name = request.form.get("food_name")
        serving_size = request.form.get('serving_size') or None
        num_calories = request.form.get('num_calories') or None
        grams_of_protein = request.form.get('grams_of_protein') or None
        grams_of_carb = request.form.get('grams_of_carb') or None
        grams_of_fat = request.form.get('grams_of_fat') or None
        user_notes = request.form.get('user_notes') or None

        new_meal = Nutrition(
            food_name=food_name,
            serving_size=serving_size,
            num_calories=num_calories,
            grams_of_protein=grams_of_protein,
            grams_of_carb=grams_of_carb,
            grams_of_fat=grams_of_fat,
            user_notes=user_notes,
            user_id=current_user.id
        )
        db.session.add(new_meal)
        db.session.commit()

        return redirect(url_for('nutrition'))
    else:
        metrics = get_dashboard_metrics(current_user.id)
        entries = Nutrition.query.filter_by(user_id=current_user.id).order_by(Nutrition.created_at.desc()).all()
        total_calories = metrics['calories_today']
        total_protein = metrics['protein_today']
        total_carbs = metrics['carbs_today']
        total_fat = metrics['fat_today']
        nutrition_goal = metrics['nutrition_goal']
        return render_template('nutrition.html', entries=entries,
            total_calories=int(total_calories), total_protein=int(total_protein),
            total_carbs=int(total_carbs), total_fat=int(total_fat),
            nutrition_goal=nutrition_goal,
            calorie_goal=metrics['calorie_goal'],
            protein_goal=metrics['protein_goal'],
            calorie_progress=metrics['calorie_progress'],
            protein_progress=metrics['protein_progress'],
            carb_goal=nutrition_goal.daily_carbs if nutrition_goal and nutrition_goal.daily_carbs else None,
            fat_goal=nutrition_goal.daily_fats if nutrition_goal and nutrition_goal.daily_fats else None,
            carb_progress=calculate_progress(total_carbs, nutrition_goal.daily_carbs if nutrition_goal else None),
            fat_progress=calculate_progress(total_fat, nutrition_goal.daily_fats if nutrition_goal else None))
    
@app.route('/delete_nutrition/<int:entry_id>', methods=['POST'])
@login_required
def delete_nutrition(entry_id):
    entry = Nutrition.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('nutrition'))
    db.session.delete(entry)
    db.session.commit()
    flash('Meal deleted.', 'success')
    return redirect(url_for('nutrition'))

@app.route('/activity', methods=['GET', 'POST'])
@login_required
def activity():
    if request.method == 'POST':
        workout_name = request.form.get('workout_name')
        muscle_group = request.form.get('muscle_group')
        num_set = int(request.form.get('num_set')) if request.form.get('num_set') else None
        num_reps = int(request.form.get('num_reps')) if request.form.get('num_reps') else None
        workout_weight = int(request.form.get('workout_weight')) if request.form.get('workout_weight') else None
        calories_burned = int(request.form.get('calories_burned')) if request.form.get('calories_burned') else None
        user_notes = request.form.get('user_notes')

        new_activity = Activity(
            workout_name=workout_name,
            muscle_group=muscle_group,
            workout_weight=workout_weight,
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
        metrics = get_dashboard_metrics(current_user.id)
        # Get user's activities only
        entries = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).all()
        
        # Calculate weekly stats
        today = datetime.now()
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
        activity_goal = metrics['activity_goal']
        weekly_goal = activity_goal.weekly_workouts if activity_goal else 4
        
        # Calculate ring progress
        ring_progress = min(100, int((weekly_count / weekly_goal) * 100)) if weekly_goal > 0 else 0
        
        chart_data = [
            {
                'date': e.created_at.strftime('%Y-%m-%d') if e.created_at else None,
                'name': e.workout_name,
                'weight': e.workout_weight,
                'sets': e.num_set,
                'reps': e.num_reps,
                'calories': e.calories_burned,
            }
            for e in reversed(entries)
        ]

        return render_template('activity.html',
            entries=entries,
            chart_data=chart_data,
            weekly_count=weekly_count,
            weekly_calories=weekly_calories,
            weekly_sets=weekly_sets,
            weekly_reps=weekly_reps,
            weekly_goal=weekly_goal,
            ring_progress=ring_progress,
            activity_goal=activity_goal
        )


@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    activity_goal = get_or_create_activity_goal(current_user.id)
    nutrition_goal = NutritionGoal.query.filter_by(user_id=current_user.id).first()
    weight_goal = WeightGoal.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        goal_type = request.form.get('goal_type')
        weekly_workouts = request.form.get('weekly_workouts', type=int)
        daily_cal = request.form.get('daily_cal', type=int)
        daily_protein = request.form.get('daily_protein', type=int)
        daily_carbs = request.form.get('daily_carbs', type=int)
        daily_fats = request.form.get('daily_fats', type=int)
        current_weight = request.form.get('current_weight', type=float)
        target_weight = request.form.get('target_weight', type=float)

        if goal_type == 'activity' and weekly_workouts and weekly_workouts > 0:
            activity_goal.weekly_workouts = weekly_workouts
            activity_goal.target_value = weekly_workouts

        if goal_type == 'nutrition' and any(value is not None for value in [daily_cal, daily_protein, daily_carbs, daily_fats]):
            if not nutrition_goal:
                nutrition_goal = NutritionGoal(user_id=current_user.id, target_value=0)
                db.session.add(nutrition_goal)
            nutrition_goal.daily_cal = daily_cal
            nutrition_goal.daily_protein = daily_protein
            nutrition_goal.daily_carbs = daily_carbs
            nutrition_goal.daily_fats = daily_fats
            nutrition_goal.target_value = daily_cal or daily_protein or daily_carbs or daily_fats or 0

        if goal_type == 'weight' and current_weight is not None and target_weight is not None:
            if not weight_goal:
                weight_goal = WeightGoal(user_id=current_user.id, target_value=target_weight)
                db.session.add(weight_goal)
            weight_goal.current_weight = current_weight
            weight_goal.target_weight = target_weight
            weight_goal.target_value = target_weight

        db.session.commit()
        flash(f'{goal_type.capitalize() if goal_type else "Goal"} updated successfully.', 'success')
        return redirect(url_for('goals'))

    metrics = get_dashboard_metrics(current_user.id)
    return render_template(
        'goals.html',
        activity_goal=activity_goal,
        nutrition_goal=nutrition_goal,
        weight_goal=weight_goal,
        calories_today=metrics['calories_today'],
        protein_today=metrics['protein_today'],
        carbs_today=metrics['carbs_today'],
        fat_today=metrics['fat_today'],
        workouts_this_week=metrics['workouts_this_week'],
        calorie_progress=metrics['calorie_progress'],
        protein_progress=metrics['protein_progress'],
        workout_progress=metrics['workout_progress'],
        weight_goal_progress=metrics['weight_goal_progress'],
        weight_goal_remaining=metrics['weight_goal_remaining'],
        latest_weight=metrics['latest_weight_entry'],
    )

@app.route('/set_workout_goal', methods=['POST'])
@login_required
def set_workout_goal():
    weekly_workouts = request.form.get('weekly_workouts', type=int)
    
    if weekly_workouts and weekly_workouts > 0:
        existing_goal = get_or_create_activity_goal(current_user.id)
        existing_goal.weekly_workouts = weekly_workouts
        existing_goal.target_value = weekly_workouts
        
        db.session.commit()
        flash(f"Weekly workout goal set to {weekly_workouts}!", "success")
    
    return redirect(url_for('goals'))

@app.route('/delete_activity/<int:entry_id>', methods=['POST'])
@login_required
def delete_activity(entry_id):
    entry = Activity.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('activity'))
    db.session.delete(entry)
    db.session.commit()
    flash('Workout deleted.', 'success')
    return redirect(url_for('activity'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User does not exist, please make an account.", "info")
            return render_template('login.html', error='Invalid credentials')
        if user.check_password(password=password):
            if not user.email_verified:
                flash('Please verify your email before logging in.', 'warning')
                return render_template('login.html')
            login_user(user, remember=True)
            next = request.args.get('next')
            if next:
                return redirect(next)
            return redirect(url_for('dashboard'))
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

        # Check if invalid email using mailboxlayer api
        if not check_email(email=email):
            flash("Email is invalid. Please choose another.", "info")
            return redirect(url_for('register'))

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

            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(email, salt='email-verify')
            verify_url = url_for('verify_email', token=token, _external=True)
            send_verification_email(email, username, verify_url)

        flash('Account created! Check your email to verify your account before logging in.', 'info')
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

def check_email(email):
    url = f'https://apilayer.net/api/check?access_key={mail_api_key}&email={email}'
    response = requests.get(url)
    data = response.json()
    return (
        data.get('smtp_check') and
        data.get('mx_found') and
        not data.get('disposable') and
        float(data.get('score', 0)) > 0.6
    )

def send_verification_email(user_email, username, verify_url):
    headers = {
        'accept': 'application/json',
        'api-key': auth_api_key,
        'content-type': 'application/json'
    }
    body = {
        'sender': {'name': 'FittWithPitt', 'email': 'jagger.hershey@hotmail.com'},
        'to': [{'email': user_email, 'name': username}],
        'subject': 'Confirm Your FittWithPitt Account',
        'htmlContent': (
            f'<html><body>'
            f'<h2>Welcome to FittWithPitt, {username}!</h2>'
            f'<p>Click the link below to verify your email address. This link expires in 1 hour.</p>'
            f'<a href="{verify_url}">Verify my account</a>'
            f'</body></html>'
        )
    }
    response = requests.post('https://api.brevo.com/v3/smtp/email', headers=headers, json=body)
    if not response.ok:
        app.logger.error(f'Brevo error {response.status_code}: {response.text}')
    return response.ok

@app.route('/verify_email/<token>')
def verify_email(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-verify', max_age=3600)
    except SignatureExpired:
        flash('Verification link has expired. Please register again.', 'danger')
        # Uncommit user from db due to needing to reregister
        return redirect(url_for('register'))
    except BadSignature:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('register'))

    user = User.query.filter_by(email=email).first()
    if user:
        user.email_verified = True
        db.session.commit()
        flash('Email verified! You can now log in.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out of your account", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
