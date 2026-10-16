# Danh mục kho tài liệu Học tập

## Dữ liệu và nguồn

Migration `20261016_0026` nhập bản chụp `backend/alembic/data/hvnh_catalog_20261016.json`, trích từ `danh_muc_hoc_phan_HVNH_va_thiet_ke_database.md` do người dùng cung cấp. Nguồn được ghi trong từng bản ghi; đây không phải xác minh độc lập từ Học viện.

- 18 ngành; ngành Kinh tế đầu tư chưa có mã.
- 355 học phần theo danh tính `(code, name, category)`, gồm 29 đại cương.
- 481 liên kết ngành–học phần chuyên ngành.
- 20 mã gắn nhiều tên khác nhau và 3 học phần thiếu mã được đánh dấu `needs_review`.
- Hai môn có cùng mã/tên xuất hiện ở cả đại cương và chuyên ngành được giữ riêng theo phân loại nguồn. Không gán toàn bộ môn đại cương cho mọi ngành.

## Triển khai

Từ thư mục `backend`, dùng Python của môi trường dự án:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m scripts.verify_study_catalog
```

Alembic chỉ nhập một lần. Dữ liệu môn đã tồn tại được giữ ID và không ghi đè tên/nguồn. Số lượng có thể lớn hơn bản nguồn nếu quản trị viên đã thêm môn. Không chạy SQL xóa bảng để nhập lại. Downgrade được chặn vì schema cũ không biểu diễn được các môn trùng hoặc thiếu mã.

## API và giao diện

- `GET /api/v1/majors`: ngành và số môn đang hoạt động.
- `GET /api/v1/subjects?q=&category=GENERAL|SPECIALIZED&major_id=&offset=&limit=`: tìm môn, phân trang (mặc định 50).
- `GET /api/v1/admin/subjects`: cùng bộ lọc, có cả môn bị tắt; chỉ superadmin.
- `PUT /api/v1/admin/subjects`: không có `id` là thêm mới; có `id` là cập nhật chính môn đó. Không dùng mã môn làm định danh cập nhật. `major_ids` tùy chọn; bỏ qua giữ liên kết cũ, `[]` xóa liên kết; môn GENERAL không gán ngành.
- Danh sách tài liệu hỗ trợ `subject_id`, `category`, `major_id` cùng bộ lọc tiêu đề hiện có.
- Vào **Hội nhóm → Học tập → Kho tài liệu** để chọn Đại cương hoặc Theo ngành. Chọn môn trong form chia sẻ độc lập với bộ lọc danh sách.
- Vào **Admin → Danh mục môn học** để rà soát, sửa tên/mã, phân loại, ngành liên quan và bật/tắt môn. Môn bị tắt không nhận chia sẻ mới; tài liệu đã duyệt vẫn giữ liên kết.

Kho tài liệu dùng các bảng `study_documents`/`study_document_files` hiện có và nhóm `hoc-tap` của hệ thống. Không tạo kho trùng với bài đăng hội nhóm. Kiểm tra thành viên, admin đúng nhóm, giới hạn 10 file/50 MB, xác minh định dạng và URL tải R2 có hạn vẫn được giữ. Kiểm thử tải file dùng R2 giả lập; không tải tài liệu kiểm thử lên bucket thật.
