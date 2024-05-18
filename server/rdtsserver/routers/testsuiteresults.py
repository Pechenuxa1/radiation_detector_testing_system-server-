import os
from datetime import datetime
from typing import Optional, Annotated
from fastapi import Response, status, APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy import select, and_, func
from sqlmodel import Session, select
from starlette.responses import FileResponse

from server.rdtsserver.db.tables import (TestSuiteResult, TestSuiteResultInfo, TestSuiteResultCreate, CrystalState)
from server.rdtsserver.dependencies import engine
from server.rdtsserver.utils.security import validate_access_token
from server.rdtsserver.utils.validator import validate_positive_number, validate_string

router = APIRouter()


@router.post("", status_code=207, response_model=int)
def handle_create_testsuiteresult(user_login: Annotated[str, Depends(validate_access_token)],
                                  testsuite_idx: int,
                                  assembly_name: str,
                                  config: UploadFile,
                                  result: UploadFile,
                                  response: Response,
                                  timestamp: Optional[str] = None):
    validate_positive_number(testsuite_idx, "Test suite id")
    assembly_name = validate_string(assembly_name, "Assembly name")
    db_testsuiteresult, response.status_code = create_testsuiteresult(testsuite_idx,
                                                                      assembly_name,
                                                                      config,
                                                                      result,
                                                                      timestamp)
    # tsr = TestSuiteResultCreate(testsuite_idx=testsuite_idx, timestamp=str(db_testsuiteresult.timestamp))
    return db_testsuiteresult.idx


@router.get("/{idx}", response_model=Optional[TestSuiteResultInfo])
def handle_read_testsuiteresult(user_login: Annotated[str, Depends(validate_access_token)], idx: int):
    validate_positive_number(idx, "Test suite results id")
    with Session(engine) as session:
        tsr = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        if tsr is None:
            raise HTTPException(status_code=400, detail=f"Test suite result with id {idx} not found!")
        tsr_info = TestSuiteResultInfo(
            idx=tsr.idx,
            assembly_name=tsr.crystal_states[0].assembly_name,
            timestamp=tsr.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            testsuite_idx=tsr.testsuite_idx,
            testsuite_name=tsr.testsuite.name
        )
        return tsr_info


@router.delete("/{idx}")
def handle_delete_testsuiteresult(user_login: Annotated[str, Depends(validate_access_token)], idx: int):
    validate_positive_number(idx, "Test suite results id")
    with Session(engine) as session:
        tsr = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        if tsr is None:
            raise HTTPException(status_code=400, detail=f"Test suite result with id {idx} not found!")

        os.remove(tsr.result_path)
        os.remove(tsr.config_path)
        session.delete(tsr)
        session.commit()


@router.get("/{idx}/config")
def handle_read_testsuiteresult_config(user_login: Annotated[str, Depends(validate_access_token)], idx: int):
    validate_positive_number(idx, "Test suite results id")
    with Session(engine) as session:
        db_testsuiteresult = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        if db_testsuiteresult is None:
            raise HTTPException(status_code=400, detail=f"Test suite result with id {idx} not found!")
        return FileResponse(path=db_testsuiteresult.config_path,
                            filename=f"config-{db_testsuiteresult.idx}-{db_testsuiteresult.timestamp}",
                            media_type='application/json')


@router.get("{idx}/result")
def handle_read_testsuiteresult_result(user_login: Annotated[str, Depends(validate_access_token)], idx: int):
    validate_positive_number(idx, "Test suite results id")
    with Session(engine) as session:
        db_testsuiteresult = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        if db_testsuiteresult is None:
            raise HTTPException(status_code=400, detail=f"Test suite result with id {idx} not found!")

        return FileResponse(path=db_testsuiteresult.result_path,
                            filename=f"{db_testsuiteresult.idx}-{db_testsuiteresult.timestamp}",
                            media_type='application/json')


@router.get("", response_model=list[TestSuiteResultInfo])
def handle_read_all_testsuiteresults(user_login: Annotated[str, Depends(validate_access_token)]):
    with Session(engine) as session:
        testsuiteresults = session.exec(select(TestSuiteResult)).all()
        tsr_info = []
        for tsr in testsuiteresults:
            tsr_info.append(
                TestSuiteResultInfo(
                    idx=tsr.idx,
                    assembly_name=tsr.crystal_states[0].assembly_name,
                    timestamp=tsr.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    testsuite_idx=tsr.testsuite_idx,
                    testsuite_name=tsr.testsuite.name
                )
            )
        #    tsr.timestamp = str(tsr.timestamp)
        return tsr_info


@router.get("/{start_date}/{end_date}", response_model=list[TestSuiteResultInfo])
def handle_read_all_testsuiteresults_during_the_time(user_login: Annotated[str, Depends(validate_access_token)], start_date: str, end_date: str):
    with Session(engine) as session:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        testsuiteresults = session.exec(select(TestSuiteResult).where(TestSuiteResult.timestamp.between(start_date, end_date)))
        tsr_info = []
        for tsr in testsuiteresults:
            tsr_info.append(
                TestSuiteResultInfo(
                    idx=tsr.idx,
                    assembly_name=tsr.crystal_states[0].assembly_name,
                    timestamp=tsr.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    testsuite_idx=tsr.testsuite_idx,
                    testsuite_name=tsr.testsuite.name
                )
            )
        #    tsr.timestamp = str(tsr.timestamp)
        return tsr_info


def save_bytes_to_file(file_path, content: bytes):
    with open(file_path, "wb") as file:
        file.write(content)


def create_testsuiteresult(user_login: Annotated[str, Depends(validate_access_token)],
                           testsuite_idx: int,
                           assembly_name: str,
                           config: UploadFile,
                           result: UploadFile,
                           timestamp: str) -> (TestSuiteResult, status):
    with (Session(engine) as session):
        subquery = (session.query(
            CrystalState.crystal_name,
            func.max(CrystalState.timestamp).label('max_time')
        ).group_by(CrystalState.crystal_name).subquery())

        query = (
            session.query(CrystalState)
            .join(subquery, and_(CrystalState.crystal_name == subquery.c.crystal_name,
                                 CrystalState.timestamp == subquery.c.max_time,
                                 CrystalState.assembly_name == assembly_name))
        )

        crystals = query.all()

        if not crystals:
            raise HTTPException(status_code=400, detail=f"Crystals in assembly {assembly_name} not found!")

        if timestamp is None:
            db_timestamp = datetime.now()
        else:
            db_timestamp = datetime.strptime(timestamp, '%Y-%m-%d%H:%M:%S')

        db_testsuiteresult = TestSuiteResult(testsuite_idx=testsuite_idx,
                                             crystal_states=crystals,
                                             timestamp=db_timestamp
                                             )
        session.add(db_testsuiteresult)
        session.commit()
        session.refresh(db_testsuiteresult)
        save_bytes_to_file(db_testsuiteresult.result_path, result.file.read())
        save_bytes_to_file(db_testsuiteresult.config_path, config.file.read())
        return db_testsuiteresult, status.HTTP_201_CREATED
