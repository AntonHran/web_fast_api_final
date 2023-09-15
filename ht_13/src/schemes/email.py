from pydantic import BaseModel, Field, EmailStr


class RequestEmail(BaseModel):
    email: EmailStr


class PasswordResetModel(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6, max_length=12)
    confirm_password: str = Field(min_length=6, max_length=12)
