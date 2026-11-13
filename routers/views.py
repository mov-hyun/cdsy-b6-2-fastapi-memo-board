from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import PROJECT_DIR

router = APIRouter(default_response_class=HTMLResponse)
templates = Jinja2Templates(directory=PROJECT_DIR / "templates")
KST = timezone(timedelta(hours=9))


def format_kst(value: datetime, format_string: str = "%Y.%m.%d %H:%M") -> str:
    return value.replace(tzinfo=timezone.utc).astimezone(KST).strftime(format_string)


templates.env.filters["kst"] = format_kst


@router.get("/", name="home")
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html")
