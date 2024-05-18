from datetime import datetime
from fastapi import APIRouter, status, HTTPException, Depends

from ..routers.crystalstates import create_crystal_state
from sqlalchemy.orm import Session
from typing import Optional, Annotated

from fastapi import Response
from sqlmodel import Session, select
from server.rdtsserver.db.tables import CrystalCreate, Crystal, CrystalRead, CrystalStateCreate, CrystalStatus, CrystalState

from server.rdtsserver.utils.validator import validate_CrystalCreate, validate_string

from server.rdtsserver.dependencies import engine
from ..utils.security import validate_access_token

router = APIRouter()


@router.post("", response_model=str)
def handle_create_crystal(user_login: Annotated[str, Depends(validate_access_token)], crystal: CrystalCreate, response: Response) -> str:
    crystal = validate_CrystalCreate(crystal)
    db_crystal, response.status_code = create_crystal(crystal)
    #if response.status_code == status.HTTP_207_MULTI_STATUS:
    #    pull_out_this_crystal_from_some_assembly(crystal.name, CrystalStatus.UNUSED)
    #    pull_out_some_crystal_from_this_assembly(crystal.assembly_name, crystal.place, CrystalStatus.UNUSED)
    #else:
        # TODO: сделать проверку полей assembly_name и place на null
        # TODO: crystalState создается всегда, убрать if-else
    #    db_crystal_state, status_code = create_crystal_state(CrystalStateCreate(
    #                                                            crystal_name=crystal.name,
    #                                                            assembly_name=crystal.assembly_name,
    #                                                            timestamp=str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    #                                                            place=crystal.place,
    #                                                            status=CrystalStatus.USED)
    #                                                        )
    return db_crystal.name


@router.get("/{name}", response_model=Optional[CrystalRead])
def handle_read_crystal(user_login: Annotated[str, Depends(validate_access_token)], name: str) -> Crystal:
    name = validate_string(value=name, object_error="Crystal name")
    with Session(engine) as session:
        crystal = session.exec(select(Crystal).where(Crystal.name == name)).one_or_none()
        if crystal is None:
            raise HTTPException(status_code=400, detail=f"Crystal {name} not found!")
        return crystal


@router.get("", response_model=list[CrystalRead])
def handle_read_all_crystals(user_login: Annotated[str, Depends(validate_access_token)]):
    with Session(engine) as session:
        return session.exec(select(Crystal)).all()


def create_crystal(crystal: CrystalCreate) -> (Crystal, status):
    with Session(engine) as session:
        pull_out_some_crystal_from_this_assembly(crystal.name, crystal.assembly_name, crystal.place, CrystalStatus.UNUSED)

        existing_crystal = session.exec(select(Crystal).where(Crystal.name == crystal.name)).one_or_none()
        if existing_crystal:
            pull_out_this_crystal_from_some_assembly(crystal.name, CrystalStatus.UNUSED)
            db_crystal = existing_crystal
            status_code = status.HTTP_207_MULTI_STATUS
        else:
            db_crystal = Crystal.from_orm(crystal)
            session.add(db_crystal)
            session.commit()
            session.refresh(db_crystal)
            status_code = status.HTTP_201_CREATED

        #pull_out_some_crystal_from_this_assembly(crystal.assembly_name, crystal.place, CrystalStatus.UNUSED)

        #db_crystal = Crystal.from_orm(crystal)
        #session.add(db_crystal)
        #session.commit()
        #session.refresh(db_crystal)
        create_crystal_state(CrystalStateCreate(
                                                crystal_name=crystal.name,
                                                assembly_name=crystal.assembly_name,
                                                timestamp=str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                                place=crystal.place,
                                                status=CrystalStatus.USED)
                                                )
        return db_crystal, status_code


def pull_out_this_crystal_from_some_assembly(crystal_name, new_status):
    with (Session(engine) as session):
        crystal_state = session.exec(select(CrystalState)
                                     .where(CrystalState.crystal_name == crystal_name)
                                     .where(CrystalState.status == CrystalStatus.USED)
                                     ).one_or_none()
        if crystal_state:
            crystal_state.status = new_status
            session.commit()


def pull_out_some_crystal_from_this_assembly(crystal_name, assembly_name, place, new_status):
    with Session(engine) as session:
        crystal_state = session.exec(select(CrystalState)
                                     .where(CrystalState.assembly_name == assembly_name)
                                     .where(CrystalState.place == place)
                                     .order_by(CrystalState.timestamp.desc())).first()

        if crystal_state and crystal_state.crystal_name != crystal_name:
            crystal_state.status = new_status
            session.commit()
