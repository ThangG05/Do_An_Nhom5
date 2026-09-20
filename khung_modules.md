# ĐỀ CƯƠNG CHI TIẾT DỰ ÁN PHÁT TRIỂN NỀN TẢNG CỘNG ĐỒNG "HVNH HUB"

---

## I. MỤC TIÊU DỰ ÁN

### 1. Đối với người quản trị (Admin)
* **Kiểm soát đầu vào hệ thống**: Chỉ cho phép đăng ký tài khoản bằng email thuộc tên miền chính thức `@hvnh.edu.vn` và yêu cầu xác thực email (qua OTP hoặc liên kết xác thực) trước khi kích hoạt tài khoản nhằm bảo đảm tính định danh nội bộ.
* **Thiết lập quy trình kiểm duyệt nội dung đa cấp**:
  * Cho phép **Group Admin** phê duyệt (`Approved`), từ chối (`Rejected`) kèm lý do đối với các bài đăng trước khi hiển thị công khai trong hội nhóm phụ trách.
  * Hỗ trợ ghim bài viết, duyệt/xóa thành viên và quản lý tương tác trong phạm vi nhóm.
* **Tiếp nhận và xử lý báo cáo vi phạm (`Report Management`)**:
  * Hỗ trợ tiếp nhận và xử lý báo cáo đối với bài viết, bình luận và người dùng.
  * Cho phép **Super Admin** tiếp nhận các báo cáo toàn hệ thống, thực hiện các biện pháp quản trị chuyên sâu như cảnh cáo, xóa nội dung vi phạm hoặc tạm khóa/khóa vĩnh viễn tài khoản người dùng.
* **Phân cấp quản trị linh hoạt theo phạm vi**:
  * **Super Admin**: Quản trị toàn hệ thống, quản lý tài khoản, cấu hình tham số, xem thống kê dashboard, xuất dữ liệu và quản lý bảo trì.
  * **Group Admin**: Quản trị thành viên và kiểm duyệt nội dung trong hội nhóm được phân công (quyền gắn liền với từng nhóm cụ thể thay vì áp dụng toàn hệ thống).

### 2. Đối với sinh viên (User)
* **Môi trường cộng đồng đa năng**: Cung cấp môi trường cộng đồng dành cho sinh viên Học viện Ngân hàng để trao đổi giáo trình, đồ dùng cá nhân (Pass đồ), tìm người ở ghép/phòng trọ, theo dõi sự kiện và chia sẻ thông tin học tập.
* **Hỗ trợ kết nối người dùng**: Tìm kiếm sinh viên theo tên hoặc mã sinh viên, gửi/chấp nhận/từ chối lời mời kết bạn, quản lý danh sách bạn bè, hủy kết bạn, chặn người dùng và nhắn tin 1-1 theo thời gian thực (Realtime Chat).
* **Hệ thống thông báo tức thời (Push/Realtime Notifications)**: Cập nhật liên tục trạng thái bài viết (được duyệt/từ chối), tương tác (Like/Comment), lời mời kết bạn và tin nhắn mới.
* **Quản lý thông tin cá nhân**: Hỗ trợ quản lý hồ sơ cá nhân (Avatar, Bio, thông tin định danh), bài viết đã đăng, các nhóm đã tham gia và các mối quan hệ bạn bè.
* **Trợ lý AI Agent RAG thông minh**: Tích hợp AI Agent hỗ trợ tra cứu thông tin liên quan đến Học viện từ các nguồn thông tin chính thức, công khai hoặc tài liệu được phép sử dụng.

---

## II. PHÂN RÃ BẢNG CHI TIẾT CÁC MODULE VÀ CHỨC NĂNG HỆ THỐNG

### 1. Phân hệ Quản trị (Admin Modules) - Chi tiết & Chuyên sâu

#### 1.1. Module Quản trị Cấp cao (Super Admin Module)
* **Bảng điều khiển & Thống kê hệ thống (`System Dashboard & Analytics`)**:
  * Thống kê tổng quan realtime: Tổng số sinh viên, số tài khoản đang hoạt động, tài khoản bị khóa, tổng số bài viết theo từng trạng thái (`Pending`, `Approved`, `Rejected`), lượt tương tác và lưu lượng tin nhắn.
  * Biểu đồ tăng trưởng người dùng, lưu lượng bài viết theo khoảng thời gian (ngày/tuần/tháng) và biểu đồ phân bổ bài viết theo từng nhóm nghiệp vụ.
* **Quản lý Tài khoản & Phân quyền (`User & Role Management`)**:
  * Tìm kiếm, lọc danh sách người dùng theo tên, mã sinh viên, email, khoa/lớp hoặc trạng thái tài khoản.
  * **Gán / Tước quyền Admin**: Cấp quyền Group Admin cho người dùng tại một hoặc nhiều nhóm cụ thể; hoặc thu hồi quyền quản trị.
  * **Xử lý tài khoản vi phạm**: Thực hiện Cảnh cáo, Tạm khóa (`Suspended`) có thời hạn hoặc Khóa vĩnh viễn (`Banned`) đối với các tài khoản vi phạm quy chế. Mở khóa tài khoản khi hết hạn hoặc sau khi xem xét khiếu nại.
  * **Xuất dữ liệu (`Data Export`)**: Cho phép lọc và xuất danh sách sinh viên, danh sách vi phạm hoặc báo cáo thống kê ra file Excel (`.xlsx`).
* **Quản lý Báo cáo Vi phạm toàn hệ thống (`System-wide Report Handling`)**:
  * Tiếp nhận tập trung tất cả báo cáo từ sinh viên đối với Bài viết, Bình luận hoặc Người dùng.
  * Xem thông tin chi tiết báo cáo: Người báo cáo, đối tượng bị báo cáo, lý do vi phạm và minh chứng đi kèm.
  * **Quyết định xử lý**:
    * **Xác nhận vi phạm (`Approved`)**: Hệ thống tự động gỡ bỏ/xóa bài viết, bình luận vi phạm và gửi thông báo cảnh cáo/áp dụng án phạt lên tài khoản bị báo cáo.
    * **Bác bỏ báo cáo (`Rejected`)**: Đánh dấu báo cáo không hợp lệ, giữ nguyên nội dung.
  * Tự động gửi thông báo kết quả xử lý về cho người dùng đã gửi báo cáo.
* **Quản lý Cấu hình & Bảo trì Hệ thống (`System Config & Maintenance`)**:
  * **Chế độ bảo trì (`Maintenance Mode`)**: Bật/Tắt trạng thái bảo trì hệ thống.
  * **Cấu hình thông báo bảo trì**: Tùy chỉnh nội dung, thời gian bảo trì dự kiến để phát thông báo tới toàn bộ ứng dụng Web và Mobile.
  * Quản lý danh mục từ khóa cấm/spam (`Blacklist Keywords`) để tự động lọc nội dung thô tục hoặc nhạy cảm.

#### 1.2. Module Quản trị Nhóm (Group Admin Module)
* **Quản lý Thành viên Nhóm (`Group Member Management`)**:
  * **Phê duyệt gia nhập**: Xem danh sách yêu cầu tham gia nhóm (`Group Join Requests`), chấp nhận hoặc từ chối sinh viên muốn gia nhập nhóm.
  * **Quản lý danh sách thành viên**: Xem danh sách thành viên trong nhóm, tìm kiếm thành viên theo tên/mã sinh viên.
  * **Mời thành viên ra khỏi nhóm (`Kick Member`)**: Xóa thành viên vi phạm quy định riêng của nhóm khỏi hội nhóm.
* **Kiểm duyệt Nội dung Nhóm (`Group Content Moderation`)**:
  * **Hàng chờ kiểm duyệt (`Pending Posts Queue`)**: Xem danh sách các bài viết đang chờ duyệt trong nhóm phụ trách.
  * **Phê duyệt (`Approve`)**: Cho phép bài viết hiển thị công khai trong hội nhóm.
  * **Từ chối (`Reject`)**: Từ chối bài viết kèm lý do phản hồi (ví dụ: *Nội dung sai chủ đề, Thiếu thông tin giá cả trong Chợ Pass đồ, Tin trọ không xác thực...*) để người đăng chỉnh sửa.
  * **Quản lý bài viết đã duyệt**: Xóa các bài viết đã hiển thị nếu phát hiện vi phạm sau đó.
  * **Ghim bài viết (`Pin Post`)**: Cho phép ghim các bài viết quan trọng (thông báo nhóm, nội quy nhóm, sự kiện nổi bật) lên đầu trang nhóm.
* **Quản lý Bình luận & Báo cáo nội bộ Nhóm**:
  * Trực tiếp xóa các bình luận Spam, thô tục hoặc gây hấn trong các bài viết thuộc nhóm mình quản lý.
  * Tiếp nhận và xử lý nhanh các báo cáo vi phạm nội dung xảy ra trong phạm vi nhóm phụ trách.

---

### 2. Phân hệ Sinh viên (User Modules) - Chi tiết & Chuyên sâu

#### 2.1. Module Xác thực & Tài khoản (`Auth & Account Management`)
* **Đăng ký tài khoản (`Register`)**: Bắt buộc nhập email định danh `@hvnh.edu.vn`. Hệ thống tự động kiểm tra cú pháp và sự tồn tại của tài khoản.
* **Xác thực Email (`Email Verification`)**: Gửi mã OTP hoặc liên kết xác thực an toàn qua email để kích hoạt tài khoản trước khi truy cập ứng dụng.
* **Lấy thông tin định danh mở rộng**: Tích hợp gọi API/truy xuất tự động từ hệ thống của Học viện (khi được cấp quyền) để chuẩn hóa tên hiển thị, mã sinh viên, lớp/khoa.
* **Đăng nhập & Duy trì phiên (`Login & Session Management`)**:
  * Đăng nhập bằng Email + Mật khẩu.
  * Cơ chế bảo mật Refresh Token và Access Token (JWT) giúp duy trì phiên đăng nhập an toàn trên Web và Mobile.
* **Quên mật khẩu / Đổi mật khẩu (`Password Recovery & Change`)**: Khôi phục mật khẩu thông qua OTP gửi về email sinh viên; hỗ trợ đổi mật khẩu định kỳ trong cài đặt tài khoản.

#### 2.2. Module Hồ sơ cá nhân (`User Profile`)
* **Xem thông tin cá nhân**: Hiển thị Avatar, Tên hiển thị, Mã sinh viên, Khoa/Ngành học, Bio (tiểu sử), danh sách bài viết đã đăng, danh sách nhóm đã tham gia và danh sách bạn bè.
* **Chỉnh sửa hồ sơ (`Edit Profile`)**: Cập nhật ảnh đại diện (upload lên Cloudflare R2), chỉnh sửa câu giới thiệu bản thân (Bio). Các thông tin định danh cứng (Họ tên, Mã SV, Email) được giữ cố định để bảo đảm tính chính xác.

#### 2.3. Module Hội nhóm (`Groups System`)
* **Cấu trúc nhóm nghiệp vụ chuyên biệt (4 nhóm chính)**:
  1. **Pass đồ**: Sàn trao đổi, mua bán giáo trình, tài liệu, đồ dùng cá nhân, thiết bị điện tử cũ dành cho sinh viên.
  2. **Ghép phòng / Tìm phòng trọ**: Tìm bạn ở ghép, đăng tin cho thuê/tìm phòng trọ khu vực gần Học viện.
  3. **Sự kiện**: Cập nhật tin tức, sự kiện, cuộc thi, hoạt động ngoại khóa do Học viện, Đoàn thanh niên, Hội sinh viên hoặc các CLB tổ chức.
  4. **Học tập**: Chia sẻ tài liệu, đề thi mẫu, kinh nghiệm học tập, thảo luận môn học.
* **Thao tác người dùng trong nhóm**:
  * Gửi yêu cầu tham gia nhóm / Rời khỏi nhóm.
  * Xem danh sách bài viết trong nhóm (lọc theo bài viết mới nhất, bài viết nổi bật, bài viết đã ghim).
  * Tìm kiếm bài viết theo từ khóa trong phạm vi nhóm.

#### 2.4. Module Bài viết & Tương tác (`Posts & Interactions`)
* **Tạo bài viết mới (`Create Post`)**:
  * Soạn thảo văn bản, hỗ trợ đính kèm nhiều hình ảnh, video hoặc tệp tin (lưu trữ trên Cloudflare R2).
  * Lựa chọn nhóm muốn đăng.
  * Bài viết sau khi gửi sẽ chuyển sang trạng thái `Pending` để chờ Group Admin duyệt.
* **Quản lý trạng thái bài viết**:
  * Sinh viên có thể theo dõi trạng thái bài đăng của mình (`Pending` - Chờ duyệt, `Approved` - Đã duyệt, `Rejected` - Bị từ chối kèm lý do).
  * Chỉnh sửa bài viết (`Edit Post`) hoặc Xóa bài viết (`Delete Post`).
* **Tương tác trên bài viết**:
  * **Thích (`Like / Unlike`)**: Tương tác cảm xúc trên bài viết công khai.
  * **Bình luận (`Comment`)**: Gửi bình luận văn bản, hình ảnh dưới bài viết; hỗ trợ trả lời bình luận (Reply comment).
* **Báo cáo vi phạm (`Report Post/Comment`)**: Sinh viên có thể gửi báo cáo đối với bài viết hoặc bình luận có nội dung vi phạm, lừa đảo, thô tục lên hệ thống quản trị.

#### 2.5. Module Kết nối Bạn bè (`Friendships & Network`)
* **Tìm kiếm sinh viên (`Search Users`)**: Tìm kiếm chính xác hoặc tương đối theo Tên sinh viên hoặc Mã sinh viên.
* **Quản lý Lời mời kết bạn (`Friend Requests`)**: Gửi lời mời kết bạn; Chấp nhận (`Accept`) hoặc Từ chối (`Reject`) lời mời kết bạn từ người khác; Hủy lời mời đã gửi.
* **Danh sách Bạn bè (`Friends List`)**: Quản lý danh sách bạn bè đã kết nối, hủy kết bạn (`Unfriend`).
* **Chặn người dùng (`Block User`)**: Chặn người dùng khác để ngăn họ xem hồ sơ, tìm kiếm hoặc gửi tin nhắn/lời mời kết bạn.

#### 2.6. Module Trò chuyện thời gian thực (`Realtime 1-1 Chat`)
* **Nhắn tin 1-1 thời gian thực (`WebSocket Chat`)**: Trò chuyện trực tiếp giữa 2 sinh viên với độ trễ cực thấp thông qua WebSocket.
* **Định dạng tin nhắn đa dạng**: Gửi tin nhắn Văn bản (Text), Hình ảnh (Image) và Tệp đính kèm (Files, tài liệu học tập...).
* **Trạng thái tin nhắn & Hiện diện (`Message Status & Presence`)**:
  * Theo dõi tiến trình tin nhắn: **Sent** (Đã gửi) $\rightarrow$ **Delivered** (Đã đến thiết bị) $\rightarrow$ **Seen** (Đã xem).
  * Hiển thị trạng thái hoạt động: **Online / Offline** thời gian thực của bạn bè.

#### 2.7. Module Thông báo (`Notifications System`)
* **Thông báo thời gian thực (`Push / Realtime Notifications`)**:
  * Thông báo trạng thái bài viết: Được duyệt (`Approved`) hoặc Bị từ chối (`Rejected`).
  * Thông báo tương tác: Có người Thích (`Like`) hoặc Bình luận (`Comment`) vào bài viết của mình.
  * Thông báo kết nối: Nhận lời mời kết bạn mới hoặc lời mời kết bạn được chấp nhận.
  * Thông báo tin nhắn: Có tin nhắn mới từ người dùng khác.
* **Quản lý thông báo**: Đánh dấu đã đọc / chưa đọc, xem danh sách thông báo theo thứ tự thời gian.