from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_login
from app.database.connection import get_session
from app.services.income_service import get_income_data


templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")
router = APIRouter(tags=["income"])


@router.get("/income")
async def income_page(
    request: Request,
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now()
    data = await get_income_data(session, user_id, now.year)
    return templates.TemplateResponse(
        request,
        "income/summary.html",
        {
            "data": data,
            "monthly_json": [asdict(m) for m in data.monthly_totals],
            "breakdown_json": [asdict(c) for c in data.category_breakdown],
        },
    )
