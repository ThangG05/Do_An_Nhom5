# Kho tài liệu Học tập và thống kê token RAG

## Chuẩn bị triển khai

1. Chạy migration backend `20261015_0025` bằng `alembic upgrade head`. Migration chỉ tạo schema; **bảng `subjects` cố ý để trống**, không có môn học bịa hoặc dữ liệu mẫu.
2. Tạo bucket Cloudflare R2 riêng tư, không gắn public domain và không cấp quyền đọc ẩn danh. Khai báo tên bucket trong `backend/.env` bằng `R2_STUDY_BUCKET_NAME`. Bucket này phải **khác** `R2_BUCKET_NAME` dùng cho media thông thường. Cặp R2 access key hiện có phải có quyền upload, đọc và xóa object của bucket mới. Không commit secret vào Git.
3. Superadmin thêm từng môn học đã xác minh qua `PUT /api/v1/admin/subjects` (mã môn, tên, ghi chú nguồn xác minh). Chỉ môn đang hoạt động được phép chọn khi chia sẻ tài liệu.

## API kho tài liệu

Tất cả API đều cần đăng nhập. Kho chỉ hoạt động với nhóm có slug `hoc-tap`; backend kiểm tra lại slug, không dựa vào việc frontend ẩn nút.

| Chức năng | Endpoint |
| --- | --- |
| Tìm môn học | `GET /api/v1/subjects?q=...` |
| Superadmin xem cả môn đã tắt | `GET /api/v1/admin/subjects` |
| Superadmin thêm/cập nhật môn | `PUT /api/v1/admin/subjects` |
| Xem/tìm tài liệu đã duyệt | `GET /api/v1/groups/{group_id}/library?q=...&subject_id=...` |
| Tài liệu tôi đã gửi | `GET /api/v1/groups/{group_id}/library/mine` |
| Gửi duyệt | `POST /api/v1/groups/{group_id}/library` (multipart: `subject_id`, `title`, `description`, `files`) |
| Chi tiết tài liệu | `GET /api/v1/groups/{group_id}/library/{document_id}` |
| Xem PDF/ảnh hoặc tải file | `GET /api/v1/groups/{group_id}/library/{document_id}/files/{file_id}/download?preview=true|false` |
| Admin xem chờ duyệt | `GET /api/v1/groups/{group_id}/library/admin/pending` |
| Admin duyệt/từ chối | `PATCH /api/v1/groups/{group_id}/library/admin/{document_id}` (`decision`: `APPROVE`/`REJECT`, `reason` khi từ chối) |
| Admin thử xóa lại file bị từ chối | `POST /api/v1/groups/{group_id}/library/admin/cleanup` |

Mỗi lần chia sẻ nhận 1–10 file, tổng tối đa 50 MiB. Backend đối chiếu phần mở rộng, MIME và chữ ký/nội dung file; chỉ nhận PDF, Word, Excel, PowerPoint và JPG/PNG/WEBP. File mới nằm ở trạng thái `PENDING`, trong bucket riêng tư, không trả public URL. Chỉ thành viên xem/tải file đã duyệt; người gửi và admin đúng nhóm có thể xem file chờ duyệt. URL R2 ký có hạn tối đa 5 phút. Xem trước chỉ áp dụng PDF/ảnh, Office tải xuống. File bị từ chối được xóa ngay; endpoint `cleanup` xử lý trường hợp R2 tạm lỗi lúc xóa. Tài liệu trong kho **không tự đi vào RAG**.

## Thống kê token

Các lượt gọi Gemini/DeepSeek thuộc pipeline RAG ghi một dòng `rag_token_usage` cho mỗi lần model thực sự trả response. Bao gồm các lượt rewrite, tóm tắt, trả lời và retry; embedding/reranking không gộp vào ba số chat LLM. Token lấy từ `usage` của provider. Nếu provider không gửi usage, cột token để `NULL` và ghi `usage_source=missing`, không suy đoán là 0. Ràng buộc `(request_id, call_index)` chống lưu trùng một lượt gọi trong cùng câu hỏi.

Chỉ Superadmin xem được thống kê:

- `GET /api/v1/admin/users?period=today|7d|30d|all|custom&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` trả tổng token trên từng user của trang danh sách.
- `GET /api/v1/admin/users/{user_id}/rag-usage` dùng cùng bộ lọc và trả tổng, theo ngày, tối đa 100 lượt gọi gần nhất.

Khoảng ngày được hiểu theo múi giờ Việt Nam, không theo ngày UTC. Dữ liệu token cũ **không được hồi tố** vì trước đây hệ thống không lưu usage provider theo từng lượt gọi.
