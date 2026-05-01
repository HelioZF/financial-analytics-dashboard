from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_login
from app.database.connection import get_session
from app.services.overview_service import get_overview_data


templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")
router = APIRouter(tags=["overview"])


@router.get("/overview")
async def overview_page(
    request: Request,
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now()
    data = await get_overview_data(session, user_id, now.month, now.year)
    return templates.TemplateResponse(
        request,
        "overview/summary.html",
        {
            "data": data,
            # Pre-converted for the template's `tojson` filter — the standard
            # JSON encoder doesn't know how to serialize dataclasses.
            "monthly_json": [asdict(m) for m in data.monthly_data],
            "income_json": [asdict(c) for c in data.income_breakdown],
            "expense_json": [asdict(c) for c in data.expense_breakdown],
        },
    )
