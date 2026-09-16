"""用户偏好 API 模块

提供用户偏好的保存、查询，以及医疗历史的查询接口。
前端调用方式（两种均需兼容）：
- JSON body:  { user_id, key, value }
- query 参数: ?user_id=...&key=...&value=...
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel

from app.agent.memory import get_long_term_memory
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()


class PreferenceSaveBody(BaseModel):
    user_id: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None


@router.post("/save")
async def save_preference(
        body: Optional[PreferenceSaveBody] = Body(None),
        user_id: Optional[str] = Query(None),
        key: Optional[str] = Query(None),
        value: Optional[str] = Query(None),
        current_user: User = Depends(get_current_user),
):
    """保存用户偏好（兼容 JSON body 与 query 参数两种方式）"""
    if body is not None:
        uid = body.user_id if body.user_id is not None else user_id
        k = body.key if body.key is not None else key
        v = body.value if body.value is not None else value
    else:
        uid, k, v = user_id, key, value

    if not uid or not k or v is None:
        raise HTTPException(status_code=400, detail="缺少 user_id / key / value 参数")

    store = get_long_term_memory()
    store.put(("user_preferences", uid), f"pref_{k}", {"key": k, "value": str(v)})
    return {"message": "偏好保存成功", "key": k, "value": str(v)}


@router.get("/list")
async def list_preferences(
        user_id: str = Query(...),
        current_user: User = Depends(get_current_user),
):
    """获取用户偏好列表"""
    store = get_long_term_memory()
    items = store.search(("user_preferences", user_id))

    lines = []
    for item in items:
        v = item.value
        if isinstance(v, dict):
            k = v.get("key")
            val = v.get("value")
        else:
            k, val = None, v
        if k and val is not None:
            lines.append(f"{k}: {val}")

    return {"preferences": "\n".join(lines)}


@router.get("/get_medical_history")
async def get_medical_history(
        user_id: str = Query(...),
        current_user: User = Depends(get_current_user),
):
    """获取用户医疗历史"""
    store = get_long_term_memory()
    items = store.search(("user_medical_history", user_id))

    if not items:
        return {"medical_history": "没有找到医疗历史"}

    parts = []
    for item in items:
        v = item.value
        content = v.get("content") if isinstance(v, dict) else str(v)
        if content and str(content).strip():
            parts.append(str(content))

    return {"medical_history": "\n\n".join(parts) if parts else "没有找到医疗历史"}
