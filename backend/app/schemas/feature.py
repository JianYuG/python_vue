from typing import Optional, List

from pydantic import BaseModel, Field


class CreateFeatureRequest(BaseModel):
    """新增地图要素请求"""
    type: int = Field(..., ge=1, le=3, description="要素类型: 1=点 2=线 3=面")
    geometry: str = Field(..., min_length=1, description="WKT几何字符串")
    name: Optional[str] = Field("", max_length=200, description="名称")
    xzqhname: Optional[str] = Field("", max_length=200, description="行政区划名称")
    code: Optional[str] = Field("", max_length=20, description="行政区划代码")
    address: Optional[str] = Field("", max_length=500, description="详细地址")
    remark: Optional[str] = Field("", max_length=1000, description="备注")


class UpdateFeatureRequest(BaseModel):
    """编辑地图要素请求"""
    type: Optional[int] = Field(None, ge=1, le=3, description="要素类型: 1=点 2=线 3=面")
    geometry: Optional[str] = Field(None, min_length=1, description="WKT几何字符串")
    name: Optional[str] = Field(None, max_length=200, description="名称")
    xzqhname: Optional[str] = Field(None, max_length=200, description="行政区划名称")
    code: Optional[str] = Field(None, max_length=20, description="行政区划代码")
    address: Optional[str] = Field(None, max_length=500, description="详细地址")
    remark: Optional[str] = Field(None, max_length=1000, description="备注")


class FeatureResponse(BaseModel):
    """地图要素响应"""
    id: int
    type: int
    geometry: str
    name: str = ""
    xzqhname: str = ""
    code: str = ""
    address: str = ""
    remark: str = ""
    created_by: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
