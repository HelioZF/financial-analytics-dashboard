from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_login
from app.database.connection import get_session
from app.services.expenses_service import get_expenses_data


templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")
router = APIRouter(tags=["expenses"])


@router.get("/expenses")
async def expenses_page(
    request: Request,
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now()
    data = await get_expenses_data(session, user_id, now.year)
    return templates.TemplateResponse(
        request,
        "expenses/summary.html",
        {
            "data": data,
            # Only the chart payloads need JSON; top_items renders server-side
            # as HTML table so the date field doesn't need a custom encoder.
            "monthly_json": [asdict(m) for m in data.monthly_totals],
            "breakdown_json": [asdict(c) for c in data.category_breakdown],
        },
    )
