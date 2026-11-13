from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.memo import Memo


class MemoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, query: str) -> Sequence[Memo]:
        statement = select(Memo).order_by(Memo.created_at.desc(), Memo.id.desc())
        if query:
            statement = statement.where(Memo.title.icontains(query, autoescape=True))
        return self.session.scalars(statement).all()

    def get(self, memo_id: int) -> Memo | None:
        return self.session.get(Memo, memo_id)

    def save(self, memo: Memo) -> None:
        self.session.add(memo)
        self.session.commit()

    def delete(self, memo: Memo) -> None:
        self.session.delete(memo)
        self.session.commit()
