from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from database import DbSession
from models.memo import CONTENT_LIMIT, TITLE_LIMIT
from repositories.memos import MemoRepository
from routers.views import templates
from services.memos import InvalidMemo, MemoNotFound, MemoService

router = APIRouter(prefix="/memos", default_response_class=HTMLResponse)


def get_memo_service(db: DbSession) -> MemoService:
    return MemoService(MemoRepository(db))


MemoServiceDep = Annotated[MemoService, Depends(get_memo_service)]
FormText = Annotated[str, Form()]


def render_form(
    request: Request,
    *,
    memo_id: int | None = None,
    title: str = "",
    content: str = "",
    errors: dict[str, str] | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "memos/form.html",
        {
            "memo_id": memo_id,
            "title": title,
            "content": content,
            "errors": errors or {},
            "title_limit": TITLE_LIMIT,
            "content_limit": CONTENT_LIMIT,
        },
        status_code=422 if errors else 200,
    )


async def memo_not_found(request: Request, _error: MemoNotFound) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "memos/not_found.html", status_code=status.HTTP_404_NOT_FOUND
    )


@router.get("", name="memo_list")
def memo_list(request: Request, service: MemoServiceDep, q: str = "") -> HTMLResponse:
    return templates.TemplateResponse(
        request, "memos/list.html", {"memos": service.list(q), "query": q.strip()}
    )


@router.get("/new", name="memo_new")
def memo_new(request: Request) -> HTMLResponse:
    return render_form(request)


@router.post("", name="memo_create", response_class=RedirectResponse, status_code=303)
def memo_create(
    request: Request, service: MemoServiceDep, title: FormText = "", content: FormText = ""
) -> Response:
    try:
        memo = service.create(title, content)
    except InvalidMemo as error:
        return render_form(request, title=title, content=content, errors=error.errors)
    return RedirectResponse(
        request.app.url_path_for("memo_detail", memo_id=memo.id), status_code=303
    )


@router.get("/{memo_id}", name="memo_detail")
def memo_detail(request: Request, memo_id: int, service: MemoServiceDep) -> HTMLResponse:
    return templates.TemplateResponse(request, "memos/detail.html", {"memo": service.get(memo_id)})


@router.get("/{memo_id}/edit", name="memo_edit")
def memo_edit(request: Request, memo_id: int, service: MemoServiceDep) -> HTMLResponse:
    memo = service.get(memo_id)
    return render_form(request, memo_id=memo.id, title=memo.title, content=memo.content)


@router.post("/{memo_id}/edit", name="memo_update", response_class=RedirectResponse, status_code=303)
def memo_update(
    request: Request,
    memo_id: int,
    service: MemoServiceDep,
    title: FormText = "",
    content: FormText = "",
) -> Response:
    try:
        memo = service.update(memo_id, title, content)
    except InvalidMemo as error:
        return render_form(
            request, memo_id=memo_id, title=title, content=content, errors=error.errors
        )
    return RedirectResponse(
        request.app.url_path_for("memo_detail", memo_id=memo.id), status_code=303
    )


@router.post(
    "/{memo_id}/delete", name="memo_delete", response_class=RedirectResponse, status_code=303
)
def memo_delete(request: Request, memo_id: int, service: MemoServiceDep) -> RedirectResponse:
    service.delete(memo_id)
    return RedirectResponse(request.app.url_path_for("memo_list"), status_code=303)
