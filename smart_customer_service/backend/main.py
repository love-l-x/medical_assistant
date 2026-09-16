"""智能医疗主入口"""
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.mysql import Base, engine
from app.database.postgres import PostgresBase, postgres_engine
from app.api import auth, chat, conversations, medical_upload, preferences


#初始化langsmith追踪
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

# MySQL 数据库表（用户认证）
try:
    Base.metadata.create_all(bind=engine)
    print("MySQL数据库连接成功")
except Exception as e:
    print(f"MySQL:数据库连接失败{e}")

# PostgresSQL 数据库表
try:
    PostgresBase.metadata.create_all(bind=postgres_engine)
    print("PostgresSql数据库连接成功")
except Exception as e:
    print(f"PostgresSql:数据库连接失败{e}")

# 创建FastAPI应用
app = FastAPI(
    title="智能医疗助手 API",
    description="基于 LangChain 1.x 和多智能体协作的医疗助手系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(chat.router, prefix="/chat", tags=["聊天"])
app.include_router(conversations.router, prefix="/conversations", tags=["会话"])
app.include_router(medical_upload.router, prefix="/documents", tags=["医疗文档"])
app.include_router(preferences.router, prefix="/preferences", tags=["用户偏好"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "智能医疗助手 API",
        "version": "1.0.0",
        "docs": "/docs",
        "tech_stack": {
            "langchain": "1.0.3",
            "langgraph": "1.0.2",
            "python": "3.12.x"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 50)
    print("智能医疗助手 API 启动中...")
    print("=" * 50)
    print(f"访问地址: http://{settings.HOST}:{settings.PORT}")
    print(f"API 文档: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 50 + "\n")

    # 启动FastAPI服务器
    uvicorn.run(
        # 指定应用入口: main.py文件中的app对象
        "main:app",
        # 服务器监听地址
        host=settings.HOST,
        # 服务器监听端口
        port=8000,
        # 开启热重载,代码修改后自动重启服务器
        reload=True
    )