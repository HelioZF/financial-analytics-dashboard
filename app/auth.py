from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session


# IMPROVE (optional): hash_password lives in seed/seed.py, verify_password lives here.
#   Consider extracting both into app/security.py so auth logic has one home.
#   Not required for this fix — just a cleaner structure if you want it later.
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


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
    return templates.TemplateResponse(request, "login.html", {"error": error})



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
