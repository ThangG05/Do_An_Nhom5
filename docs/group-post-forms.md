# Form bài đăng hội nhóm — Web, phiên bản 2

Triển khai theo `mo_ta_ui_ux_bai_dang_hoi_nhom.md`. Giữ **4 hội nhóm riêng** và quyền thành viên/quản trị viên hiện có. Chưa thay đổi Flutter.

## Dữ liệu và SQL

Đã kiểm tra schema đang kết nối: `posts.category` là `VARCHAR(30)`, `posts.listing_data` và `posts.location_data` là `JSONB`. Không cần thêm bảng/cột, không xóa bảng hoặc backfill bằng dữ liệu suy đoán.

Thông tin chuyên biệt được lưu trong `listing_data`, có `_form_version: 2`. `post_media` tiếp tục quản lý tệp và thứ tự tệp. `location_data` giữ tên, địa chỉ và tọa độ khi người dùng chủ động chọn GPS/tìm kiếm. Nhập vị trí bằng chữ không bắt buộc tọa độ.

| Nhóm | Dữ liệu bắt buộc | Tùy chọn |
|---|---|---|
| Pass đồ | `marketListing.productName`, `price`, `location` | `content`, tệp |
| Sự kiện | `eventListing.eventName`, `eventDate`, `eventTime`, `location`, `content` | tệp |
| Ghép phòng | `roomListing.location`, `content` | `rentPerMonth`, tệp |
| Học tập | `studyListing.subjectName`, `content` | tệp |

Giá là số nguyên VNĐ không âm, tối đa 15 chữ số; JSON giữ chuỗi số để tương thích client cũ. `0` ở Pass đồ hiển thị “Tặng miễn phí”. Ngày theo `YYYY-MM-DD`, giờ bắt đầu theo `HH:mm`, theo giờ Việt Nam. Không tự điền tên địa điểm, giờ tổ chức hay tiện ích giả định.

## API và tương thích

- `POST /api/v1/users/me/posts`: Home/trang cá nhân gửi `category`; backend tìm đúng nhóm, kiểm tra thành viên và lưu bài `PENDING`.
- `POST /api/v1/groups/{id}/posts`: form trong nhóm; backend **tự xác định category từ nhóm**, không tin category do client gửi. Lưu đủ thông tin chuyên biệt, không chỉ `content` như trước.
- Cả hai nhận `form_version: 2` từ web mới. Backend kiểm tra các trường theo bảng trên trước khi lưu.
- Payload không có version được xem là v1, tiếp tục hỗ trợ Flutter đang phát hành. Đây là tương thích có chủ đích, không phải v1 đã đáp ứng validation mới. Khi nâng Flutter cần gửi đủ trường và `form_version: 2`, sau đó mới bỏ nhánh v1.
- Bài cũ vẫn đọc được khi thiếu tiêu đề/thông tin mới; không dựng dữ liệu thay cho người dùng.
- `PATCH /api/v1/posts/{id}` lưu thông tin chuyên biệt, kiểm tra lại dữ liệu v2; không cho chuyển nhóm/category của bài đã đăng. Bài nhóm sau sửa quay về `PENDING` để không vượt qua kiểm duyệt.
- Feed, profile, bài hội nhóm và hàng chờ admin cùng nhận các trường `marketListing`, `roomListing`, `eventListing`, `studyListing`.
- Tìm kiếm trong nhóm bao gồm nội dung, tên vật phẩm/sự kiện/môn học và vị trí.

Ví dụ gửi trong nhóm Sự kiện (ID nhóm lấy từ API, không hard-code):

```json
{
  "form_version": 2,
  "content": "Cùng xem phim và giao lưu với các bạn sinh viên.",
  "media_ids": [],
  "eventListing": {
    "eventName": "Movie Night",
    "eventDate": "2026-12-20",
    "eventTime": "18:00",
    "location": "Hội trường A"
  },
  "location": { "name": "Hội trường A" }
}
```

## Trải nghiệm web

- Chọn nhóm bằng thẻ màu/icon ở form dùng chung; mở từ nhóm thì khóa đúng nhóm đó.
- Form chỉ hiện trường liên quan, dấu `*` cho trường bắt buộc, ghi rõ trường tùy chọn.
- Báo lỗi sát trường, đưa focus về trường sai đầu tiên; giữ bản nháp khi API lỗi.
- Xem trước trực tiếp trên desktop; nút xem trước riêng cho màn hình nhỏ.
- Dùng lại LocationPicker hiện có; sửa tên vị trí thủ công sẽ bỏ tọa độ cũ để tránh liên kết sai.
- Đính kèm tối đa 10 tệp. Client kiểm tra định dạng, tệp rỗng và giới hạn mặc định: ảnh 5 MB, video 100 MB, âm thanh/tài liệu 25 MB. Backend tiếp tục kiểm tra dung lượng cấu hình, chữ ký tệp, quyền sở hữu và trạng thái READY. Nếu đổi cấu hình giới hạn server, cần đồng bộ giới hạn client.
- Khóa submit và chỉnh form khi đang gửi; tệp đã tải thành công được giữ để thử lại khi lưu bài thất bại.
- Thẻ bài dùng chung hiển thị nhãn nhóm, tiêu đề, giá/ngày giờ/môn học; không đổi cơ chế quyền đọc, thích, bình luận và thông báo.
- Có nền sáng/tối, không tràn ngang trên màn hình nhỏ.

## Kiểm thử

Backend (chạy từ `backend`):

```powershell
..\.venv\Scripts\python.exe -m pytest tests/test_services/test_group_post_forms.py tests/test_services/test_read_path_batching.py tests/test_services/test_group_batching.py tests/test_services/test_post_visibility.py -q
```

Web (chạy từ `frontend`):

```powershell
npx tsc --noEmit
npx playwright test --config playwright.group-post.config.ts
```

UI tests dùng API fixtures trong Playwright để kiểm tra giao diện/payload, **không tạo dữ liệu mock trong ứng dụng hoặc ghi dữ liệu vào database thật**. Backend tests kiểm tra validation, quyền đăng, dữ liệu lưu/serialize, tương thích v1 và duyệt lại sau sửa. Kiểm thử upload Cloudflare R2, GPS và toàn bộ vòng duyệt trên môi trường triển khai vẫn cần tài khoản/tệp thật.

Ngoài phạm vi lần này: Flutter, hashtag, lọc giá/ngày/vị trí nâng cao, thời gian kết thúc sự kiện, phân loại sâu nhu cầu phòng trọ.
