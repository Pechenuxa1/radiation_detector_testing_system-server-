from fastapi import APIRouter, status
from sqlalchemy.orm import Session
from typing import Optional

from fastapi import Response
from sqlmodel import Session, select
from rdtsserver.db.tables import CrystalCreate, Crystal, CrystalRead

from rdtsserver.dependencies import engine

router = APIRouter()


@router.post("", response_model=str)
def handle_create_crystal(crystal: CrystalCreate, response: Response) -> str:
    db_crystal, response.status_code = create_crystal(crystal)
    return db_crystal.name


@router.get("/{name}", response_model=Optional[CrystalRead])
def handle_read_crystal(name: str) -> Crystal:
    with Session(engine) as session:
        return session.exec(select(Crystal).where(Crystal.name == name)).one_or_none()


@router.get("", response_model=list[CrystalRead])
def handle_read_all_crystals():
    with Session(engine) as session:
        return session.exec(select(Crystal)).all()


def create_crystal(crystal: CrystalCreate) -> (Crystal, status):
    with Session(engine) as session:
        existing_crystal = session.exec(select(Crystal).where(Crystal.name == crystal.name)).one_or_none()
        if existing_crystal:
            return existing_crystal, status.HTTP_207_MULTI_STATUS

        db_crystal = Crystal.from_orm(crystal)
        session.add(db_crystal)
        session.commit()
        session.refresh(db_crystal)
        return db_crystal, status.HTTP_201_CREATED
