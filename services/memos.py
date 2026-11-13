from dataclasses import dataclass
from datetime import datetime, timezone

from models.memo import CONTENT_LIMIT, MAX_MEMO_ID, TITLE_LIMIT, Memo
from repositories.memos import MemoRepository


@dataclass(frozen=True)
class MemoView:
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, memo: Memo) -> "MemoView":
        return cls(memo.id, memo.title, memo.content, memo.created_at, memo.updated_at)


class MemoNotFound(Exception):
    pass


class InvalidMemo(Exception):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("메모 입력값을 확인해 주세요.")
        self.errors = errors


class MemoService:
    def __init__(self, repository: MemoRepository) -> None:
        self.repository = repository

    def list(self, query: str) -> list[MemoView]:
        return [MemoView.from_model(memo) for memo in self.repository.list(query.strip())]

    def get(self, memo_id: int) -> MemoView:
        return MemoView.from_model(self._get_memo(memo_id))

    def create(self, title: str, content: str) -> MemoView:
        title, content = self._validate(title, content)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        memo = Memo(title=title, content=content, created_at=now, updated_at=now)
        self.repository.save(memo)
        return MemoView.from_model(memo)

    def update(self, memo_id: int, title: str, content: str) -> MemoView:
        memo = self._get_memo(memo_id)
        memo.title, memo.content = self._validate(title, content)
        memo.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.repository.save(memo)
        return MemoView.from_model(memo)

    def delete(self, memo_id: int) -> None:
        self.repository.delete(self._get_memo(memo_id))

    def _get_memo(self, memo_id: int) -> Memo:
        if not 1 <= memo_id <= MAX_MEMO_ID:
            raise MemoNotFound(memo_id)
        memo = self.repository.get(memo_id)
        if memo is None:
            raise MemoNotFound(memo_id)
        return memo

    @staticmethod
    def _validate(title: str, content: str) -> tuple[str, str]:
        title, content = title.strip(), content.strip()
        errors = {}
        if not title:
            errors["title"] = "제목을 입력해 주세요."
        elif len(title) > TITLE_LIMIT:
            errors["title"] = f"제목을 {TITLE_LIMIT}자 이내로 입력해 주세요."
        if not content:
            errors["content"] = "내용을 입력해 주세요."
        elif len(content) > CONTENT_LIMIT:
            errors["content"] = f"내용을 {CONTENT_LIMIT:,}자 이내로 입력해 주세요."
        if errors:
            raise InvalidMemo(errors)
        return title, content
