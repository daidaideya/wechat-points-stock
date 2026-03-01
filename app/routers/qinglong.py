from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas
from app.dependencies import verify_token, get_db
from app.services import qinglong_service

router = APIRouter(
    tags=["qinglong"],
    dependencies=[Depends(verify_token)]
)

@router.post("/api/v1/qinglong/report")
def report_points(report: schemas.PointsReportRequest, db: Session = Depends(get_db)):
    return qinglong_service.process_points_report(db, report)

@router.post("/api/v1/stock-report")
def report_stock(report: schemas.StockReportRequest, db: Session = Depends(get_db)):
    return qinglong_service.process_stock_report(db, report)
