from sqlalchemy import Integer, Column, String, func, DateTime

from app.database.mysql import Base


class User(Base):
    # 表名
    __tablename__ = "users"

    # 用户ID
    id = Column(Integer, primary_key=True, index=True)

    # 用户名
    username = Column(String(100), unique=True, index=True,nullable=False)

    #邮箱
    email = Column(String(100), unique=True, index=True,nullable=False)

    # 密码哈希
    password_hash = Column(String(100), nullable=False)

    #创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    #更新时间
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),onupdate=func.now())