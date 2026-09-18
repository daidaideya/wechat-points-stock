import os
import struct
import uuid

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import verify_token, get_db
from app.config import settings
from app import models

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": (".jpg", (b"\xff\xd8\xff",)),
    "image/png": (".png", (b"\x89PNG\r\n\x1a\n",)),
    "image/gif": (".gif", (b"GIF87a", b"GIF89a")),
    "image/webp": (".webp", (b"RIFF",)),
}

JPEG_SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}

router = APIRouter(
    prefix="/api/v1/upload",
    tags=["upload"],
    dependencies=[Depends(verify_token)]
)


def _jpeg_dimensions(data: bytes):
    if not data.startswith(b"\xff\xd8"):
        return None

    offset = 2
    while offset + 3 < len(data):
        if data[offset] != 0xFF:
            return None
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            return None

        marker = data[offset]
        offset += 1
        if marker in {0x01, 0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            return None

        segment_length = struct.unpack_from(">H", data, offset)[0]
        if segment_length < 2 or offset + segment_length > len(data):
            return None
        if marker in JPEG_SOF_MARKERS and segment_length >= 7:
            height, width = struct.unpack_from(">HH", data, offset + 3)
            return width, height
        offset += segment_length
    return None


def _webp_dimensions(data: bytes):
    if len(data) < 16 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None

    offset = 12
    while offset + 8 <= len(data):
        chunk_type = data[offset : offset + 4]
        chunk_size = struct.unpack_from("<I", data, offset + 4)[0]
        payload_start = offset + 8
        payload_end = payload_start + chunk_size
        if payload_end > len(data):
            return None
        payload = data[payload_start:payload_end]

        if chunk_type == b"VP8X" and len(payload) >= 10:
            width = 1 + int.from_bytes(payload[4:7], "little")
            height = 1 + int.from_bytes(payload[7:10], "little")
            return width, height
        if chunk_type == b"VP8 " and len(payload) >= 10:
            frame_start = payload.find(b"\x9d\x01\x2a")
            if frame_start >= 0 and frame_start + 7 <= len(payload):
                width, height = struct.unpack_from("<HH", payload, frame_start + 3)
                return width & 0x3FFF, height & 0x3FFF
        if chunk_type == b"VP8L" and len(payload) >= 5 and payload[0] == 0x2F:
            width = 1 + ((payload[1] | (payload[2] << 8)) & 0x3FFF)
            height = 1 + (((payload[2] >> 6) | (payload[3] << 2) | (payload[4] << 10)) & 0x3FFF)
            return width, height

        offset = payload_end + (chunk_size & 1)
    return None


def _image_dimensions(path: str, content_type: str):
    with open(path, "rb") as source:
        data = source.read(MAX_UPLOAD_BYTES + 1)

    if content_type == "image/png":
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            return None
        return struct.unpack_from(">II", data, 16)
    if content_type == "image/gif":
        if len(data) < 10 or data[:6] not in (b"GIF87a", b"GIF89a"):
            return None
        return struct.unpack_from("<HH", data, 6)
    if content_type == "image/jpeg":
        return _jpeg_dimensions(data)
    if content_type == "image/webp":
        return _webp_dimensions(data)
    return None


def _validate_image_dimensions(path: str, content_type: str):
    dimensions = _image_dimensions(path, content_type)
    if not dimensions or dimensions[0] <= 0 or dimensions[1] <= 0:
        raise HTTPException(status_code=400, detail="无法解析图片尺寸")
    width, height = dimensions
    if width * height > MAX_IMAGE_PIXELS:
        raise HTTPException(status_code=413, detail="图片像素不能超过 25 MP")

@router.post("/image")
def upload_image(
    file: UploadFile = File(...),
    product_id: str = Form(None),
    program_id: str = Form(None),
    db: Session = Depends(get_db)
):
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    content_type = (file.content_type or "").lower().strip()
    image_format = ALLOWED_IMAGE_TYPES.get(content_type)
    if image_format is None:
        raise HTTPException(status_code=415, detail="仅支持 JPEG、PNG、GIF、WebP 图片")

    ext, signatures = image_format
    first_chunk = file.file.read(32)
    signature_ok = any(first_chunk.startswith(signature) for signature in signatures)
    if content_type == "image/webp":
        signature_ok = first_chunk.startswith(b"RIFF") and first_chunk[8:12] == b"WEBP"
    if not first_chunk or not signature_ok:
        raise HTTPException(status_code=400, detail="上传内容不是有效的图片文件")

    # Generate a server-controlled filename; never trust the client extension.
    filename = f"{uuid.uuid4()}{ext}"
    if product_id:
        # Sanitize product_id to be safe for filename
        safe_pid = "".join(c for c in product_id if c.isalnum() or c in ('-', '_'))
        filename = f"{safe_pid}_{filename}"
        
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file in bounded chunks so a forged Content-Length cannot exhaust disk.
    total_bytes = len(first_chunk)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(first_chunk)
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="图片不能超过 10 MiB")
                buffer.write(chunk)
    except Exception:
        try:
            os.unlink(file_path)
        except OSError:
            pass
        raise
    finally:
        file.file.close()

    if total_bytes <= len(first_chunk):
        try:
            os.unlink(file_path)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail="图片内容为空")

    try:
        _validate_image_dimensions(file_path, content_type)
    except HTTPException:
        try:
            os.unlink(file_path)
        except OSError:
            pass
        raise
    except Exception as exc:
        try:
            os.unlink(file_path)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail="无法解析图片尺寸") from exc
        
    # Update Product if product_id provided
    if product_id and program_id:
        product = db.query(models.Product).filter(
            models.Product.program_id == program_id,
            models.Product.product_id == product_id
        ).first()
        
        if product:
            # Store relative path for web access
            relative_path = f"/static/uploads/{filename}"
            product.image_local_path = relative_path
            db.commit()
            
    return {"filename": filename, "path": f"/static/uploads/{filename}"}
