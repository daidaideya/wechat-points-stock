import os
import uuid

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import verify_token, get_db
from app.config import settings
from app import models

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": (".jpg", (b"\xff\xd8\xff",)),
    "image/png": (".png", (b"\x89PNG\r\n\x1a\n",)),
    "image/gif": (".gif", (b"GIF87a", b"GIF89a")),
    "image/webp": (".webp", (b"RIFF",)),
}

router = APIRouter(
    prefix="/api/v1/upload",
    tags=["upload"],
    dependencies=[Depends(verify_token)]
)

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
