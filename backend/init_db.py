"""
数据库初始化脚本

使用方法：
    python init_db.py

功能：
    1. 自动创建 sys_user 表（如果不存在）
"""
import asyncio
import sys
import os

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.models.sys_user import Base


async def init_db():
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        print("✅ 数据库表创建成功！")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
