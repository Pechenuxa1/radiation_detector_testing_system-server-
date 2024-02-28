from datetime import datetime
from typing import Optional

from fastapi import Response, status, APIRouter, HTTPException
from sqlmodel import Session, select
from server.rdtsserver.db.tables import Assembly, AssemblyCreate, AssemblyRead, \
    CrystalCreate, CrystalStateCreate, CrystalStatus
from server.rdtsserver.dependencies import engine
from server.rdtsserver.routers.crystals import create_crystal, pull_out_this_crystal_from_some_assembly, \
    pull_out_some_crystal_from_this_assembly
from server.rdtsserver.routers.crystalstates import create_crystal_state
from server.rdtsserver.utils.validator import validate_string, validate_AssemblyCreate

router = APIRouter()


@router.post("", status_code=207, response_model=str)
def handle_create_assembly(assembly: AssemblyCreate, response: Response):
    assembly = validate_AssemblyCreate(assembly=assembly)
    db_assembly, response.status_code = create_assembly(assembly)
    return db_assembly.name


@router.get("/{name}", response_model=Optional[AssemblyRead])
def handle_read_assembly(name: str):
    name = validate_string(value=name, object_error="Assembly name")
    with Session(engine) as session:
        assembly = session.exec(select(Assembly).where(Assembly.name == name)).one_or_none()
        if assembly is None:
            raise HTTPException(status_code=400, detail=f"Assembly {name} not found!")
        return assembly


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
                db_crystal, crystal_status_code = create_crystal(CrystalCreate(
                    name=crystal_name,
                    assembly_name=assembly.name,
                    place=place)
                )

                #pull_out_this_crystal_from_some_assembly(crystal_name, CrystalStatus.UNUSED)
                #pull_out_some_crystal_from_this_assembly(crystal_name, db_assembly.name, place, CrystalStatus.UNUSED)

                #create_crystal_state(CrystalStateCreate(
                #    timestamp=str(timestamp),
                #    crystal_name=db_crystal.name,
                #    assembly_name=db_assembly.name,
                #    place=place,
                #    status=CrystalStatus.USED)
                #)

    return db_assembly, status_code
