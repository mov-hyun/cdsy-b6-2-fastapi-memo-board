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

## 동작 확인

1. 홈에서 **새 메모 작성**을 눌러 제목과 내용을 저장합니다. 상세 화면을 새로고침한 뒤 목록에 메모가 한 건만 생성됐는지 확인합니다.
2. 상세에서 **메모 수정**을 눌러 내용을 변경합니다. 저장 후 상세에서 변경된 내용을 확인합니다.
3. 상세에서 **메모 삭제**를 누르고 확인합니다. 목록에서 사라졌는지 확인하고, 기존 상세 URL을 열어 `404` 안내 화면을 확인합니다.
4. 브라우저 개발자 도구의 네트워크 탭에서 **로그 보존**을 켜면 각 변경 요청의 `POST 303`과 이어지는 `GET 200`을 확인할 수 있습니다.
5. 메모를 한 건 저장한 상태에서 서버를 종료하고 다시 실행합니다. 목록과 상세에 같은 메모가 남아 있는지 확인합니다.

## SQLite 데이터 확인

첫 실행 시 프로젝트 폴더에 `database.db`가 생성됩니다. 메모를 하나 저장한 뒤 같은 폴더에서 다음 명령으로 DB에 기록된 값을 확인할 수 있습니다.

```bash
python -c "import sqlite3; db = sqlite3.connect('database.db'); print(db.execute('SELECT id, title, content, created_at, updated_at FROM memos ORDER BY id').fetchall()); db.close()"
```

DB에는 일시를 UTC로 저장하며 화면에서는 한국 표준시로 표시합니다.
