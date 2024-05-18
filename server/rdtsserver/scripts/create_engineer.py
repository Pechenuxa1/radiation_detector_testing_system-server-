from sqlmodel.orm.session import Session
from sqlmodel import select

from server.rdtsserver.db.tables import User
from server.rdtsserver.dependencies import engine, ROLE_ENGINEER
from server.rdtsserver.utils.security import pwd_context
from fastapi.exceptions import HTTPException

engineer = User(login="engineer", hashed_password=pwd_context.hash("engineer"), role=ROLE_ENGINEER)

with Session(engine) as session:
    user = session.exec(select(User).where(User.login == engineer.login)).one_or_none()
    if user is None:
        session.add(engineer)
        session.commit()
        session.refresh(engineer)