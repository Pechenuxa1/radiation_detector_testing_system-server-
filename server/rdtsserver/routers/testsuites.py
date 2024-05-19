import os
from datetime import datetime
from typing import Optional, Annotated
from fastapi import Response, status, APIRouter, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlmodel import Session, select
from server.rdtsserver.db.tables import TestSuite
from server.rdtsserver.dependencies import engine

from server.rdtsserver.db.tables import TestSuiteRead
from server.rdtsserver.utils.security import validate_access_token

from server.rdtsserver.utils.validator import validate_string

router = APIRouter()


@router.post("", status_code=207, response_model=int)
def handle_create_testsuite(user_login: Annotated[str, Depends(validate_access_token)],
                            name: str,
                            version: str,
                            zip_file: UploadFile,
                            response: Response,
                            timestamp: Optional[str] = None):
    name = validate_string(name, "Test suite name")
    version = validate_string(version, "Test suite version")
    db_testsuite, response.status_code = create_testsuite(name, version, zip_file, timestamp)
    return db_testsuite.idx


@router.get("/{name}", response_model=Optional[TestSuiteRead])
def handle_read_testsuite(user_login: Annotated[str, Depends(validate_access_token)], name: str):
    name = validate_string(value=name, object_error="Testsuite name")
    with (Session(engine) as session):
        testsuite = session.exec(select(TestSuite)
                                 .where(TestSuite.name == name)
                                 .order_by(TestSuite.version.desc())).first()
        if testsuite is None:
            raise HTTPException(status_code=400, detail=f"Test suite {name} not found!")
        return TestSuiteRead(
            idx=testsuite.idx,
            name=testsuite.name,
            version=testsuite.version,
            timestamp=testsuite.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        )


@router.delete("/{name}/{version}")
def handle_delete_testsuite(user_login: Annotated[str, Depends(validate_access_token)], name: str, version: str):
    name = validate_string(value=name, object_error="Testsuite name")
    with Session(engine) as session:
        testsuite: TestSuite = session.exec(select(TestSuite)
                                 .where(TestSuite.name == name)
                                 .where(TestSuite.version == version)).one_or_none()

        if testsuite is None:
            raise HTTPException(status_code=400, detail=f"Test suite {name} not found!")

        testsuites_other = session.exec(select(TestSuite)
                                 .where(TestSuite.name == name)
                                 .where(TestSuite.version != version)).all()

        if len(testsuites_other) == 0:
            for testsuiteresult in testsuite.testsuiteresults:
                os.remove(testsuiteresult.result_path)
                os.remove(testsuiteresult.config_path)
                session.delete(testsuiteresult)
                session.commit()

            os.remove(testsuite.path)

        session.delete(testsuite)
        session.commit()


@router.get("/download/{name}")
def handle_download_testsuite(user_login: Annotated[str, Depends(validate_access_token)], name: str):
    name = validate_string(value=name, object_error="Testsuite name")
    with (Session(engine) as session):
        testsuite: TestSuite = session.exec(select(TestSuite)
                                            .where(TestSuite.name == name)
                                            .order_by(TestSuite.version.desc())).first()
        if testsuite:
            timestamp = testsuite.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            return FileResponse(path=testsuite.path, filename=f"{testsuite.name}", media_type='application/zip')

        raise HTTPException(status_code=400, detail=f"Test suite {name} not found!")


@router.get("", response_model=list[TestSuiteRead])
def handle_read_all_testsuites(user_login: Annotated[str, Depends(validate_access_token)]):
    with Session(engine) as session:
        testsuites = session.exec(select(TestSuite)).all()
        testsuites_read = []
        for testsuite in testsuites:
            testsuites_read.append(TestSuiteRead(
                idx=testsuite.idx,
                name=testsuite.name,
                version=testsuite.version,
                timestamp=testsuite.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ))
        return testsuites_read


@router.get("/{start_date}/{end_date}", response_model=list[TestSuiteRead])
def handle_read_all_testsuites_during_the_time(user_login: Annotated[str, Depends(validate_access_token)], start_date: str, end_date: str):
    with Session(engine) as session:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        testsuites = session.exec(select(TestSuite).where(TestSuite.timestamp.between(start_date, end_date))).all()
        testsuites_read = []
        for testsuite in testsuites:
            testsuites_read.append(TestSuiteRead(
                idx=testsuite.idx,
                name=testsuite.name,
                version=testsuite.version,
                timestamp=testsuite.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ))
        return testsuites_read


def save_bytes_to_file(file_path, file: UploadFile):
    content = file.file.read()
    with open(file_path, "wb") as file:
        file.write(content)


def create_testsuite(name: str,
                     version: str,
                     zip_file: UploadFile,
                     timestamp: str) -> (TestSuite, status):
    with Session(engine) as session:
        status_code = status.HTTP_207_MULTI_STATUS
        db_testsuite = session.exec(select(TestSuite)
                                    .where(TestSuite.name == name)
                                    .where(TestSuite.version == version)).one_or_none()
        if db_testsuite is None:
            if timestamp is None:
                db_timestamp = datetime.now()
            else:
                db_timestamp = datetime.strptime(timestamp, '%Y-%m-%d%H:%M:%S')
            status_code = status.HTTP_201_CREATED
            db_testsuite = TestSuite(name=name,
                                     version=version,
                                     timestamp=db_timestamp)
            session.add(db_testsuite)
            session.commit()
            session.refresh(db_testsuite)
            os.mkdir(db_testsuite.results_path)
            save_bytes_to_file(db_testsuite.path, zip_file)
        return db_testsuite, status_code

