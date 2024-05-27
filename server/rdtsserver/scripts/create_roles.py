from sqlmodel.orm.session import Session
from sqlmodel import select

from server.rdtsserver.db.tables import Role, RoleName
from server.rdtsserver.dependencies import engine, ROLE_ADMIN, ROLE_ENGINEER, ROLE_USER

with Session(engine) as session:
    if session.exec(select(Role).where(Role.idx == ROLE_ADMIN)).one_or_none() is None:
        session.add(Role(idx=ROLE_ADMIN, name=RoleName.ADMIN))
        session.commit()

    if session.exec(select(Role).where(Role.idx == ROLE_ENGINEER)).one_or_none() is None:
        session.add(Role(idx=ROLE_ENGINEER, name=RoleName.ENGINEER))
        session.commit()

    if session.exec(select(Role).where(Role.idx == ROLE_USER)).one_or_none() is None:
        session.add(Role(idx=ROLE_USER, name=RoleName.USER))
        session.commit()
