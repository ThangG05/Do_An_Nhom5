# HVNH Hub — Đặc tả 3 chế độ kiểm duyệt bình luận

## 1. Mục tiêu

Thiết kế một setting quản trị để chọn cách hệ thống xử lý bình luận. Phạm vi của model hiện tại chỉ là phát hiện nội dung **xúc phạm/thù ghét**. Model phân loại bình luận thành:

- `CLEAN`: bình luận không bị nhận diện là xúc phạm/thù ghét.
- `VIOLATION`: bình luận có nội dung `OFFENSIVE` hoặc `HATE`.

Model sử dụng là **PhoBERT-base-v2 + Focal Loss**, fine-tune trên ViHSD và ViHOS. Model không được dùng để kết luận spam, quảng cáo, sai chủ đề hoặc các loại vi phạm khác.

## 2. Setting kiểm duyệt

Setting có ba lựa chọn loại trừ lẫn nhau:

| Giá trị | Tên hiển thị | Cách xử lý bình luận |
|---|---|---|
| `OFF` | Tắt | Không gọi model và không kiểm tra blacklist. Bình luận tiếp tục theo luồng hiện tại. |
| `AI_AUTO_BLOCK` | Tự động chặn | Gọi PhoBERT. Chặn bình luận khi điểm `VIOLATION` đạt hoặc vượt ngưỡng cấu hình; cho phép bình luận khi điểm thấp hơn ngưỡng. |
| `BLACKLIST_ONLY` | Blacklist | Không gọi model. Chặn bình luận khớp với từ/cụm từ đang hoạt động trong blacklist; cho phép bình luận không khớp. |

Chỉ áp dụng chế độ đang được chọn. Khi chọn `BLACKLIST_ONLY`, AI không chạy. Khi chọn `AI_AUTO_BLOCK`, blacklist không được dùng để quyết định thay cho model.

## 3. Chế độ Tắt

Khi `moderation_mode = OFF`:

1. Không gửi nội dung bình luận đến model.
2. Không kiểm tra blacklist.
3. Giữ nguyên quy trình đăng bình luận hiện có.

Đây là chế độ mặc định khi triển khai setting lần đầu.

## 4. Chế độ Tự động chặn bằng AI

### Luồng xử lý

1. Nhận nội dung bình luận.
2. Chuẩn hóa đầu vào đúng như khi fine-tune: Unicode NFKC, chuẩn hóa khoảng trắng và word segmentation bằng PyVi.
3. Gửi văn bản đến model PhoBERT-base-v2.
4. Đọc điểm dự đoán của lớp `VIOLATION`.
5. So sánh điểm với `ai_block_threshold`:
   - `score >= threshold`: lưu bình luận với trạng thái `BLOCKED_BY_AI`.
   - `score < threshold`: tiếp tục xử lý/hiển thị bình luận theo luồng bình thường.

### Giá trị khởi tạo

- Model: `vinai/phobert-base-v2` đã fine-tune.
- Loss: Focal Loss với cấu hình được notebook chọn bằng validation.
- Ngưỡng thử ban đầu: `0.6584175` (có thể hiển thị gọn là `0.6584`).
- Đầu ra policy sau fine-tune: `moderation_policy.json`.

Ngưỡng `0.6584` được chọn trên validation ViHSD và ViHOS để ưu tiên precision cao, với điều kiện precision Wilson lower bound tối thiểu 90% và tỷ lệ CLEAN bị chặn tối đa 1% trên cả hai nguồn validation. Trên test công khai, ngưỡng này chặn 147/1.132 vi phạm ở ViHSD và 93/531 vi phạm ở ViHOS; có 6 bình luận sạch bị chặn trong test ViHSD và 0 trong test ViHOS. Vì vậy ngưỡng này chỉ bắt một phần nhỏ các trường hợp có dấu hiệu rõ.

Các con số trên là benchmark công khai, không bảo đảm hiệu năng tương tự trên bình luận HVNH Hub. Không ghi nhận `0.6584` như một ngưỡng đã được xác thực trên dữ liệu HVNH.

### Khi model lỗi

Nếu model không tải được, inference lỗi hoặc hết thời gian chờ:

- Không tự động chặn bình luận do lỗi hệ thống.
- Cho bình luận đi theo luồng bình thường.
- Ghi log lỗi kỹ thuật để quản trị viên kiểm tra.

Không xóa bình luận đã lưu; thay đổi trạng thái sang `BLOCKED_BY_AI` để có thể kiểm tra và khôi phục.

## 5. Chế độ Blacklist

### Luồng xử lý

1. Quản trị viên thêm từ hoặc cụm từ vào blacklist.
2. Khi có bình luận mới, chuẩn hóa văn bản và các mục trong blacklist.
3. Nếu bình luận khớp một mục đang hoạt động, lưu trạng thái `BLOCKED_BY_BLACKLIST`.
4. Nếu không khớp, cho bình luận đi theo luồng bình thường.

### Quy tắc khớp

- So khớp không phân biệt chữ hoa/chữ thường.
- Chuẩn hóa Unicode NFKC và khoảng trắng trước khi so khớp.
- Với cụm từ, ưu tiên khớp theo ranh giới từ/cụm từ; tránh chặn chỉ vì một chuỗi ký tự xuất hiện bên trong một từ khác.
- Mỗi mục có trạng thái bật/tắt để quản trị viên có thể tạm ngừng mà không xóa lịch sử.
- Blacklist là danh sách do quản trị viên quản lý; nó không được tự động sinh hoặc thay đổi từ dự đoán của model.

## 6. Cấu hình và phân quyền

Setting nên được quản lý phía backend, không chỉ lưu trạng thái trong giao diện.

Các trường cấu hình tối thiểu:

```text
moderation_mode: OFF | AI_AUTO_BLOCK | BLACKLIST_ONLY
ai_model_name: vinai/phobert-base-v2
ai_model_version: version/checkpoint đã triển khai
ai_block_threshold: 0.6584175
updated_by: user_id quản trị viên
updated_at: thời điểm cập nhật
```

Chỉ tài khoản có quyền quản trị mới được đổi chế độ, ngưỡng AI hoặc nội dung blacklist. Mọi thay đổi setting cần lưu người thực hiện và thời điểm.

## 7. Log quyết định

Với mỗi quyết định chặn, lưu tối thiểu:

- ID bình luận.
- Chế độ được áp dụng.
- Hành động: `BLOCKED_BY_AI`, `BLOCKED_BY_BLACKLIST` hoặc cho phép.
- Với AI: model version, điểm `VIOLATION`, ngưỡng tại thời điểm xử lý.
- Với blacklist: ID mục blacklist khớp.
- Thời điểm xử lý.
- Lỗi inference nếu có.

Không cần tạo bản sao nội dung bình luận trong log nếu nội dung đã được lưu ở bảng bình luận; liên kết bằng ID để giảm lưu trữ dư thừa.

## 8. Tiêu chí nghiệm thu

- Chọn `OFF`: không phát sinh request đến model và không áp dụng blacklist.
- Chọn `AI_AUTO_BLOCK`: quyết định dùng đúng model version và ngưỡng đang lưu; vượt ngưỡng thì chặn, dưới ngưỡng thì cho qua.
- Chọn `BLACKLIST_ONLY`: không gọi model; chỉ chặn khi khớp mục blacklist đang hoạt động.
- Model lỗi trong `AI_AUTO_BLOCK`: bình luận không bị chặn chỉ vì lỗi inference; lỗi được ghi log.
- Bình luận bị chặn vẫn được lưu để quản trị viên tra cứu và khôi phục.
- Đổi setting có hiệu lực phía backend và được ghi nhận lịch sử.
