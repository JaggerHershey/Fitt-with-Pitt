import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app as flask_app
from models import db
from models.user_model import User


@pytest.fixture
def app():
    flask_app.config.update(
        TESTING=True,
        LOGIN_DISABLED=False,
    )

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

        yield flask_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_credentials():
    token = uuid.uuid4().hex[:8]
    return {
        "username": f"user_{token}",
        "email": f"{token}@example.com",
        "password": "Password123!",
    }


@pytest.fixture
def create_user(app):
    def _create_user(username="tester", email="tester@example.com", password="Password123!"):
        with app.app_context():
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
            db.session.expunge(user)
            return user

    return _create_user


@pytest.fixture
def register_user(client):
    def _register(username, email, password):
        return client.post(
            "/register",
            data={
                "username": username,
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )

    return _register


@pytest.fixture
def login_user(client):
    def _login(username, password):
        return client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    return _login
