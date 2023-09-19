from datetime import date, timedelta
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ht_13.src.database.models_ import Contact, User, UserToContact
from ht_13.src.schemes.contacts import ContactModel

logger = logging.getLogger(__name__)


async def get_contact_ids(user: User, db: Session) -> list[int]:
    """
    The get_contact_ids function takes a user and database session as arguments.
    It returns a list of contact ids associated with the given user.

    :param user: User: Get the user's id
    :param db: Session: Pass the database session to the function
    :return: A list of contact_ids
    :doc-author: Trelent
    """
    contact_ids = db.query(UserToContact.contact_id).filter_by(user_id=user.id).all()
    return [cont.contact_id for cont in contact_ids]


async def get_all(limit: int, offset: int, user: User, db: Session):
    """
    The get_all function returns a list of contacts for the user.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Determine the starting point of the query
    :param user: User: Get the user's id
    :param db: Session: Pass the database session to the function
    :return: A list of contacts
    :doc-author: Trelent
    """
    contact_ids = await get_contact_ids(user, db)
    contacts: list = (
        db.query(Contact)
        .filter(Contact.id.in_(contact_ids))
        .limit(limit)
        .offset(offset)
        .all()
    )
    return contacts


async def get_contact_by_id(contact_id: int, user: User, db: Session):
    """
    The get_contact_by_id function returns a contact object from the database
        if it exists.

    :param contact_id: int: Pass in the contact id of the contact to be retrieved
    :param user: User: Get the user's id
    :param db: Session: Pass the database session to the function
    :return: A contact object
    :doc-author: Trelent
    """
    contact_ids = await get_contact_ids(user, db)
    if contact_id in contact_ids:
        contact = db.query(Contact).filter_by(id=contact_id).first()
        return contact


async def create_record(contact_id: int, user: User, db: Session):
    """
    The create_record function creates a new record in the UserToContact table.
        Args:
            contact_id (int): The id of the contact to be added to the user's list.
            user (User): The current logged-in user, whose list will be updated with this new contact.
            db (Session): A database session object that is used for querying and updating records in our database.

    :param contact_id: int: Specify the contact that is being added to the database
    :param user: User: Get the user id from the database
    :param db: Session: Pass the database session to the function
    :return: The created record
    :doc-author: Trelent
    """
    record = UserToContact(user_id=user.id, contact_id=contact_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


async def create_contact(body: ContactModel, user: User, db: Session):
    """
    The create_contact function creates a new contact in the database.
        It takes in a ContactModel object, which is validated by pydantic and then converted into an SQLAlchemy model.
        The function then adds the contact to the database and commits it.  If there are any errors, they are caught and rolled back.

    :param body: ContactModel: Create a new contact object
    :param user: User: Get the user id of the logged in user
    :param db: Session: Pass the database session to the function
    :return: The contact object
    :doc-author: Trelent
    """
    contact = Contact(**body.model_dump())
    try:
        db.add(contact)
        db.commit()
        db.refresh(contact)
        await create_record(contact.id, user, db)
        return contact
    except IntegrityError as err:
        db.rollback()
        print(err)
        await check(contact, user, db)


async def check(contact: Contact, user: User, db):
    """
    The check function is used to check if a contact already exists in the database.
    If it does, then we create a record for that user and contact in the UserToContact table.

    :param contact: Contact: Pass the contact object to the function
    :param user: User: Get the user_id of the current user
    :param db: Access the database
    :return: A list of contacts that the user does not have in their contact list
    :doc-author: Trelent
    """
    existing_contact = (
        db.query(Contact).filter_by(phone_number=contact.phone_number).first()
    )
    user_contacts = db.query(UserToContact.contact_id).filter_by(user_id=user.id).all()
    if existing_contact and existing_contact.id not in [cont.contact_id for cont in user_contacts]:
        await create_record(existing_contact.id, user, db)


async def update(contact_id: int, body: ContactModel, user: User, db: Session):
    """
    The update function updates a contact in the database.
        Args:
            contact_id (int): The id of the contact to update.
            body (ContactModel): The updated information for the specified user.

    :param contact_id: int: Specify the contact to delete
    :param body: ContactModel: Get the data from the request body
    :param user: User: Get the user id of the current logged in user
    :param db: Session: Access the database
    :return: The contact object
    :doc-author: Trelent
    """
    contact = await get_contact_by_id(contact_id, user, db)
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.phone_number = body.phone_number
        contact.email = body.email
        contact.birth_date = body.birth_date
        contact.notes = body.notes
        db.commit()
        db.refresh(contact)
    return contact


async def remove(contact_id: int, user: User, db: Session):
    """
    The remove function removes a contact from the database.
        Args:
            contact_id (int): The id of the contact to be removed.
            user (User): The user who is removing the contact.
            db (Session): A connection to our database, used for
            querying and updating data.

    :param contact_id: int: Specify the id of the contact to be removed
    :param user: User: Get the user id from the token
    :param db: Session: Pass the database session to the function
    :return: The contact object that was removed
    :doc-author: Trelent
    """
    contact = await get_contact_by_id(contact_id, user, db)
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def search(parameter: str | int, user: User, db: Session):
    """
    The search function is used to search for contacts in the database.
    It takes a parameter, which can be either a string or an integer, and searches through all of the attributes
    of Contact objects in the database.
    The function returns a list of Contact objects that match any attribute with the given parameter.

    :param parameter: str | int: Search for a contact in the database
    :param user: User: Get the user's contact list
    :param db: Session: Pass the database session to the function
    :return: A list of contacts, which match the search parameter
    :doc-author: Trelent
    """
    attributes: list[str] = list(vars(Contact).keys())
    result = []
    contact_ids = await get_contact_ids(user, db)
    for attribute in attributes:
        try:
            query = (
                db.query(Contact)
                .filter(
                    Contact.id.in_(contact_ids),
                    getattr(Contact, attribute).ilike("%" + parameter + "%")
                    if attribute != "id"
                    else None,
                )
                .all()
            )
        except Exception as error:
            logger.error(f"Error during proceeding SQL-query: {str(error)}")
            continue
        if query:
            result.extend([rec for rec in query if rec not in result])
    return result


async def birthdays(user: User, db: Session):
    """
    The birthdays function returns a list of contacts whose birthdays are within the next 7 days.

    :param user: User: Get the user id from the request
    :param db: Session: Pass the database session to the function
    :return: A list of contacts that have birthdays in the next 7 days
    :doc-author: Trelent
    """
    current_date = date.today()
    dates: list = [current_date + timedelta(days=i) for i in range(7)]
    result = []
    contacts = [
        contact
        for contact in await get_all(limit=100, offset=0, user=user, db=db)
        if contact.birth_date
    ]
    for contact in contacts:
        b_date = date(
            year=current_date.year,
            month=contact.birth_date.month,
            day=contact.birth_date.day,
        )
        if b_date in dates:
            result.append(contact)
    return result
