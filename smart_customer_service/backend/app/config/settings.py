import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"

load_dotenv(dotenv_path=env_path,override=True)

class Settings:
    """应用配置"""

    #AI模型配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    #langsmith配置
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL","")
    POSTGRES_SHORT_TERM_URL = os.getenv("POSTGRES_SHORT_TERM_URL")
    POSTGRES_LONG_TERM_URL = os.getenv("POSTGRES_LONG_TERM_URL")
    POSTGRES_SESSION_URL = os.getenv("POSTGRES_SESSION_URL")

    #应用配置
    #JWT Token
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 525600

    #服务器配置
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")

settings = Settings()
