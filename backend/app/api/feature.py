from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.result import Result
from app.core.security import decode_access_token
from app.models.map_feature import MapFeature
from app.schemas.feature import CreateFeatureRequest, UpdateFeatureRequest, FeatureResponse

router = APIRouter(prefix="/api/features", tags=["地图要素"])


def _get_user_id(request: Request) -> str:
    """从请求头 Token 中提取用户名，失败返回空字符串"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return ""
    payload = decode_access_token(auth_header[7:])
    if not payload:
        return ""
    return payload.get("username", "")


@router.post("", summary="新增地图要素")
async def create_feature(
    body: CreateFeatureRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """保存一条地图要素记录"""
    username = _get_user_id(request)

    feature = MapFeature(
        type=body.type,
        geometry=body.geometry,
        name=body.name or None,
        xzqhname=body.xzqhname or None,
        code=body.code or None,
        address=body.address or None,
        remark=body.remark or None,
        created_by=username or None,
    )
    db.add(feature)
    await db.flush()
    await db.refresh(feature)

    return Result.ok(data=feature.to_dict(), message="保存成功")


@router.get("/all", summary="获取所有地图要素")
async def get_all_features(db: AsyncSession = Depends(get_db)):
    """获取全部地图要素，用于前端图层渲染"""
    stmt = select(MapFeature).order_by(MapFeature.id.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    data = [row.to_dict() for row in rows]
    return Result.ok(data=data)


@router.put("/{feature_id}", summary="编辑地图要素")
async def update_feature(
    feature_id: int,
    body: UpdateFeatureRequest,
    db: AsyncSession = Depends(get_db),
):
    """根据 ID 编辑地图要素（属性 + 几何均可修改）"""
    stmt = select(MapFeature).where(MapFeature.id == feature_id)
    result = await db.execute(stmt)
    feature = result.scalar_one_or_none()
    if not feature:
        return Result.bad_request(message="要素不存在")

    update_data = body.dict(exclude_unset=True)
    if not update_data:
        return Result.bad_request(message="未提供任何修改字段")

    for field, value in update_data.items():
        setattr(feature, field, value if value is not None else None)
    await db.flush()
    await db.refresh(feature)

    return Result.ok(data=feature.to_dict(), message="编辑成功")


@router.delete("/{feature_id}", summary="删除地图要素")
async def delete_feature(
    feature_id: int,
    db: AsyncSession = Depends(get_db),
):
    """根据 ID 删除地图要素"""
    stmt = select(MapFeature).where(MapFeature.id == feature_id)
    result = await db.execute(stmt)
    feature = result.scalar_one_or_none()
    if not feature:
        return Result.bad_request(message="要素不存在")

    await db.delete(feature)
    await db.flush()

    return Result.ok(message="删除成功")
