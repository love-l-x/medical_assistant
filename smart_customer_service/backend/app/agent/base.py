"""
基础模块 - 提供模型初始化和通用工具
"""

from langchain_openai import ChatOpenAI
from app.config.settings import settings

def get_model():
    return ChatOpenAI(
        model="qwen3.5-plus",
        api_key=settings.DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.3
    )