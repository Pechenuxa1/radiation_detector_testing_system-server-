from datetime import datetime
from typing import Optional
from fastapi import Response, status, APIRouter, UploadFile
from pydantic import Json
from sqlalchemy import select, JSON
from sqlmodel import Session, select
from starlette.responses import FileResponse, JSONResponse
from typing import Dict

from rdtsserver.db.tables import TestSuiteResult, TestSuiteResultInfo
from rdtsserver.dependencies import engine


router = APIRouter()


@router.post("", status_code=207, response_model=int)
def handle_create_testsuiteresult(testsuite_idx: int,
                                  assembly_idx: int,
                                  config: UploadFile,
                                  result: UploadFile,
                                  response: Response):
    db_testsuiteresult, response.status_code = create_testsuiteresult(testsuite_idx,
                                                                      assembly_idx,
                                                                      config,
                                                                      result)
    return db_testsuiteresult.idx

@router.get("/{idx}", response_model=Optional[TestSuiteResultInfo])
def handle_read_testsuiteresult_config(idx: int):
    with Session(engine) as session:
        return session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
@router.get("/config/{idx}")
def handle_read_testsuiteresult(idx: int):
    with Session(engine) as session:
        db_testsuiteresut = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        return FileResponse(path=db_testsuiteresut.config_path,
                            filename=f"config-{db_testsuiteresut.assembly.name}-{db_testsuiteresut.timestamp}",
                            media_type='application/json')
@router.get("/result/{idx}")
def handle_read_testsuiteresult(idx: int):
    with Session(engine) as session:
        db_testsuiteresut = session.exec(select(TestSuiteResult).where(TestSuiteResult.idx == idx)).one_or_none()
        return FileResponse(path=db_testsuiteresut.result_path,
                            filename=f"{db_testsuiteresut.assembly.name}-{db_testsuiteresut.timestamp}",
                            media_type='application/json')


@router.get("", response_model=list[TestSuiteResultInfo])
def handle_read_all_testsuiteresults():
    with Session(engine) as session:
        return session.exec(select(TestSuiteResult)).all()


def save_bytes_to_file(file_path, content: bytes):
    with open(file_path, "wb") as file:
        file.write(content)


def create_testsuiteresult(testsuite_idx: int,
                           assembly_idx: int,
                           config: UploadFile,
                           result: UploadFile) -> (TestSuiteResult, status):
    with Session(engine) as session:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db_testsuiteresult = TestSuiteResult(testsuite_idx=testsuite_idx,
                                             assembly_idx=assembly_idx,
                                             timestamp=timestamp)
        session.add(db_testsuiteresult)
        session.commit()
        session.refresh(db_testsuiteresult)
        save_bytes_to_file(db_testsuiteresult.result_path, result.file.read())
        save_bytes_to_file(db_testsuiteresult.config_path, config.file.read())
        return db_testsuiteresult, status.HTTP_201_CREATED
