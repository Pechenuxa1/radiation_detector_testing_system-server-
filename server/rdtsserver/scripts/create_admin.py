from sqlmodel.orm.session import Session
from sqlmodel import select

from server.rdtsserver.db.tables import User
from server.rdtsserver.dependencies import engine, ROLE_ADMIN
from server.rdtsserver.utils.security import pwd_context
from fastapi.exceptions import HTTPException

admin = User(login="admin", hashed_password=pwd_context.hash("admin"), role=ROLE_ADMIN)

with Session(engine) as session:
    user = session.exec(select(User).where(User.login == admin.login)).one_or_none()
    if user is None:
        session.add(admin)
        session.commit()
        session.refresh(admin)

