from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.result import Result

router = APIRouter(prefix="/api/doorplate", tags=["门牌搜索"])


@router.get("/search", summary="门牌搜索（分页）")
async def search_doorplate(
    districtid: str = Query("", description="行政区划代码（districtid），前缀匹配"),
    tsmc: str = Query("", description="门牌名称（tsmc），模糊匹配"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=50, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    """
    分页查询 ST_DOORPLATE 表。
    至少需要传一个搜索条件，否则返回提示。
    总数使用 EXPLAIN 估算避免精确 count 全表扫描超时。
    """
    if not districtid and not tsmc:
        return Result.ok(data={
            "items": [],
            "total": 0,
            "page": page,
            "pageSize": pageSize,
            "hint": "请至少输入一个搜索条件",
        })

    offset = (page - 1) * pageSize

    # 构建 WHERE 条件（参数化防注入）
    conditions = []
    params = {"limit": pageSize, "offset": offset}

    if districtid:
        conditions.append("districtid LIKE :districtid")
        params["districtid"] = districtid + "%"

    if tsmc:
        conditions.append("tsmc LIKE :tsmc")
        params["tsmc"] = "%" + tsmc.replace("'", "''") + "%"

    where_clause = "WHERE " + " AND ".join(conditions)

    # ★ 用 EXPLAIN 估算行数替代精确 count（避免千万级数据全表扫描）
    # asyncpg 不支持 FORMAT JSON，用 TEXT 格式解析 rows=... 行
    explain_sql = text(
        f'EXPLAIN SELECT 1 FROM "ST_DOORPLATE" {where_clause}'
    )
    explain_result = await db.execute(explain_sql, params)
    total = 0
    for row in explain_result.fetchall():
        line = row[0]
        if "rows=" in line:
            # 解析 "rows=1000" 格式
            import re
            match = re.search(r'rows=(\d+)', line)
            if match:
                total = int(match.group(1))
                break

    # 查数据（用 ST_AsText 把 the_geom 转 WKT）
    data_sql = text(f"""
        SELECT gid, xzqh, tsmc, districtid, ST_AsText(the_geom) AS wkt
        FROM "ST_DOORPLATE"
        {where_clause}
        ORDER BY gid
        LIMIT :limit OFFSET :offset
    """)
    data_result = await db.execute(data_sql, params)
    rows = data_result.fetchall()

    items = []
    for row in rows:
        items.append({
            "gid": row[0],
            "xzqh": row[1] or "",
            "tsmc": row[2] or "",
            "districtid": row[3] or "",
            "wkt": row[4] or "",
        })

    return Result.ok(data={
        "items": items,
        "total": total,
        "page": page,
        "pageSize": pageSize,
    })