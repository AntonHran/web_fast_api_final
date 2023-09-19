import pickle
from datetime import datetime, timedelta
from typing import Optional

import redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from ht_13.src.database.database_ import get_db
from ht_13.src.repository import users as repository_users
from ht_13.src.conf.config import settings


class Token:
    SECRET_KEY_A = settings.secret_key_a
    SECRET_KEY_R = settings.secret_key_r
    ALGORITHM = settings.algorithm

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        The create_access_token function creates a new access token.

        :param self: Access the class attributes
        :param data: dict: A dictionary containing the claims to be encoded in the JWT
        :param expires_delta: Optional[float]: An optional parameter specifying how long, in seconds,
                the access token should last before expiring. If not specified, it defaults to 15 minutes.
        :return: A jwt token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY_A, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        The create_refresh_token function creates a refresh token for the user.

        :param self: Represent the instance of the class
        :param data: dict: Pass in the user's id and username
        :param expires_delta: Optional[float]: Set the expiration time of the refresh token. The time
        in seconds until the refresh token expires. Defaults to None, which is 7 days from creation date.
        :return: A refresh token that is encoded with the secret key
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"}
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY_R, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function is used to decode the refresh token.
        It will raise an exception if the token is invalid or has expired.
        If it's valid, it returns the email address of the user.

        :param self: Represent the instance of the class
        :param refresh_token: str: Pass the refresh token to the function
        :return: The email of the user, which is stored in the sub claim
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY_R, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def create_email_token(self, data: dict):  # !!!
        """
        The create_email_token function is used to create a token that will be sent to the user's email address.
        The token contains the following data:
            - iat (issued at): The time when the token was created.
            - exp (expiration): The time when this token expires and becomes invalid. This is set to 1 day from now, but can be changed in settings if needed.
            - scope: A string indicating what this particular JWT can do/what it has access to on our server side code.

        :param self: Represent the instance of the class
        :param data: dict: Pass in the data that will be encoded into the token
        :return: A token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=1)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "email_token"}
        )
        token = jwt.encode(to_encode, self.SECRET_KEY_A, algorithm=self.ALGORITHM)
        return token

    def get_email_from_token(self, token: str):
        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        It does this by decoding the JWT using our SECRET_KEY_A and ALGORITHM, then checking to make sure that it has a scope of &quot;email_token&quot;.
        If so, it returns the sub (subject) field from the payload. If not, it raises an HTTPException with status code 401 Unauthorized.

        :param self: Represent the instance of the class
        :param token: str: Pass in the token that is sent to the user's email
        :return: The email associated with the token
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY_A, algorithms=[self.ALGORITHM])
            if payload["scope"] == "email_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )


class Hash:
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
        The verify_password function takes a plain-text password and hashed
        password as arguments. It then uses the verify method of the PasswordContext
        object to check if they match. If they do, it returns True; otherwise, it returns False.

        :param self: Represent the instance of the class
        :param plain_password: Pass in the password that is being verified
        :param hashed_password: Check if the password is correct
        :return: True or false
        :doc-author: Trelent
        """
        return self.password_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        The get_password_hash function is a helper function that uses the passlib library to hash
        the password. The hashing algorithm used by this function is PBKDF2 with HMAC-SHA256, which
        is considered secure and recommended for most applications.

        :param self: Represent the instance of the class
        :param password: str: Pass in the password that is to be hashed
        :return: A hash of the password
        :doc-author: Trelent
        """
        return self.password_context.hash(password)


class CurrentUser:
    SECRET_KEY_A = settings.secret_key_a
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    red = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        """
        The get_current_user function is a dependency that will be used in the
            get_current_active_user endpoint. It takes a token as an argument and
            returns the user object if it exists, or raises an exception otherwise.

        :param self: Refer to the current object
        :param token: str: Get the token from the request header
        :param db: Session: Get the database session
        :return: A user object
        :doc-author: Trelent
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY_A, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if not email:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = self.red.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.red.set(f"user:{email}", pickle.dumps(user))
            self.red.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user


auth_token = Token()
auth_password = Hash()
auth_user = CurrentUser()
