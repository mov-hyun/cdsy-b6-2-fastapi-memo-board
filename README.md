# 메모 게시판

브라우저에서 메모를 작성하고 목록과 상세를 조회하며, 저장한 메모를 수정하거나 삭제하는 FastAPI 웹 앱입니다. 목록에서 제목으로 검색할 수 있습니다.

## 실행 방법

Python 3.10 이상이 필요합니다. GitHub에서 시작하는 경우 저장소를 복제한 뒤 프로젝트 폴더로 이동합니다.

```bash
git clone https://github.com/mov-hyun/cdsy-b6-2-fastapi-memo-board.git
cd cdsy-b6-2-fastapi-memo-board
```

압축 파일로 받았다면 압축을 푼 뒤 `README.md`가 있는 폴더에서 아래 명령부터 실행합니다.

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell에서는 `py -m venv .venv`로 가상환경을 만들고 `.\.venv\Scripts\Activate.ps1`로 활성화합니다. 이후 설치와 실행 명령은 같습니다.

터미널에서 `Application startup complete.`와 `Uvicorn running on http://127.0.0.1:8000`을 확인하고 브라우저에서 [메모 게시판](http://localhost:8000)을 엽니다. 서버를 종료하려면 `Ctrl+C`를 누릅니다.

macOS 또는 Linux에서 이미 가상환경과 패키지를 설치했다면 `.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000`으로 바로 실행할 수 있습니다.

## 화면과 요청

| 메서드 | 경로 | 동작 |
| --- | --- | --- |
| GET | `/` | 홈과 목록·작성 링크 |
| GET | `/memos` | 메모 목록. `?q=검색어`로 제목 검색 |
| GET | `/memos/new` | 등록 폼 |
| POST | `/memos` | 등록 후 상세로 `303` |
| GET | `/memos/{memo_id}` | 번호, 제목, 내용, 작성·수정 일시 |
| GET | `/memos/{memo_id}/edit` | 기존 값을 채운 수정 폼 |
| POST | `/memos/{memo_id}/edit` | 수정 후 상세로 `303` |
| POST | `/memos/{memo_id}/delete` | 삭제 후 목록으로 `303` |

등록·수정 폼에 빈 값이나 길이 제한을 넘긴 값을 보내면 입력 내용을 유지한 채 `422`와 필드별 안내를 표시합니다. 존재하지 않는 메모를 조회하면 `404` 안내 화면이 표시됩니다. 상세 화면에서 삭제를 누르면 확인 창이 열립니다.

## 코드 구조와 요청 흐름

| 위치 | 역할 |
| --- | --- |
| `main.py` | FastAPI 앱 구성과 시작 시 DB 테이블 생성 |
| `database.py` | SQLite 엔진 구성과 `Depends`에 연결할 요청별 세션 제공 |
| `routers/` | GET 조회, `Form()`을 이용한 POST 입력 수신, HTML 응답과 리다이렉트 |
| `services/` | 메모 입력 검증, 작성·수정 일시 처리, 조회 결과를 DTO로 변환 |
| `repositories/` | SQLAlchemy 세션으로 조회, 검색, 저장, 삭제 |
| `models/` | 단일 `Memo` ORM 모델과 SQLite 테이블 매핑 |
| `templates/`, `static/` | Jinja2 화면과 CSS |

예를 들어 등록 폼을 제출하면 `POST /memos` 라우터가 제목과 내용을 받습니다. 서비스가 입력을 검증하고 저장소가 `Memo`를 SQLite에 커밋하면, 라우터가 `RedirectResponse(status_code=303)`를 반환합니다. 브라우저는 `Location` 헤더에 담긴 상세 URL을 GET으로 요청합니다. 상세 라우터가 서비스와 저장소를 거쳐 조회한 DTO를 Jinja2에 전달하고 `TemplateResponse`로 HTML을 렌더링합니다.

GET은 화면 조회에 사용하고 POST는 데이터 변경에 사용합니다. 등록·수정·삭제 성공 후에는 GET 화면에 도착하므로, 그 화면을 새로고침하면 GET만 다시 실행됩니다. 이 흐름이 POST → Redirect → GET(PRG)입니다.

### 레이어를 분리하는 이유

폼 읽기, 필수값 검사, SQLAlchemy 쿼리, HTML 응답을 각 라우터에 모두 넣으면 등록과 수정에 같은 검증 규칙이 중복됩니다. 제목 길이 규칙을 바꿀 때 두 곳을 수정해야 하고, 한 곳이 누락되면 등록과 수정의 결과가 달라집니다. 검색 조건을 바꾸는 작업도 화면 처리 코드와 섞여 변경 범위가 커집니다. 검증만 확인하려 해도 HTTP 요청과 테스트 DB를 함께 준비해야 합니다.

현재 등록과 수정은 모두 `MemoService._validate()`를 사용합니다. `MemoRepository.list()`에 제목 검색 쿼리가 모여 있고, 라우터는 서비스가 반환한 `MemoView`를 화면에 전달합니다. 그래서 서비스 검증은 저장소를 대역으로 바꿔 HTTP나 SQLite 없이 확인할 수 있고, 실제 쿼리와 커밋은 테스트 DB에서 저장소를 직접 호출해 확인할 수 있습니다.

### ORM 세션과 트랜잭션

`Depends(get_db)`는 요청마다 SQLAlchemy `Session`을 열고 사용이 끝나면 닫습니다. 조회는 `session.get()`과 `select()`로 `Memo` 객체를 가져옵니다. 등록은 `session.add()`, 수정은 조회한 객체의 필드 변경, 삭제는 `session.delete()`로 세션에 반영합니다. `flush`는 이 변경을 SQL로 보내고, 저장소의 `commit()`은 필요한 `flush`를 수행한 뒤 트랜잭션을 확정합니다. 예외로 요청이 종료되면 세션을 닫을 때 남은 미커밋 트랜잭션이 롤백됩니다. `expire_on_commit=False` 덕분에 서비스는 커밋 직후 별도의 새 조회 없이 생성된 ID와 메모 필드로 `MemoView`를 만들 수 있습니다. [SQLAlchemy 세션 문서](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)

## 동작 확인

1. 홈에서 **새 메모 작성**을 눌러 제목과 내용을 저장합니다. 상세 화면을 새로고침한 뒤 목록에 메모가 한 건만 생성됐는지 확인합니다.
2. 상세에서 **메모 수정**을 눌러 내용을 변경합니다. 저장 후 상세에서 변경된 내용을 확인합니다.
3. 상세에서 **메모 삭제**를 누르고 확인합니다. 목록에서 사라졌는지 확인하고, 기존 상세 URL을 열어 `404` 안내 화면을 확인합니다.
4. 브라우저 개발자 도구의 네트워크 탭에서 **로그 보존**을 켜면 각 변경 요청의 `POST 303`과 이어지는 `GET 200`을 확인할 수 있습니다.
5. 메모를 한 건 저장한 상태에서 서버를 종료하고 다시 실행합니다. 목록과 상세에 같은 메모가 남아 있는지 확인합니다.

Python 3.10에서 실행한 Uvicorn 로그 중 PRG에 해당하는 요청을 발췌했습니다. 상세 화면을 새로고침했을 때는 `GET /memos/1`만 한 번 더 기록됐습니다.

```text
"POST /memos HTTP/1.1" 303 See Other
"GET /memos/1 HTTP/1.1" 200 OK
"GET /memos/1 HTTP/1.1" 200 OK
"POST /memos/1/edit HTTP/1.1" 303 See Other
"GET /memos/1 HTTP/1.1" 200 OK
"POST /memos/1/delete HTTP/1.1" 303 See Other
"GET /memos HTTP/1.1" 200 OK
"GET /memos/1 HTTP/1.1" 404 Not Found
```

## SQLite 데이터 확인

첫 실행 시 `database.py` 옆에 `database.db`가 생성됩니다. 파일 생성과 갱신을 위해 서버를 실행하는 계정에 해당 폴더 쓰기 권한이 필요합니다. 메모를 하나 저장한 뒤 같은 폴더에서 다음 명령으로 DB에 기록된 값을 확인할 수 있습니다.

```bash
python -c "import sqlite3; db = sqlite3.connect('database.db'); print(db.execute('SELECT id, title, content, created_at, updated_at FROM memos ORDER BY id').fetchall()); db.close()"
```

DB에는 일시를 UTC로 저장하며 화면에서는 한국 표준시로 표시합니다.

## 확장 설계

아래는 현재 SQLite·Jinja2 기반 단일 모델 앱을 출발점으로 한 후속 설계입니다.

### SQLite에서 PostgreSQL로 전환

1. PostgreSQL 서버에 대상 DB와 접속 계정을 준비합니다. 전환용 가상환경에서 동기 드라이버를 `python -m pip install "psycopg[binary]"`로 설치합니다. [Psycopg 설치 문서](https://www.psycopg.org/psycopg3/docs/basic/install.html)
2. `database.py`에서 엔진에 전달하는 URL을 `sqlite` 파일 경로에서 `postgresql+psycopg://사용자:비밀번호@호스트:5432/DB이름` 형식으로 바꿉니다. 예를 들어 `DATABASE_URL` 환경변수에 접속 URL을 넣고 `create_engine(os.environ["DATABASE_URL"])`로 읽습니다. `check_same_thread`는 SQLite 드라이버 옵션이므로 PostgreSQL 엔진에서는 빼고, `SessionLocal`은 새 엔진에 연결합니다. [SQLAlchemy PostgreSQL 접속 문서](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg)
3. `models/memo.py`의 `sqlite_autoincrement`와 기본 키 타입을 검토합니다. 기존 SQLite의 64비트 메모 번호 범위를 유지한다면 PostgreSQL에서는 `BigInteger`와 자동 생성 설정을 사용합니다. 대상 DB에 스키마를 만든 후 `database.db`를 백업하고 기존 행을 ID와 일시까지 복사합니다. ID를 직접 복사했다면 다음 자동 생성 번호가 최대 ID를 넘도록 시퀀스를 맞춥니다. 전환 전에 행 수, 표본 데이터, CRUD와 제목 검색 결과를 비교합니다.

DB 연결은 `database.py`, 조회와 쓰기는 저장소에 모여 있으므로, 이식할 때 템플릿과 입력 검증을 그대로 재사용할 수 있습니다. 엔진 URL 변경은 이후 요청이 향하는 DB를 바꾸는 작업이며, 기존 행의 복사는 별도 작업입니다.

### 모델 간 일대다 관계 추가

예를 들어 카테고리 하나에 여러 메모를 연결하려면 `Category` 모델과 `categories` 테이블을 추가하고 `Memo.category_id`를 `ForeignKey("categories.id")`로 선언합니다. `Category.memos`에 `relationship(back_populates="category")`, `Memo.category`에 `relationship(back_populates="memos")`를 정의합니다. `ForeignKey`는 DB에서 참조 무결성을 지키고 `relationship()`은 Python에서 양쪽 객체를 탐색할 수 있게 합니다. SQLite를 계속 쓴다면 각 연결에서 `PRAGMA foreign_keys=ON`을 적용합니다. [SQLAlchemy 일대다 관계 문서](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#one-to-many), [SQLite 외래 키 설정](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support)

기존 `database.db`에는 `category_id` 열이 없으므로 시작 시 실행되는 `Base.metadata.create_all()`과 별도로 마이그레이션이 필요합니다. DB를 백업하고 카테고리 테이블을 생성한 뒤, 처음에는 `NULL`을 허용하는 외래 키 열을 추가합니다. 카테고리를 필수로 한다면 기존 메모를 기본 카테고리에 배정한 후 `NOT NULL`을 적용합니다. SQLite에서 기존 제약조건을 바꿀 때는 새 구조로 테이블을 만들고 데이터를 복사하는 배치 마이그레이션을 사용할 수 있습니다. 카테고리 삭제 시 연결된 메모를 재분류한 뒤 삭제를 허용할지 등의 정책도 정해야 합니다. [Alembic의 SQLite 배치 마이그레이션 문서](https://alembic.sqlalchemy.org/en/latest/batch.html)

### Jinja2 SSR에서 JSON REST API로 전환

서비스의 검증과 SQLite 저장소는 재사용하고, FastAPI에 `/api/memos` 라우터를 추가할 수 있습니다. 등록·수정은 `Form()` 대신 JSON 요청을 Pydantic 스키마로 받습니다. 응답은 `MemoView`에서 공개 필드를 담은 Pydantic 응답 모델로 변환하며, 일시는 시간대가 표시된 ISO 8601 문자열로 보냅니다. [FastAPI 응답 모델 문서](https://fastapi.tiangolo.com/tutorial/response-model/)

| API 요청 | 응답 |
| --- | --- |
| `GET /api/memos?q=검색어` | `200`과 메모 목록 JSON |
| `GET /api/memos/{memo_id}` | `200`과 메모 상세 JSON |
| `POST /api/memos` | `201`과 생성된 메모 JSON. `Location`에 API 상세 URL |
| `PUT /api/memos/{memo_id}` | 제목·내용 전체를 받아 수정. `200`과 수정된 메모 JSON |
| `DELETE /api/memos/{memo_id}` | `204`와 빈 본문 |

프런트엔드는 홈·목록·상세·작성·수정의 화면 경로를 관리하고 `fetch`로 JSON을 받아 화면을 그립니다. 서버가 Jinja2에 넘기던 목록·상세 DTO는 API 응답 데이터가 되고, 작성·수정 폼은 JSON을 전송합니다. 지금은 서버가 `303`으로 화면 이동을 안내하지만, 전환 후에는 프런트엔드가 `201`이나 `200`을 받으면 상세로 이동하고 `204`를 받으면 목록을 갱신합니다. `422` JSON의 필드 오류는 폼에 표시하고 입력값을 유지하며, `404`는 프런트의 메모 없음 화면으로 처리합니다.
