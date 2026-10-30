# HVNH Hub Flutter — tiến độ thiết kế iOS-inspired

## Audit giao diện hiện có

App dùng Flutter Material với `AppTheme.light`, `CupertinoIcons`, `AppPageBar` và `AppBackButton`; không có package UI/animation bên ngoài. `AppShell` có 5 tab (`Trang chủ`, `Hội nhóm`, `Khám phá`, `Tin nhắn`, `Thông báo`) và giữ state bằng `IndexedStack`. Các màn đẩy lên gồm đăng nhập/đăng ký/khôi phục mật khẩu, tạo bài, chi tiết bài/bình luận, nhóm/kiểm duyệt/kho tài liệu, hội thoại, trợ lý AI, hồ sơ/tìm bạn bè, quản trị hệ thống. Dữ liệu đi qua repository và backend hiện có; đợt này không thay đổi contract.

| Trước | Thiết kế mới trong đợt này | Nơi áp dụng |
| --- | --- | --- |
| Màu/spacing/bo góc/motion rải rác | Semantic palette, spacing/radius/motion tokens; TabBar/segmented/switch nhất quán | `core/theme` |
| Hero navy tĩnh | Brand hero có lớp chiều sâu và tilt khi chạm, tắt khi reduced motion | Login, Home, Hội nhóm |
| Tab bar icon rời và nhỏ | Vùng chọn dạng pill mềm, target rộng hơn | `AppShell` |
| Vòng quay hoặc chữ trống thô | Skeleton tĩnh, empty/error có icon, thông điệp và thử lại | Feed, Hội nhóm, Tin nhắn, Kho tài liệu, Quản trị |
| Nút camera chồng avatar | Chạm trực tiếp avatar để xem/đổi; nhãn screen reader | Hồ sơ |
| Hành động đăng bài xếp dọc | Action chips ngang, dễ quét và chạm | Feed |
| Card nhóm thiếu phân loại | Icon/accent theo nhóm, trạng thái thành viên dạng pill | Hội nhóm |
| Nút gửi AI rời ô nhập | CTA tròn 46px, keyboard send/drag-dismiss | Trợ lý AI |

## Quyết định thiết kế và hiệu năng

- Giữ navy/xanh/vàng HVNH làm bộ màu chính; màu phụ chỉ giúp nhận diện nhóm.
- Không thêm dependency. Hiệu ứng 3D dùng `Matrix4` và `AnimatedContainer` của Flutter, chỉ cho ba hero ở đầu màn hình, không chạy trên feed/chat dài. Khi `disableAnimations` bật, card không tilt và duration về 0.
- Skeleton tĩnh không shimmer liên tục để giảm repaint và hao pin.
- Giữ `IndexedStack`, đường đi, xác thực, phân quyền, API/repository và state cũ.
- Bỏ ép `TargetPlatform.iOS` toàn app để Android giữ các hành vi nền tảng cần thiết; vẻ ngoài iOS đến từ component/theme riêng.

## Kiểm tra

- `dart format` đã format các file sửa; Dart CLI gặp lỗi quyền ghi telemetry ở `AppData` sau khi format.
- `dart analyze lib test`: không có lỗi hoặc warning của mã; còn các lint mức `info` về dấu ngoặc từ code hiện hữu. CLI cũng báo lỗi quyền ghi telemetry sau khi phân tích.
- `flutter test --no-pub test/widget_test.dart`: Flutter CLI không xuất kết quả trong khoảng 40 giây tại môi trường này, đã dừng để tránh treo. Test mới cho palette, hero reduced motion và empty-state action đã viết nhưng chưa xác nhận chạy.
- Chưa có emulator/iOS simulator và chưa chụp ảnh trước/sau hoặc đo FPS. Cần kiểm tra thực tế trên màn nhỏ, dark mode và iPhone.

## Chưa hoàn tất

Đây là đợt nền tảng + các màn được dùng nhiều, chưa phải xác nhận toàn bộ app đạt acceptance criteria. Dark palette đã có nhưng chưa bật dark mode vì nhiều màn cũ vẫn đặt màu sáng cố định; cần chuyển chúng sang semantic tokens trước để không giảm độ tương phản. Các màn quản trị, thư viện tài liệu, hội thoại chi tiết và thẻ trích dẫn AI cần tiếp tục rà responsive, keyboard, text scale và trạng thái bất thường trên thiết bị thật.
