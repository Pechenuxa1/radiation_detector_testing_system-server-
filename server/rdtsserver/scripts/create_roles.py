from sqlmodel.orm.session import Session
from sqlmodel import select

from server.rdtsserver.db.tables import Role, RoleName
from server.rdtsserver.dependencies import engine, ROLE_ADMIN, ROLE_ENGINEER

with Session(engine) as session:
    if session.exec(select(Role).where(Role.idx == ROLE_ADMIN)).one_or_none() is None:
        session.add(Role(idx=1, name=RoleName.ADMIN))
        session.commit()

    if session.exec(select(Role).where(Role.idx == ROLE_ENGINEER)).one_or_none() is None:
        session.add(Role(idx=2, name=RoleName.ENGINEER))
        session.commit()
