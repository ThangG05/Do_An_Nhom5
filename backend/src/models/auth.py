from pydantic import BaseModel, Field, field_validator

class LoginRequest(BaseModel):
    email: str
    password: str


class EmailRegistrationRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class VerifyEmailCodeRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    code: str = Field(..., pattern=r"^[0-9]{4}$")


class CompleteRegistrationRequest(BaseModel):
    registration_token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(character.isalpha() for character in value):
            raise ValueError("Mật khẩu phải có ít nhất một chữ cái.")
        if not any(character.isdigit() for character in value):
            raise ValueError("Mật khẩu phải có ít nhất một chữ số.")
        return value


class MessageResponse(BaseModel):
    message: str
    retry_after: int | None = None


class RegistrationVerifiedResponse(BaseModel):
    registration_token: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=1, description="Google ID token")

class PasswordResetRequest(BaseModel): email:str
class PasswordResetConfirmRequest(BaseModel):
    email:str;code:str=Field(pattern=r"^[0-9]{4}$");new_password:str=Field(min_length=8,max_length=128)
class PasswordChangeRequest(BaseModel):
    current_password:str;new_password:str=Field(min_length=8,max_length=128)


class AuthUserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    avatar_url: str | None = None
    is_new_user: bool
    system_role: str = "USER"
    admin_group_slugs: list[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserResponse
