from sqlalchemy import Column, BigInteger, String, SmallInteger, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SysUser(Base):
    """系统用户表 —— 映射数据库中已有的 sys_user 表"""
    __tablename__ = "sys_user"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码 (BCrypt加密)")
    nickname = Column(String(50), nullable=True, comment="昵称")
    email = Column(String(100), nullable=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")
    status = Column(SmallInteger, nullable=False, server_default="1", comment="状态: 1=正常, 0=禁用")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), comment="更新时间")

    @property
    def is_active(self):
        """是否启用"""
        return self.status == 1

    def to_dict(self, exclude_fields=None):
        """转换为字典"""
        data = {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname or "",
            "email": self.email or "",
            "phone": self.phone or "",
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if exclude_fields:
            for field in exclude_fields:
                data.pop(field, None)
        return data
