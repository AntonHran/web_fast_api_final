from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from ht_13.src.services.auth import auth_token
from ht_13.src.conf.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME="Contacts App",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    The send_email function sends an email to the user with a link that they can click on to verify their email address.
    The function takes in three parameters:
        -email: The user's email address, which is used as the recipient of the message.
        -username: The username of the user, which is used in a greeting within the body of the message.
        -host: The hostname (domain) where this application is running, which will be included in a link within

    :param email: EmailStr: Validate the email address
    :param username: str: Pass the username to the email template
    :param host: str: Pass in the host of the website
    :return: A coroutine object, which is a generator-based asynchronous function
    :doc-author: Trelent
    """
    try:
        token_verification = auth_token.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)
