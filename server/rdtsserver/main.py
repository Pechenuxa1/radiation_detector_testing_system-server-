from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, Security, HTTPException, status, Response
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlmodel import Session, select

from server.rdtsserver.db.tables import RDTSDatabase, User
from server.rdtsserver.dependencies import engine, get_session
from server.rdtsserver.routers import assemblies, crystals, crystalstates, testsuites, testsuiteresults
from server.rdtsserver.utils.security import Token, authenticate_user, create_access_token, oauth2_scheme, pwd_context, \
    validate_token


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    RDTSDatabase.metadata.create_all(engine)
    yield


rdts_app = FastAPI(title="RDTS Server", version="1.0.1", lifespan=lifespan)
rdts_app.include_router(assemblies.router,
                        prefix="/assemblies",
                        tags=["assemblies"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(crystals.router,
                        prefix="/crystals",
                        tags=["crystals"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(crystalstates.router,
                        prefix="/crystalstates",
                        tags=["crystalstates"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(testsuites.router,
                        prefix="/testsuites",
                        tags=["testsuites"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(testsuiteresults.router,
                        prefix="/testsuiteresults",
                        tags=["testsuiteresults"],
                        dependencies=[Depends(get_session)])


@rdts_app.get("/health")
def health() -> str:
    return "Server is running!"


load_dotenv('server/rdtsserver/config.env')


@rdts_app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


class UserRegister(BaseModel):
    login: str
    password: str


@rdts_app.post("/sign_up", response_model=User)
async def sign_up(user: UserRegister):
    new_user = create_user(user)
    return new_user


def create_user(user: UserRegister) -> User:
    with Session(engine) as session:
        new_user = session.exec(select(User).where(User.login == user.login)).one_or_none()
        if new_user is not None:
            raise HTTPException(status_code=400, detail=f"User with login {user.login} already exists!")
        new_user = User(login=user.login, hashed_password=pwd_context.hash(user.password))
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user


@rdts_app.get("/private")
def private(token: Annotated[str, Depends(validate_token)]):
    return f"Token: {token}"
