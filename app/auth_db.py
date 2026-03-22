from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATA_DIR = Path("./auth_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = "sqlite:///./auth_data/api_keys.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_auth_db():
    # Create schema lazily to avoid circular imports at module load
    from .auth_models import Base
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
