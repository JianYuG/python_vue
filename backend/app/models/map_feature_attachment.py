from datetime import datetime

from sqlalchemy import Column, BigInteger, Integer, String, DateTime, func

from app.models.sys_user import Base


class MapFeatureAttachment(Base):
    """地图要素附件表"""
    __tablename__ = "map_feature_attachment"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增ID")
    feature_id = Column(BigInteger, nullable=False, index=True, comment="关联要素ID")
    filename = Column(String(200), nullable=False, comment="原始文件名")
    file_type = Column(String(50), nullable=False, comment="文件类型(image/document/pdf等)")
    file_ext = Column(String(20), nullable=True, comment="文件扩展名")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    created_by = Column(String(50), nullable=True, comment="上传人")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="上传时间")

    def to_dict(self):
        return {
            "id": self.id,
            "feature_id": self.feature_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_ext": self.file_ext,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "created_by": self.created_by or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }