from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    password: str = Field(..., min_length=4, max_length=100)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2)
    password: str = Field(..., min_length=4)


class AuthResponse(BaseModel):
    success: bool
    token: str = ""
    username: str = ""
    user_id: int = 0
    message: str = ""


class UserInfo(BaseModel):
    user_id: int
    username: str
