from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_login
from app.database.connection import get_session
from app.services.export_service import transactions_to_csv


router = APIRouter(tags=["export"])


@router.get("/export/csv")
async def export_csv(
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        transactions_to_csv(session, user_id),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
