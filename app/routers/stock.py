from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.database import get_db
from app import models, schemas_stock
from app.services import cleanup_service
from app.dependencies import verify_token
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter(
    prefix="/api/v1/stock",
    tags=["stock-management"],
    # dependencies=[Depends(verify_token)] # Optional: Decide if UI needs token or if it's open like /points
)

templates = Jinja2Templates(directory="templates")

# --- API Endpoints ---

@router.post("/product", response_model=schemas_stock.ProductResponse)
def create_or_update_product(
    product_in: schemas_stock.ProductCreateUpdate, 
    db: Session = Depends(get_db),
    # token: str = Depends(verify_token) # Enable if auth required
):
    # 1. Validate Program ID
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == product_in.program_id).first()
    if not program:
        # For strict validation as requested: "Interface must validate program_id validity"
        # If strict:
        raise HTTPException(status_code=404, detail=f"Mini Program with ID '{product_in.program_id}' not found. Please create the program first.")
        # If loose (auto-create):
        # program = models.MiniProgram(program_id=product_in.program_id, program_name="Unknown")
        # db.add(program)
        # db.flush()

    # 2. Determine Product ID
    p_id = product_in.product_id
    if not p_id:
        p_id = product_in.product_name # Fallback to name as ID
    
    # 3. Check if exists
    product = db.query(models.Product).filter(
        models.Product.program_id == product_in.program_id,
        models.Product.product_id == p_id
    ).first()
    
    if product:
        # Update
        product.product_name = product_in.product_name
        product.image_url = product_in.image_url
        product.points = product_in.points
        if product_in.stock is not None:
            # Record history if stock changed
            if product.stock != product_in.stock:
                history = models.StockHistory(
                    program_id=product.program_id,
                    product_id=product.product_id,
                    old_stock=product.stock,
                    new_stock=product_in.stock,
                    change_time=datetime.utcnow()
                )
                db.add(history)
            product.stock = product_in.stock
    else:
        # Create
        product = models.Product(
            program_id=product_in.program_id,
            product_id=p_id,
            product_name=product_in.product_name,
            image_url=product_in.image_url,
            points=product_in.points,
            stock=product_in.stock if product_in.stock is not None else 0
        )
        db.add(product)
        # Record initial history
        history = models.StockHistory(
            program_id=product_in.program_id,
            product_id=p_id,
            old_stock=0,
            new_stock=product_in.stock if product_in.stock is not None else 0,
            change_time=datetime.utcnow()
        )
        db.add(history)
    
    # Prune history
    try:
        settings = cleanup_service.get_or_create_settings(db)
        cleanup_service.prune_stock_history(db, settings.max_log_entries, settings.max_retention_days)
    except Exception as e:
        print(f"Error pruning stock history: {e}")

    db.commit()
    db.refresh(product)
    return product


@router.get("/programs", response_model=List[schemas_stock.ProgramStockSummary])
def get_programs_stock_summary(db: Session = Depends(get_db)):
    """
    Get list of programs with product count and total stock.
    """
    # Aggregation query
    # We want: program_id, program_name, count(products), sum(products.stock)
    
    results = db.query(
        models.MiniProgram.program_id,
        models.MiniProgram.program_name,
        func.count(models.Product.id).label("product_count"),
        func.sum(models.Product.stock).label("total_stock")
    ).outerjoin(models.Product, models.MiniProgram.program_id == models.Product.program_id)\
     .group_by(models.MiniProgram.program_id, models.MiniProgram.program_name)\
     .order_by(desc(models.MiniProgram.sort_order), desc("total_stock"))\
     .all()
    
    summary_list = []
    for r in results:
        summary_list.append({
            "program_id": r.program_id,
            "program_name": r.program_name or "Unknown",
            "product_count": r.product_count,
            "total_stock": r.total_stock or 0
        })
    return summary_list

@router.get("/programs/{program_id}/products", response_model=schemas_stock.PaginatedProducts)
def get_program_products(
    program_id: str,
    page: int = 1,
    size: int = 20,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(models.Product.program_id == program_id)
    
    if q:
        query = query.filter(models.Product.product_name.contains(q))
    
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }

@router.get("/search", response_model=schemas_stock.PaginatedProducts)
def search_products_global(
    q: str = Query(..., min_length=1),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    """
    Global search for products across all programs.
    """
    query = db.query(models.Product).filter(models.Product.product_name.contains(q))
    
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }

# --- HTML Views ---
# Assuming we want to mount these on a web path, e.g., /stock-manager
# But user request says "Stock Management System", so let's provide APIs and maybe pages.
# The user already has `app/routers/web.py`. We can put page routes there or here.
# Let's keep APIs here. Page routes can be here too if prefixed differently or just use the same router.

@router.get("/view", response_class=HTMLResponse)
def view_stock_dashboard(request: Request):
    return templates.TemplateResponse("stock_dashboard.html", {"request": request})

@router.get("/view/{program_id}", response_class=HTMLResponse)
def view_program_stock(request: Request, program_id: str, db: Session = Depends(get_db)):
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    return templates.TemplateResponse("stock_program_detail.html", {"request": request, "program": program})

