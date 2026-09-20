# Tích hợp RAG vào HVNH Hub

RAG được nhúng trực tiếp trong backend:

`frontend hoặc Flutter -> backend :8000/api/v1/ai/* -> RAG cùng tiến trình`

Frontend và Flutter không gọi RAG trực tiếp, không giữ khóa AI và không cần
biết cấu trúc nội bộ của RAG. RAG dùng bộ giải mã access token của backend và
`user.id` để cô lập lịch sử hội thoại.

## Chạy local

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn src.main:app --reload --port 8000
```

Lệnh trên khởi động cả backend và RAG trong một tiến trình uvicorn, cùng cổng
`8000`. Không cần mở terminal hoặc cổng `8001`. Frontend chạy riêng:

```powershell
cd frontend
npm run dev
```

Sau khi đăng nhập, mở `/assistant` hoặc chọn **Trợ lý AI** trên thanh điều
hướng.

## Cấu hình

Giữ toàn bộ khóa backend và RAG trong file chung `backend/.env`. Cả hai bộ cấu hình
đều đọc file này; khi triển khai có thể đổi đường dẫn bằng `HVNH_ENV_FILE`. Module
`src.agents.rag_runtime` tự đặt chế độ xác thực nội bộ:

```env
AUTH_SERVICE_URL=inprocess://backend
```

Không đưa `.env` hoặc khóa bí mật vào Git. `AUTH_JWT_SECRET` của RAG không cần
trùng `JWT_SECRET_KEY` của backend vì chế độ nhúng dùng trực tiếp bộ giải mã
token của backend.

## Cơ sở dữ liệu và migration

Backend là nguồn Alembic duy nhất cho cơ sở dữ liệu Neon dùng chung. **Không
chạy** `alembic upgrade head` trong thư mục `RAG`, vì lịch sử migration độc lập
của RAG có revision trùng tên với backend. Mọi migration mới phải được tạo
trong `backend/alembic/versions`.

## Kiểm tra

```powershell
cd RAG
..\.venv\Scripts\python.exe -m pytest -q
```

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```

OpenAPI backend phải có `/api/v1/ai/chat` và các route
`/api/v1/ai/conversations`.

## Triển khai bằng Docker

```powershell
docker compose up --build -d
```

Compose tạo một container và chỉ publish cổng `8000`. Web và Flutter luôn gọi
`/api/v1/ai/*`. Cấu hình không chạy Alembic độc lập của RAG.
