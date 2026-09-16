from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

Session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

#ORM模型
Base =  declarative_base()

def get_db():
    db = Session_local()

    try:
        yield db
    finally:
        db.close()