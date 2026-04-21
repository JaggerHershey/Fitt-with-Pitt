from models.user_model import User


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_register_creates_user_and_redirects_to_login(app, register_user, user_credentials):
    response = register_user(
        user_credentials["username"],
        user_credentials["email"],
        user_credentials["password"],
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Welcome back" in body
    assert "Sign in" in body

    with app.app_context():
        user = User.query.filter_by(username=user_credentials["username"]).first()
        assert user is not None
        assert user.email == user_credentials["email"]
        assert user.check_password(user_credentials["password"])


def test_register_rejects_duplicate_email(app, register_user):
    register_user("alpha", "shared@example.com", "Password123!")

    response = register_user("beta", "shared@example.com", "Password123!")
    body = response.get_data(as_text=True)

    assert "Email is already taken" in body

    with app.app_context():
        assert User.query.filter_by(email="shared@example.com").count() == 1


def test_login_and_logout_flow(client, create_user, login_user):
    create_user(username="member", email="member@example.com", password="Password123!")

    login_response = login_user("member", "Password123!")
    login_body = login_response.get_data(as_text=True)

    assert login_response.status_code == 200
    assert "Dashboard" in login_body

    logout_response = client.get("/logout", follow_redirects=True)
    logout_body = logout_response.get_data(as_text=True)

    assert logout_response.status_code == 200
    assert "logged out" in logout_body.lower()


def test_login_rejects_invalid_password(create_user, login_user):
    create_user(username="member", email="member@example.com", password="Password123!")

    response = login_user("member", "wrong-password")

    assert response.status_code == 200
    assert "Invalid credentials" in response.get_data(as_text=True)
