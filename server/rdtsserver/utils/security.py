import os
from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from pydantic import BaseModel
from starlette import status

from server.rdtsserver.db.tables import User
from server.rdtsserver.dependencies import engine
from sqlmodel import Session, select
from passlib.context import CryptContext
from jose import JWTError, jwt

'''
api_key_header = APIKeyHeader(name="api-key", auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key == os.getenv("API_KEY"):
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
'''


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(login: str):
    with Session(engine) as session:
        user: User = session.exec(select(User).where(User.login == login)).one_or_none()
        if user is not None:
            return user


def authenticate_user(login: str, password: str):
    user = get_user(login)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return encoded_jwt


def validate_token(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return token



