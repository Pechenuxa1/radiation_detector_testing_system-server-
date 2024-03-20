import os
from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from server.rdtsserver.db.tables import User
from server.rdtsserver.dependencies import engine
from sqlmodel import Session, select
from passlib.context import CryptContext
from jose import JWTError, jwt


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sign_in")


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
    encoded_jwt = jwt.encode(to_encode, os.getenv("ACCESS_TOKEN_SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(float(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("REFRESH_TOKEN_SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return encoded_jwt


def validate_access_token(token: Annotated[str, Depends(oauth2_scheme)]):
    credential_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = jwt.decode(token, os.getenv("ACCESS_TOKEN_SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        if payload['scope'] != "access_token" or payload['sub'] is None:
            raise credential_exception
        user = get_user(payload['sub'])
        if user.access_token != token:
            return credential_exception
    except JWTError:
        raise credential_exception
    return payload['sub']


def validate_refresh_token(token: Annotated[str, Depends(oauth2_scheme)]):
    credential_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = jwt.decode(token, os.getenv("REFRESH_TOKEN_SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        if payload['scope'] != "refresh_token" or payload['sub'] is None:
            raise credential_exception
        user = get_user(payload['sub'])
        if user.refresh_token != token:
            return credential_exception
    except JWTError:
        raise credential_exception
    return payload['sub']

