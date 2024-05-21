from datetime import datetime
from typing import Optional, Annotated

from fastapi import Response, status, APIRouter, HTTPException, Depends
from sqlalchemy import func
from sqlmodel import Session, select
from server.rdtsserver.db.tables import Assembly, AssemblyCreate, AssemblyRead, \
    CrystalCreate, Period, CrystalState, CrystalStatus
from server.rdtsserver.dependencies import engine
from server.rdtsserver.routers.crystals import create_crystal
from server.rdtsserver.utils.security import validate_access_token
from server.rdtsserver.utils.validator import validate_string, validate_AssemblyCreate

router = APIRouter()


@router.post("", status_code=207, response_model=str)
def handle_create_assembly(user_login: Annotated[str, Depends(validate_access_token)], assembly: AssemblyCreate, response: Response):
    assembly = validate_AssemblyCreate(assembly=assembly)
    db_assembly, response.status_code = create_assembly(assembly)
    return db_assembly.name


@router.get("/{name}", response_model=Optional[AssemblyRead])
def handle_read_assembly(user_login: Annotated[str, Depends(validate_access_token)], name: str):
    name = validate_string(value=name, object_error="Assembly name")
    with Session(engine) as session:
        assembly = session.exec(select(Assembly).where(Assembly.name == name)).one_or_none()
        if assembly is None:
            raise HTTPException(status_code=400, detail=f"Assembly {name} not found!")
        return AssemblyRead(
            name=assembly.name,
            crystal_quantity=assembly.crystal_quantity,
            current_crystals=assembly.current_crystals,
            timestamp=assembly.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        )


@router.delete("/{name}")
def handle_delete_assembly(user_login: Annotated[str, Depends(validate_access_token)], name: str):
    name = validate_string(value=name, object_error="Assembly name")
    with Session(engine) as session:
        assembly: Assembly = session.exec(select(Assembly).where(Assembly.name == name)).one_or_none()

        if assembly is None:
            raise HTTPException(status_code=400, detail=f"Assembly with name {name} not found!")

        delete_crystal_states(assembly)
        session.delete(assembly)
        session.commit()


@router.get("", response_model=list[AssemblyRead])
def handle_read_all_assemblies(user_login: Annotated[str, Depends(validate_access_token)]):
    with Session(engine) as session:
        assemblies = session.exec(select(Assembly)).all()
        assemblies_read = []
        for assembly in assemblies:
            assemblies_read.append(AssemblyRead(
                name=assembly.name,
                crystal_quantity=assembly.crystal_quantity,
                current_crystals=assembly.current_crystals,
                timestamp=assembly.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ))
        return assemblies_read


@router.get("/{start_date}/{end_date}", response_model=list[AssemblyRead])
def handle_read_all_assemblies_during_the_time(user_login: Annotated[str, Depends(validate_access_token)], start_date: str, end_date: str):
    with Session(engine) as session:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(microsecond=0)
        end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(microsecond=0)
        results = session.query(
            CrystalState.assembly_name,
            CrystalState.timestamp,
            func.array_agg(CrystalState.crystal_name)
        ).where(
            CrystalState.timestamp.between(start_date, end_date)
        ).group_by(CrystalState.assembly_name, CrystalState.timestamp).all()
        assemblies_read = []
        for assembly_name, timestamp, crystal_names in results:
            print(f"Assembly read: {assembly_name, timestamp, crystal_names}")
            if assembly_name is not None:
                assemblies_read.append(AssemblyRead(
                    name=assembly_name,
                    crystal_quantity=len(crystal_names),
                    current_crystals=crystal_names,
                    timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S")
                ))
        return assemblies_read


def create_assembly(assembly: AssemblyCreate) -> (Assembly, status):
    with Session(engine) as session:
        status_code = status.HTTP_207_MULTI_STATUS
        db_assembly = session.exec(select(Assembly).where(Assembly.name == assembly.name).where(Assembly.timestamp == datetime.strptime(assembly.timestamp, '%Y-%m-%d %H:%M:%S').replace(microsecond=0))).one_or_none()
        if db_assembly:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Assembly with name {assembly.name} and time {assembly.timestamp} already exists!")
        db_assembly = session.exec(select(Assembly).where(Assembly.name == assembly.name)).one_or_none()
        if assembly.timestamp is None:
            timestamp = datetime.now().replace(microsecond=0)
        else:
            timestamp = datetime.strptime(assembly.timestamp, '%Y-%m-%d %H:%M:%S').replace(microsecond=0)

        if db_assembly is None:
            status_code = status.HTTP_201_CREATED
            db_assembly = Assembly(name=assembly.name, timestamp=timestamp)
            #db_assembly = Assembly.from_orm(assembly)
            session.add(db_assembly)
            session.commit()
            session.refresh(db_assembly)
        crystals: [str] = assembly.crystals

        for place, crystal_name in enumerate(crystals):
            if crystal_name:
                db_crystal, crystal_status_code = create_crystal(CrystalCreate(
                    name=crystal_name,
                    assembly_name=assembly.name,
                    place=place),
                timestamp
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


def delete_crystal_states(assembly: Assembly):
    with Session(engine) as session:
        crystal_states = session.exec(select(CrystalState)
                                      .where(CrystalState.assembly_name == assembly.name)
                                      .where(CrystalState.status == CrystalStatus.USED))

        for crystal_state in crystal_states:
            crystal_state.status = CrystalStatus.UNUSED
        session.commit()

