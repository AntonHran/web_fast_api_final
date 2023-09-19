from sqlalchemy.orm import Session
from libgravatar import Gravatar

from ht_13.src.database.models_ import User
from ht_13.src.schemes.users import UserModel


async def get_user_by_email(email: str, db: Session) -> User | None:
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user with that email if it exists. If no such user exists,
    it returns None.

    :param email: str: Pass the email address of a user to the function
    :param db: Session: Pass the database session to the function
    :return: A user object if the user exists, or none if it doesn't
    :doc-author: Trelent
    """
    return db.query(User).filter_by(email=email).first()


async def create_user(body: UserModel, db: Session):
    """
    The create_user function creates a new user in the database.
        Args:
            body (UserModel): The UserModel object to be created.
            db (Session): The SQLAlchemy session object used for querying the database.

    :param body: UserModel: Pass the user data to the function
    :param db: Session: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    gr = Gravatar(body.email)
    avatar = gr.get_image()
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token, db: Session):
    """
    The update_token function updates the refresh token for a user in the database.
        Args:
            user (User): The User object to update.
            refresh_token (str): The new refresh token to store in the database.
            db (Session): A connection to our Postgres database.

    :param user: User: Identify the user that is being updated
    :param refresh_token: Update the user's refresh_token in the database
    :param db: Session: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    user.refresh_token = refresh_token
    db.commit()


async def confirm_email(email: str, db: Session):
    """
    The confirm_email function takes an email and a database session as arguments.
    It then uses the get_user_by_email function to retrieve the user with that email address,
    and sets their confirmed field to True. It then commits this change to the database.

    :param email: str: Get the email of the user
    :param db: Session: Access the database
    :return: Nothing, so the return type is none
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def reset_password(user: User, new_password: str, db: Session):
    """
    The reset_password function takes a user and new_password as arguments,
    and updates the password of the user in the database.


    :param user: User: Get the user object from the database
    :param new_password: str: Pass in the new password
    :param db: Session: Access the database
    :return: Nothing
    :doc-author: Trelent
    """
    user.password = new_password
    db.commit()


async def update_avatar(email: str, url: str, db: Session):
    """
    The update_avatar function updates the avatar of a user.

    :param email: str: Specify the email of the user that is being updated
    :param url: str: Update the avatar of a user
    :param db: Session: Access the database
    :return: The user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user
