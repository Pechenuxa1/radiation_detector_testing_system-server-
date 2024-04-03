from datetime import datetime

from fastapi import UploadFile
from sqlmodel import select

from sqlmodel import SQLModel, Session
from typing import Optional
from enum import Enum, auto
from sqlmodel import Field, Relationship
from sqlalchemy import DateTime

from server.rdtsserver.dependencies import engine


class RDTSDatabase(SQLModel):
    pass


class CrystalStatus(Enum):
    USED = auto()  # используется - используется в данный timestamp сборкой assembly_id.
    UNUSED = auto()  # не используется - использовался некоторой сборкой, но потом был удален или перемещен в другую
    DESTROYED = auto()  # уничтожен - не используется никакой сборкой. assembly_id и place отсутствует


# crystals_states_testsuiteresults = Table('crystal_states_testsuiteresults', RDTSDatabase.metadata,
#                                         Column('crystalstate_idx', Integer,
#                                                ForeignKey('crystals_states.idx')
#                                                ),
#                                         Column('testsuiteresult_idx', Integer,
#                                                ForeignKey('testsuiteresults.idx')
#                                                )
#                                         )

class CrystalStateTestsuiteresult(RDTSDatabase, table=True):
    __tablename__ = "crystalstate_testsuiteresult_table"
    idx: Optional[int] = Field(None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    crystalstate_idx: Optional[int] = Field(None, foreign_key="crystals_states.idx", primary_key=True)
    testsuiteresult_idx: Optional[int] = Field(None, foreign_key="testsuiteresults.idx", primary_key=True)


# ================= Assembly =================
class AssemblyBase(RDTSDatabase):
    name: str


class Assembly(AssemblyBase, table=True):
    __tablename__ = "assemblies"
    # idx: Optional[int] = Field(None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    name: str = Field(None, primary_key=True)
    crystals: list["CrystalState"] = Relationship(back_populates="assembly")

    # testsuiteresults: list["TestSuiteResult"] = Relationship(back_populates="assembly")

    @property
    def crystal_quantity(self) -> int:
        with (Session(engine) as session):
            # crystal_count = session.query(select(CrystalState).where(CrystalState.assembly_name == self.name)).count()
            crystal_state = session.exec(select(CrystalState)
                                         .where(CrystalState.assembly_name == self.name)
                                         .where(CrystalState.status == CrystalStatus.USED)
                                         .order_by(CrystalState.place.desc())
                                         ).first()
            if crystal_state is None:
                return 0
            return crystal_state.place + 1

    @property
    def current_crystals(self) -> list[Optional[str]]:
        return self.crystals_at_timestamp(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def crystals_at_timestamp(self, timestamp) -> list[Optional[str]]:
        crystals = []
        n = self.crystal_quantity
        for place in range(n):
            with Session(engine) as session:
                crystal_state = session.exec(select(CrystalState)
                                             .where(CrystalState.assembly_name == self.name)
                                             .where(CrystalState.place == place)
                                             .where(CrystalState.timestamp <= timestamp)
                                             .order_by(CrystalState.timestamp.desc())
                                             ).first()
                name = None
                if crystal_state and (crystal_state.status == CrystalStatus.USED):
                    crystal = session.exec(select(Crystal).where(Crystal.name == crystal_state.crystal_name)).first()
                    if crystal:
                        name = crystal.name
                crystals.append(name)
        return crystals


class AssemblyCreate(AssemblyBase):
    # name: str
    crystals: list[str]


class AssemblyRead(AssemblyBase):
    # idx: int
    name: str
    crystal_quantity: int
    current_crystals: list[Optional[str]]


# ================= Crystal =================

class CrystalBase(RDTSDatabase):
    name: str


class Crystal(CrystalBase, table=True):
    __tablename__ = "crystals"
    name: str = Field(None, primary_key=True)

    crystal_states: list["CrystalState"] = Relationship(back_populates="crystal")

    @property
    def current_assembly(self) -> Optional[str]:
        with Session(engine) as session:
            query = session.query(CrystalState).filter(CrystalState.crystal_name == self.name)
            query = query.order_by(CrystalState.timestamp.desc())
            crystal_state = query.first()
            if crystal_state and crystal_state.status == CrystalStatus.USED:
                assembly = session.exec(
                    select(Assembly).where(Assembly.name == crystal_state.assembly_name)).one_or_none()
                if assembly:
                    return assembly.name
            return None

    @property
    def current_status(self) -> Optional[CrystalStatus]:
        with Session(engine) as session:
            query = session.query(CrystalState).filter(CrystalState.crystal_name == self.name)
            query = query.order_by(CrystalState.timestamp.desc())
            crystal_state = query.first()
            return crystal_state.status


class CrystalCreate(CrystalBase):
    name: str
    assembly_name: str
    place: int


class CrystalRead(CrystalBase):
    name: str
    current_assembly: Optional[str]
    current_status: Optional["CrystalStatus"]


# ================= CrystalState =================
class CrystalStateBase(RDTSDatabase):
    # idx: int
    crystal_name: str
    assembly_name: str
    timestamp: str
    place: int
    status: CrystalStatus


class CrystalState(CrystalStateBase, table=True):
    __tablename__ = "crystals_states"
    idx: int = Field(None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    crystal_name: str = Field(foreign_key="crystals.name")
    assembly_name: str = Field(foreign_key="assemblies.name")
    timestamp: str = Field(sa_type=DateTime)

    # testsuiteresults: list["TestSuiteResult"] = relationship("TestSuiteResult",
    #                                                         secondary=crystals_states_testsuiteresults,
    #                                                         back_populates="crystals")
    testsuiteresults: list["TestSuiteResult"] = Relationship(back_populates="crystal_states",
                                                             link_model=CrystalStateTestsuiteresult
                                                             )
    assembly: Assembly = Relationship(back_populates="crystals")
    crystal: Crystal = Relationship(back_populates="crystal_states")


class CrystalStateCreate(CrystalStateBase):
    pass


class CrystalStateRead(CrystalStateBase):
    pass


# ================= TestSuite =================

class TestSuiteBase(RDTSDatabase):
    name: str
    version: str


class TestSuite(TestSuiteBase, table=True):
    __tablename__ = "testsuites"
    idx: Optional[int] = Field(None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    name: str = Field()
    version: str = Field()
    timestamp: str

    testsuiteresults: list["TestSuiteResult"] = Relationship(back_populates="testsuite")

    @property
    def versions(self) -> list[str]:
        with Session(engine) as session:
            testsuites = session.exec(select(TestSuite).where(TestSuite.name == self.name)).all()
            return [testsuite.name for testsuite in testsuites]

    @property
    def path(self) -> str:
        return f"/testsuites/{self.name}_v{self.version.replace('.', '-')}.zip"

    @property
    def results_path(self) -> str:
        return f"/results/{self.name}_v{self.version.replace('.', '-')}"


class TestSuiteRead(TestSuiteBase):
    idx: int


# ================= TestResult =================

# class TestResultBase(RDTSDatabase):
#    testsuiteresult_idx: int
#    name: str
#    result: str


# class TestResult(TestResultBase, table=True):
#    __tablename__ = "testresults"
#    testsuiteresult_idx: int = Field(primary_key=True, foreign_key="testsuiteresults.idx")
#    name: str = Field(primary_key=True)
#
#    testsuiteresult: "TestSuiteResult" = Relationship(back_populates="testsresults")

# class TestResultCreate(TestResultBase):
#    pass
#    result: JSON


# ================= TestSuiteResult =================
class TestSuiteResultBase(RDTSDatabase):
    # testsuite_name: str
    # testsuite_version: str
    testsuite_idx: int
    # crystal_name: str
    timestamp: str


#    params: JSON


class TestSuiteResult(TestSuiteResultBase, table=True):
    __tablename__ = "testsuiteresults"
    idx: int = Field(None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    # testsuite_name: str = Field(foreign_key="testsuites.name")
    # testsuite_version: str = Field(foreign_key="testsuites.version")
    testsuite_idx: int = Field(foreign_key="testsuites.idx")
    # assembly_name: str = Field(foreign_key="assemblies.name")
    # crystal_name: str = Field(foreign_key="crystals.name")
    timestamp: str = Field(sa_type=DateTime)

    #    testsresults: list[TestResult] = Relationship(back_populates="testsuiteresult")
    testsuite: TestSuite = Relationship(back_populates="testsuiteresults")
    # assembly: Assembly = Relationship(back_populates="testsuiteresults")
    # crystals: list["CrystalState"] = relationship("CrystalState",
    #                                              secondary=crystals_states_testsuiteresults,
    #                                              back_populates="testsuiteresults")
    crystal_states: list["CrystalState"] = Relationship(back_populates="testsuiteresults",
                                                        link_model=CrystalStateTestsuiteresult
                                                        )

    @property
    def result_path(self) -> str:
        return f"{self.testsuite.results_path}/{str(self.testsuite_idx)}-{self.timestamp}.json"

    @property
    def config_path(self) -> str:
        return f"{self.testsuite.results_path}/config-{str(self.testsuite_idx)}-{self.timestamp}.json"


class TestSuiteResultCreate(TestSuiteResultBase):
    pass


class TestSuiteResultInfo(TestSuiteResultBase):
    idx: int
    assembly_name: str


# Порядок сохранения результатов тестов (Клиент):
# Запрос на обновление/создание сборки (+ получаем id)
# Запрос на обновление/создание набора тестов (+ получаем id)
# Запрос на создание TestSuiteResult

# Порядок сохранения набора тестов (Сервер):
# Что получаем? название, zip c python модулем

# Порядок сохранения результатов набора тестов (Сервер):


class UserRegister(RDTSDatabase):
    login: str
    password: str


class User(RDTSDatabase, table=True):
    __tablename__ = "users"
    idx: int = Field(None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    login: str = Field()
    hashed_password: str = Field()
    role: str = Field()
    access_token: str = Field(default=None)
    refresh_token: str = Field(default=None)


class Role(RDTSDatabase, table=True):
    __tablename__ = "roles"
    idx: int = Field(None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    name: str = Field()


class Token(RDTSDatabase):
    access_token: str
    refresh_token: str
