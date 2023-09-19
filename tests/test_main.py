import os
import sys

from fastapi.testclient import TestClient

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from ht_13 import contacts_


client = TestClient(contacts_.app)


def test_read_contacts_():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Here your contacts!"}
