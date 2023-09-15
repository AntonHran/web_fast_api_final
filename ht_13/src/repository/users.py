from sqlalchemy.orm import Session
from libgravatar import Gravatar

from ht_13.src.database.models_ import User
from ht_13.src.schemes.users import UserModel


async def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter_by(email=email).first()


async def create_user(body: UserModel, db: Session):
    gr = Gravatar(body.email)
    avatar = gr.get_image()
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token, db: Session):
    user.refresh_token = refresh_token
    db.commit()


async def confirm_email(email: str, db: Session):
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def reset_password(user: User, new_password: str, db: Session):
    user.password = new_password
    db.commit()


async def update_avatar(email: str, url: str, db: Session):
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user
