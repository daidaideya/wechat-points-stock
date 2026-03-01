from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models
from datetime import datetime, timedelta
from app.services import cleanup_service

router = APIRouter(
    tags=["web"]
)

templates = Jinja2Templates(directory="templates")

from pydantic import BaseModel
from typing import Optional, List

class AccountUpdate(BaseModel):
    nickname: Optional[str] = None
    device: Optional[str] = None
    phone: Optional[str] = None

class SortOrderUpdate(BaseModel):
    wechat_ids: List[str]

@router.put("/api/v1/accounts/sort-order")
async def update_sort_order(update: SortOrderUpdate, db: Session = Depends(get_db)):
    for index, wechat_id in enumerate(update.wechat_ids):
        account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
        if account:
            account.sort_order = index
            db.add(account)
    db.commit()
    return JSONResponse(content={"status": "success"})

class LogSettingsUpdate(BaseModel):
    max_log_entries: int
    max_retention_days: int

@router.get("/settings")
async def system_settings(request: Request, db: Session = Depends(get_db)):
    s = cleanup_service.get_or_create_settings(db)
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": s
    })

@router.post("/api/v1/settings/logs")
async def update_log_settings(update: LogSettingsUpdate, db: Session = Depends(get_db)):
    s = cleanup_service.get_or_create_settings(db)
    s.max_log_entries = max(0, update.max_log_entries)
    s.max_retention_days = max(0, update.max_retention_days)
    s.updated_at = datetime.utcnow()
    db.add(s)
    # Apply pruning immediately
    cleanup_service.prune_points_history(db, s.max_log_entries, s.max_retention_days)
    cleanup_service.prune_stock_history(db, s.max_log_entries, s.max_retention_days)
    db.commit()
    return JSONResponse(content={"status": "success"})

@router.put("/api/v1/accounts/{wechat_id}")
async def update_account(wechat_id: str, update: AccountUpdate, db: Session = Depends(get_db)):
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        # Create new account if not exists
        account = models.WechatAccount(
            wechat_id=wechat_id, 
            nickname=update.nickname,
            device=update.device,
            phone=update.phone
        )
        db.add(account)
    else:
        if update.nickname is not None:
            account.nickname = update.nickname
        if update.device is not None:
            account.device = update.device
        if update.phone is not None:
            account.phone = update.phone
        db.add(account)
    
    db.commit()
    return JSONResponse(content={"status": "success"})


@router.get("/users")
async def user_list(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(models.WechatAccount).order_by(models.WechatAccount.sort_order.asc(), models.WechatAccount.id.asc()).all()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "accounts": accounts
    })

from sqlalchemy import or_, and_
from pypinyin import pinyin, lazy_pinyin, Style

def get_program_pinyin_data(program_name):
    """Generate pinyin search terms for a program name."""
    if not program_name:
        return []
    
    # Full pinyin (e.g., 'meirishipin')
    full_pinyin = "".join(lazy_pinyin(program_name))
    
    # First letters (e.g., 'mrsp')
    first_letters = "".join([p[0][0] for p in pinyin(program_name, style=Style.FIRST_LETTER)])
    
    return full_pinyin, first_letters

def get_program_last_updates(db: Session, program_ids: List[str]):
    """Get the last update time (report_time) for a list of program IDs."""
    if not program_ids:
        return {}
        
    rows = db.query(
        models.PointsHistory.program_id,
        func.max(models.PointsHistory.report_time)
    ).filter(
        models.PointsHistory.program_id.in_(program_ids)
    ).group_by(models.PointsHistory.program_id).all()
    
    return {r[0]: r[1].isoformat() if r[1] else None for r in rows}

@router.get("/api/v1/programs")
async def get_programs_api(
    request: Request, 
    page: int = 1, 
    size: int = 21, 
    q: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.MiniProgram)
    programs = []
    total = 0
    
    if is_favorite is not None:
        if is_favorite:
            query = query.filter(models.MiniProgram.is_favorite == 1)
        else:
            query = query.filter(or_(models.MiniProgram.is_favorite == 0, models.MiniProgram.is_favorite == None))
    
    if q:
        # ... existing search logic ...
        # If filtering by q, we need to respect is_favorite too.
        # The complex logic below splits memory vs SQL filtering.
        # We need to inject is_favorite filter into that.
        
        # Simplified approach: Apply is_favorite filter to query first (already done above)
        # Then count.
        total_count = query.count() # This query has is_favorite filter if applied
        
        if total_count < 2000:
            # Memory filtering approach
            # Fetch all matching is_favorite first
            all_programs = query.order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()
            filtered_programs = []
            q_lower = q.lower()
            
            for prog in all_programs:
                # 1. Direct match (Name or ID)
                if (prog.program_name and q in prog.program_name) or (q in prog.program_id.lower()):
                    filtered_programs.append(prog)
                    continue
                
                # 2. Pinyin match (if name exists)
                if prog.program_name:
                    full_pinyin, first_letters = get_program_pinyin_data(prog.program_name)
                    if q_lower in full_pinyin or q_lower in first_letters:
                        filtered_programs.append(prog)
                        continue
            
            # Manual pagination
            total = len(filtered_programs)
            start = (page - 1) * size
            end = start + size
            programs = filtered_programs[start:end]
            
        else:
             # Fallback to simple SQL filter for large datasets
             query = query.filter(or_(
                 models.MiniProgram.program_name.contains(q),
                 models.MiniProgram.program_id.contains(q)
             ))
             query = query.order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc())
             total = query.count()
             programs = query.offset((page - 1) * size).limit(size).all()
    else:
        # No search query, just order by sort_order
        query = query.order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc())
        total = query.count()
        programs = query.offset((page - 1) * size).limit(size).all()
    
    # Enhance programs with last_update_time AND has_stock
    program_ids = [p.program_id for p in programs]
    last_updates = get_program_last_updates(db, program_ids)
    
    # Batch check stock existence
    has_stock_map = {}
    if program_ids:
        stock_rows = db.query(models.Product.program_id).filter(models.Product.program_id.in_(program_ids)).distinct().all()
        has_stock_ids = set(r[0] for r in stock_rows)
        for pid in program_ids:
            has_stock_map[pid] = pid in has_stock_ids
    
    items = []
    for p in programs:
        item = {
            "id": p.id,
            "program_id": p.program_id,
            "program_name": p.program_name,
            "auth_type": p.auth_type,
            "sort_order": p.sort_order,
            "is_favorite": p.is_favorite == 1,
            "last_update_time": last_updates.get(p.program_id),
            "has_stock": has_stock_map.get(p.program_id, False),
            "note": p.note
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "has_more": (page * size) < total
    }

@router.get("/api/v1/programs/{program_id}/stock")
async def get_program_stock(program_id: str, db: Session = Depends(get_db)):
    """Get all products for a specific program and the max points held by any user."""
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    products = db.query(models.Product).filter(models.Product.program_id == program_id).all()
    
    # Calculate max points currently held by any user for this program
    # 1. Get latest report_time for each user for this program
    subquery = db.query(
        models.PointsHistory.wechat_id,
        func.max(models.PointsHistory.report_time).label('max_time')
    ).filter(
        models.PointsHistory.program_id == program_id
    ).group_by(
        models.PointsHistory.wechat_id
    ).subquery()
    
    # 2. Get the points from those latest records and find the max
    # We query PointsHistory joined with subquery
    max_points_val = db.query(func.max(models.PointsHistory.points)).join(
        subquery, 
        and_(
            models.PointsHistory.wechat_id == subquery.c.wechat_id,
            models.PointsHistory.report_time == subquery.c.max_time
        )
    ).scalar()
    
    current_max_user_points = max_points_val if max_points_val is not None else 0
    
    items = []
    for p in products:
        img_url = p.image_url
        if p.image_local_path:
            # Check if it's a relative path in static folder or absolute path
            # Assuming images are stored in 'static/images/' and image_local_path stores that relative path
            # or stores absolute path.
            # If it stores "static/images/foo.jpg", we want "/static/images/foo.jpg"
            # If it stores absolute "/root/.../static/images/foo.jpg", we need to strip.
            # Let's assume standard storage: "static/images/..."
            
            path_str = str(p.image_local_path)
            if "static/" in path_str:
                # Extract part after "static/" and prepend "/static/"
                # Or if it starts with static, just prepend /
                if not path_str.startswith("/"):
                    img_url = "/" + path_str
                else:
                    # If it's absolute, find static index
                    idx = path_str.find("/static/")
                    if idx != -1:
                        img_url = path_str[idx:]
            
        items.append({
            "product_name": p.product_name,
            "points": p.points,
            "stock": p.stock,
            "image_url": img_url
        })
        
    # Default Sort: by stock desc (available first), then points asc
    items.sort(key=lambda x: (x['stock'] <= 0, x['points']))
    
    return {
        "program_name": program.program_name if program else program_id,
        "max_user_points": current_max_user_points,
        "products": items
    }

@router.get("/api/v1/programs/favorites")
async def get_favorite_programs(db: Session = Depends(get_db)):
    """Get list of favorite programs."""
    programs = db.query(models.MiniProgram).filter(models.MiniProgram.is_favorite == 1).order_by(models.MiniProgram.id.asc()).all()
    
    items = []
    for p in programs:
        items.append({
            "program_id": p.program_id,
            "program_name": p.program_name or p.program_id
        })
        
    return {"items": items}

@router.get("/favorites")
async def favorites_list(request: Request, db: Session = Depends(get_db)):
    # Render page 1 (first 21 items) server-side, similar to /programs
    programs = db.query(models.MiniProgram).filter(models.MiniProgram.is_favorite == 1).order_by(models.MiniProgram.id.asc()).limit(21).all()
    
    program_ids = [p.program_id for p in programs]
    last_updates = get_program_last_updates(db, program_ids)
    
    # Batch check stock existence
    has_stock_map = {}
    if program_ids:
        stock_rows = db.query(models.Product.program_id).filter(models.Product.program_id.in_(program_ids)).distinct().all()
        has_stock_ids = set(r[0] for r in stock_rows)
        for pid in program_ids:
            has_stock_map[pid] = pid in has_stock_ids
    
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "programs": programs,
        "last_updates": last_updates,
        "has_stock_map": has_stock_map
    })

@router.get("/programs")
async def program_list(request: Request, db: Session = Depends(get_db)):
    programs = db.query(models.MiniProgram).order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).limit(21).all()
    
    program_ids = [p.program_id for p in programs]
    last_updates = get_program_last_updates(db, program_ids)

    # Batch check stock existence for server-side first page rendering
    has_stock_map = {}
    if program_ids:
        stock_rows = db.query(models.Product.program_id).filter(models.Product.program_id.in_(program_ids)).distinct().all()
        has_stock_ids = set(r[0] for r in stock_rows)
        for pid in program_ids:
            has_stock_map[pid] = pid in has_stock_ids
    
    return templates.TemplateResponse("programs.html", {
        "request": request,
        "programs": programs,
        "last_updates": last_updates,
        "has_stock_map": has_stock_map
    })

@router.get("/api/v1/programs/{program_id}/rankings")
async def get_program_rankings(program_id: str, db: Session = Depends(get_db)):
    """Get user points ranking for a specific program."""
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    
    # 1. Get all accounts
    all_accounts = db.query(models.WechatAccount).order_by(models.WechatAccount.sort_order.asc(), models.WechatAccount.id.asc()).all()
    
    # 2. Get latest points for this program
    history = db.query(models.PointsHistory).filter(
        models.PointsHistory.program_id == program_id
    ).order_by(models.PointsHistory.report_time.desc()).all()
    
    user_points_map = {}
    for h in history:
        if h.wechat_id not in user_points_map:
            user_points_map[h.wechat_id] = h

    # 3. Merge all accounts
    rankings = []
    for acc in all_accounts:
        points = 0
        report_time = None
        
        if acc.wechat_id in user_points_map:
            h = user_points_map[acc.wechat_id]
            points = h.points
            report_time = h.report_time.strftime('%Y-%m-%d %H:%M:%S') if h.report_time else None
            
        rankings.append({
            "nickname": acc.nickname,
            "wechat_id": acc.wechat_id,
            "device": acc.device,
            "phone": acc.phone,
            "points": points,
            "report_time": report_time
        })

    # Sort by points desc
    rankings.sort(key=lambda x: x['points'], reverse=True)
    
    return {
        "program_name": program.program_name if program else program_id,
        "rankings": rankings
    }

@router.get("/api/v1/programs/{program_id}/ranking")
async def get_program_ranking(program_id: str, sort: Optional[str] = None, db: Session = Depends(get_db)):
    """API to get user points ranking for a specific program."""
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    
    # 1. Get all accounts
    all_accounts = db.query(models.WechatAccount).order_by(models.WechatAccount.sort_order.asc(), models.WechatAccount.id.asc()).all()
    
    # 2. Get latest points for this program
    history = db.query(models.PointsHistory).filter(
        models.PointsHistory.program_id == program_id
    ).order_by(models.PointsHistory.report_time.desc()).all()
    
    user_points_map = {}
    for h in history:
        if h.wechat_id not in user_points_map:
            user_points_map[h.wechat_id] = h

    # 3. Merge all accounts
    user_points_list = []
    for acc in all_accounts:
        points_val = 0
        report_time = None
        
        if acc.wechat_id in user_points_map:
            h = user_points_map[acc.wechat_id]
            points_val = h.points
            report_time = h.report_time.strftime('%Y-%m-%d %H:%M:%S') if h.report_time else None
        
        user_points_list.append({
            "wechat_id": acc.wechat_id,
            "nickname": acc.nickname,
            "device": acc.device,
            "phone": acc.phone,
            "points": points_val,
            "report_time": report_time
        })

    # Convert to list and sort by points
    reverse_sort = True
    if sort == 'asc':
        reverse_sort = False
        
    user_points_list.sort(key=lambda x: x['points'], reverse=reverse_sort)
    
    program_name = program.program_name if program and program.program_name else program_id
    
    return {
        "program_name": program_name,
        "program_id": program_id,
        "ranking": user_points_list
    }

@router.get("/programs/{program_id}")
async def program_details(program_id: str, request: Request, sort: Optional[str] = None, db: Session = Depends(get_db)):
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    if not program:
        # If program doesn't exist in mini_programs table but has points history, we might want to create a dummy obj
        # Or just return 404. Let's return 404 for now, or just show ID.
        # But wait, we might have points history for programs not in MiniProgram table? 
        # Ideally they should be synced. Let's assume strict relation or create a dummy object if needed.
        # For robustness, if not found, create a dummy object with ID.
        program = models.MiniProgram(program_id=program_id, program_name=program_id)
    
    # 1. Get all accounts to ensure we list everyone
    all_accounts = db.query(models.WechatAccount).order_by(models.WechatAccount.sort_order.asc(), models.WechatAccount.id.asc()).all()
    
    # 2. Get latest points for this program
    history = db.query(models.PointsHistory).filter(
        models.PointsHistory.program_id == program_id
    ).order_by(models.PointsHistory.report_time.desc()).all()
    
    user_points_map = {}
    for h in history:
        if h.wechat_id not in user_points_map:
            user_points_map[h.wechat_id] = h

    class DummyUserPoint:
        def __init__(self, account):
            self.account = account
            self.wechat_id = account.wechat_id
            self.points = 0  # Treat as 0/Unregistered
            self.report_time = None

    # 3. Merge all accounts
    user_points_list = []
    for acc in all_accounts:
        if acc.wechat_id in user_points_map:
            user_points_list.append(user_points_map[acc.wechat_id])
        else:
            user_points_list.append(DummyUserPoint(acc))

    # Convert to list and sort by points
    # Default is descending (High to Low), if sort='asc' then ascending (Low to High)
    reverse_sort = True
    if sort == 'asc':
        reverse_sort = False
        
    user_points_list.sort(key=lambda x: x.points, reverse=reverse_sort)
    
    return templates.TemplateResponse("program_details.html", {
        "request": request,
        "program": program,
        "user_points": user_points_list
    })

class ProgramUpdate(BaseModel):
    auth_type: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    note: Optional[str] = None

@router.put("/api/v1/programs/{program_id}")
async def update_program(program_id: str, update: ProgramUpdate, db: Session = Depends(get_db)):
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    if not program:
        # Should we auto-create if missing? 
        # Typically update expects existence, but for robustness let's create if missing 
        # (similar to details view logic)
        program = models.MiniProgram(program_id=program_id, program_name=program_id)
        db.add(program)
    
    if update.auth_type is not None:
        if update.auth_type not in ["code", "token", "app"]:
            raise HTTPException(status_code=400, detail="Invalid auth type")
        program.auth_type = update.auth_type
        
    if update.is_pinned is not None:
        # Backward compatibility / Migration
        # We repurpose sort_order as is_favorite logic if needed, but we have separate column now.
        # Let's keep sort_order untouched or set to 0.
        program.sort_order = 1 if update.is_pinned else 0
        
    if update.is_favorite is not None:
        program.is_favorite = 1 if update.is_favorite else 0

    if update.note is not None:
        program.note = update.note
        
    db.commit()
    return JSONResponse(content={"status": "success"})

@router.delete("/api/v1/programs/{program_id}")
async def delete_program(program_id: str, db: Session = Depends(get_db)):
    # Check if program exists
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    
    # Delete related points history
    db.query(models.PointsHistory).filter(models.PointsHistory.program_id == program_id).delete()
    
    # Delete related products
    db.query(models.Product).filter(models.Product.program_id == program_id).delete()
    
    # Delete program if exists
    if program:
        db.delete(program)
    
    db.commit()
    return JSONResponse(content={"status": "success"})

@router.delete("/api/v1/accounts/{wechat_id}")
async def delete_account(wechat_id: str, db: Session = Depends(get_db)):
    # Check if account exists
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Delete related points history
    db.query(models.PointsHistory).filter(models.PointsHistory.wechat_id == wechat_id).delete()
    
    # Delete account
    db.delete(account)
    db.commit()
    return JSONResponse(content={"status": "success"})

@router.delete("/api/v1/accounts/{wechat_id}/programs/{program_id}")
async def delete_program_points(wechat_id: str, program_id: str, db: Session = Depends(get_db)):
    # Delete points history for this specific account and program
    deleted_count = db.query(models.PointsHistory).filter(
        models.PointsHistory.wechat_id == wechat_id,
        models.PointsHistory.program_id == program_id
    ).delete()
    
    db.commit()
    return JSONResponse(content={"status": "success", "deleted_count": deleted_count})

@router.get("/api/v1/programs/unreported")
async def get_unreported_programs(db: Session = Depends(get_db)):
    """Get list of programs that haven't been updated today."""
    # 1. Get all programs
    programs = db.query(models.MiniProgram).all()
    program_ids = [p.program_id for p in programs]
    
    # 2. Get last updates
    last_updates = get_program_last_updates(db, program_ids)
    
    # 3. Filter for unreported today
    # Logic: If last_update is None OR date part != today's date
    # Note: We treat the DB time as "Local" time string directly, matching frontend logic
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    unreported = []
    for p in programs:
        last_time_iso = last_updates.get(p.program_id)
        is_reported_today = False
        
        if last_time_iso:
            # Extract YYYY-MM-DD from ISO string
            # ISO format is typically 'YYYY-MM-DDTHH:MM:SS.ssssss'
            last_date_str = last_time_iso.split('T')[0]
            if last_date_str == today_str:
                is_reported_today = True
        
        if not is_reported_today:
            unreported.append({
                "program_id": p.program_id,
                "program_name": p.program_name or p.program_id,
                "last_report_time": last_time_iso
            })
            
    return {"items": unreported}

@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Statistics
    account_count = db.query(models.WechatAccount).count()
    program_count = db.query(models.MiniProgram).count()
    
    # Calculate unreported count
    # We can reuse the logic, but optimized for count if possible.
    # For now, let's just do the same logic as it's robust.
    programs = db.query(models.MiniProgram).all()
    program_ids = [p.program_id for p in programs]
    last_updates = get_program_last_updates(db, program_ids)
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    unreported_count = 0
    
    for pid in program_ids:
        last_time_iso = last_updates.get(pid)
        is_reported_today = False
        if last_time_iso:
            last_date_str = last_time_iso.split('T')[0]
            if last_date_str == today_str:
                is_reported_today = True
        
        if not is_reported_today:
            unreported_count += 1

    points_records_count = db.query(models.PointsHistory).count()
    
    # New Metrics
    total_products_count = db.query(models.Product).count()
    out_of_stock_count = db.query(models.Product).filter(models.Product.stock == 0).count()
    favorite_count = db.query(models.MiniProgram).filter(models.MiniProgram.is_favorite == 1).count()
    token_auth_count = db.query(models.MiniProgram).filter(models.MiniProgram.auth_type == 'token').count()
    cached_images_count = db.query(models.Product).filter(models.Product.image_local_path.isnot(None)).count()
    
    # Active accounts today (UTC based, approximate for today)
    # Ideally should align with "Unreported" logic which checks ISO strings
    # But SQL filter is faster. Let's use simple UTC start of day.
    # Actually, unreported logic uses "today_str" based on local machine time.
    # Let's match that.
    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # Adjust for potential timezone mismatch if DB is UTC but app is CST. 
    # Assuming DB stores UTC.
    # If app is running in CST (China), datetime.now() is CST. 
    # start_of_day (CST) -> UTC is -8 hours.
    # Let's just use the string comparison logic for consistency if volume is low, 
    # OR use a roughly correct timestamp.
    # Given the scale, query is better.
    # Let's assume report_time is UTC. 
    # CST Today 00:00 = UTC Yesterday 16:00.
    start_of_day_utc = start_of_day - timedelta(hours=8)
    active_accounts_today = db.query(models.PointsHistory.wechat_id).filter(
        models.PointsHistory.report_time >= start_of_day_utc
    ).distinct().count()

    # Recent Activities: Get top 5 distinct mini program updates
    # We fetch a larger batch first, then deduplicate by program_id in Python
    raw_history = db.query(models.PointsHistory).order_by(models.PointsHistory.report_time.desc()).limit(50).all()
    
    recent_program_updates = []
    seen_programs = set()
    
    for h in raw_history:
        if h.program_id not in seen_programs:
            recent_program_updates.append(h)
            seen_programs.add(h.program_id)
            if len(recent_program_updates) >= 5:
                break
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "account_count": account_count,
        "program_count": program_count,
        "unreported_count": unreported_count,
        "points_records_count": points_records_count,
        "recent_program_updates": recent_program_updates,
        "total_products_count": total_products_count,
        "out_of_stock_count": out_of_stock_count,
        "favorite_count": favorite_count,
        "token_auth_count": token_auth_count,
        "cached_images_count": cached_images_count,
        "active_accounts_today": active_accounts_today
    })

@router.get("/api/v1/accounts/{wechat_id}/points_details")
async def get_account_points_details(wechat_id: str, db: Session = Depends(get_db)):
    # Get all programs
    all_programs = db.query(models.MiniProgram).all()
    
    # Get latest points for each program for this account
    user_points = db.query(models.PointsHistory).filter(
        models.PointsHistory.wechat_id == wechat_id
    ).order_by(models.PointsHistory.report_time.desc()).all()
    
    # Group history by program_id
    from collections import defaultdict
    history_map = defaultdict(list)
    for p in user_points:
        history_map[p.program_id].append(p)
    
    # Deduplicate by program_id (keep first/latest)
    latest_map = {}
    for p in user_points:
        if p.program_id not in latest_map:
            latest_map[p.program_id] = p
    
    # Helper to calculate daily diff
    # Today is based on CST (UTC+8) to match WeChat context
    tz_offset = timedelta(hours=8)
    now_cst = datetime.utcnow() + tz_offset
    today_cst_date = now_cst.date()

    def calculate_diff(program_id, current_points):
        if current_points == "未注册":
            return 0
        
        records = history_map.get(program_id, [])
        if not records:
            return 0 # Should not happen if current_points is valid
            
        latest = records[0]
        # Check if latest update is today (CST)
        latest_cst = (latest.report_time or datetime.utcnow()) + tz_offset
        
        if latest_cst.date() == today_cst_date:
            # It updated today. Find last value from before today.
            prev_points = 0 # Default baseline for new users
            found_prev = False
            for r in records[1:]:
                r_cst = (r.report_time or datetime.utcnow()) + tz_offset
                if r_cst.date() < today_cst_date:
                    prev_points = r.points
                    found_prev = True
                    break
            
            # If no previous record found (e.g. first day), treat prev as 0.
            # Diff = current - 0
            return current_points - prev_points
        else:
            # Latest update was before today. No change today.
            return 0

    final_points_list = []
    processed_program_ids = set()
    
    # 1. Add programs from the master list
    for prog in all_programs:
        processed_program_ids.add(prog.program_id)
        if prog.program_id in latest_map:
            p = latest_map[prog.program_id]
            final_points_list.append({
                "program_id": p.program_id,
                "program_name": p.program.program_name if p.program else p.program_id,
                "points": p.points,
                "diff": calculate_diff(p.program_id, p.points),
                "report_time": p.report_time.strftime('%Y-%m-%d %H:%M:%S') if p.report_time else None
            })
        else:
            final_points_list.append({
                "program_id": prog.program_id,
                "program_name": prog.program_name or prog.program_id,
                "points": "未注册",
                "diff": 0,
                "report_time": None
            })
            
    # 2. Add any leftover programs that user has but aren't in the master list
    for pid, p_obj in latest_map.items():
        if pid not in processed_program_ids:
            final_points_list.append({
                "program_id": p_obj.program_id,
                "program_name": p_obj.program.program_name if p_obj.program else p_obj.program_id,
                "points": p_obj.points,
                "diff": calculate_diff(p_obj.program_id, p_obj.points),
                "report_time": p_obj.report_time.strftime('%Y-%m-%d %H:%M:%S') if p_obj.report_time else None
            })
            
    # Sort by points: Unregistered (0/"未注册") first, then others desc
    # "未注册" is a string, others are numbers.
    # Logic:
    # 1. Unregistered ("未注册")
    # 2. 0 points
    # 3. >0 points (descending)
    
    def sort_key(item):
        p = item['points']
        if p == "未注册":
            return (0, 0) # Priority 0 (Highest)
        elif p == 0:
            return (1, 0) # Priority 1
        else:
            return (2, -p) # Priority 2, then negative points for desc sort
            
    final_points_list.sort(key=sort_key)
            
    return final_points_list

@router.get("/points")
async def points_list(request: Request, db: Session = Depends(get_db)):
    # Group points by Wechat Account
    accounts = db.query(models.WechatAccount).all()
    
    # Get all programs to ensure we show them even if user has no points
    all_programs = db.query(models.MiniProgram).all()
    
    class DummyPoint:
        def __init__(self, program):
            self.program = program
            self.program_id = program.program_id
            self.points = "未注册"
            self.report_time = None

    data = []
    for acc in accounts:
        # Get latest points for each program for this account
        user_points = db.query(models.PointsHistory).filter(
            models.PointsHistory.wechat_id == acc.wechat_id
        ).order_by(models.PointsHistory.report_time.desc()).all()
        
        # Deduplicate by program_id (keep first/latest)
        latest_map = {}
        for p in user_points:
            if p.program_id not in latest_map:
                latest_map[p.program_id] = p
        
        # Calculate active programs count directly
        # Active = points != 0 and points != "未注册"
        # Since we are iterating all programs + history, we can check.
        
        active_count = 0
        processed_program_ids = set()
        
        # Check master programs
        for prog in all_programs:
            processed_program_ids.add(prog.program_id)
            if prog.program_id in latest_map:
                p = latest_map[prog.program_id]
                if p.points != 0:
                    active_count += 1
            else:
                # DummyPoint is "未注册", so not active
                pass
                
        # Check leftovers
        for pid, p_obj in latest_map.items():
            if pid not in processed_program_ids:
                if p_obj.points != 0:
                    active_count += 1

        data.append({
            "account": acc,
            "points": [], # Empty list to avoid rendering details server-side
            "active_program_count": active_count
        })
        
    return templates.TemplateResponse("points.html", {
        "request": request,
        "data": data
    })

@router.get("/stock")
async def stock_list(
    request: Request, 
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Get products query
    query = db.query(models.Product)
    
    if q:
        query = query.filter(models.Product.product_name.contains(q))
        
    products = query.all()
    
    # Pre-calculate max user points per program
    # This gets the max points ever recorded for each program.
    # Ideally we should get max of *current* points per user, but for simplicity/performance
    # we take the max of history. Since history is usually append-only and increasing or fluctuating,
    # "Highest ever" or "Highest recent" is a good proxy.
    # To be more precise: Get latest record for each (program, user), then max of those.
    # But doing that in SQL for all programs is complex.
    # Let's just get the simple max(points) from history for each program.
    # It represents "Highest score seen".
    
    max_user_points_query = db.query(
        models.PointsHistory.program_id,
        func.max(models.PointsHistory.points).label('max_points')
    ).group_by(models.PointsHistory.program_id).all()
    
    max_user_points_map = {r.program_id: r.max_points for r in max_user_points_query}

    # Group products by program
    products_by_program = {}
    for product in products:
        # Normalize image url for direct inline thumbnail display
        display_image_url = None
        if product.image_local_path:
            path_str = str(product.image_local_path)
            if path_str.startswith("/static/"):
                display_image_url = path_str
            elif path_str.startswith("static/"):
                display_image_url = "/" + path_str
            else:
                display_image_url = path_str
        elif product.image_url:
            display_image_url = str(product.image_url)

        # Attach transient attribute for template rendering
        product.display_image_url = display_image_url

        program_id = product.program_id
        if program_id not in products_by_program:
            program_name = product.program.program_name if product.program else program_id
            products_by_program[program_id] = {
                "program_name": program_name,
                "products": [],
                "max_user_points": max_user_points_map.get(program_id, 0)
            }
        products_by_program[program_id]["products"].append(product)
    
    return templates.TemplateResponse("stock.html", {
        "request": request,
        "products_by_program": products_by_program,
        "q": q
    })
