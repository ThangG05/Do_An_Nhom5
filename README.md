# HVNH Hub
ae cd frontend sau đó cài : npm install ( nếu chưa có)

các file .env chứa các key mật dùng trong dự án và sẽ không được pub ra ngoài vì vậy lưu tất cả các key vào .env
```bash
cd backend -> copy .env.example .env ( tạo file .env để lưu key trong dự án bắt buộc phải chạy)

cd frontend -> npm run dev ( chạy fe)

cd backend -> uvicorn src.main:app --reload --port 8000 (chạy be)

Các tài liệu hướng dẫn style fe ở trong doc

setup môi trường
python -m venv .venv
.venv\Scripts\activate
cd backend 
pip install -r requirements.txt
