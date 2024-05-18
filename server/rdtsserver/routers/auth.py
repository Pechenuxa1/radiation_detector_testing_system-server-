import os
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from server.rdtsserver.dependencies import engine, ROLE_ADMIN

from server.rdtsserver.db.tables import User, Token
from server.rdtsserver.db.tables import UserRegister
from sqlmodel.orm.session import Session
from sqlmodel.sql.expression import select
from fastapi.exceptions import HTTPException

from server.rdtsserver.utils.security import pwd_context, authenticate_user, \
    create_access_token, create_refresh_token, validate_refresh_token, validate_access_token, get_user, check_role

router = APIRouter()


@router.post('/sign-up', status_code=status.HTTP_201_CREATED, response_model=User)
async def sign_up(user_login: Annotated[str, Depends(validate_access_token)], user: UserRegister):
    check_role(user_login, [ROLE_ADMIN])
    new_user = create_user(user)
    return new_user


def create_user(user: UserRegister) -> User:
    with Session(engine) as session:
        new_user = session.exec(select(User).where(User.login == user.login)).one_or_none()
        if new_user is not None:
            raise HTTPException(status_code=400, detail=f"User with login \"{user.login}\" already exists!")
        new_user = User(login=user.login, hashed_password=pwd_context.hash(user.password), role=user.role)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user


@router.post('/sign-in', status_code=status.HTTP_200_OK, response_model=Token)
async def sign_in(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.login, "scope": "access_token"}, expires_delta=timedelta(minutes=float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    )
    refresh_token = create_refresh_token(
        data={"sub": user.login, "scope": "refresh_token"}, expires_delta=timedelta(minutes=float(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")))
    )
    with Session(engine) as session:
        user.access_token = access_token
        user.refresh_token = refresh_token
        session.add(user)
        session.commit()
        session.refresh(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get('/refresh', status_code=status.HTTP_200_OK, response_model=Token)
def refresh_token(refresh_token: str):
    user_login = validate_refresh_token(refresh_token)

    access_token = create_access_token(
        data={"sub": user_login, "scope": "access_token"},
        expires_delta=timedelta(minutes=float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    )

    user = get_user(user_login)
    with Session(engine) as session:
        user.access_token = access_token
        session.add(user)
        session.commit()
        session.refresh(user)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/sign-out", status_code=status.HTTP_200_OK)
def sign_out(user_login: Annotated[str, Depends(validate_access_token)]):
    with Session(engine) as session:
        user = get_user(user_login)
        user.access_token = None
        user.refresh_token = None
        session.add(user)
        session.commit()
        session.refresh(user)


@router.get("/get-me")
def get_me(user_login: Annotated[str, Depends(validate_access_token)]):
    check_role(user_login, [ROLE_ADMIN])
    return f"User login: {user_login}"


@router.get("/get-users", response_model=list[str])
def get_users(user_login: Annotated[str, Depends(validate_access_token)]):
    check_role(user_login, [ROLE_ADMIN])
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        logins = []
        for user in users:
            logins.append(user.login)
        return logins



