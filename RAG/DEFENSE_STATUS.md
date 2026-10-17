# Trạng thái phòng thủ RAG HVNH Hub

Đối chiếu với `HVNH_Hub_RAG_Defense_Mechanisms.md` (17/10/2026). Các kiểm soát dưới đây chạy trong ứng dụng; đánh giá production vẫn cần kiểm thử với dữ liệu và hạ tầng triển khai thật.

| Nhóm | Kiểm soát hiện có | Phần còn cần vận hành/đánh giá |
|---|---|---|
| D1 | Chuẩn hóa Unicode, giới hạn đầu vào, chặn mẫu prompt injection trước cả bước đọc lịch sử. | Bổ sung tập tấn công mới khi phát hiện biến thể. |
| D2 | Giới hạn byte, trang PDF, kích thước văn bản và giải nén Office; bỏ HTML/DOCX/XLSX ẩn và tệp Office có nội dung thực thi. | Kiểm tra malware ở lớp lưu trữ nếu bổ sung upload công khai. |
| D3 | Kiểm tra tài liệu lúc crawl, chunk, index và ngay trước khi gửi ngữ cảnh cho LLM; từ chối đoạn đáng ngờ. | Quy trình duyệt thủ công cần làm sạch nội dung trước khi phát hành. |
| D4 | Crawler giới hạn nguồn, domain, đường dẫn; hash phát hiện phiên bản trùng; truy xuất loại nguồn đã tắt hoặc không còn thuộc phạm vi. | Chưa có đối chiếu ngữ nghĩa giữa nhiều văn bản để phát hiện thông tin giả nhưng khác câu chữ. |
| D5 | Qdrant chỉ trả ứng viên; PostgreSQL xác nhận point ID, hash, nội dung, phiên bản, trạng thái và quyền. Kết quả lexical cũng kiểm tra trạng thái/hash. | Đo thêm độ trễ truy vấn PostgreSQL trong môi trường production. |
| D6 | Quyền PUBLIC/AUTHENTICATED/GROUP được kiểm tra ở API và khi truy xuất; chỉ nhóm ACTIVE được tính thành viên. Quyền sở hữu hội thoại được kiểm tra bằng SQL. | Kiểm thử tích hợp với tài khoản thật và các trạng thái nhóm. |
| D7 | Câu trả lời thông tin vẫn cần bằng chứng và kiểm tra nguồn cho từng nhận định. Lời chào/cảm ơn/tạm biệt ngắn dùng câu trả lời định sẵn, không đưa ra dữ kiện học viện và không gọi LLM. | Vẫn cần đánh giá chất lượng suy luận bằng bộ câu hỏi chuẩn. |
| D8 | Chỉ nhận citation ID thuộc ngữ cảnh đã xác minh; mỗi câu có nhận định phải dẫn nguồn; kiểm tra số tiền, ngày, mã và URL. | Bộ kiểm chứng theo quy tắc không chứng minh được mọi quan hệ ngữ nghĩa. |
| D9 | Lịch sử có giới hạn, chỉ dùng để viết lại câu hỏi; câu hỏi mới được kiểm tra trước bước này; hội thoại kiểm tra chủ sở hữu. | Định kỳ rà soát tóm tắt lịch sử được tạo bởi mô hình. |
| D10 | Kiểm tra phiên bản hiện hành, trạng thái index, năm học và thời hạn hiệu lực; truy vấn lịch sử mới được dùng phiên bản lưu trữ. | Theo dõi chất lượng metadata ngày hiệu lực của tài liệu cũ. |
| D11 | Rate limit Redis, giới hạn đồng thời, timeout, giới hạn tải và kiểm tra URL/redirect của crawler. | DNS pinning ở tầng HTTP và chính sách WAF cần cấu hình hạ tầng riêng. |
| D12 | Audit cho lượt hỏi và từ chối bảo mật; log đếm tài liệu/ứng viên bị loại, không ghi nội dung câu hỏi hay tài liệu. | Cần kết nối log với hệ thống cảnh báo vận hành. |

Khi phát hành sau bản cập nhật này, kiểm tra Qdrant có payload `content_hash` như `point_payload()` hiện hành. Point cũ thiếu hash sẽ bị loại an toàn; cần chạy lại pipeline index để những tài liệu đó xuất hiện trong kết quả.

Kiểm thử tại chỗ: từ thư mục gốc chạy `.\.venv\Scripts\python.exe -m pytest RAG/tests -q`.
