"""
空间分析 API
基于 PostGIS 提供以下空间分析功能：
  1. buffer       - 缓冲区分析
  2. nearest      - 最邻近分析
  3. spatial_query- 空间查询（矩形范围/关系查询）
  4. overlay      - 叠加分析（交集/并集/差集）
  5. convex_hull  - 凸包分析
  6. centroid     - 质心提取
"""
import json
import re
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.result import Result
from app.models.ingest_table import IngestTable
from sqlalchemy import select

router = APIRouter(prefix="/api/spatial", tags=["空间分析"])

# ─────────────────────────────────────────────
# 安全校验：只允许操作 ingest_ 前缀的入库表
# ─────────────────────────────────────────────
_TABLE_RE = re.compile(r'^ingest_[a-z0-9_]+$')


def _check_table(name: str) -> bool:
    return bool(_TABLE_RE.match(name))


def _bad_table(name: str):
    return Result.bad_request(message=f"非法表名: {name}，只允许操作 ingest_ 前缀的入库表")


# ─────────────────────────────────────────────
# 结果格式化工具
# ─────────────────────────────────────────────

def _row_to_feature(geojson_str: str, props: dict) -> dict:
    """将一行查询结果转为 GeoJSON Feature"""
    try:
        geom = json.loads(geojson_str) if geojson_str else None
    except Exception:
        geom = None
    # 过滤掉 None 值的属性
    clean_props = {k: v for k, v in props.items() if v is not None}
    return {"type": "Feature", "geometry": geom, "properties": clean_props}


def _build_fc(features: list) -> dict:
    return {"type": "FeatureCollection", "features": features}


# ─────────────────────────────────────────────
# 请求体模型
# ─────────────────────────────────────────────

class BufferReq(BaseModel):
    table_name: str
    distance: float = Field(default=100, description="缓冲距离，单位：米")
    union_result: bool = Field(default=False, description="是否将所有缓冲区合并为一个")


class NearestReq(BaseModel):
    table_name: str
    lng: float
    lat: float
    limit: int = Field(default=5, ge=1, le=100, description="返回最近要素数量")


class SpatialQueryReq(BaseModel):
    table_name: str
    bbox: List[float] = Field(description="查询范围 [minx, miny, maxx, maxy]")
    relation: str = Field(default="intersects", description="空间关系: intersects/within/contains")


class OverlayReq(BaseModel):
    table_a: str
    table_b: str
    operation: str = Field(default="intersection", description="叠加操作: intersection/union/difference")


class ConvexHullReq(BaseModel):
    table_name: str


class CentroidReq(BaseModel):
    table_name: str


# ─────────────────────────────────────────────
# 获取含 geom 字段的入库表列表
# ─────────────────────────────────────────────

@router.get("/tables", summary="列出所有含geom字段的入库表")
async def list_geom_tables(db: AsyncSession = Depends(get_db)):
    """
    查询 ingest_table_meta 元数据表，筛选出含 geom 字段的入库记录，
    返回表名列表供前端图层选择器使用。
    """
    stmt = select(IngestTable).order_by(IngestTable.created_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    tables = []
    for row in rows:
        try:
            cols = json.loads(row.columns_json or "[]")
        except Exception:
            cols = []
        has_geom = any(c.get("name") == "geom" for c in cols)
        if has_geom:
            tables.append({
                "id": row.id,
                "table_name": row.table_name,
                "original_filename": row.original_filename,
                "row_count": row.row_count,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "columns": [c["name"] for c in cols if c.get("name") != "geom"],
            })
    return Result.ok(data=tables)


# ─────────────────────────────────────────────
# 1. 缓冲区分析
# ─────────────────────────────────────────────

@router.post("/buffer", summary="缓冲区分析")
async def buffer_analysis(req: BufferReq, db: AsyncSession = Depends(get_db)):
    """
    对指定入库表中所有要素的 geom 字段做缓冲区计算（ST_Buffer）。
    distance 单位为米，使用 geography 转换以保证精度。
    union_result=true 时将所有缓冲区合并为一个多边形。
    """
    if not _check_table(req.table_name):
        return _bad_table(req.table_name)

    tbl = req.table_name
    dist = req.distance

    if req.union_result:
        sql_str = f"""
            SELECT
                ST_AsGeoJSON(
                    ST_Union(ST_Buffer(geom::geography, :dist)::geometry)
                ) AS geojson,
                COUNT(*) AS src_count
            FROM "{tbl}"
            WHERE geom IS NOT NULL
        """
    else:
        # JOIN 原表将完整属性字段一并返回
        sql_str = f"""
            SELECT
                ST_AsGeoJSON(ST_Buffer(t.geom::geography, :dist)::geometry) AS _geojson,
                t.*
            FROM "{tbl}" t
            WHERE t.geom IS NOT NULL
        """

    result = await db.execute(text(sql_str), {"dist": dist})
    rows = result.mappings().all()

    if req.union_result:
        row = rows[0] if rows else {}
        features = []
        if row.get("geojson"):
            features.append(_row_to_feature(row["geojson"], {"src_count": row.get("src_count", 0)}))
        attrs = [{"src_count": row.get("src_count", 0)}] if features else []
    else:
        features = []
        attrs = []
        for r in rows:
            r_dict = dict(r)
            geojson_str = r_dict.pop("_geojson", None)
            r_dict.pop("geom", None)
            if geojson_str:
                r_dict["buffer_dist_m"] = dist
                features.append(_row_to_feature(geojson_str, r_dict))
                attrs.append(r_dict)

    return Result.ok(data={
        "geojson": _build_fc(features),
        "count": len(features),
        "analysis_type": "buffer",
        "attributes": attrs,
        "params": {"distance_m": dist, "union": req.union_result},
    })


# ─────────────────────────────────────────────
# 2. 最邻近分析
# ─────────────────────────────────────────────

@router.post("/nearest", summary="最邻近分析")
async def nearest_analysis(req: NearestReq, db: AsyncSession = Depends(get_db)):
    """
    以给定经纬度为中心，在指定入库表中查找最近的 N 个要素，
    返回按距离升序排列的要素及其距离（米）。
    """
    if not _check_table(req.table_name):
        return _bad_table(req.table_name)

    tbl = req.table_name

    # 带回原始属性字段 + 距离
    # 注意：表中 geom 字段 SRID=4490，参考点需用相同 SRID
    sql_str = f"""
        SELECT
            ST_AsGeoJSON(t.geom) AS _geojson,
            ROUND(
                ST_Distance(
                    t.geom::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4490)::geography
                )::numeric, 2
            ) AS distance_m,
            t.*
        FROM "{tbl}" t
        WHERE t.geom IS NOT NULL
        ORDER BY
            ST_Distance(
                t.geom::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4490)::geography
            )
        LIMIT :lim
    """

    result = await db.execute(text(sql_str), {"lng": req.lng, "lat": req.lat, "lim": req.limit})
    rows = result.mappings().all()

    features = []
    attrs = []
    for r in rows:
        r_dict = dict(r)
        geojson_str = r_dict.pop("_geojson", None)
        r_dict.pop("geom", None)
        if geojson_str:
            r_dict["distance_m"] = float(r_dict.get("distance_m", 0))
            features.append(_row_to_feature(geojson_str, r_dict))
            attrs.append(r_dict)

    return Result.ok(data={
        "geojson": _build_fc(features),
        "count": len(features),
        "analysis_type": "nearest",
        "attributes": attrs,
        "params": {"center": [req.lng, req.lat], "limit": req.limit},
    })


# ─────────────────────────────────────────────
# 3. 空间查询
# ─────────────────────────────────────────────

@router.post("/spatial_query", summary="空间查询")
async def spatial_query(req: SpatialQueryReq, db: AsyncSession = Depends(get_db)):
    """
    在指定入库表中，使用矩形 bbox 过滤要素。
    relation 支持：intersects（相交）/ within（在范围内）/ contains（包含范围）。
    """
    if not _check_table(req.table_name):
        return _bad_table(req.table_name)

    if len(req.bbox) != 4:
        return Result.bad_request(message="bbox 必须为 [minx, miny, maxx, maxy] 格式")

    valid_relations = {"intersects", "within", "contains"}
    relation = req.relation.lower()
    if relation not in valid_relations:
        return Result.bad_request(message=f"relation 只支持: {', '.join(valid_relations)}")

    tbl = req.table_name
    minx, miny, maxx, maxy = req.bbox

    # 构建查询多边形（bbox）
    bbox_wkt = f"POLYGON(({minx} {miny},{maxx} {miny},{maxx} {maxy},{minx} {maxy},{minx} {miny}))"

    # 不同空间关系的函数映射
    rel_fn_map = {
        "intersects": "ST_Intersects",
        "within": "ST_Within",
        "contains": "ST_Contains",
    }
    fn = rel_fn_map[relation]

    # 使用子查询，在 Python 层过滤掉 geom 二进制列，减少内存占用
    sql_str = f"""
        SELECT
            ST_AsGeoJSON(geom) AS _geojson,
            *
        FROM "{tbl}"
        WHERE geom IS NOT NULL
          AND {fn}(geom, ST_GeomFromText(:bbox_wkt, 4490))
        LIMIT 1000
    """

    result = await db.execute(text(sql_str), {"bbox_wkt": bbox_wkt})
    rows = result.mappings().all()

    features = []
    attrs = []
    for r in rows:
        r_dict = dict(r)
        geojson_str = r_dict.pop("_geojson", None)
        r_dict.pop("geom", None)
        if geojson_str:
            features.append(_row_to_feature(geojson_str, r_dict))
            attrs.append(r_dict)

    return Result.ok(data={
        "geojson": _build_fc(features),
        "count": len(features),
        "analysis_type": "spatial_query",
        "attributes": attrs,
        "params": {"bbox": req.bbox, "relation": relation},
    })


# ─────────────────────────────────────────────
# 4. 叠加分析
# ─────────────────────────────────────────────

@router.post("/overlay", summary="叠加分析")
async def overlay_analysis(req: OverlayReq, db: AsyncSession = Depends(get_db)):
    """
    对两个入库表的几何字段进行叠加分析：
    - intersection：交集（两图层相交部分）
    - union：并集（两图层合并）
    - difference：差集（table_a 中去掉与 table_b 相交的部分）
    """
    for tbl in [req.table_a, req.table_b]:
        if not _check_table(tbl):
            return _bad_table(tbl)

    valid_ops = {"intersection", "union", "difference"}
    op = req.operation.lower()
    if op not in valid_ops:
        return Result.bad_request(message=f"operation 只支持: {', '.join(valid_ops)}")

    tbl_a = req.table_a
    tbl_b = req.table_b

    op_fn_map = {
        "intersection": "ST_Intersection",
        "union": "ST_Union",
        "difference": "ST_Difference",
    }
    fn = op_fn_map[op]

    # 用 CTE 避免同一聚合子查询重复执行 4 次
    sql_str = f"""
        WITH
            ga AS (SELECT ST_Union(geom) AS g FROM "{tbl_a}" WHERE geom IS NOT NULL),
            gb AS (SELECT ST_Union(geom) AS g FROM "{tbl_b}" WHERE geom IS NOT NULL),
            result AS (SELECT {fn}(ga.g, gb.g) AS geom FROM ga, gb)
        SELECT
            ST_AsGeoJSON(r.geom)  AS geojson,
            ST_GeometryType(r.geom) AS geom_type,
            CASE
                WHEN ST_GeometryType(r.geom) LIKE '%Polygon%'
                THEN ROUND(ST_Area(r.geom::geography)::numeric, 2)
                ELSE NULL
            END AS area_m2,
            (SELECT COUNT(*) FROM "{tbl_a}" WHERE geom IS NOT NULL) AS count_a,
            (SELECT COUNT(*) FROM "{tbl_b}" WHERE geom IS NOT NULL) AS count_b
        FROM result r
    """

    result = await db.execute(text(sql_str))
    row = result.mappings().first()

    features = []
    attrs = []
    if row and row.get("geojson"):
        op_label = {"intersection": "交集", "union": "并集", "difference": "差集"}.get(op, op)
        props = {
            "叠加方式": op_label,
            "图层A": tbl_a,
            "图层B": tbl_b,
            "几何类型": row.get("geom_type", ""),
            "面积(m²)": float(row["area_m2"]) if row.get("area_m2") else 0,
            "图层A要素数": int(row["count_a"]) if row.get("count_a") else 0,
            "图层B要素数": int(row["count_b"]) if row.get("count_b") else 0,
        }
        features.append(_row_to_feature(row["geojson"], props))
        attrs.append(props)

    return Result.ok(data={
        "geojson": _build_fc(features),
        "count": len(features),
        "analysis_type": "overlay",
        "attributes": attrs,
        "params": {"table_a": tbl_a, "table_b": tbl_b, "operation": op},
    })


# ─────────────────────────────────────────────
# 5. 凸包分析
# ─────────────────────────────────────────────

@router.post("/convex_hull", summary="凸包分析")
async def convex_hull_analysis(req: ConvexHullReq, db: AsyncSession = Depends(get_db)):
    """
    计算指定入库表中所有要素几何的凸包（最小凸多边形）。
    """
    if not _check_table(req.table_name):
        return _bad_table(req.table_name)

    tbl = req.table_name

    sql_str = f"""
        SELECT
            ST_AsGeoJSON(ST_ConvexHull(ST_Collect(geom))) AS geojson,
            COUNT(*) AS src_count
        FROM "{tbl}"
        WHERE geom IS NOT NULL
    """

    result = await db.execute(text(sql_str))
    row = result.mappings().first()

    features = []
    if row and row.get("geojson"):
        features.append(_row_to_feature(row["geojson"], {
            "src_count": row.get("src_count", 0),
            "analysis": "凸包",
        }))

    return Result.ok(data={
        "geojson": _build_fc(features),
        "count": len(features),
        "analysis_type": "convex_hull",
    })


# ─────────────────────────────────────────────
# 6. 质心提取
# ─────────────────────────────────────────────

@router.post("/centroid", summary="质心提取")
async def centroid_analysis(req: CentroidReq, db: AsyncSession = Depends(get_db)):
    """
    提取指定入库表中每个要素几何的质心点（ST_Centroid）。
    """
    if not _check_table(req.table_name):
        return _bad_table(req.table_name)

    tbl = req.table_name

    # 质心坐标 + 原始属性字段
    sql_str = f"""
        SELECT
            ST_AsGeoJSON(ST_Centroid(t.geom)) AS _geojson,
            ST_X(ST_Centroid(t.geom)) AS cx,
            ST_Y(ST_Centroid(t.geom)) AS cy,
            t.*
        FROM "{tbl}" t
        WHERE t.geom IS NOT NULL
    """

    result = await db.execute(text(sql_str))
    rows = result.mappings().all()

    features = []
    attrs = []
    for r in rows:
        r_dict = dict(r)
        geojson_str = r_dict.pop("_geojson", None)
        r_dict.pop("geom", None)
        if geojson_str:
            if r_dict.get("cx") is not None:
                r_dict["cx"] = round(float(r_dict["cx"]), 6)
            if r_dict.get("cy") is not None:
                r_dict["cy"] = round(float(r_dict["cy"]), 6)
            features.append(_row_to_feature(geojson_str, r_dict))
            attrs.append(r_dict)

    return Result.ok(data={
        "geojson": _build_fc(features),
        "count": len(features),
        "analysis_type": "centroid",
        "attributes": attrs,
    })
