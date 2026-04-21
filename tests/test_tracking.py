from models.activity_model import Activity
from models.bodyweight_model import BodyWeight
from models.goal_model import ActivityGoal, NutritionGoal, WeightGoal
from models.nutrition_model import Nutrition
from models import db


def login_default_user(create_user, login_user):
    create_user(username="member", email="member@example.com", password="Password123!")
    return login_user("member", "Password123!")


def test_logging_nutrition_updates_daily_summary(app, client, create_user, login_user):
    login_default_user(create_user, login_user)

    client.post(
        "/nutrition",
        data={
            "food_name": "Greek Yogurt",
            "serving_size": 170,
            "num_calories": 150,
            "grams_of_protein": 15,
            "grams_of_carb": 8,
            "grams_of_fat": 4,
            "user_notes": "Post workout snack",
        },
        follow_redirects=True,
    )

    response = client.get("/nutrition")
    body = response.get_data(as_text=True)

    assert "Greek Yogurt" in body
    assert "150" in body
    assert "15" in body

    with app.app_context():
        entry = Nutrition.query.one()
        assert entry.food_name == "Greek Yogurt"
        assert entry.num_calories == 150
        assert entry.grams_of_protein == 15


def test_logging_activity_updates_weekly_views(app, client, create_user, login_user):
    login_default_user(create_user, login_user)

    client.post(
        "/activity",
        data={
            "workout_name": "Bench Press",
            "muscle_group": "chest",
            "num_set": 4,
            "num_reps": 8,
            "workout_weight": 185,
            "calories_burned": 220,
            "user_notes": "Strong session",
        },
        follow_redirects=True,
    )

    activity_response = client.get("/activity")
    dashboard_response = client.get("/dashboard")
    activity_body = activity_response.get_data(as_text=True)
    dashboard_body = dashboard_response.get_data(as_text=True)

    assert "Bench Press" in activity_body
    assert "1 of 4" in activity_body
    assert "1 / 4 sessions" in dashboard_body

    with app.app_context():
        entry = Activity.query.one()
        assert entry.workout_name == "Bench Press"
        assert entry.calories_burned == 220


def test_goal_forms_update_independently(app, client, create_user, login_user):
    login_default_user(create_user, login_user)

    client.post(
        "/goals",
        data={
            "goal_type": "nutrition",
            "daily_cal": 2200,
            "daily_protein": 180,
            "daily_carbs": 220,
            "daily_fats": 70,
        },
        follow_redirects=True,
    )

    client.post(
        "/goals",
        data={
            "goal_type": "activity",
            "weekly_workouts": 5,
        },
        follow_redirects=True,
    )

    client.post(
        "/goals",
        data={
            "goal_type": "weight",
            "current_weight": 185,
            "target_weight": 170,
        },
        follow_redirects=True,
    )

    with app.app_context():
        nutrition_goal = NutritionGoal.query.one()
        activity_goal = ActivityGoal.query.one()
        weight_goal = WeightGoal.query.one()

        assert nutrition_goal.daily_cal == 2200
        assert nutrition_goal.daily_protein == 180
        assert activity_goal.weekly_workouts == 5
        assert weight_goal.current_weight == 185
        assert weight_goal.target_weight == 170


def test_activity_goal_update_does_not_overwrite_nutrition_goal(app, client, create_user, login_user):
    login_default_user(create_user, login_user)

    client.post(
        "/goals",
        data={
            "goal_type": "nutrition",
            "daily_cal": 2100,
            "daily_protein": 160,
            "daily_carbs": 200,
            "daily_fats": 65,
        },
        follow_redirects=True,
    )

    client.post(
        "/goals",
        data={
            "goal_type": "activity",
            "weekly_workouts": 6,
        },
        follow_redirects=True,
    )

    with app.app_context():
        nutrition_goal = NutritionGoal.query.one()
        activity_goal = ActivityGoal.query.one()

        assert nutrition_goal.daily_cal == 2100
        assert nutrition_goal.daily_protein == 160
        assert activity_goal.weekly_workouts == 6


def test_dashboard_reflects_saved_goals_and_weight_progress(app, client, create_user, login_user):
    login_default_user(create_user, login_user)

    client.post(
        "/goals",
        data={
            "goal_type": "nutrition",
            "daily_cal": 2000,
            "daily_protein": 150,
            "daily_carbs": 220,
            "daily_fats": 60,
        },
        follow_redirects=True,
    )
    client.post(
        "/goals",
        data={
            "goal_type": "activity",
            "weekly_workouts": 3,
        },
        follow_redirects=True,
    )
    client.post(
        "/goals",
        data={
            "goal_type": "weight",
            "current_weight": 185,
            "target_weight": 170,
        },
        follow_redirects=True,
    )
    client.post(
        "/nutrition",
        data={
            "food_name": "Chicken Bowl",
            "serving_size": 250,
            "num_calories": 600,
            "grams_of_protein": 45,
            "grams_of_carb": 50,
            "grams_of_fat": 20,
        },
        follow_redirects=True,
    )
    client.post(
        "/activity",
        data={
            "workout_name": "Run",
            "muscle_group": "cardio",
            "num_set": 1,
            "num_reps": 1,
            "workout_weight": 0,
            "calories_burned": 300,
        },
        follow_redirects=True,
    )
    client.post(
        "/log_weight",
        data={
            "weight": 180,
            "unit": "lbs",
            "notes": "Morning",
        },
        follow_redirects=True,
    )

    response = client.get("/dashboard")
    body = response.get_data(as_text=True)

    assert "600 / 2000 kcal" in body
    assert "45 / 150 grams" in body
    assert "1 / 3 sessions" in body
    assert "Weight Goal" in body
    assert "10.0 lbs to go" in body

    with app.app_context():
        assert Nutrition.query.count() == 1
        assert Activity.query.count() == 1
        assert BodyWeight.query.count() == 1


def test_delete_nutrition_rejects_other_users_entry(app, client, create_user, login_user):
    owner = create_user(username="owner", email="owner@example.com", password="Password123!")
    intruder = create_user(username="intruder", email="intruder@example.com", password="Password123!")

    with app.app_context():
        entry = Nutrition(
            food_name="Owned Meal",
            num_calories=500,
            grams_of_protein=30,
            user_id=owner.id,
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    login_user("intruder", "Password123!")
    response = client.post(f"/delete_nutrition/{entry_id}", follow_redirects=True)

    assert "Not authorized." in response.get_data(as_text=True)

    with app.app_context():
        assert Nutrition.query.get(entry_id) is not None
