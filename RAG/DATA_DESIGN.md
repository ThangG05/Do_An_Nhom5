# Thiết kế dữ liệu tổng thể HVNH Hub V2

## 1. Phạm vi hệ thống

HVNH Hub gồm hai miền độc lập nhưng dùng chung định danh người dùng:

1. **Community Platform**: xác thực email HVNH, hồ sơ, nhóm, bài viết, kiểm duyệt,
   tương tác, kết bạn, chat realtime, thông báo và báo cáo.
2. **AI/RAG Service**: quản lý tri thức chính thức, phiên bản tài liệu, vector index,
   hội thoại AI nhiều lượt và citation.

Hai loại hội thoại phải tách riêng:

- `conversations/messages`: chat giữa người dùng.
- `ai_conversations/ai_messages`: hỏi đáp với AI.

Schema triển khai đầy đủ nằm trong `base_v2.sql`. `base.md` được giữ nguyên để đối chiếu.

## 2. Nơi lưu dữ liệu

| Thành phần | Trách nhiệm |
|---|---|
| PostgreSQL | Source of truth cho nghiệp vụ, metadata tài liệu, chunk text, lịch sử AI và citation |
| Cloudflare R2 | Nội dung nhị phân: avatar, ảnh/video, file chat và file nguồn RAG |
| Qdrant | Embedding của chunk; point ID bằng `ai_document_chunks.id` |
| Redis | Cache, OTP/rate limit ngắn hạn, WebSocket presence và pub/sub; không là source of truth |

Không lưu binary lớn trong PostgreSQL và không coi payload Qdrant là bản dữ liệu chuẩn.

## 3. Các miền dữ liệu

### Identity và phân quyền

- `users`: danh tính đăng nhập, trạng thái tài khoản, xác thực email.
- `profiles`: thông tin sinh viên 1-1 với user.
- `roles`, `user_roles`: vai trò toàn hệ thống, ví dụ `SUPER_ADMIN`, `USER`.
- Quyền `ADMIN` theo nhóm nằm ở `group_members.role`, không đưa vào role toàn hệ thống.
- `email_verification_codes`: chỉ lưu hash của OTP.
- `refresh_tokens`: chỉ lưu hash token, hỗ trợ rotation qua `replaced_by_id`.

### Community và kiểm duyệt

- `groups`, `group_members`: hội nhóm và quyền trong phạm vi nhóm.
- `posts`: nội dung và đầy đủ dấu vết duyệt/từ chối.
- `media_files`: metadata object trên R2 dùng chung.
- `post_media`: liên kết media với bài viết và thứ tự hiển thị.
- `comments`: hỗ trợ reply qua `parent_id` và soft delete.
- `post_likes`: khóa chính kép ngăn like trùng.
- `reports`: hàng đợi xử lý báo cáo. Vì target đa hình (`USER/POST/COMMENT`), tính tồn tại
  của `target_id` phải được kiểm tra trong service transaction.

### Social graph

- `friend_requests`: chặn hai lời mời pending ngược chiều cho cùng một cặp.
- `friendships`: chỉ lưu một hàng cho một quan hệ, luôn bảo đảm `user_low_id < user_high_id`.
- `user_blocks`: một chiều, có unique tự nhiên bằng khóa chính kép.

### Chat realtime và thông báo

- `conversations`, `conversation_members`, `messages`: lịch sử chat bền vững.
- `message_receipts`: delivered/seen theo từng người nhận; không đặt một status chung trên message.
- `message_attachments`: tái sử dụng metadata R2 từ `media_files`.
- `notifications`: có `read_at`, actor và payload; Redis/WebSocket chỉ làm kênh phát realtime.

### AI/RAG

- `ai_documents`: thực thể tài liệu logic, loại tài liệu, năm học, hiệu lực và quyền truy cập.
- `ai_document_versions`: snapshot bất biến của từng lần cập nhật tài liệu.
- `ai_document_chunks`: đoạn văn bản bất biến và ánh xạ 1-1 sang Qdrant point.
- `ai_conversations`: phiên hỏi đáp và bản tóm tắt lịch sử dài.
- `ai_messages`: từng lượt hỏi/đáp, câu hỏi viết lại và filter retrieval đã dùng.
- `ai_message_citations`: liên kết câu trả lời với chunk và lưu snapshot nguồn tại thời điểm trả lời.

## 4. Đáp ứng nghiệp vụ RAG

### Quy chế 2025/2026

Lọc Qdrant/PostgreSQL theo:

```text
document_type = REGULATION
academic_year = 2025/2026
status = INDEXED
```

`effective_from/effective_to` phân biệt hiệu lực. `ai_document_versions` giữ bản cũ để trả lời
câu hỏi lịch sử mà không làm mất nguồn.

### Thông báo mới

Vector similarity không xác định được "mới nhất". Retrieval phải kết hợp:

```text
document_type = ANNOUNCEMENT
status = INDEXED
published_at DESC
```

Có thể giới hạn cửa sổ thời gian trước khi semantic search hoặc rerank.

### Hỏi đáp lịch sử

Nếu câu hỏi chứa năm học/thời điểm rõ ràng, không ép `is_current = true`. Nếu không có thời điểm,
ưu tiên phiên bản hiện hành. Mọi answer và citation đã phát sinh được giữ trong bảng AI riêng.

### Hội thoại nhiều lượt

`sequence_number` xác định thứ tự tuyệt đối trong phiên. `rewritten_question` lưu câu hỏi độc lập
đã suy ra từ ngữ cảnh. Khi context dài, cập nhật `summary` và `summary_until_sequence`, rồi gửi
summary + các lượt gần nhất vào LLM.

### Trích dẫn nguồn

Mỗi citation trỏ tới đúng chunk, đồng thời giữ snapshot tiêu đề, URL, trang và section. Vì vậy citation
vẫn hiển thị đúng khi tài liệu có phiên bản mới. Không xóa cứng version/chunk đã được trích dẫn;
archive tài liệu và xóa point Qdrant theo quy trình đồng bộ.

## 5. Luồng dữ liệu AI

```text
Nguồn chính thức / file được phép
  -> ai_documents + ai_document_versions(PENDING)
  -> lấy nội dung từ web/R2
  -> chuẩn hóa + SHA-256
  -> chunking
  -> ai_document_chunks
  -> embedding BAAI/bge-m3
  -> Qdrant point (id = chunk.id)
  -> version.status = INDEXED

Câu hỏi
  -> lưu ai_messages(USER)
  -> viết lại câu hỏi theo lịch sử
  -> xác định temporal/access filters
  -> Qdrant retrieval + optional rerank
  -> sinh câu trả lời chỉ từ context
  -> lưu ai_messages(ASSISTANT)
  -> lưu ai_message_citations
```

## 6. Những vấn đề đã sửa từ `base.md`

- Các foreign key bắt buộc chuyển thành `NOT NULL`.
- Dùng `timestamptz` thay vì `timestamp` để Web/Mobile nhất quán múi giờ.
- Bỏ index trùng do `PRIMARY KEY`/`UNIQUE` đã tự tạo index.
- Sửa tìm kiếm tên bằng `pg_trgm` và `gin_trgm_ops`.
- Thêm dấu vết kiểm duyệt bài viết.
- Chuẩn hóa friendship để không có cặp đảo chiều trùng nhau.
- Tách delivery/read receipt theo người nhận.
- Tách chat xã hội khỏi hội thoại AI.
- Thêm versioning, temporal metadata, ingestion lifecycle và access filter cho RAG.
- Chuẩn hóa media qua một bảng metadata R2.
- Chỉ lưu hash của OTP và refresh token.

## 7. Ràng buộc ở tầng service

Một số invariant không thể biểu diễn gọn bằng foreign key và cần transaction/service validation:

- Chỉ email `@hvnh.edu.vn` được tạo tài khoản (DB cũng có check phòng thủ).
- Group Admin chỉ duyệt nội dung thuộc nhóm mình quản trị.
- `reports.target_id` phải tồn tại đúng theo `target_type`.
- Direct conversation có đúng hai thành viên và không tạo trùng cặp.
- Người bị block không thể gửi lời mời hoặc tin nhắn.
- `ai_documents.current_version_id` phải thuộc chính document đó.
- Payload Qdrant phải mang access metadata và chỉ trả tài liệu người hỏi có quyền xem.
- Chỉ version `INDEXED` mới được dùng để sinh câu trả lời.

## 8. Hướng triển khai

Không import trực tiếp schema V2 vào database đang có dữ liệu. Chuyển từng miền thành Alembic migration,
seed hai role hệ thống, thêm test constraint/index, sau đó mới viết repository/service. Với môi trường mới,
`base_v2.sql` có thể dùng làm đặc tả chuẩn để sinh model và migration đầu tiên.
