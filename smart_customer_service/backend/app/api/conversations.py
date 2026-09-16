# 创建会话路由实例
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from app.agent.memory import get_short_term_memory
from app.api.auth import get_current_user
from app.database.postgres import get_postgres_db
from app.models.conversation import Conversation
from app.models.user import User

router = APIRouter()

class ConversationCreate(BaseModel):
    id:str

    title:str

#创建新会话接口
@router.post("/create")
async def create_conversation(
        conversation:ConversationCreate,
        user_id:int,
        # 当前登录用户（依赖注入，用于权限验证）
        current_user:User = Depends(get_current_user),
        # PostgresSQL 数据库会话（依赖注入）
        db:Session = Depends(get_postgres_db)
):
    """创建新会话"""
    try:
        existing_conv = db.query(Conversation).filter(Conversation.id == conversation.id).first()

        if existing_conv:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="会话ID已经存在")

        new_conv = Conversation(
            id=conversation.id,
            user_id=user_id,
            title=conversation.title,
            last_message="",
            last_active=datetime.now(),
            created_at=datetime.now(),
        )

        db.add(new_conv)

        db.commit()

        db.refresh(new_conv)

        #返回创建成功的响应
        return  {
            "message":"会话创建成功",
            "conversation":{
                "id":new_conv.id,
                "user_id":new_conv.user_id,
                "title":new_conv.title,
                "last_message":new_conv.last_message,
                "last_active":new_conv.last_active,
                "created_at":new_conv.created_at,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败：{str(e)}"
        )

#获取会话列表接口
@router.get("/list")
async def list_conversations(

    user_id:int,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_postgres_db)
):
    """获取用户的会话列表"""
    try:
        conversations = (db.query(Conversation).
                         filter(Conversation.user_id == user_id)
                         .order_by(Conversation.last_active.desc()).all())

        result = []

        for conv in conversations:
            result.append({
                # 会话 ID
                "id": conv.id,
                # 会话标题
                "title": conv.title,
                # 最后一条消息
                "last_message": conv.last_message,
                # 最后活跃时间
                "last_active": conv.last_active,
                # 创建时间
                "created_at": conv.created_at
            })

        return{
            "conversations":result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表：{str(e)}"
        )

#获取会话详细接口
@router.get("/get")
async def get_conversation(
        conversation_id:str,
        current_user:User = Depends(get_current_user),
        db:Session = Depends(get_postgres_db)
):
    """获取会话详情和消息列表"""
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        #初始化消息列表
        message_list=[]

        try:

            checkpointer = get_short_term_memory()

            if checkpointer:
                config = {"configurable":{"thread_id":conversation.id}}

                checkpoints = list(checkpointer.list(config))

                if checkpoints:
                    latest = checkpoints[0]

                    checkpoint_data = latest.checkpoint

                    channel_values = checkpoint_data.get("channel_values", {})

                    messages = channel_values.get("messages", [])

                    for msg in messages:
                        # 兼容消息对象（BaseMessage）和序列化后的字典两种形式
                        if isinstance(msg, dict):
                            msg_type = msg.get("type")
                            msg_content = msg.get("content")
                        else:
                            msg_type = getattr(msg, "type", None)
                            msg_content = getattr(msg, "content", None)

                        if msg_type in ['human','ai']:
                            if msg_content and str(msg_content).strip():
                                role = "user" if msg_type == "human" else "assistant"
                                message_list.append({
                                    "role":role,
                                    "content":msg_content,
                                })
        except Exception as e:            # 如果读取短记忆失败，打印错误日志（非致命，不影响主流程）
            print(f"[ERROR] 读取短记忆失败: {e}")
            # 导入 traceback 模块
            import traceback
            # 打印详细的错误堆栈信息
            print(traceback.format_exc())

        #返回会话详情和消息列表
        return{
            "conversation":{
                # 会话 ID
                "id": conversation.id,
                # 会话标题
                "title": conversation.title,
                # 最后一条消息
                "last_message": conversation.last_message,
                # 最后活跃时间
                "last_active": conversation.last_active,
                # 创建时间
                "created_at": conversation.created_at
            },
            "messages":message_list
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话详情失败: {str(e)}"
        )

#删除会话接口
@router.delete("/delete")
async def delete_conversation(
        conversation_id:str,
        current_user:User = Depends(get_current_user),
        db:Session = Depends(get_postgres_db)
):
    """删除会话（MySQL会话记录 + LangGraph短记忆checkpoints）"""
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
                                )
        try:
            checkpointer = get_short_term_memory()

            if checkpointer:
                checkpointer.delete_thread(thread_id=conversation.id)

                print(f"[OK] 清理短记忆checkpoint: thread_id={conversation_id}")
        except Exception as e:
           # 如果清理短记忆失败，打印警告日志（非致命，继续删除数据库记录）
           print(f"[WARN] 清理短记忆失败（非致命）: {e}")

        # 2. 删除 PostgresSQL 数据库中的会话记录
        db.delete(conversation)
        # 提交事务，保存删除操作
        db.commit()        # 返回删除成功的响应
        return {
            "message": "会话删除成功"
        }
    except HTTPException:
        # 如果是 HTTPException（如会话不存在），直接抛出，不包装
        raise
    except Exception as e:
        # 如果发生其他异常，抛出 500 服务器错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )


