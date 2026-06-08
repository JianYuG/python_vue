from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.result import Result
from app.models.xzqh import Xzqh

router = APIRouter(prefix="/api/xzqh", tags=["行政区划"])


def _build_node(row: Xzqh) -> dict:
    """将 Xzqh 行转为前端级联树节点"""
    bbox = ""
    centroid = ""
    if row.raw:
        minx = row.raw.get("MINX")
        miny = row.raw.get("MINY")
        maxx = row.raw.get("MAXX")
        maxy = row.raw.get("MAXY")
        if all(v is not None for v in (minx, miny, maxx, maxy)):
            bbox = f"{minx},{miny},{maxx},{maxy}"
        labelx = row.raw.get("LABELX") or row.raw.get("CENTERX")
        labely = row.raw.get("LABELY") or row.raw.get("CENTERY")
        if labelx is not None and labely is not None:
            centroid = f"{labelx},{labely}"

    return {
        "value": row.code,
        "label": row.name or "",
        "fullname": row.fullname or "",
        "level": row.level,
        "bbox": bbox,
        "centroid": centroid,
    }


# code 前缀长度 → 对应层级
_PREFIX_LEN = {1: 2, 2: 4, 3: 6, 4: 9}

# 内存缓存（行政区划数据极少变动，缓存1小时）
_tree_cache: dict = {"data": None, "expires_at": None}
_CACHE_TTL = timedelta(hours=1)


@router.get("/tree", summary="获取行政区划级联树（1-4级）")
async def get_xzqh_tree(db: AsyncSession = Depends(get_db)):
    """
    返回省/市/区县/乡镇 4 级级联树。
    每节点: value(code), label(name), fullname, level, bbox, centroid, children
    """
    # 检查内存缓存
    now = datetime.now()
    if _tree_cache["data"] is not None and _tree_cache["expires_at"] and now < _tree_cache["expires_at"]:
        return Result.ok(data=_tree_cache["data"])

    # 只查 1-4 级，不查第 5 级（村社，2.6 万条数据量大且前端暂不需要）
    stmt = (
        select(Xzqh)
        .where(Xzqh.level.in_([1, 2, 3, 4]))
        .order_by(Xzqh.level, Xzqh.code)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    # 按层级分组
    level_map: dict = {1: [], 2: [], 3: [], 4: []}
    for row in rows:
        node = _build_node(row)
        node["children"] = []
        level_map[row.level].append(node)

    # 构建 code → node 的索引，用于快速查找父节点
    code_index: dict = {}
    for node_list in level_map.values():
        for node in node_list:
            code_index[node["value"]] = node

    # 逐层挂载子节点到父节点
    for lv in [2, 3, 4]:
        parent_prefix_len = _PREFIX_LEN[lv - 1]
        for node in level_map[lv]:
            parent_code = node["value"][:parent_prefix_len]
            parent = code_index.get(parent_code)
            if parent:
                parent["children"].append(node)

    # 写入缓存
    _tree_cache["data"] = level_map[1]
    _tree_cache["expires_at"] = now + _CACHE_TTL

    return Result.ok(data=level_map[1])
