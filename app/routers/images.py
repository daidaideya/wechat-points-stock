from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.dependencies import verify_token, get_db
from app.config import settings
from app import models
import shutil
import os
import uuid

router = APIRouter(
    prefix="/api/v1/upload",
    tags=["upload"],
    dependencies=[Depends(verify_token)]
)

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    product_id: str = Form(None),
    program_id: str = Form(None),
    db: Session = Depends(get_db)
):
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    if product_id:
        # Sanitize product_id to be safe for filename
        safe_pid = "".join(c for c in product_id if c.isalnum() or c in ('-', '_'))
        filename = f"{safe_pid}_{filename}"
        
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
        
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
