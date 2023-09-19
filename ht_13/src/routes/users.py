from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from ht_13.src.database.database_ import get_db
from ht_13.src.database.models_ import User
from ht_13.src.repository import users as repository_users
from ht_13.src.services.auth import auth_user
from ht_13.src.schemes.users import UserResponse
from ht_13.src.services.cloud_image import CloudImage


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(auth_user.get_current_user)):
    """
    The read_users_me function returns the current user's information.

    :param current_user: User: Get the current user
    :return: The current_user object, which is the user that has been authenticated
    :doc-author: Trelent
    """
    return current_user


@router.patch('/avatar', response_model=UserResponse)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_user.get_current_user),
                             db: Session = Depends(get_db)):
    """
    The update_avatar_user function updates the avatar of a user.

    :param file: UploadFile: Get the file from the request
    :param current_user: User: Get the current user
    :param db: Session: Access the database
    :return: The updated user
    :doc-author: Trelent
    """
    public_id = CloudImage.generate_name_avatar(current_user.email)
    r = CloudImage.upload(file.file, public_id)
    src_url = CloudImage.get_url_for_avatar(public_id, r)
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user
