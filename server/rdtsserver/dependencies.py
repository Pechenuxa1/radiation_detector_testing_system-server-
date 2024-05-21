from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql+psycopg2://rdts:rdts@postgres:5432/rdtsdb", echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


ROLE_ADMIN = 1
ROLE_ENGINEER = 2
