import os
from datetime import datetime
from typing import Optional
from fastapi import Response, status, APIRouter, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlmodel import Session, select
from rdtsserver.db.tables import TestSuite
from rdtsserver.dependencies import engine

from rdtsserver.db.tables import TestSuiteRead

router = APIRouter()


@router.post("", status_code=207, response_model=int)
def handle_create_testsuite(name: str,
                            version: str,
                            zip_file: UploadFile,
                            response: Response):
    db_testsuite, response.status_code = create_testsuite(name, version, zip_file)
    return db_testsuite.idx


@router.get("/{name}", response_model=Optional[TestSuiteRead])
def handle_read_testsuite(name: str):
    with (Session(engine) as session):
        return session.exec(select(TestSuite)
                                .where(TestSuite.name == name)
                                .order_by(TestSuite.version.desc())).first()


@router.get("/download/{name}")
def handle_download_testsuite(name: str):
    with (Session(engine) as session):
        testsuite: TestSuite = session.exec(select(TestSuite)
                                                .where(TestSuite.name == name)
                                                .order_by(TestSuite.version.desc())).first()
        if testsuite:
            return FileResponse(path=testsuite.path, filename=f"{testsuite.name}", media_type='application/zip')
        return None


@router.get("", response_model=list[TestSuiteRead])
def handle_read_all_testsuites():
    with Session(engine) as session:
        return session.exec(select(TestSuite)).all()


def save_bytes_to_file(file_path, file: UploadFile):
    content = file.file.read()
    with open(file_path, "wb") as file:
        file.write(content)


def create_testsuite(name: str,
                     version: str,
                     zip_file: UploadFile) -> (TestSuite, status):
    with Session(engine) as session:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status_code = status.HTTP_207_MULTI_STATUS
        db_testsuite = session.exec(select(TestSuite)
                                    .where(TestSuite.name == name)
                                    .where(TestSuite.version == version)).one_or_none()
        if db_testsuite is None:
            status_code = status.HTTP_201_CREATED
            db_testsuite = TestSuite(name=name,
                                     version=version,
                                     timestamp=timestamp)
            session.add(db_testsuite)
            session.commit()
            session.refresh(db_testsuite)
            os.mkdir(db_testsuite.results_path)
            save_bytes_to_file(db_testsuite.path, zip_file)
        return db_testsuite, status_code
