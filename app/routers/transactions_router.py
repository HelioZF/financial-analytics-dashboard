from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_login
from app.database.connection import get_session
from app.schemas.contracts import TransactionListFilters
from app.services.transactions_service import (
    create_transaction,
    list_categories,
    list_transactions,
)


templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")
router = APIRouter(tags=["transactions"])


def _parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_date(value: str | None) -> date | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_type(value: str | None) -> str | None:
    if value in ("income", "expense"):
        return value
    return None


def _build_url(base: str, params: dict, page: int) -> str:
    """Build a URL preserving non-empty filters and overriding page."""
    clean = {k: v for k, v in params.items() if v not in (None, "")}
    clean["page"] = str(page)
    return f"{base}?{urlencode(clean)}"


@router.get("/transactions")
async def transactions_list(
    request: Request,
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    qp = request.query_params

    # Default time window: if user landed with no query params at all, scope
    # to the full current calendar month. Once they submit the form (even with
    # empty fields), respect their explicit choice.
    if not qp:
        today = datetime.now().date()
        last_day = monthrange(today.year, today.month)[1]
        default_from = date(today.year, today.month, 1)
        default_to = date(today.year, today.month, last_day)
    else:
        default_from = None
        default_to = None

    filters = TransactionListFilters(
        category_id=_parse_int(qp.get("category_id")),
        date_from=_parse_date(qp.get("date_from")) or default_from,
        date_to=_parse_date(qp.get("date_to")) or default_to,
        type=_parse_type(qp.get("type")),
        page=_parse_int(qp.get("page")) or 1,
    )

    result = await list_transactions(
        session,
        user_id,
        category_id=filters.category_id,
        date_from=filters.date_from,
        date_to=filters.date_to,
        type_=filters.type,
        page=filters.page,
    )
    categories = await list_categories(session)

    # URL builders for pagination — preserve current filters, swap page.
    base_params = {
        "category_id": filters.category_id,
        "date_from": filters.date_from.isoformat() if filters.date_from else "",
        "date_to": filters.date_to.isoformat() if filters.date_to else "",
        "type": filters.type or "",
    }
    prev_url = (
        _build_url("/transactions", base_params, result.page - 1)
        if result.page > 1
        else None
    )
    next_url = (
        _build_url("/transactions", base_params, result.page + 1)
        if result.page < result.total_pages
        else None
    )

    return templates.TemplateResponse(
        request,
        "transactions/list.html",
        {
            "result": result,
            "filters": filters,
            "categories": categories,
            "prev_url": prev_url,
            "next_url": next_url,
        },
    )


@router.get("/transactions/new")
async def transaction_form(
    request: Request,
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    categories = await list_categories(session)
    return templates.TemplateResponse(
        request,
        "transactions/form.html",
        {
            "categories": categories,
            "form_data": {},
            "errors": [],
        },
    )


@router.post("/transactions/new")
async def transaction_create(
    request: Request,
    amount: str = Form(""),
    category_id: str = Form(""),
    transaction_date: str = Form(""),
    description: str = Form(""),
    user_id: int = Depends(require_login),
    session: AsyncSession = Depends(get_session),
):
    errors: list[str] = []
    parsed_amount: Decimal | None = None
    parsed_category: int | None = None
    parsed_date: date | None = None

    try:
        parsed_amount = Decimal(amount)
        if parsed_amount <= 0:
            errors.append("Amount must be greater than zero.")
            parsed_amount = None
    except (InvalidOperation, ValueError):
        errors.append("Amount must be a valid number (e.g. 12.50).")

    try:
        parsed_category = int(category_id)
    except ValueError:
        errors.append("Please select a category.")

    try:
        parsed_date = date.fromisoformat(transaction_date)
    except ValueError:
        errors.append("Date must be a valid YYYY-MM-DD value.")

    desc = description.strip() or None

    form_data = {
        "amount": amount,
        "category_id": category_id,
        "transaction_date": transaction_date,
        "description": description,
    }

    async def render_errors(error_list: list[str]):
        categories = await list_categories(session)
        return templates.TemplateResponse(
            request,
            "transactions/form.html",
            {
                "categories": categories,
                "form_data": form_data,
                "errors": error_list,
            },
            status_code=400,
        )

    if errors:
        return await render_errors(errors)

    try:
        await create_transaction(
            session,
            user_id,
            amount=parsed_amount,
            category_id=parsed_category,
            transaction_date=parsed_date,
            description=desc,
        )
    except ValueError as exc:
        return await render_errors([str(exc)])

    # PRG pattern: 303 See Other so a reload doesn't re-POST.
    return RedirectResponse("/transactions", status_code=303)
