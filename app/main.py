from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import qinglong, images, web, stock

app = FastAPI(title="WeChat Points & Stock Monitor")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(web.router)
app.include_router(qinglong.router)
app.include_router(stock.router)
app.include_router(images.router)

# Root path is now handled by web.router
# @app.get("/")
# def read_root():
#     return {"message": "Welcome to WeChat Points & Stock Monitor System"}
