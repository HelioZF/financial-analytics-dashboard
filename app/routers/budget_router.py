from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_login
from app.database.connection import get_session
from app.services.budget_service import get_budget_data


templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")
router = APIRouter(tags=["budget"])


@router.get("/budget")
async def budget_page(
    request: Request,
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now()
    data = await get_budget_data(session, user_id, now.month, now.year)
    return templates.TemplateResponse(
        request,
        "budget/summary.html",
        {"data": data},
    )
