from typing import List
# from datetime import date

from fastapi import Depends, HTTPException, Path, Query, APIRouter, status
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from ht_13.src.database.database_ import get_db
from ht_13.src.repository import contacts as repository_contacts
from ht_13.src.schemes.contacts import ContactModel, ContactResponse
from ht_13.src.database.models_ import User, Role
from ht_13.src.services.auth import auth_user
from ht_13.src.services.roles import RoleAccess


router = APIRouter(prefix="/contacts", tags=["contacts"])

allowed_get = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_create = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_update = RoleAccess([Role.admin, Role.moderator])
allowed_remove = RoleAccess([Role.admin])
allowed_search = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_get_birthdays = RoleAccess([Role.admin, Role.moderator, Role.user])


@router.get("/", response_model=List[ContactResponse],
            dependencies=[Depends(allowed_get), Depends(RateLimiter(times=10, seconds=60))],
            description="For all. No more than 10 requests per minute.")
async def get_contacts(
        limit: int = Query(10, le=100),
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_user.get_current_user)
):
    """
    The get_contacts function returns a list of contacts.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip
    :param db: Session: Pass a database session to the function
    :param current_user: User: Get the user that is currently logged in
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_all(limit, offset, current_user, db)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(allowed_get), Depends(RateLimiter(times=10, seconds=60))],
            description="For all. No more than 10 requests per minute."
            )
async def get_contact(contact_id: int = Path(ge=1),
                      current_user: User = Depends(auth_user.get_current_user),
                      db: Session = Depends(get_db)):
    """
    The get_contact function is a GET request that returns the contact with the given ID.
    The function takes in an integer as a path parameter, and uses it to query for the contact.
    If no such contact exists, then an HTTP 404 error is returned.

    :param contact_id: int: Get the contact id from the path
    :param current_user: User: Get the current user from the database
    :param db: Session: Get a database session
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact_by_id(contact_id, current_user, db)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.post("/", response_model=ContactResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_create), Depends(RateLimiter(times=4, seconds=60))],
             description="For all. No more than 4 creations per minute."
             )
async def create_contact(body: ContactModel,
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    """
    The create_contact function creates a new contact in the database.
        The function takes in a ContactModel object, which is validated by pydantic.
        If the validation fails, an HTTPException is raised with status code 400 (Bad Request).

    :param body: ContactModel: Specify the data that is required to create a contact
    :param current_user: User: Get the user that is currently logged in
    :param db: Session: Pass the database session to the repository layer
    :return: A contactmodel object
    :doc-author: Trelent
    """
    contact = await repository_contacts.create_contact(body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Such contact already exists")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(allowed_update)],
            description="For moderators and admin"
            )
async def update_contact(
        body: ContactModel,
        contact_id: int = Path(ge=1),
        current_user: User = Depends(auth_user.get_current_user),
        db: Session = Depends(get_db)
):
    """
    The update_contact function updates a contact in the database.
        The function takes an id, body and current_user as parameters.
        It returns a ContactModel object if successful.

    :param body: ContactModel: Get the data from the request body
    :param contact_id: int: Get the contact id from the url
    :param current_user: User: Get the current user from the database
    :param db: Session: Pass the database session to the repository layer
    :return: A contactmodel object
    :doc-author: Trelent
    """
    contact = await repository_contacts.update(contact_id, body, current_user, db)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(allowed_remove)],
               description="For admin only"
               )
async def delete_contact(contact_id: int = Path(ge=1),
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Specify the id of the contact to be deleted
    :param current_user: User: Get the user object from the database
    :param db: Session: Get the database connection
    :return: The deleted contact
    :doc-author: Trelent
    """
    contact = await repository_contacts.remove(contact_id, current_user, db)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.get("/search/", response_model=List[ContactResponse],
            dependencies=[Depends(allowed_search), Depends(RateLimiter(times=10, seconds=60))],
            description="For all. No more than 10 requests per minute."
            )
async def search_by(parameter: str | int,
                    current_user: User = Depends(auth_user.get_current_user),
                    db: Session = Depends(get_db)):
    """
    The search_by function searches for a contact by name or phone number.
        The function takes in the parameter to search by, the current user, and a database session.
        It then calls on the repository_contacts module's search function to perform this task.
        If no contacts are found, it raises an HTTPException with status code 404 Not Found.

    :param parameter: str | int: Search for a contact by name or phone number
    :param current_user: User: Get the current user
    :param db: Session: Access the database
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.search(parameter, current_user, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contacts


@router.get("/birthdays/", response_model=List[ContactResponse],
            dependencies=[Depends(allowed_get_birthdays), Depends(RateLimiter(times=10, seconds=60))],
            description="For all. No more than 10 requests per minute."
            )
async def get_birthdays(current_user: User = Depends(auth_user.get_current_user),
                        db: Session = Depends(get_db)):
    """
    The get_birthdays function returns a list of contacts that have birthdays in the current month.

    :param current_user: User: Get the current user from the database
    :param db: Session: Pass the database session to the repository layer
    :return: A list of contacts that have a birthday today
    :doc-author: Trelent
    """
    contacts = await repository_contacts.birthdays(current_user, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contacts
