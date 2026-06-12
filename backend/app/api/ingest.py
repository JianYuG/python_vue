"""
数据入库 API
支持 Excel、CSV、Shapefile 等结构化数据上传，
每次导入自动在数据库中创建独立数据表，
提供入库记录列表查询和按记录删除（含 DROP TABLE）功能。
"""
import io
import json
import random
import string
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.result import Result
from app.core.security import decode_access_token
from app.models.ingest_table import IngestTable

router = APIRouter(prefix="/api/ingest", tags=["数据入库"])

# 支持的文件类型（.zip 用于打包的 Shapefile）
ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx", ".dbf", ".shp", ".zip"}
# 最大文件大小 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024


def _get_username(request: Request) -> str:
    """从 Authorization header 提取用户名"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return ""
    payload = decode_access_token(auth[7:])
    if not payload:
        return ""
    return payload.get("username", "")


def _gen_table_name() -> str:
    """生成唯一表名，格式: ingest_YYYYMMDD_xxxxxx"""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    date_str = datetime.utcnow().strftime("%Y%m%d")
    return f"ingest_{date_str}_{suffix}"


def _safe_col_name(name: str) -> str:
    """将列名转为安全的 PostgreSQL 标识符（小写，特殊字符转下划线）"""
    import re
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9_\u4e00-\u9fff]", "_", name)
    if name and name[0].isdigit():
        name = "col_" + name
    return name or "col"


def _pg_type(val) -> str:
    """根据 Python 值猜测 PostgreSQL 类型"""
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, int):
        return "bigint"
    if isinstance(val, float):
        return "double precision"
    return "text"


def _geojson_to_wkt(geo: dict) -> str:
    """将 GeoJSON geometry dict 转为 WKT 字符串（支持常见几何类型）"""
    gtype = geo.get("type", "")
    coords = geo.get("coordinates")

    def _fmt_coord(c):
        return f"{c[0]} {c[1]}"

    def _fmt_ring(ring):
        return "(" + ", ".join(_fmt_coord(c) for c in ring) + ")"

    if gtype == "Point":
        return f"POINT ({_fmt_coord(coords)})"
    elif gtype == "MultiPoint":
        pts = ", ".join(f"({_fmt_coord(c)})" for c in coords)
        return f"MULTIPOINT ({pts})"
    elif gtype == "LineString":
        return f"LINESTRING ({', '.join(_fmt_coord(c) for c in coords)})"
    elif gtype == "MultiLineString":
        lines = ", ".join(f"({', '.join(_fmt_coord(c) for c in line)})" for line in coords)
        return f"MULTILINESTRING ({lines})"
    elif gtype == "Polygon":
        rings = ", ".join(_fmt_ring(r) for r in coords)
        return f"POLYGON ({rings})"
    elif gtype == "MultiPolygon":
        polys = []
        for poly in coords:
            rings = ", ".join(_fmt_ring(r) for r in poly)
            polys.append(f"({rings})")
        return f"MULTIPOLYGON ({', '.join(polys)})"
    elif gtype == "GeometryCollection":
        geoms = [_geojson_to_wkt(g) for g in geo.get("geometries", [])]
        return f"GEOMETRYCOLLECTION ({', '.join(g for g in geoms if g)})"
    return ""


def _infer_col_types(rows: List[dict], columns: List[str]) -> dict:
    """遍历前 200 行数据推断每列类型"""
    col_types = {c: "text" for c in columns}
    sample = rows[:200]
    for col in columns:
        types_seen = set()
        for row in sample:
            v = row.get(col)
            if v is None or str(v).strip() == "":
                continue
            types_seen.add(_pg_type(v))
        # 如果有 text 就用 text，否则取第一个非 text
        if "text" not in types_seen and types_seen:
            col_types[col] = types_seen.pop()
    return col_types


async def _parse_file(file: UploadFile, content: bytes) -> List[dict]:
    """解析上传文件，返回字典列表"""
    from pathlib import Path
    ext = Path(file.filename or "").suffix.lower()

    if ext == ".csv":
        import pandas as pd
        df = pd.read_csv(io.BytesIO(content), dtype=str)
        df = df.where(df.notna(), None)
        return df.to_dict(orient="records")

    if ext in (".xls", ".xlsx"):
        import pandas as pd
        df = pd.read_excel(io.BytesIO(content), dtype=str)
        df = df.where(df.notna(), None)
        return df.to_dict(orient="records")

    if ext in (".shp", ".zip"):
        import shapefile
        import tempfile, os, zipfile
        # SHP 文件必须和 .dbf/.shx 一起上传，接受 zip 打包
        with tempfile.TemporaryDirectory() as tmpdir:
            # 解压 zip
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    zf.extractall(tmpdir)
            except zipfile.BadZipFile:
                raise ValueError("文件不是有效的 zip 压缩包，请将 .shp/.dbf/.shx 打包成 zip 后上传")

            # 递归查找 .shp 文件（可能在子目录中）
            shp_path = None
            for root, dirs, files in os.walk(tmpdir):
                for fname in files:
                    if fname.lower().endswith(".shp"):
                        shp_path = os.path.join(root, fname)
                        break
                if shp_path:
                    break
            if not shp_path:
                raise ValueError("zip 中未找到 .shp 文件，请确保压缩包内包含 .shp/.dbf/.shx 文件")

            shp_dir = os.path.dirname(shp_path)
            shp_stem = os.path.splitext(os.path.basename(shp_path))[0]

            def _find_file(stem, fext):
                """大小写不敏感查找文件"""
                exact = os.path.join(shp_dir, stem + fext)
                if os.path.exists(exact):
                    return exact
                for f in os.listdir(shp_dir):
                    if f.lower() == (stem + fext).lower():
                        return os.path.join(shp_dir, f)
                return None

            # 读取 .prj 获取坐标系 SRID（默认 4326）
            srid = 4326
            prj_found = _find_file(shp_stem, ".prj")
            if prj_found:
                try:
                    with open(prj_found, "r", encoding="utf-8", errors="ignore") as pf:
                        prj_wkt = pf.read().strip()
                    # 简单规则：含 "GCS_WGS_1984" 或 "WGS 1984" → 4326
                    # 含 "CGCS2000" → 4490；含 "Beijing_1954" → 4214
                    # 更精确需 pyproj，这里做常见匹配
                    prj_upper = prj_wkt.upper()
                    if "CGCS2000" in prj_upper or "CHINA_GEODETIC" in prj_upper:
                        srid = 4490
                    elif "BEIJING_1954" in prj_upper or "BEIJING 1954" in prj_upper:
                        srid = 4214
                    elif "XIAN_1980" in prj_upper or "XIAN 1980" in prj_upper:
                        srid = 4610
                    elif "WGS_1984" in prj_upper or "WGS 1984" in prj_upper:
                        srid = 4326
                except Exception:
                    pass

            shp_file = open(shp_path, "rb")
            dbf_found = _find_file(shp_stem, ".dbf")
            shx_found = _find_file(shp_stem, ".shx")
            dbf_file = open(dbf_found, "rb") if dbf_found else None
            shx_file = open(shx_found, "rb") if shx_found else None

            try:
                sf = shapefile.Reader(
                    shp=shp_file,
                    dbf=dbf_file,
                    shx=shx_file,
                )
                field_names = [f[0] for f in sf.fields[1:]]  # 跳过 DeletionFlag
                records = []
                for sr in sf.shapeRecords():
                    row = dict(zip(field_names, sr.record))
                    shape = sr.shape
                    # 将几何转为 WKT，用特殊键传递给上层
                    if shape.shapeType != 0:
                        try:
                            geo = shape.__geo_interface__
                            wkt = _geojson_to_wkt(geo)
                            if wkt:
                                row["__geom_wkt__"] = wkt
                                row["__geom_srid__"] = srid
                        except Exception:
                            pass
                    records.append(row)
            finally:
                shp_file.close()
                if dbf_file:
                    dbf_file.close()
                if shx_file:
                    shx_file.close()
            return records

    if ext == ".dbf":
        import shapefile
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            dbf_path = os.path.join(tmpdir, "data.dbf")
            with open(dbf_path, "wb") as f:
                f.write(content)
            sf = shapefile.Reader(dbf=dbf_path)
            field_names = [f[0] for f in sf.fields[1:]]
            records = [dict(zip(field_names, r)) for r in sf.records()]
            return records

    raise ValueError(f"不支持的文件类型: {ext}")


@router.post("/upload", summary="上传结构化数据入库")
async def upload_ingest(
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    上传 Excel / CSV / SHP(zip) / DBF 文件，
    自动解析并在数据库中创建对应的数据表，同时记录元信息。
    """
    username = _get_username(request)

    # 校验文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return Result.bad_request(message="文件超过 100MB 大小限制")

    from pathlib import Path
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return Result.bad_request(message=f"不支持的文件格式: {ext}，支持 csv/xls/xlsx/shp(zip)/dbf")

    # 解析文件
    try:
        rows = await _parse_file(file, content)
    except Exception as e:
        return Result.bad_request(message=f"文件解析失败: {str(e)}")

    if not rows:
        return Result.bad_request(message="文件内容为空，无法入库")

    # 处理列名（安全化）；过滤掉几何特殊键
    GEOM_KEYS = {"__geom_wkt__", "__geom_srid__"}
    raw_columns = [k for k in rows[0].keys() if k not in GEOM_KEYS]

    # 判断是否含几何信息（SHP 数据）
    has_geom = any("__geom_wkt__" in row for row in rows)
    # 取第一行有几何的 SRID
    geom_srid = 4326
    for row in rows:
        if "__geom_srid__" in row:
            geom_srid = row["__geom_srid__"]
            break

    col_map = {}  # raw -> safe
    for rc in raw_columns:
        safe = _safe_col_name(rc)
        base_safe = safe
        idx = 1
        while safe in col_map.values():
            safe = f"{base_safe}_{idx}"
            idx += 1
        col_map[rc] = safe

    safe_columns = list(col_map.values())

    # 推断列类型（只看普通列）
    mapped_rows = [{col_map[k]: v for k, v in row.items() if k in col_map} for row in rows]
    col_types = _infer_col_types(mapped_rows, safe_columns)

    # 生成唯一表名
    table_name = _gen_table_name()

    # 动态建表 DDL（SHP 额外增加 geom 列）
    col_defs = ", ".join(f'"{c}" {col_types[c]}' for c in safe_columns)
    if has_geom:
        col_defs += f', "geom" geometry(Geometry, {geom_srid})'
    create_ddl = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id SERIAL PRIMARY KEY, {col_defs})'
    await db.execute(text(create_ddl))

    # 批量插入数据
    if mapped_rows:
        if has_geom:
            # 含几何：单独构建带 ST_GeomFromText 的 INSERT
            cols_quoted = ", ".join(f'"{c}"' for c in safe_columns) + ', "geom"'
            placeholders = ", ".join(f":{c}" for c in safe_columns) + \
                           f", ST_GeomFromText(:__wkt__, {geom_srid})"
            insert_sql = text(
                f'INSERT INTO "{table_name}" ({cols_quoted}) VALUES ({placeholders})'
            )
            for raw_row, mapped_row in zip(rows, mapped_rows):
                cleaned = {}
                for col in safe_columns:
                    val = mapped_row.get(col)
                    cleaned[col] = None if (val is None or (isinstance(val, str) and val.strip() == "")) else val
                cleaned["__wkt__"] = raw_row.get("__geom_wkt__") or None
                await db.execute(insert_sql, cleaned)
        else:
            cols_quoted = ", ".join(f'"{c}"' for c in safe_columns)
            placeholders = ", ".join(f":{c}" for c in safe_columns)
            insert_sql = text(
                f'INSERT INTO "{table_name}" ({cols_quoted}) VALUES ({placeholders})'
            )
            for row in mapped_rows:
                cleaned = {}
                for col in safe_columns:
                    val = row.get(col)
                    cleaned[col] = None if (val is None or (isinstance(val, str) and val.strip() == "")) else val
                await db.execute(insert_sql, cleaned)

    # 保存元数据（geom 列单独记录）
    columns_info = [{"name": c, "type": col_types[c]} for c in safe_columns]
    if has_geom:
        columns_info.append({"name": "geom", "type": f"geometry(Geometry,{geom_srid})"})
    meta = IngestTable(
        original_filename=file.filename or "unknown",
        table_name=table_name,
        columns_json=json.dumps(columns_info, ensure_ascii=False),
        row_count=len(rows),
        created_by=username or None,
        created_at=datetime.utcnow(),
    )
    db.add(meta)
    await db.flush()
    await db.refresh(meta)

    return Result.ok(data=meta.to_dict(), message="入库成功")


@router.get("/list", summary="查询所有入库记录")
async def list_ingest(db: AsyncSession = Depends(get_db)):
    """返回所有数据入库记录（按时间倒序）"""
    stmt = select(IngestTable).order_by(IngestTable.created_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return Result.ok(data=[r.to_dict() for r in rows])


@router.delete("/{record_id}", summary="删除入库记录及对应数据表")
async def delete_ingest(record_id: int, db: AsyncSession = Depends(get_db)):
    """删除元数据记录并 DROP 对应数据表"""
    stmt = select(IngestTable).where(IngestTable.id == record_id)
    result = await db.execute(stmt)
    meta = result.scalar_one_or_none()
    if not meta:
        return Result.bad_request(message="记录不存在")

    table_name = meta.table_name

    # 先删除元数据记录
    await db.delete(meta)
    await db.flush()

    # DROP 数据表（如果存在）
    try:
        await db.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
    except Exception as e:
        # 即使 DROP 失败也返回成功（元数据已删除）
        return Result.ok(message=f"元数据已删除，但数据表删除失败: {str(e)}")

    return Result.ok(message="删除成功")
