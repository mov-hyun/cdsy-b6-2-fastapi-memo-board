from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import PROJECT_DIR, Base, engine
from routers import memos, views
from services.memos import MemoNotFound


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="메모 게시판", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=PROJECT_DIR / "static"), name="static")
app.include_router(views.router)
app.include_router(memos.router)
app.add_exception_handler(MemoNotFound, memos.memo_not_found)
