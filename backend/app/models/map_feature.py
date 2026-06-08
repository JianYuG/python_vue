from datetime import datetime

from sqlalchemy import Column, BigInteger, SmallInteger, String, Text, DateTime, func

from app.models.sys_user import Base


class MapFeature(Base):
    """地图要素表"""
    __tablename__ = "map_feature"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增ID")
    type = Column(SmallInteger, nullable=False, comment="要素类型: 1=点 2=线 3=面")
    geometry = Column(Text, nullable=False, comment="WKT几何字符串")
    name = Column(String(200), nullable=True, comment="名称")
    xzqhname = Column(String(200), nullable=True, comment="行政区划名称")
    code = Column(String(20), nullable=True, comment="行政区划代码")
    address = Column(String(500), nullable=True, comment="详细地址")
    remark = Column(String(1000), nullable=True, comment="备注")
    created_by = Column(String(50), nullable=True, comment="创建人")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "geometry": self.geometry,
            "name": self.name or "",
            "xzqhname": self.xzqhname or "",
            "code": self.code or "",
            "address": self.address or "",
            "remark": self.remark or "",
            "created_by": self.created_by or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
