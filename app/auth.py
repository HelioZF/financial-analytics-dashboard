from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def require_login(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=302,
            headers={"Location": "/login"},
        )
    return user_id


router = APIRouter(tags=["auth"])


@router.get("/login")
async def login_form(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        text("SELECT id, password_hash FROM users WHERE username = :u"),
        {"u": username},
    )
    row = result.first()
    if not row or not verify_password(password, row.password_hash):
        return RedirectResponse("/login?error=invalid", status_code=302)
    request.session["user_id"] = row.id
    return RedirectResponse("/", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
