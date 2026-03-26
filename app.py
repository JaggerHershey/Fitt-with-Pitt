from flask import Flask, flash, render_template, redirect, url_for, request
from models import db
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models.user_model import User
from models.nutrition_model import Nutrition
from models.activity_model import Activity

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
    return render_template('dashboard.html')

@app.route('/nutrition')
@login_required
def nutrition():
    return render_template('nutrition.html')

@app.route('/activity')
@login_required
def activity():
    return render_template('activity.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Current user already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Otherwise deal with associated request
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        # Potentially add 'remember' checkbox and change login to associated value
        # Current default is remember=True

        # Check user exists
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User does not exist, please make an account.", "info")
            return render_template('login.html', error='Invalid credentials')
        # Check user against database hashed info
        # If authorized, login and redirect to home
        if user.check_password(password=password):
            login_user(user, remember=True)
            # Route to requested page
            next = request.args.get('next')
            if next:
                return redirect(next)
            return redirect(url_for('home'))
        # Otherwise throw login error
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

        # Check if username or email is unique throw error if not
        existing_username = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email is already taken. Please choose another.", "info")
            return redirect(url_for('register'))
        elif existing_username:
            flash("Username is already taken. Please choose another.", "info")
            return redirect(url_for('register'))
        else:
            # Set new user specifications
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            # Save new user in database
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