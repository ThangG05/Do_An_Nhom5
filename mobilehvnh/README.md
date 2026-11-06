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
flutter run -d chrome --web-hostname localhost --web-port 5000
```

Trong VS Code mở thư mục gốc `Web_HVNH`, chọn cấu hình **HVNH Flutter Web (Google Login)** ở Run and Debug rồi nhấn F5. Cấu hình này cố định Chrome ở `http://localhost:5000`; nút Run mặc định của Flutter thường dùng cổng ngẫu nhiên.

Flutter Web dùng `http://127.0.0.1:8000/api/v1` và trình duyệt gửi CORS preflight `OPTIONS`. Mặc định backend chỉ cho phép origin trong `CORS_ORIGINS` (mặc định `http://localhost:3000`); để chạy local tại port `5000`, bật `CORS_ALLOW_LOCAL_DEV_ORIGINS=true` trong `.env` phát triển hoặc thêm chính xác `http://localhost:5000` vào `CORS_ORIGINS`. Không bật lựa chọn local này khi triển khai production.

Google Login trên Chrome dùng nút Google Identity Services riêng, không dùng luồng native của Android. OAuth Web Client trong Google Cloud phải cho phép đúng **Authorized JavaScript origin** của Flutter: thêm `http://localhost:5000` (chỉ origin, không thêm đường dẫn hay dấu `/` cuối). Nếu dùng `127.0.0.1` thay cho `localhost`, phải thêm origin tương ứng riêng. Cổng ngẫu nhiên của `flutter run -d chrome` thường không có trong danh sách origin nên Google Login sẽ không hoạt động. Chạy Chrome **không cần** OAuth Android/SHA-1.

Nếu Google hiện **Access blocked: Authorization Error** hoặc `origin_mismatch`, mở Google Cloud Console → Google Auth Platform → Clients → Web OAuth Client có ID trùng `GOOGLE_CLIENT_ID` trong `backend/.env` → **Authorized JavaScript origins** → thêm `http://localhost:5000`. Sau khi lưu, chạy lại Flutter Web và thử lại. Đây là cấu hình phía Google Cloud; thay đổi origin trong code không thể thay thế bước này. Nếu trang lỗi ghi mã khác `origin_mismatch` (ví dụ `access_denied` hoặc `redirect_uri_mismatch`), cần đọc đúng mã đó trước khi sửa cấu hình tiếp.

Nếu lỗi xảy ra trên ứng dụng Android cài/chạy bằng Android Emulator hoặc điện thoại thật (không phải Chrome), **Authorized JavaScript origins không áp dụng**. Khi đó OAuth Android Client phải khai báo đúng application ID/package name và SHA-1 của signing certificate; Web Client ID vẫn được dùng làm server client ID để backend xác minh ID token.

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

### Đóng gói Android release

Bản release phải dùng upload keystore riêng; không dùng debug keystore để phát hành. Từ PowerShell tại thư mục `mobilehvnh`, tạo keystore (Keytool sẽ hỏi mật khẩu, không đưa mật khẩu vào dòng lệnh):

```powershell
keytool -genkeypair -v -keystore android/app/hvnhhub-upload.jks -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 -alias hvnhhub-upload
```

Tạo `android/key.properties` cục bộ, điền mật khẩu vừa chọn và nội dung:

```properties
storePassword=<mật khẩu keystore>
keyPassword=<mật khẩu key>
keyAlias=hvnhhub-upload
storeFile=app/hvnhhub-upload.jks
```

`key.properties` và keystore đã được loại khỏi Git. Sao lưu keystore và mật khẩu an toàn; mất chúng sẽ khiến không thể ký bản cập nhật bằng cùng một khóa. Tạo Android OAuth credential với package `vn.edu.hvnh.hub` và SHA-1 của keystore phát hành trước khi kiểm tra Google Login trên APK/AAB.

Tạo Android App Bundle để phát hành hoặc APK để cài thử:

```powershell
flutter build appbundle --release --dart-define=API_BASE_URL=https://hvnhhub.id.vn/api/v1 --dart-define=WEB_BASE_URL=https://hvnhhub.id.vn
```

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://hvnhhub.id.vn/api/v1 --dart-define=WEB_BASE_URL=https://hvnhhub.id.vn
```

Khi phát hành bản cập nhật, tăng `version` trong `pubspec.yaml` (đặc biệt là số build sau dấu `+`).

### Build IPA bằng GitHub Actions

Workflow `.github/workflows/ios_build.yml` chạy thủ công trên runner macOS, build IPA ký Ad Hoc và lưu artifact `hvnhhub-ios-ipa`. Cấu hình repository GitHub ở chế độ private và thêm các GitHub Actions secrets sau trong **Settings → Secrets and variables → Actions**:

- `IOS_TEAM_ID`: Team ID trong Apple Developer account.
- `IOS_CERTIFICATE_BASE64`: certificate Apple Distribution dạng `.p12`, mã hóa Base64.
- `IOS_CERTIFICATE_PASSWORD`: mật khẩu export file `.p12`.
- `IOS_PROVISIONING_PROFILE_BASE64`: Ad Hoc provisioning profile đã chứa App ID `vn.edu.hvnh.hub` và UDID iPhone cần cài.
- `IOS_PROFILE_NAME`: tên profile đúng như trường `Name` trong provisioning profile.
- `IOS_GOOGLE_CLIENT_ID`: iOS OAuth Client ID tạo với Bundle ID `vn.edu.hvnh.hub`.
- `IOS_GOOGLE_REVERSED_CLIENT_ID`: URL scheme đảo của iOS OAuth Client ID.

Không commit certificate, provisioning profile hoặc thông tin ký vào Git. Tài khoản Apple Developer phải có quyền tạo certificate/profile Ad Hoc; thêm UDID từng iPhone vào profile rồi tải lại profile sau khi có thay đổi. Trong GitHub, mở **Actions → Build HVNH Hub iOS IPA → Run workflow**. Tải `.ipa` ở mục Artifacts sau khi job thành công. Cài trực tiếp lên các thiết bị đã đăng ký trong profile; workflow không tự gửi app lên App Store/TestFlight.
