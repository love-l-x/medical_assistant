from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

# PostgresSQL 会话管理数据库
postgres_engine = create_engine(
    settings.POSTGRES_SESSION_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

postgres_Session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=postgres_engine
)

#ORM模型
PostgresBase =  declarative_base()

def get_postgres_db():
    db = postgres_Session_local()

    try:
        yield db
    finally:
        db.close()
