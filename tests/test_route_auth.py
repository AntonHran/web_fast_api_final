from unittest.mock import MagicMock

from ht_13.src.database.models_ import User
from ht_13.src.conf import messages


def test_create_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("ht_13.src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["email"] == user.get("email")


def test_repeat_create_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("ht_13.src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 409, response.text
    payload = response.json()
    assert payload["detail"] == "Account already exists"


def test_login_user_not_confirmed(client, user):
    response = client.post("/api/auth/login", data={"username": user.get("email"), "password": user.get("password")})
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == messages.EMAIL_NOT_CONFIRMED


def test_login_user(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": user.get("email"), "password": user.get("password")})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["token_type"] == messages.TOKEN_TYPE


def test_login_user_with_wrong_password(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": user.get("email"), "password": "password"})
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == messages.INVALID_PASSWORD


def test_login_user_with_wrong_email(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": "eaxample@test.com", "password": user.get("password")})
    assert response.status_code == 401, response.text
    payload = response.json()  # token
    assert payload["detail"] == messages.INVALID_EMAIL


def test_refresh_token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("ht_13.src.routes.auth.send_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    token = response.json()

    response_ = client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token['refresh_token']}"},
    )
    assert response_.status_code == 200, response_.text
    data = response_.json()
    assert data["refresh_token"] == token["refresh_token"]

    assert data["token_type"] == messages.TOKEN_TYPE


def test_refresh_token_(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("ht_13.src.routes.auth.send_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    token = response.json()

    response_ = client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_.status_code == 401, response_.text
    data = response_.json()
    current_user.refresh_token = token["refresh_token"]
    assert data["detail"] == messages.COULD_NOT_VALIDATE_CREDENTIALS


def test_refresh_token__(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("ht_13.src.routes.auth.send_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    token = response.json()

    response_ = client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    assert response_.status_code == 401, response_.text
    data = response_.json()
    assert data['detail'] == messages.INVALID_SCOPE_FOR_TOKEN


def test_request_email(client, user, session, monkeypatch):
    response = client.post(
        "/api/auth/request_email",
        json={"email": user.get("email")},
    )
    print(response.json())
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed"


def test_reset_password(client, user):
    response = client.post("/api/auth/reset_password", json={
        "email": user.get("email"),
        "new_password": "123456",
        "confirm_password": "123456"
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    print(payload)
    assert payload["message"] == "Password reset complete!"


def test_reset_password_(client, user):
    response = client.post("/api/auth/reset_password", json={
        "email": "lkbm@example.com",
        "new_password": "123456",
        "confirm_password": "123456"
    })
    assert response.status_code == 404, response.text
    payload = response.json()
    print(payload)
    assert payload["detail"] == messages.INVALID_EMAIL


def test_reset_password__(client, user):
    response = client.post("/api/auth/reset_password", json={
        "email": user.get("email"),
        "new_password": "123456",
        "confirm_password": "123450"
    })
    assert response.status_code == 409, response.text
    payload = response.json()
    print(payload)
    assert payload["detail"] == messages.PASSWORDS_NOT_EQUAL
