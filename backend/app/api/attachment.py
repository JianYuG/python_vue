import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.result import Result
from app.core.security import decode_access_token
from app.models.map_feature_attachment import MapFeatureAttachment

router = APIRouter(prefix="/api/attachments", tags=["附件管理"])

# 文件存储目录
UPLOAD_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {
    # 图片
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
    # 文档
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # PDF
    ".pdf",
    # 其他
    ".txt", ".csv", ".zip", ".rar",
}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def _get_user_id(request: Request) -> str:
    """从请求头 Token 中提取用户名"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return ""
    payload = decode_access_token(auth_header[7:])
    if not payload:
        return ""
    return payload.get("username", "")


def _classify_file(ext: str) -> str:
    """根据扩展名分类文件类型"""
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
    pdf_exts = {".pdf"}
    doc_exts = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
    if ext in image_exts:
        return "image"
    elif ext in pdf_exts:
        return "pdf"
    elif ext in doc_exts:
        return "document"
    else:
        return "other"


def _is_previewable(file_type: str) -> bool:
    """浏览器是否可以直接预览"""
    return file_type in ("image", "pdf")


@router.post("/upload/{feature_id}", summary="上传附件")
async def upload_attachment(
    feature_id: int,
    files: List[UploadFile] = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """为指定要素上传附件（支持多文件）"""
    username = _get_user_id(request)
    uploaded = []

    for file in files:
        # 校验文件大小
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            return Result.bad_request(message=f"文件 {file.filename} 超过50MB大小限制")

        # 校验文件类型
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return Result.bad_request(message=f"文件类型 {ext} 不允许上传")

        # 生成唯一文件名保存到磁盘
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = UPLOAD_DIR / unique_name
        with open(save_path, "wb") as f:
            f.write(content)

        # 写入数据库
        file_type = _classify_file(ext)
        attachment = MapFeatureAttachment(
            feature_id=feature_id,
            filename=file.filename or "unknown",
            file_type=file_type,
            file_ext=ext,
            file_size=len(content),
            file_path=f"uploads/{unique_name}",
            created_by=username or None,
        )
        db.add(attachment)
        await db.flush()
        await db.refresh(attachment)
        uploaded.append(attachment.to_dict())

    return Result.ok(data=uploaded, message="上传成功")


@router.get("/list/{feature_id}", summary="获取要素附件列表")
async def list_attachments(
    feature_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取指定要素的全部附件"""
    stmt = select(MapFeatureAttachment).where(
        MapFeatureAttachment.feature_id == feature_id
    ).order_by(MapFeatureAttachment.created_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    data = [row.to_dict() for row in rows]
    # 补充 previewable 字段
    for item in data:
        item["previewable"] = _is_previewable(item["file_type"])

    return Result.ok(data=data)


@router.get("/download/{attachment_id}", summary="下载/预览附件")
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """下载或预览附件，浏览器可预览的图片/PDF直接返回文件流"""
    stmt = select(MapFeatureAttachment).where(
        MapFeatureAttachment.id == attachment_id
    )
    result = await db.execute(stmt)
    att = result.scalar_one_or_none()
    if not att:
        return Result.bad_request(message="附件不存在")

    # 构建磁盘绝对路径
    # 项目根目录
    _project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    file_abs_path = _project_root / att.file_path
    if not file_abs_path.exists():
        return Result.bad_request(message="文件不存在或已被删除")

    # 浏览器可预览的类型：直接返回文件流（inline）
    if _is_previewable(att.file_type):
        media_type = None
        if att.file_type == "image":
            media_type = f"image/{att.file_ext.lstrip('.')}"
            # jpg 的 MIME 是 image/jpeg
            if att.file_ext in (".jpg", ".jpeg"):
                media_type = "image/jpeg"
            elif att.file_ext == ".png":
                media_type = "image/png"
            elif att.file_ext == ".gif":
                media_type = "image/gif"
        elif att.file_type == "pdf":
            media_type = "application/pdf"
        return FileResponse(
            path=str(file_abs_path),
            media_type=media_type,
            filename=att.filename,
            content_disposition_type="inline",
        )

    # 不可预览类型：以附件方式下载（attachment）
    return FileResponse(
        path=str(file_abs_path),
        filename=att.filename,
        media_type="application/octet-stream",
        content_disposition_type="attachment",
    )


@router.delete("/{attachment_id}", summary="删除附件")
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除附件记录及磁盘文件"""
    stmt = select(MapFeatureAttachment).where(
        MapFeatureAttachment.id == attachment_id
    )
    result = await db.execute(stmt)
    att = result.scalar_one_or_none()
    if not att:
        return Result.bad_request(message="附件不存在")

    # 删除磁盘文件
    _project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    file_abs_path = _project_root / att.file_path
    if file_abs_path.exists():
        try:
            file_abs_path.unlink()
        except Exception:
            pass  # 文件删除失败不影响数据库记录删除

    # 删除数据库记录
    await db.delete(att)
    await db.flush()

    return Result.ok(message="删除成功")