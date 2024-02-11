from datetime import datetime
from typing import Optional

from fastapi import Response, status, APIRouter
from sqlalchemy import Integer
from sqlmodel import Session, select
from rdtsserver.db.tables import Assembly, AssemblyCreate, AssemblyRead, \
    CrystalCreate, CrystalStateCreate, CrystalStatus, CrystalState

from rdtsserver.dependencies import engine
from rdtsserver.routers.crystals import create_crystal
from rdtsserver.routers.crystalstates import create_crystal_state

router = APIRouter()


@router.post("", status_code=207, response_model=str)
def handle_create_assembly(assembly: AssemblyCreate, response: Response):
    db_assembly, response.status_code = create_assembly(assembly)
    return db_assembly.name


@router.get("/{name}", response_model=Optional[AssemblyRead])
def handle_read_assembly(name: str):
    with Session(engine) as session:
        return session.exec(select(Assembly).where(Assembly.name == name)).one_or_none()


@router.get("", response_model=list[AssemblyRead])
def handle_read_all_assemblies():
    with Session(engine) as session:
        return session.exec(select(Assembly)).all()


def create_assembly(assembly: AssemblyCreate) -> (Assembly, status):
    with Session(engine) as session:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status_code = status.HTTP_207_MULTI_STATUS
        db_assembly = session.exec(select(Assembly).where(Assembly.name == assembly.name)).one_or_none()
        if db_assembly is None:
            status_code = status.HTTP_201_CREATED
            db_assembly = Assembly.from_orm(assembly)
            session.add(db_assembly)
            session.commit()
            session.refresh(db_assembly)
        crystals: [str] = assembly.crystals

        for place, crystal_name in enumerate(crystals):
            if crystal_name:
                db_crystal, crystal_status_code = create_crystal(CrystalCreate(name=crystal_name))
                pull_out_this_crystal_from_some_assembly(db_crystal.name, CrystalStatus.UNUSED)
                pull_out_some_crystal_from_this_assembly(db_assembly.name, place, CrystalStatus.UNUSED)

                crystal_state = CrystalStateCreate(timestamp=str(timestamp),
                                                   crystal_name=db_crystal.name,
                                                   assembly_name=db_assembly.name,
                                                   place=place,
                                                   status=CrystalStatus.USED)
                db_crystal_state, crystal_state_status_code = create_crystal_state(crystal_state)
    return db_assembly, status_code


def pull_out_this_crystal_from_some_assembly(crystal_name, new_status):
    with (Session(engine) as session):
        crystal_state = session.exec(select(CrystalState)
                                     .where(CrystalState.crystal_name == crystal_name)
                                     .where(CrystalState.status == CrystalStatus.USED)
                                     ).one_or_none()
        if crystal_state:
            crystal_state.status = new_status
            session.commit()


def pull_out_some_crystal_from_this_assembly(assembly_name, place, new_status):
    with Session(engine) as session:
        crystal_state = session.exec(select(CrystalState)
                                     .where(CrystalState.assembly_name == assembly_name)
                                     .where(CrystalState.place == place)
                                     .order_by(CrystalState.timestamp.desc())).first()
        if crystal_state:
            crystal_state.status = new_status
            session.commit()
