from configparser import ConfigParser
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from ht_13.src.conf.config import settings


url = settings.sqlalchemy_database_url

engine = create_engine(url, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    The get_db function is a context manager that returns the database session.
    It also handles any exceptions that may occur during the session, and closes
    the connection when it's done.

    :return: A database session
    :doc-author: Trelent
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    finally:
        db.close()
