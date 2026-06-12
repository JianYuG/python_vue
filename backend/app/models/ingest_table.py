"""
数据入库元数据模型
记录每次数据入库的元信息（文件名、生成的表名、字段列表等）
"""
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.sys_user import Base


class IngestTable(Base):
    __tablename__ = "ingest_table_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 原始文件名
    original_filename = Column(String(256), nullable=False)
    # 数据库中生成的表名（唯一）
    table_name = Column(String(128), nullable=False, unique=True)
    # 字段列表（JSON 存储，格式: [{"name":"col","type":"text"}, ...]）
    columns_json = Column(Text, nullable=False, default="[]")
    # 行数
    row_count = Column(Integer, nullable=False, default=0)
    # 创建人
    created_by = Column(String(64), nullable=True)
    # 创建时间
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "table_name": self.table_name,
            "columns": json.loads(self.columns_json or "[]"),
            "row_count": self.row_count,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
