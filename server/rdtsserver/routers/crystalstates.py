from typing import Optional

from fastapi import status, APIRouter
from sqlmodel import Session, select
from rdtsserver.db.tables import CrystalStateCreate, CrystalState, CrystalStateRead
from rdtsserver.dependencies import engine

router = APIRouter()


#@router.post("", status_code=200)
#def handle_create_crystal_state(crystal_state: CrystalStateCreate):
#    db_crystal_state, status_code = create_crystal_state(crystal_state)
#    return "Successfully created"


#@router.get("/{idx}", response_model=Optional[CrystalStateRead])
#def handle_read_crystal_state(idx: int):
#    with Session(engine) as session:
#        return session.exec(select(CrystalState).where(CrystalState.idx == idx)).one_or_none()


#@router.get("", response_model=list[CrystalStateRead])
#def handle_read_all_crystals_states():
#    with Session(engine) as session:
#        return session.exec(select(CrystalState)).all()


def create_crystal_state(crystal_state: CrystalStateCreate) -> (CrystalState, status):
    with Session(engine) as session:
        db_crystal_state = CrystalState.from_orm(crystal_state)
        session.add(db_crystal_state)
        session.commit()
        session.refresh(db_crystal_state)
        return db_crystal_state, status.HTTP_201_CREATED
