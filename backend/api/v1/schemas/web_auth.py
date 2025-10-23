from pydantic import BaseModel

class WebAccountCreate(BaseModel):
    email: str
    password: str

class WebAccountLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class SetPasswordRequest(BaseModel):
    email: str
    password: str
