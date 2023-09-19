import os
import sys
import unittest
from datetime import date
from unittest.mock import MagicMock, patch, AsyncMock

from sqlalchemy.orm import Session

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from ht_13.src.repository.contacts import (
    get_contact_ids,
    get_all,
    get_contact_by_id,
    create_contact,
    create_record,
    update,
    remove,
    search,
    birthdays,
)

from ht_13.src.database.models_ import Contact, User, UserToContact
from ht_13.src.schemes.contacts import ContactModel


class TestContactsRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="test@test.com")

    async def test_get_all(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query(
            Contact
        ).filter().limit().offset().all.return_value = contacts
        result = await get_all(10, 0, self.user, self.session)
        self.assertEqual(result, contacts)

    async def test_create_contact(self):
        body = ContactModel(
            first_name="Harley",
            last_name="Quinn",
            email="harley@example.com",
            phone_number="+380501234567",
            birth_date=date(year=2016, month=12, day=4),
            notes="yorkshire terrier",
        )
        result = await create_contact(body, self.user, self.session)
        self.assertEqual(result.first_name, body.first_name)
        self.assertTrue(hasattr(result, "id"))

    async def test_get_contact_ids(self):
        contact_ids = [
            UserToContact(user_id=self.user.id, contact_id=1),
            UserToContact(user_id=self.user.id, contact_id=2),
        ]
        self.session.query(
            UserToContact.contact_id
        ).filter_by().all.return_value = contact_ids
        result = await get_contact_ids(self.user, self.session)
        self.assertEqual(result, [cont.contact_id for cont in contact_ids])

    async def test_get_contact_by_id(self):
        con = Contact()
        contact_ids = [
            UserToContact(user_id=self.user.id, contact_id=con.id),
            UserToContact(user_id=self.user.id, contact_id=2),
        ]
        self.session.query(UserToContact.contact_id).filter_by().all.return_value = contact_ids
        self.session.query().filter_by().first.return_value = con
        result = await get_contact_by_id(con.id, self.user, self.session)
        self.assertEqual(result, con)

    async def test_create_record(self):
        result = UserToContact(user_id=1, contact_id=1,)
        res = await create_record(2, self.user, self.session)
        self.session.query(UserToContact).all.filter_by(id=2).all.return_value = result
        self.assertEqual(result.user_id, res.user_id)
        self.assertIsNot(result.contact_id, res.contact_id)
        self.assertTrue(hasattr(result, "id"))

    async def test_remove(self):
        cont = Contact()

        async def get_contact_by_id_mock(contact_id, user, db):
            return cont

        with patch("ht_13.src.repository.contacts.get_contact_by_id", get_contact_by_id_mock):
            result = await remove(cont.id, self.user, self.session)
        self.assertEqual(result, cont)

    async def test_search(self):
        cont_1 = Contact(id=1, first_name="Harley", email="harley@example.com")
        cont_2 = Contact(id=2, first_name="Jessica", email="jessica@example.com")
        contacts = [cont_1, cont_2]
        get_contact_ids_mock = AsyncMock()
        with patch("ht_13.src.repository.contacts.get_contact_ids", get_contact_ids_mock):
            search_result = await search("Harley", self.user, self.session)

        self.assertIsInstance(search_result, list)
        for contact in search_result:
            self.assertIn("Harley", contact.first_name)

    async def test_search_(self):
        cont = Contact(id=2, first_name="Jessica", email="jessica@example.com")
        contacts = [cont]
        get_contact_ids_mock = AsyncMock()
        with patch("ht_13.src.repository.contacts.get_contact_ids", get_contact_ids_mock):
            search_result = await search("Harley", self.user, self.session)
        self.assertIsNot(search_result, [cont])

    async def test_birthdays(self):
        cont_1 = Contact(id=1, first_name="Harley", birth_date=date(2020, 9, 21))
        cont_2 = Contact(id=2, first_name="Jessica", birth_date=date(2015, 12, 10))
        contacts = [cont_1, cont_2]
        self.session.query(Contact).filter().limit().offset().all.return_value = contacts
        result = await birthdays(self.user, self.session)
        self.assertEqual(result, [cont_1])

    async def test_birthdays_no_match(self):
        cont_1 = Contact(id=1, first_name="Harley", birth_date=date(2020, 9, 19))
        cont_2 = Contact(id=2, first_name="Jessica", birth_date=date(2015, 12, 10))
        contacts = [cont_1, cont_2]
        self.session.query(Contact).filter().limit().offset().all.return_value = contacts
        result = await birthdays(self.user, self.session)
        self.assertEqual(result, [])

    async def test_update__(self):
        """
        The test_update__ function tests the update function.
        It does so by creating a Contact object, and then using the patch decorator to mock out
        the get_contact_by_id function from contacts.py in order to return that contact object.
        The test then calls update with the mocked contact id, body (a ContactModel), user (self.user) and session (self.session).
        Finally it asserts that result is equal to cont, which was created at the beginning of this test.

        :param self: Represent the instance of the object that is passed to the method
        :return: The updated contact
        :doc-author: Trelent
        """
        cont = Contact()
        body = ContactModel(
            first_name="Harley",
            last_name="Quinn",
            email="harley@example.com",
            phone_number="+380501234567",
            birth_date=date(year=2016, month=12, day=4),
            notes="yorkshire terrier",
        )

        async def get_contact_by_id_mock(contact_id, user, db):
            return cont

        with patch("ht_13.src.repository.contacts.get_contact_by_id", get_contact_by_id_mock):
            result = await update(cont.id, body, self.user, self.session)

        self.assertEqual(result, cont)
        self.assertEqual(result.first_name, body.first_name)
        self.assertTrue(hasattr(result, "id"))


if __name__ == "__main__":
    unittest.main()
