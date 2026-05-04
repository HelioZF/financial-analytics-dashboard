from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.auth import router as auth_router
from app.routers.overview_router import router as overview_router
from app.routers.expenses_router import router as expenses_router
from app.routers.income_router import router as income_router
from app.routers.budget_router import router as budget_router
from app.routers.transactions_router import router as transactions_router
from app.routers.export_router import router as export_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Finance Dashboard", version="0.1.0")

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, max_age=60*60*24)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# Include routers
app.include_router(auth_router)
app.include_router(overview_router)
app.include_router(expenses_router)
app.include_router(income_router)
app.include_router(budget_router)
app.include_router(transactions_router)
app.include_router(export_router)


# income
# budgets
# transactions
# reports
# export

@app.get("/")
async def read_root(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/overview", status_code=302)
    return RedirectResponse(url="/login", status_code=302)
    
@app.get("/health")
async def health_check():
    return {"status": "ok"}