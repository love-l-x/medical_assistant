"""聊天 API 模块
提供聊天接口（非流式，一次性返回完整内容）
短记忆由LangGraph自动管理（PostgresSaver）
支持文档上传后的智能分析
"""
import traceback
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse

from app.agent.multi_agent import create_medical_agent_system
from app.api.auth import get_current_user
from app.database.postgres import get_postgres_db
from app.models.conversation import Conversation
from app.models.user import User

# 创建聊天路由实例
router = APIRouter()

class ChatRequest(BaseModel):
    """聊天请求数据模型：定义前端发送的数据结构"""
    user_id:str

    message:str

    thread_id:str

@router.post("/send")
async def send_message(
        request: ChatRequest,
        current_user:User = Depends(get_current_user),
        db:Session = Depends(get_postgres_db)
):
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.thread_id,
            Conversation.user_id == current_user.id
        ).first()
        if conversation:
            conversation.last_message = request.message[:50] + ("..." if len(request.message) > 50 else "" )

            conversation.last_active = datetime.now()

            db.commit()

        # 创建医疗智能体系统
        graph = create_medical_agent_system()

        initial_state = {
            # 用户消息列表（包含当前消息）
            "messages": [HumanMessage(content=request.message)],
            # 用户 ID
            "user_id": request.user_id,
            # 会话线程 ID
            "thread_id": request.thread_id,
            # 医疗文档列表（初始为空）
            "medical_documents": [],
            # 下一个节点（由路由决定）
            "next": None
        }

        # 配置参数：用于 LangGraph 检查点（自动保存短记忆）
        config={
            "configurable":{
                "user_id":request.user_id,
                "thread_id":request.thread_id,
            }
        }

        # 初始化助手回复内容为空字符串
        assistant_content = ""

        try:
            result = graph.invoke(initial_state,config=config)

            if result.get("messages"):
                last_message = result.get("messages")[-1]

                assistant_content = last_message.content
        except Exception as e:
            print(f"智能体执行失败:{e}")
            import traceback
            #打印详细的错误堆栈信息
            print(traceback.format_exc())

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"智能体执行失败: {str(e)}"
            )
        #返回完整回复内容
        return JSONResponse(
            content={
                # 请求成功标志
                "success": True,
                # 助手的完整回复内容
                "message": assistant_content
            },
            # HTTP 状态码 200（成功）
            status_code = 200
        )
    except Exception as e:
        # 如果发生未捕获的异常，导入 traceback 模块
        import traceback
        # 打印详细错误堆栈信息
        print(f"发送消息失败: {traceback.format_exc()}")
        # 抛出 500 服务器错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )