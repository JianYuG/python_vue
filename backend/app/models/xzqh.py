from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.models.sys_user import Base


class Xzqh(Base):
    """行政区划表"""
    __tablename__ = "xzqh"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增ID")
    name = Column(String(100), nullable=True, comment="短名")
    fullname = Column(String(200), nullable=True, comment="全称")
    code = Column(String(20), nullable=True, index=True, comment="行政区划码")
    level = Column(Integer, nullable=True, comment="层级: 1省 2市 3区县 4乡镇 5村社")
    # geom 字段暂不映射，前端不需要 WKB 数据
    raw = Column(JSONB, nullable=True, comment="原始数据(含bbox/centroid等)")
