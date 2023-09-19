from unittest.mock import MagicMock

from ht_13.src.database.models_ import User
from ht_13.src.conf import messages


def test_create_user(client, user, monkeypatch):
    """
    The test_create_user function tests the /api/auth/signup endpoint.
    It does so by creating a user and then sending that user to the endpoint.
    The test_create_user function also uses monkeypatching to mock out the send_email function, which is called in routes.py.

    :param client: Make requests to the flask application
    :param user: Create a user in the database
    :param monkeypatch: Mock the send_email function
    :return: The response of the post request
    :doc-author: Trelent
    """
    mock_send_email = MagicMock()
    monkeypatch.setattr("ht_13.src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["email"] == user.get("email")


def test_repeat_create_user(client, user, monkeypatch):
    """
    The test_repeat_create_user function tests the /api/auth/signup endpoint.
    It does this by creating a user, then attempting to create another user with the same email address.
    The test asserts that the response status code is 409 (Conflict) and that the payload contains an error message.

    :param client: Make requests to the flask application
    :param user: Create a user in the database
    :param monkeypatch: Mock the send_email function
    :return: A 409 status code and a detail message
    :doc-author: Trelent
    """
    mock_send_email = MagicMock()
    monkeypatch.setattr("ht_13.src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 409, response.text
    payload = response.json()
    assert payload["detail"] == "Account already exists"


def test_login_user_not_confirmed(client, user):
    """
    The test_login_user_not_confirmed function tests that a user cannot login if they have not confirmed their email.
        It does this by creating a new user, and then attempting to login with the credentials of that user.
        The test asserts that the response status code is 401 (Unauthorized), and also checks for an error message in the payload.

    :param client: Make requests to the flask application
    :param user: Create a user in the database
    :return: A 401 status code and a message that the user has not confirmed their email address
    :doc-author: Trelent
    """
    response = client.post("/api/auth/login", data={"username": user.get("email"), "password": user.get("password")})
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == messages.EMAIL_NOT_CONFIRMED


def test_login_user(client, user, session):
    """
    The test_login_user function tests the login endpoint.
    It does so by first creating a user, then confirming that user's account, and finally logging in with that confirmed
    user's credentials. If all of these steps are successful, the test passes.

    :param client: Make requests to the api
    :param user: Create a user in the database
    :param session: Add the user to the database
    :return: A payload with a token_type of &quot;bearer&quot;
    :doc-author: Trelent
    """
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": user.get("email"), "password": user.get("password")})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["token_type"] == messages.TOKEN_TYPE


def test_login_user_with_wrong_password(client, user, session):
    """
    The test_login_user_with_wrong_password function tests the login endpoint with a wrong password.
    It should return 401 Unauthorized and an error message.

    :param client: Make requests to the api
    :param user: Pass the user fixture into this function
    :param session: Get the current user from the database
    :return: 401 status code and invalid_password message
    :doc-author: Trelent
    """
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": user.get("email"), "password": "password"})
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == messages.INVALID_PASSWORD


def test_login_user_with_wrong_email(client, user, session):
    """
    The test_login_user_with_wrong_email function tests the login endpoint with a wrong email.
        It should return 401 and an error message.

    :param client: Make requests to the api
    :param user: Create a user in the database
    :param session: Create a new user in the database
    :return: A 401 status code and a message indicating that the email is invalid
    :doc-author: Trelent
    """
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": "eaxample@test.com", "password": user.get("password")})
    assert response.status_code == 401, response.text
    payload = response.json()  # token
    assert payload["detail"] == messages.INVALID_EMAIL


def test_refresh_token(client, user, session, monkeypatch):
    """
    The test_refresh_token function tests the refresh_token endpoint.
    It does so by first creating a user, and then logging in with that user.
    The login function returns an access token and a refresh token, which are used to test the
    refresh_token endpoint. The test asserts that the response status code is 200 (OK), and also
    that the returned data contains both an access token and a refresh token.

    :param client: Create a test client
    :param user: Create a user in the database
    :param session: Create a new user and the monkeypatch parameter is used to mock the send_email function
    :param monkeypatch: Mock the send_email function
    :return: A new access token
    :doc-author: Trelent
    """
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
    """
    The test_refresh_token_ function tests the refresh_token endpoint.
    It does so by first creating a user, then logging in with that user and getting a token.
    Then it tries to get another token using the refresh_token from the previous response.
    This should fail because we have not confirmed our email yet.

    :param client: Create a test client
    :param user: Create a user in the database
    :param session: Create a session for the test
    :param monkeypatch: Mock the send_email function
    :return: 401 and a message saying that the credentials could not be validated
    :doc-author: Trelent
    """
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
    """
    The test_refresh_token__ function tests the refresh_token endpoint.
    It does so by first mocking the send_email function, which is used in the register endpoint.
    Then it sets a user's confirmed field to True and commits that change to the database.
    Next, it sends a POST request to /api/auth/login with valid credentials for that user and stores
    the response token in a variable called token. Then it sends another GET request to /api/auth/refresh_token
    with an Authorization header containing Bearer {token['access_token']}. It asserts that this returns 401 Unauthorized,
    and then

    :param client: Make requests to the flask application
    :param user: Create a user in the database
    :param session: Create a new session for the test
    :param monkeypatch: Mock the send_email function
    :return: 401 status code and message invalid_scope_for_token
    :doc-author: Trelent
    """
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
    """
    The test_request_email function tests the /api/auth/request_email endpoint.
    It does this by first creating a client, user, and session using fixtures.
    Then it uses the client to make a POST request to /api/auth/request_email with an email address as JSON data.
    The response is then checked for status code 200 (OK) and that its JSON data contains a message saying &quot;Your email is already confirmed&quot;.

    :param client: Make a request to the api
    :param user: Create a user object that is used to test the request_email endpoint
    :param session: Create a new session for the test
    :param monkeypatch: Mock the send_email function
    :return: A 200 status code and a message saying that the email is already confirmed
    :doc-author: Trelent
    """
    response = client.post(
        "/api/auth/request_email",
        json={"email": user.get("email")},
    )
    print(response.json())
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed"


def test_reset_password(client, user):
    """
    The test_reset_password function tests the reset_password endpoint.
    It does this by first creating a user, then sending a POST request to the /api/auth/reset_password endpoint with that user's email and new password.
    The response is checked for status code 200, which indicates success.

    :param client: Make requests to the flask application
    :param user: Pass in the user object that was created
    :return: A 200 status code and a message that says &quot;password reset complete!&quot;
    :doc-author: Trelent
    """
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
    """
    The test_reset_password_ function tests the reset_password endpoint.
        It does so by sending a POST request to /api/auth/reset_password with an invalid email address,
        and then asserts that the response status code is 404 (Not Found), and that the payload's detail key has a value of &quot;Invalid Email&quot;.


    :param client: Make requests to the api
    :param user: Create a user in the database
    :return: The message &quot;invalid email&quot;
    :doc-author: Trelent
    """
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
    """
    The test_reset_password__ function tests the reset_password endpoint.
        It does so by sending a POST request to /api/auth/reset_password with an email and two passwords, one of which is incorrect.
        The test asserts that the response status code is 409 (Conflict) and that the payload contains a detail message explaining why.

    :param client: Make requests to the api
    :param user: Get the user's email
    :return: A 409 status code and a message that the passwords do not match
    :doc-author: Trelent
    """
    response = client.post("/api/auth/reset_password", json={
        "email": user.get("email"),
        "new_password": "123456",
        "confirm_password": "123450"
    })
    assert response.status_code == 409, response.text
    payload = response.json()
    print(payload)
    assert payload["detail"] == messages.PASSWORDS_NOT_EQUAL
