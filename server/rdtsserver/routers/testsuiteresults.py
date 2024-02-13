from datetime import datetime
from typing import Optional
from fastapi import Response, status, APIRouter, UploadFile
from pydantic import Json
from sqlalchemy import select, JSON
from sqlmodel import Session, select
from starlette.responses import FileResponse, JSONResponse
from typing import Dict

from rdtsserver.db.tables import (TestSuiteResult, TestSuiteResultInfo, TestSuiteResultCreate, TestSuiteResultBase,
                                  TestSuite)
from rdtsserver.dependencies import engine

router = APIRouter()


@router.post("", status_code=207, response_model=Optional[TestSuiteResultCreate])
def handle_create_testsuiteresult(testsuite_idx: str,
                                  assembly_name: str,
                                  config: UploadFile,
                                  result: UploadFile,
                                  response: Response):
    db_testsuiteresult, response.status_code = create_testsuiteresult(testsuite_idx,
                                                                      assembly_name,
                                                                      config,
                                                                      result)
    return db_testsuiteresult


@router.get("/{idx}", response_model=Optional[TestSuiteResultInfo])
def handle_read_testsuiteresult_config(idx: int):
    with Session(engine) as session:
        return session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()

@router.get("/{idx}/config")
def handle_read_testsuiteresult(idx: int):
    with Session(engine) as session:
        db_testsuiteresult = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        return FileResponse(path=db_testsuiteresult.config_path,
                            filename=f"config-{db_testsuiteresult.assembly.name}-{db_testsuiteresult.timestamp}",
                            media_type='application/json')

@router.get("{idx}/result")
def handle_read_testsuiteresult(idx: int):
    with Session(engine) as session:
        db_testsuiteresult = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        return FileResponse(path=db_testsuiteresult.result_path,
                            filename=f"{db_testsuiteresult.assembly.name}-{db_testsuiteresult.timestamp}",
                            media_type='application/json')


@router.get("", response_model=list[TestSuiteResultInfo])
def handle_read_all_testsuiteresults():
    with Session(engine) as session:
        return session.exec(select(TestSuiteResult)).all()


def save_bytes_to_file(file_path, content: bytes):
    with open(file_path, "wb") as file:
        file.write(content)


def create_testsuiteresult(testsuite_idx: str,
                           assembly_name: str,
                           config: UploadFile,
                           result: UploadFile) -> (TestSuiteResult, status):
    with Session(engine) as session:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db_testsuiteresult = TestSuiteResult(testsuite_idx=testsuite_idx,
                                             assembly_name=assembly_name,
                                             timestamp=timestamp)
        session.add(db_testsuiteresult)
        session.commit()
        session.refresh(db_testsuiteresult)
        save_bytes_to_file(db_testsuiteresult.result_path, result.file.read())
        save_bytes_to_file(db_testsuiteresult.config_path, config.file.read())
        return db_testsuiteresult, status.HTTP_201_CREATED
