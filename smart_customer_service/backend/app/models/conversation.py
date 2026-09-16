from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func

from app.database.postgres import PostgresBase

"""PostgresSQL会话模型"""
class Conversation(PostgresBase):

    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True, index=True)

    user_id = Column(Integer, nullable=False, index=True)

    title = Column(String(255),nullable=False)

    last_message = Column(Text)

    last_active = Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())

    created_at = Column(DateTime(timezone=True),server_default=func.now())

