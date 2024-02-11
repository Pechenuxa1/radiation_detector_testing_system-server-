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
def handle_create_testsuiteresult(testsuite_name: str,
                                  testsuite_version: str,
                                  assembly_name: str,
                                  config: UploadFile,
                                  result: UploadFile,
                                  response: Response):
    db_testsuiteresult, response.status_code = create_testsuiteresult(testsuite_name,
                                                                      testsuite_version,
                                                                      assembly_name,
                                                                      config,
                                                                      result)
    return db_testsuiteresult


@router.get("/{testsuite_name}/{testsuite_version}/{assembly_name}", response_model=Optional[TestSuiteResultInfo])
def handle_read_testsuiteresult_config(testsuite_name: str, testsuite_version: str, assembly_name: str):
    with Session(engine) as session:
        testsuite = session.exec(select(TestSuite)
                                 .where(TestSuite.name == testsuite_name)
                                 .where(TestSuite.version == testsuite_version)).one_or_none()
        if testsuite is None:
            return None

        return session.exec(select(TestSuiteResult)
                            .where(TestSuiteResult.testsuite_idx == testsuite.idx)).one_or_none()


@router.get("/{testsuite_name}/{testsuite_version}/{assembly_name}/config")
def handle_read_testsuiteresult(testsuite_name: str, testsuite_version: str, assembly_name: str):
    with Session(engine) as session:
        testsuite = session.exec(select(TestSuite)
                                 .where(TestSuite.name == testsuite_name)
                                 .where(TestSuite.version == testsuite_version)).one_or_none()
        if testsuite is None:
            return None

        db_testsuiteresult = session.exec(select(TestSuiteResult)
                                          .where(TestSuiteResult.testsuite_idx == testsuite.idx)).one_or_none()
        return FileResponse(path=db_testsuiteresult.config_path,
                            filename=f"config-{db_testsuiteresult.assembly.name}-{db_testsuiteresult.timestamp}",
                            media_type='application/json')


@router.get("/{testsuite_name}/{testsuite_version}/{assembly_name}/result")
def handle_read_testsuiteresult(testsuite_name: str, testsuite_version: str, assembly_name: str):
    with Session(engine) as session:
        testsuite = session.exec(select(TestSuite)
                                 .where(TestSuite.name == testsuite_name)
                                 .where(TestSuite.version == testsuite_version)).one_or_none()
        if testsuite is None:
            return None

        db_testsuiteresult = session.exec(select(TestSuiteResult)
                                          .where(TestSuiteResult.testsuite_idx == testsuite.idx)).one_or_none()

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


def create_testsuiteresult(testsuite_name: str,
                           testsuite_version: str,
                           assembly_name: str,
                           config: UploadFile,
                           result: UploadFile) -> (TestSuiteResult, status):
    with Session(engine) as session:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        testsuite = session.exec(select(TestSuite)
                                 .where(TestSuite.name == testsuite_name)
                                 .where(TestSuite.version == testsuite_version)).one_or_none()
        if testsuite is None:
            return None, status.HTTP_400_BAD_REQUEST
        db_testsuiteresult = TestSuiteResult(testsuite_name=testsuite_name,
                                             testsuite_idx=testsuite.idx,
                                             testsuite_version=testsuite_version,
                                             assembly_name=assembly_name,
                                             timestamp=timestamp)
        session.add(db_testsuiteresult)
        session.commit()
        session.refresh(db_testsuiteresult)
        save_bytes_to_file(db_testsuiteresult.result_path, result.file.read())
        save_bytes_to_file(db_testsuiteresult.config_path, config.file.read())
        return db_testsuiteresult, status.HTTP_201_CREATED
