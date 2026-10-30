# HVNH Hub Mobile

Ứng dụng Flutter dùng chung FastAPI, PostgreSQL, R2, Redis và RAG với bản web HVNH Hub.

## Chạy trên Android Emulator

1. Chạy backend tại cổng `8000`.
2. Mở một Android Emulator trong Android Studio.
3. Chạy:

```powershell
flutter pub get
flutter run -d <ANDROID_EMULATOR_ID>
```

Mặc định ứng dụng gọi `http://10.0.2.2:8000/api/v1`, là địa chỉ máy host nhìn từ Android Emulator.

Nếu Android Studio đang chọn **Chrome, Edge hoặc Windows** thay vì Android Emulator, ứng dụng không chạy như Android. Chạy Flutter Web bằng lệnh sau khi cần kiểm tra trên trình duyệt:

```powershell
flutter run -d chrome --web-hostname localhost --web-port 3000
```

Trong VS Code mở thư mục gốc `Web_HVNH`, chọn cấu hình **HVNH Flutter Web (Google Login)** ở Run and Debug rồi nhấn F5. Cấu hình này cũng cố định Chrome ở `http://localhost:3000`; nút Run mặc định của Flutter thường dùng cổng ngẫu nhiên.

Flutter Web dùng `http://127.0.0.1:8000/api/v1` và trình duyệt gửi CORS preflight `OPTIONS`. Backend chỉ cho phép các cổng localhost ngẫu nhiên khi `CORS_ALLOW_LOCAL_DEV_ORIGINS=true` trong `.env` phát triển. Không bật lựa chọn này khi triển khai production.

Google Login trên Chrome dùng nút Google Identity Services riêng, không dùng luồng native của Android. OAuth Web Client trong Google Cloud phải cho phép đúng **Authorized JavaScript origin** của Flutter, ví dụ `http://localhost:3000` với lệnh trên. Nếu trang Next.js cũng đang dùng cổng 3000, dừng Next.js khi thử Flutter hoặc chọn cổng khác rồi thêm origin đó trong Google Cloud và CORS backend. Cổng ngẫu nhiên của `flutter run -d chrome` thường không có trong danh sách origin nên Google Login sẽ không hoạt động. Chạy Chrome **không cần** OAuth Android/SHA-1.

Nếu Google hiện **Access blocked: Authorization Error**, mở Google Cloud Console → Google Auth Platform → Clients → Web OAuth Client có ID trùng `GOOGLE_CLIENT_ID` trong `backend/.env` → **Authorized JavaScript origins**, thêm `http://localhost:3000` (không thêm đường dẫn `/login`, `/signup` hoặc dấu `/` ở cuối). Địa chỉ trên thanh Chrome phải đúng `localhost:3000`; `127.0.0.1:3000` là một origin khác. Sau khi lưu, đóng phiên Flutter cũ, chạy lại bằng cấu hình trên và thử lại. Nếu trang lỗi ghi mã khác `origin_mismatch` (ví dụ `access_denied` hoặc `redirect_uri_mismatch`), cần đọc đúng mã đó trước khi sửa cấu hình tiếp.

Ảnh được backend trả bằng URL tải có chữ ký từ Cloudflare R2. Flutter Web hiển thị ảnh R2 qua phần tử ảnh của trình duyệt để tránh lỗi CORS khi bucket chưa cho phép origin của Flutter; Android tải URL đó trực tiếp. Khi triển khai production, vẫn nên cấu hình CORS cho bucket R2 với origin web thực tế để có hiệu năng hiển thị tốt hơn. Nếu ảnh cũ hết hạn URL ký, làm mới màn hình để lấy URL mới từ API.

## Chạy trên điện thoại thật

Điện thoại và máy chạy backend phải dùng chung mạng. Thay `<IP-MAY-TINH>` bằng IPv4 LAN của máy:

```powershell
flutter run --dart-define=API_BASE_URL=http://<IP-MAY-TINH>:8000/api/v1
```

Backend cần lắng nghe trên mạng LAN, ví dụ:

```powershell
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Kiểm tra chất lượng

```powershell
dart format lib test
dart analyze
flutter test
```

## Kiến trúc

Mỗi module chia thành `data`, `domain`, `presentation`; dependency được khởi tạo tập trung trong `lib/app/di/app_dependencies.dart`. Token được lưu bằng secure storage, access token tự làm mới bằng refresh token và đăng xuất sẽ thu hồi refresh token trên backend.

Các luồng đã dùng API thật gồm: đăng nhập/đăng ký email, feed và phân trang cursor, đăng bài/media/vị trí, bình luận, hội nhóm, quản trị nhóm, tin nhắn realtime, thông báo, hồ sơ, bạn bè, RAG và quản trị hệ thống.

Đăng nhập Google native cần cấu hình OAuth Android (package name, SHA-1/SHA-256 và Android client ID) trước khi bật trong bản phát hành.

### OAuth Android cho Google Login

Trong cùng Google Cloud project đang chứa Web OAuth Client của backend, tạo thêm credential loại **Android** với:

- Package name: `vn.edu.hvnh.hub`
- SHA-1/SHA-256 của **chính bản APK đang cài**, không chép fingerprint từ máy thành viên khác. Trên Windows, chạy trong `mobilehvnh/android`:

```powershell
.\gradlew.bat :app:signingReport
```

Tìm `Variant: debug` và sao chép SHA-1 vào credential Android. Mỗi debug keystore của từng máy có thể khác nhau; nếu nhiều thành viên chạy app, cần đăng ký fingerprint tương ứng trong cùng Google Cloud project. Bản release/Play App Signing cũng có fingerprint riêng.

Flutter đọc Web Client ID hiện tại từ endpoint công khai `/system/public-config`, endpoint này lấy `GOOGLE_CLIENT_ID` từ env backend. Vì vậy đổi OAuth Web Client trong env không cần sửa/hardcode lại ID trong Flutter; hãy khởi động lại backend sau khi cập nhật env.

Khi tạo keystore phát hành, cần tạo thêm Android OAuth credential cho package trên với SHA-1/SHA-256 của keystore release.

App truyền Web Client ID vừa đọc được bằng `serverClientId`, nên không bắt buộc có `google-services.json` chỉ để đăng nhập Google. Nếu cửa sổ chọn tài khoản đóng ngay sau khi chọn, đó **cũng có thể là lỗi OAuth Android**, không nhất thiết là người dùng tự hủy. Hãy kiểm tra package, SHA-1, Web Client ID, Google Play services và log `Google Sign-In Android` trong Debug Console. Backend vẫn chỉ chấp nhận tài khoản Google Workspace `@hvnh.edu.vn`.
