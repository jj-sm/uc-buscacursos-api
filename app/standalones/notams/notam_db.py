import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL_N = os.getenv("NOTAMS_DB_URL", "sqlite:///./data/notams.db")

engine_n = create_engine(
    DATABASE_URL_N, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_n)


def get_db_n():
    db_n = SessionLocal()
    try:
        yield db_n
    finally:
        db_n.close()
