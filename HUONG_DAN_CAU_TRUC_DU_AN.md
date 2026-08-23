# Quy ước cấu trúc & đặt tên file — Dự án P-034

> Tài liệu này dành cho **cả team**, đặc biệt là những bạn lần đầu làm việc với FastAPI.
> Đọc xong bạn sẽ trả lời được: *"Code này viết vào file nào, đặt tên gì, để ở thư mục nào?"*
>
> - Muốn hiểu **luồng chạy** của 1 request → đọc [HUONG_DAN_LUONG_CODE.md](HUONG_DAN_LUONG_CODE.md)
> - Muốn biết **quy ước đặt file** → đọc file này

---

## 0. Ba nguyên tắc vàng

1. **Một file = một nhiệm vụ.** File dài quá 200 dòng là tín hiệu cần tách.
2. **Code chảy theo một chiều duy nhất:**
   `endpoint → service → (agent / db / API ngoài)`.
   Tầng dưới **không bao giờ** import ngược lên tầng trên.
3. **Không copy-paste giữa các file.** Cần dùng lại → đưa vào `services/`, `core/`, `lib/`, `hooks/`.

Chỉ cần sai nguyên tắc 2 là dự án sẽ dính lỗi `ImportError: cannot import name ... (most likely due to a circular import)` — lỗi phổ biến nhất khi mới học FastAPI.

### Đọc nhanh trong 5 phút

Backend có nhiều thư mục nhưng để viết được API đầu tiên, bạn **chỉ cần mở 3 file** này và bắt chước:

| Đọc theo thứ tự | File | Nó làm gì |
|---|---|---|
| 1️⃣ | `src/models/chat.py` | Hình dạng JSON gửi lên / trả về |
| 2️⃣ | `src/api/endpoints/chat.py` | Khai báo URL, nhận request, gọi service |
| 3️⃣ | `src/services/chat_service.py` | Logic thật sự |

Ba file đó chính là công thức ở [mục 5](#5--công-thức-thêm-1-api-mới-trong-5-bước). Mọi thứ còn lại (`core/`, `config.py`, `main.py`, `routes.py`) đã viết sẵn — bạn gần như không phải đụng vào.

---

## 1. Bản đồ toàn dự án

```
P-034/
├── src/                        # 🐍 BACKEND (FastAPI + LangGraph)
│   ├── main.py                 #   Điểm khởi động app — CHỈ lắp ráp, không viết logic
│   ├── config.py               #   Đọc biến môi trường từ .env
│   │
│   ├── api/                    #   Tầng HTTP — "Controller"
│   │   ├── routes.py           #     Gom tất cả router con (không chứa endpoint)
│   │   └── endpoints/          #     ⭐ Mỗi domain 1 file: chat.py, voice.py, auth.py...
│   │
│   ├── models/                 #   Pydantic schema = hình dạng JSON vào/ra API
│   │   ├── chat.py             #     Mỗi domain 1 file
│   │   ├── common.py           #     Schema dùng chung (lỗi, phân trang)
│   │   └── schemas.py          #     ⚠️ DEPRECATED — chỉ re-export, đừng thêm gì vào đây
│   │
│   ├── services/               #   Business logic — KHÔNG biết gì về HTTP
│   │   ├── llm.py              #     Khởi tạo client LLM
│   │   └── chat_service.py     #     Logic của domain chat
│   │
│   ├── agents/                 #   🧠 LangGraph
│   │   ├── graph.py            #     Định nghĩa đồ thị (node + edge)
│   │   ├── state.py            #     AgentState — dữ liệu truyền giữa các node
│   │   ├── nodes/              #     Mỗi bước xử lý 1 file
│   │   └── tools/              #     Hàm agent có thể tự gọi (@tool)
│   │
│   └── core/                   #   Hạ tầng dùng chung toàn app (viết 1 lần rồi thôi)
│       ├── exceptions.py       #     Lỗi nghiệp vụ + handler trả JSON thống nhất
│       └── logging.py          #     Cấu hình log (dùng thay cho print)
│
├── tests/                      # 🧪 Soi gương src/ (xem mục 9)
│
├── frontend/                   # ⚛️ FRONTEND (Next.js App Router)
│   ├── app/                    #   ⭐ Chỉ chứa ROUTE — mỗi thư mục = 1 URL
│   ├── components/             #   Component tái sử dụng
│   ├── hooks/                  #   State + logic của UI
│   ├── lib/                    #   Gọi API, hàm tiện ích
│   └── types/                  #   Kiểu TypeScript khớp với Pydantic bên backend
│
├── docs/ eval/ presentation/   # 📄 Tài liệu, đánh giá, slide (không phải code chạy)
└── scripts/ .claude/ .cursor/  # 🪝 Hook log AI của chương trình AI20K
```

---

## 2. Backend — mỗi thư mục dùng để làm gì

| Thư mục | Đặt file gì vào đây | ĐƯỢC import từ | KHÔNG được import |
|---|---|---|---|
| `api/endpoints/` | Định nghĩa URL, method, response_model. Mỗi handler ≤ 10 dòng. | `models/`, `services/` | `agents/` (phải đi qua service) |
| `models/` | Class Pydantic (`BaseModel`) | chỉ `pydantic` + `models/` khác | `api/`, `services/`, `agents/` |
| `services/` | Logic nghiệp vụ, gọi LLM / API ngoài / DB | `models/`, `agents/`, `core/` | `fastapi` ❌ |
| `agents/nodes/` | 1 bước xử lý trong graph, nhận `state` trả `dict` | `state`, `services/`, `tools/` | `api/` |
| `agents/tools/` | Hàm gắn `@tool` để agent tự gọi | `services/` | `api/`, `graph.py` |
| `core/` | Logging, exception, hằng số dùng chung | `config` | tất cả phần còn lại |

**Mẹo nhớ:** nếu bạn định gõ `from fastapi import ...` trong file thuộc `services/`, `agents/` hay `models/` → **bạn đang viết sai chỗ**.

> **Người mới chỉ cần nắm 3 thư mục đầu bảng.** `agents/` là phần LangGraph (xem chương 4 của guidebook),
> còn `core/` viết sẵn rồi — bạn gần như không bao giờ phải sửa.

---

## 3. Quy ước đặt tên (Python)

| Loại | Quy tắc | ✅ Đúng | ❌ Sai |
|---|---|---|---|
| File / thư mục | `snake_case`, danh từ, tiếng Anh, không dấu | `voice_service.py` | `VoiceService.py`, `xuLyGiongNoi.py` |
| File endpoint | tên **domain số nhiều hoặc danh từ chung** | `endpoints/conversations.py` | `endpoints/api2.py`, `endpoints/new.py` |
| File node | `<việc>_node.py` | `nodes/transcribe_node.py` | `nodes/node1.py` |
| File service | `<domain>_service.py` | `services/voice_service.py` | `services/helper.py` |
| Class | `PascalCase` | `ChatRequest`, `NotFoundError` | `chat_request` |
| Schema | `<Việc>Request` / `<Việc>Response` | `TranscribeRequest` | `TranscribeInput`, `Data` |
| Hàm / biến | `snake_case`, động từ dẫn đầu | `handle_chat()`, `get_llm()` | `Handle_Chat()`, `data2()` |
| Hàm async | bắt buộc `async def` nếu bên trong có `await` | `async def handle_chat()` | `def handle_chat()` rồi `await` |
| Hằng số | `UPPER_SNAKE_CASE` | `MAX_AUDIO_MB = 25` | `maxAudioMb` |
| Biến router | luôn đặt tên `router` | `router = APIRouter(...)` | `chat_router = ...` |
| Private | thêm `_` đầu | `_eval_node()` | — |

**Tiếng Việt:** đặt tên file/hàm/biến bằng **tiếng Anh**; docstring và comment thì viết **tiếng Việt** cho cả team dễ đọc.

---

## 4. Luồng 1 request (sau khi tái cấu trúc)

```
POST /api/v1/chat
   │
   ▼
main.py                    gắn router, CORS, exception handler
   │
   ▼
api/routes.py              gom router → chuyển tới đúng domain
   │
   ▼
api/endpoints/chat.py      nhận ChatRequest (Pydantic tự validate → 422 nếu sai)
   │                       ❗ chỉ gọi service, không viết logic
   ▼
services/chat_service.py   logic nghiệp vụ; lỗi → raise AppError
   │
   ▼
agents/graph.py            chạy đồ thị: analyze_node → respond_node
   │
   ▼
ChatResponse → JSON trả về client
```

Lỗi được `core/exceptions.py` bắt và trả về đúng một định dạng:

```json
{ "error": { "code": "external_service_error", "message": "Agent xử lý thất bại: ..." } }
```

---

## 5. ⭐ Công thức: thêm 1 API mới trong 5 bước

Ví dụ thật: tính năng **voice-to-text** (`POST /api/v1/voice/transcribe`).

### Bước 1 — Schema: `src/models/voice.py`

```python
from pydantic import BaseModel, Field


class TranscribeRequest(BaseModel):
    audio_url: str = Field(..., description="Link file audio cần chuyển thành text")


class TranscriptSegment(BaseModel):
    start: float = Field(..., ge=0, description="Giây bắt đầu")
    end: float = Field(..., ge=0, description="Giây kết thúc")
    text: str


class TranscribeResponse(BaseModel):
    text: str
    segments: list[TranscriptSegment] = []
```

### Bước 2 — Service: `src/services/voice_service.py`

```python
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.models.voice import TranscribeResponse

logger = get_logger(__name__)


async def transcribe(audio_url: str) -> TranscribeResponse:
    logger.info("Transcribe %s", audio_url)
    try:
        ...  # gọi Whisper / PhoWhisper ở đây
    except Exception as exc:
        raise ExternalServiceError(f"STT thất bại: {exc}") from exc
    return TranscribeResponse(text="...", segments=[])
```

### Bước 3 — Endpoint: `src/api/endpoints/voice.py`

```python
from fastapi import APIRouter

from src.models.voice import TranscribeRequest, TranscribeResponse
from src.services import voice_service

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post("/transcribe", response_model=TranscribeResponse, summary="Chuyển audio thành text")
async def transcribe(request: TranscribeRequest) -> TranscribeResponse:
    return await voice_service.transcribe(request.audio_url)
```

### Bước 4 — Đăng ký router: `src/api/routes.py` (thêm đúng 2 dòng)

```python
from src.api.endpoints import chat, health, voice   # ← thêm voice

router.include_router(voice.router)                 # ← thêm dòng này
```

> ❗ **Không sửa `main.py`.** Nếu bạn thấy mình đang sửa `main.py` để thêm API, tức là đang làm sai.

### Bước 5 — Test: `tests/test_api/test_voice.py`

```python
import pytest


@pytest.mark.asyncio
async def test_transcribe_requires_audio_url(client):
    response = await client.post("/api/v1/voice/transcribe", json={})
    assert response.status_code == 422
```

Chạy kiểm tra: `make check` (lint + format + test), rồi mở http://localhost:8000/docs xem API mới đã hiện chưa.

> Nếu tính năng cần **agent xử lý qua nhiều bước**, thêm node vào `src/agents/nodes/<việc>_node.py`,
> thêm field vào `AgentState` (`src/agents/state.py`), rồi nối vào `graph.py` bằng `add_node` + `add_edge`.

---

## 6. Frontend — Next.js App Router

### Thư mục nào để làm gì

| Thư mục | Nội dung | Quy tắc đặt tên |
|---|---|---|
| `app/` | **Chỉ chứa route.** Tên thư mục = URL | thư mục `kebab-case`; file bắt buộc là `page.tsx` / `layout.tsx` |
| `components/` | Component tái sử dụng, chia theo domain: `ui/`, `chat/`, `voice/` | file `PascalCase.tsx` trùng tên component |
| `hooks/` | State + logic UI | `use<Việc>.ts` — `useChat.ts`, `useRecorder.ts` |
| `lib/` | Gọi API (`api.ts`), hàm tiện ích (`utils.ts`) | `camelCase.ts` |
| `types/` | Interface khớp với Pydantic backend | `<domain>.ts` |

### File đặc biệt trong `app/`

| File | Ý nghĩa | Ví dụ URL |
|---|---|---|
| `app/page.tsx` | Trang chủ | `/` |
| `app/login/page.tsx` | Trang đăng nhập | `/login` |
| `app/dashboard/layout.tsx` | Khung bao mọi trang trong `/dashboard` | — |
| `app/dashboard/[id]/page.tsx` | Route động, đọc `params.id` | `/dashboard/123` |
| `app/loading.tsx` / `error.tsx` | UI khi đang tải / khi lỗi | — |

### 3 quy tắc phải nhớ

1. **`"use client"` ở dòng đầu file** nếu component có `useState`, `useEffect`, `onClick`, `onChange`.
   Thiếu dòng này → lỗi *"You're importing a component that needs useState..."*.
2. **Không `fetch()` trực tiếp trong component.** Mọi lời gọi backend đi qua `lib/api.ts`.
3. **Page chỉ lắp ghép component**, logic để trong `hooks/`.

### Thêm 1 trang mới

```
Muốn có URL /dashboard/history
→ tạo frontend/app/dashboard/history/page.tsx   (export default function HistoryPage)
→ component riêng của trang: frontend/components/history/HistoryList.tsx
→ logic gọi API: thêm hàm vào frontend/lib/api.ts
```

### Chạy frontend lần đầu

```bash
cd frontend
npm install
cp .env.local.example .env.local     # trỏ NEXT_PUBLIC_API_URL về backend
npm run dev                          # http://localhost:3000
```

> Trước khi chạy `npm install`, VS Code sẽ báo đỏ *"Cannot find module 'react'"* — đó là bình thường, cài xong sẽ hết.
> Backend phải đang chạy ở cổng 8000 thì chat mới hoạt động.

---

## 7. Testing

`tests/` **soi gương** `src/`:

| File nguồn | File test |
|---|---|
| `src/api/endpoints/chat.py` | `tests/test_api/test_chat.py` |
| `src/services/chat_service.py` | `tests/test_services/test_chat_service.py` |
| `src/agents/graph.py` | `tests/test_agents/test_graph.py` |

- Tên hàm test: `test_<việc>_<tình huống>` — `test_transcribe_requires_audio_url`.
- Hàm test async phải có `@pytest.mark.asyncio`.
- **Không gọi OpenAI thật trong test** (tốn tiền, chậm, kết quả đổi liên tục) → dùng fixture `mock_llm` trong `tests/conftest.py` hoặc class giả như `_FakeAgent` trong `tests/test_services/test_chat_service.py`.
- Fixture dùng chung đặt ở `tests/conftest.py`, không copy sang từng file.

Chạy: `make test` hoặc `pytest tests/ -v`.

---

## 8. Bật database (khi cần)

Hiện dự án **chưa dùng database** nên không có thư mục `src/db/` — đừng tạo sớm.
Khi nào thật sự cần lưu dữ liệu thì làm 4 bước sau:

1. Bỏ comment `sqlalchemy` (và `psycopg2-binary` nếu dùng PostgreSQL) trong `requirements.txt`, rồi `pip install -r requirements.txt`
2. Đặt `DATABASE_URL` trong `.env`
3. Tạo `src/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import get_settings

settings = get_settings()
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Lớp cha cho mọi ORM model."""


def get_db() -> Generator[Session, None, None]:
    """Mở 1 session cho mỗi request, đóng lại khi request xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

4. Tạo `src/db/models.py` (các bảng) và dùng trong endpoint:

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/conversations")
def list_conversations(db: DbSession):
    ...
```

⚠️ **Phân biệt hai loại "model"** — chỗ này người mới hay nhầm nhất:

| | `src/models/*.py` | `src/db/models.py` |
|---|---|---|
| Thư viện | Pydantic | SQLAlchemy |
| Mô tả | JSON đi vào / đi ra API | Bảng trong database |
| Ví dụ | `ChatRequest` | `Conversation`, `Message` |

Không dùng ORM model làm `response_model` và ngược lại — luôn chuyển đổi ở tầng service.

---

## 9. Git — quy ước nhánh & commit

```
main                 code chạy được, không commit thẳng
└── feature/<tên>    mỗi tính năng 1 nhánh:  feature/voice-to-text
    fix/<tên>        sửa lỗi:                fix/chat-500-error
```

Commit theo Conventional Commits (tiếng Việt được, prefix tiếng Anh):

```
feat: thêm API transcribe audio thành text
fix: sửa lỗi 500 khi message rỗng
docs: cập nhật hướng dẫn cấu trúc thư mục
refactor: tách logic chat ra chat_service
test: thêm test cho voice_service
```

Trước khi tạo Pull Request: `make check` phải xanh.

---

## 10. Checklist trước khi push

- [ ] File đặt đúng thư mục theo bảng ở mục 2
- [ ] Tên file/class/hàm theo đúng mục 3
- [ ] Endpoint không chứa logic — logic nằm ở `services/`
- [ ] Không có `from fastapi import ...` trong `services/`, `agents/`, `models/`
- [ ] Không có `print()` — dùng `get_logger(__name__)`
- [ ] Schema mới có `Field(..., description=...)` để Swagger đọc được
- [ ] Có ít nhất 1 test cho phần vừa viết
- [ ] Không commit `.env`, `node_modules/`, file audio/dữ liệu lớn
- [ ] `make check` chạy xanh

---

## 11. Lỗi người mới hay gặp

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| `ImportError ... circular import` | Import ngược chiều (service import từ api) | Xem lại mũi tên ở mục 2 |
| `ModuleNotFoundError: No module named 'src'` | Chạy sai thư mục | Chạy `uvicorn src.main:app` từ **thư mục gốc** dự án |
| API mới không hiện ở `/docs` | Quên `include_router` trong `routes.py` | Thêm 2 dòng ở Bước 4, mục 5 |
| `422 Unprocessable Entity` | Body không khớp schema | Mở `/docs` xem đúng field, hoặc sửa Pydantic model |
| `RuntimeWarning: coroutine ... was never awaited` | Quên `await` khi gọi hàm `async` | Thêm `await` |
| CORS error trên trình duyệt | `CORS_ORIGINS` trong `.env` chưa có `http://localhost:3000` | Sửa `.env` rồi restart server |
| Frontend gọi API 404 | Sai `NEXT_PUBLIC_API_URL` hoặc thiếu tiền tố `/api/v1` | Kiểm tra `frontend/.env.local` và `lib/api.ts` |
| `You're importing a component that needs useState` | Thiếu `"use client"` | Thêm vào dòng đầu file |
| Sửa `.env` mà không thấy đổi | `get_settings()` có cache `@lru_cache` | Restart server |

---

## 12. Tra nhanh: "Code này viết vào đâu?"

| Tôi muốn... | Viết vào file |
|---|---|
| Thêm một URL / endpoint mới | `src/api/endpoints/<domain>.py` |
| Đổi hình dạng JSON request/response | `src/models/<domain>.py` |
| Viết logic nghiệp vụ | `src/services/<domain>_service.py` |
| Gọi API bên ngoài (Whisper, S3...) | `src/services/<tên>.py` |
| Thêm 1 bước xử lý cho agent | `src/agents/nodes/<việc>_node.py` + nối vào `src/agents/graph.py` |
| Cho agent tự gọi được 1 hàm | `src/agents/tools/<tên>_tool.py` |
| Thêm dữ liệu truyền giữa các node | `src/agents/state.py` |
| Thêm biến môi trường | `.env.example` + `src/config.py` |
| Thêm loại lỗi mới | `src/core/exceptions.py` |
| Thêm bảng database | `src/db/models.py` (chưa có — tạo mới theo mục 8) |
| Thêm trang web mới | `frontend/app/<đường-dẫn>/page.tsx` |
| Thêm nút / ô nhập dùng lại nhiều nơi | `frontend/components/ui/<Tên>.tsx` |
| Thêm hàm gọi backend | `frontend/lib/api.ts` |
| Thêm state cho màn hình | `frontend/hooks/use<Việc>.ts` |

---

Có chỗ nào chưa rõ, hỏi trong nhóm trước khi tự đặt quy ước riêng — quan trọng nhất là **cả team làm giống nhau**.
