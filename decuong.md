Mục tiêu
Đối với người quản trị
• Kiểm soát đầu vào của hệ thống bằng cách chỉ cho phép đăng ký tài khoản bằng email thuộc tên miền @hvnh.edu.vn và yêu cầu xác thực email trước khi kích hoạt tài khoản.
• Thiết lập quy trình kiểm duyệt nội dung, cho phép Group Admin phê duyệt hoặc từ chối bài đăng trước khi hiển thị công khai trong hội nhóm.
• Hỗ trợ tiếp nhận và xử lý báo cáo đối với bài viết, bình luận và người dùng; cho phép Super Admin thực hiện các biện pháp quản trị như xóa nội dung vi phạm hoặc khóa tài khoản.
• Phân cấp quản trị theo phạm vi: Super Admin quản trị toàn hệ thống, Group Admin quản trị thành viên và nội dung trong nhóm được phân công.
Đối với sinh viên
• Cung cấp môi trường cộng đồng dành cho sinh viên Học viện Ngân hàng để trao đổi giáo trình, đồ dùng cá nhân, tìm người ở ghép/phòng trọ, theo dõi sự kiện và chia sẻ thông tin học tập.
• Hỗ trợ kết nối người dùng thông qua tìm kiếm sinh viên, gửi lời mời kết bạn, quản lý danh sách bạn bè và nhắn tin 1-1 theo thời gian thực.
• Cung cấp hệ thống thông báo về trạng thái bài viết, tương tác, lời mời kết bạn và tin nhắn mới.
• Hỗ trợ quản lý hồ sơ cá nhân, bài viết đã đăng, các nhóm đã tham gia và các mối quan hệ bạn bè.
• Tích hợp AI Agent hỗ trợ tra cứu thông tin liên quan đến Học viện từ các nguồn thông tin chính thức, công khai hoặc tài liệu được phép sử dụng.
Nội dung thực hiện và kết quả dự kiến

1. Chuẩn bị và lập kế hoạch
   • Xác định đề tài: Xây dựng nền tảng cộng đồng đa nền tảng “HVNH Hub” dành cho sinh viên Học viện Ngân hàng.
   • Xác định phạm vi: phát triển đồng thời Web và Mobile; Web sử dụng Next.js, Mobile sử dụng Flutter; hai nền tảng dùng chung Backend API.
   • Lập kế hoạch kiến trúc: FastAPI làm Backend dùng chung, PostgreSQL làm cơ sở dữ liệu chính, Cloudflare R2 lưu trữ dữ liệu đa phương tiện, WebSocket phục vụ realtime.
   • Lập kế hoạch AI: xây dựng hệ thống RAG sử dụng BAAI/bge-m3 để tạo embedding và Qdrant làm vector database; dữ liệu lấy từ các nguồn chính thức, công khai của Học viện và các tài liệu được phép sử dụng.
2. Phân tích yêu cầu
   • Yêu cầu xác thực và quản lý tài khoản: Chỉ cho phép đăng ký bằng email @hvnh.edu.vn; người dùng phải xác thực email bằng OTP hoặc liên kết xác thực trước khi kích hoạt tài khoản. Việc lấy thông tin định danh mở rộng từ hệ thống của Học viện chỉ thực hiện khi có quyền truy cập API phù hợp.
   • Yêu cầu hội nhóm: Hệ thống gồm các nhóm nghiệp vụ chính: Pass đồ; Ghép phòng / tìm phòng trọ; Sự kiện; Học tập. Người dùng có thể tham gia nhóm, xem nội dung và tương tác theo quyền được cấp.
   • Yêu cầu bài viết và tương tác: Bài viết hỗ trợ văn bản, nhiều hình ảnh và video; có các trạng thái pending, approved, rejected. Người dùng có thể Like/Unlike, Comment và báo cáo nội dung.
   • Yêu cầu kết nối người dùng: Hỗ trợ tìm kiếm sinh viên theo tên hoặc mã sinh viên, gửi/chấp nhận/từ chối lời mời kết bạn, hủy kết bạn và chặn người dùng.
   • Yêu cầu giao tiếp thời gian thực: Chat 1-1 hỗ trợ văn bản, hình ảnh và tệp; quản lý các trạng thái sent, delivered, seen và trạng thái online/offline.
   • Yêu cầu thông báo: Thông báo cho các sự kiện như bài viết được duyệt/từ chối, Like/Comment, lời mời kết bạn và tin nhắn mới.
   • Yêu cầu phân quyền: Gồm Super Admin, Group Admin và User. Quyền Group Admin được gắn với từng hội nhóm thay vì áp dụng trên toàn hệ thống.
   • Yêu cầu đa nền tảng: Web và Mobile sử dụng chung Backend API và PostgreSQL để bảo đảm tính nhất quán dữ liệu.
   • Yêu cầu lưu trữ đa phương tiện: Ảnh, video và tệp được lưu trên Cloudflare R2; PostgreSQL lưu metadata và object_key/thông tin tham chiếu.
   • Yêu cầu AI Agent: Sử dụng RAG để truy xuất thông tin liên quan đến Học viện. Dữ liệu được thu thập, làm sạch, chia đoạn, tạo embedding bằng BAAI/bge-m3 và lưu trên Qdrant; câu trả lời ưu tiên dựa trên ngữ cảnh truy xuất và kèm nguồn tham khảo khi có thể.
3. Thiết kế hệ thống
   • Thiết kế kiến trúc tổng thể theo mô hình Client - Backend API - Data/Storage Services: Next.js và Flutter cùng giao tiếp với FastAPI.
   • Thiết kế cơ sở dữ liệu PostgreSQL cho users, groups, group_members, posts, post_media, comments, post_likes, friend_requests, friendships, user_blocks, conversations, messages, notifications và reports.
   • Thiết kế API và cơ chế xác thực/ủy quyền; sử dụng Access Token và Refresh Token; kiểm soát quyền ở Backend.
   • Thiết kế Cloudflare R2 cho avatar, ảnh/video bài viết và tệp đính kèm; ưu tiên cơ chế upload/download an toàn bằng object key và URL có kiểm soát.
   • Thiết kế WebSocket cho Chat realtime; Redis là thành phần mở rộng khi cần cache, presence hoặc mở rộng kết nối realtime.
   • Thiết kế AI Agent RAG gồm: nguồn dữ liệu, crawler/ingestion, làm sạch, chunking, embedding BAAI/bge-m3, Qdrant retrieval, lọc metadata, reranking (nếu triển khai) và sinh câu trả lời có trích dẫn nguồn.
   • Thiết kế giao diện bằng Figma, bảo đảm luồng nghiệp vụ nhất quán giữa Web và Mobile.
4. Phát triển hệ thống
   • Phát triển Backend FastAPI dùng chung cho Web và Flutter; tổ chức theo các module Auth, User, Group, Post, Friend, Chat, Notification, Report và AI Agent.
   • Phát triển Web bằng Next.js và ứng dụng Mobile bằng Flutter dựa trên cùng API contract.
   • Phát triển chức năng xác thực email, đăng nhập, Access Token/Refresh Token và phân quyền.
   • Phát triển hội nhóm, bài viết, kiểm duyệt bài viết, Like/Unlike, Comment và Report.
   • Phát triển hệ thống bạn bè và Chat 1-1 realtime qua WebSocket.
   • Tích hợp Cloudflare R2 cho dữ liệu đa phương tiện.
   • Phát triển pipeline RAG và API AI Agent sử dụng BAAI/bge-m3 + Qdrant.
5. Kiểm thử hệ thống
   • Kiểm thử chức năng, API, tích hợp, giao diện, phân quyền và bảo mật.
   • Kiểm thử đồng bộ dữ liệu giữa Web và Mobile trên cùng Backend/PostgreSQL.
   • Kiểm thử luồng bài viết: tạo bài, upload media, kiểm duyệt, Like/Comment và báo cáo.
   • Kiểm thử hệ thống bạn bè, Chat realtime, sent/delivered/seen và online/offline.
   • Kiểm thử hiệu năng các API quan trọng, độ trễ WebSocket và truy vấn PostgreSQL.
   • Đánh giá AI Agent bằng tập câu hỏi chuẩn; đánh giá retrieval (ví dụ Recall@K/MRR khi phù hợp), độ đúng câu trả lời, faithfulness và độ chính xác của trích dẫn nguồn.
6. Triển khai
   • Đóng gói ứng dụng Flutter dưới dạng APK để thử nghiệm trên thiết bị Android; triển khai Web và Backend trên môi trường server.
   • Triển khai PostgreSQL, Cloudflare R2 và Qdrant; cấu hình biến môi trường và bảo mật thông tin kết nối.
   • Kiểm tra các quy trình end-to-end: đăng ký/đăng nhập, đăng bài, kiểm duyệt, tương tác, kết bạn, nhắn tin và hỏi đáp AI.
   • Xây dựng tài liệu cài đặt, tài liệu API và hướng dẫn sử dụng cho sinh viên/quản trị viên.
7. Bảo trì và mở rộng
   • Theo dõi phản hồi người dùng, log hệ thống và các lỗi phát sinh trong quá trình thử nghiệm.
   • Tối ưu truy vấn PostgreSQL, API, cơ chế tải media và hiệu năng truy xuất của hệ thống RAG.
   • Xây dựng cơ chế cập nhật định kỳ dữ liệu Học viện để hạn chế thông tin lỗi thời trong AI Agent.
   • Mở rộng hệ thống đánh giá uy tín người dùng trong phân hệ Pass đồ.
   • Tích hợp bản đồ cho phân hệ Ghép phòng / tìm phòng trọ.
   • Khi quy mô tăng, có thể bổ sung Redis, cân bằng tải hoặc tách các module có tải lớn như Chat, Notification và AI Agent thành dịch vụ độc lập.
   Kết quả dự kiến đạt được
   • Hoàn thiện nền tảng cộng đồng HVNH Hub hoạt động trên cả Web và Mobile, sử dụng chung Backend và PostgreSQL.
   • Hoàn thiện cơ chế xác thực email Học viện, phân quyền Super Admin/Group Admin/User và quy trình kiểm duyệt nội dung.
   • Hoàn thiện các nghiệp vụ hội nhóm, bài viết, tương tác, bạn bè, Chat realtime, thông báo và báo cáo.
   • Quản lý dữ liệu đa phương tiện trên Cloudflare R2 thay vì lưu trực tiếp trong PostgreSQL.
   • Tích hợp AI Agent RAG sử dụng BAAI/bge-m3 và Qdrant để hỗ trợ sinh viên tra cứu thông tin Học viện từ nguồn dữ liệu được phép sử dụng.
   • Triển khai thử nghiệm và có kết quả kiểm thử/đánh giá về chức năng, hiệu năng, realtime và chất lượng RAG.
   Giải pháp công nghệ: FastAPI, PostgreSQL, Next.js, Flutter, Cloudflare R2, Qdrant, BAAI/bge-m3, WebSocket.
