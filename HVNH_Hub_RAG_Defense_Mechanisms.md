# Các cơ chế phòng thủ cần xây dựng cho hệ thống RAG HVNH Hub

> **Mục đích:** Danh sách tổng quan các nhóm cơ chế bảo vệ cần có hoặc cần hoàn thiện để hướng tới triển khai production. Đây là đề xuất thiết kế, không phải kết luận hệ thống hiện đang thiếu toàn bộ các cơ chế.

## Danh sách cơ chế phòng thủ

| Nhóm | Cơ chế phòng thủ cần xây dựng | Mức ưu tiên |
|---|---|---|
| **D1** | **Input Guardrails** – Kiểm tra, giới hạn và phát hiện prompt injection trong câu hỏi người dùng | **P1** |
| **D2** | **Document Security & Content Sanitization** – Kiểm tra tài liệu HTML, PDF, DOCX, XLSX trước khi đưa vào kho tri thức | **P0** |
| **D3** | **Indirect Prompt Injection Defense** – Phát hiện và cô lập các chỉ thị độc hại được nhúng trong tài liệu truy xuất | **P0** |
| **D4** | **Knowledge Poisoning Defense** – Xác minh độ tin cậy nguồn, phát hiện tài liệu giả mạo, trùng lặp và thao túng tri thức | **P0** |
| **D5** | **Retrieval Security** – Kiểm soát truy xuất Qdrant và PostgreSQL, chống thao túng kết quả tìm kiếm và reranking | **P0** |
| **D6** | **Access Control & Data Isolation** – Kiểm soát phân quyền PUBLIC / AUTHENTICATED / GROUP, ngăn truy cập tài liệu và hội thoại trái phép | **P0** |
| **D7** | **Grounding & Hallucination Defense** – Bắt buộc câu trả lời dựa trên bằng chứng truy xuất, từ chối khi thiếu thông tin | **P0** |
| **D8** | **Citation Verification** – Xác thực nguồn trích dẫn, kiểm tra tính chính xác của thông tin và ngăn giả mạo citation | **P0** |
| **D9** | **Conversation Memory Security** – Chống đầu độc lịch sử hội thoại, rò rỉ dữ liệu và thao túng quá trình viết lại câu hỏi | **P1** |
| **D10** | **Document Version & Freshness Control** – Kiểm soát phiên bản, thời gian hiệu lực và ngăn sử dụng tài liệu lỗi thời | **P1** |
| **D11** | **API & Infrastructure Protection** – Rate limiting, concurrency limiting, timeout, chống SSRF và lạm dụng tài nguyên | **P1** |
| **D12** | **Security Monitoring & Audit Logging** – Ghi log, phát hiện hành vi bất thường, cảnh báo và truy vết sự cố | **P1** |

## Quy ước mức ưu tiên

- **P0:** Ưu tiên bắt buộc trước khi triển khai production, đặc biệt khi có rủi ro lộ dữ liệu, đầu độc nguồn hoặc trả lời sai có vẻ đáng tin.
- **P1:** Ưu tiên cao, cần hoàn thiện để vận hành an toàn, ổn định và có khả năng giám sát.

## Các cơ chế nên ưu tiên triển khai trước

**D3, D4, D6, D7 và D8**: tập trung chống tấn công qua tài liệu, kiểm soát nguồn tri thức, bảo vệ phân quyền và bảo đảm câu trả lời có căn cứ.

## Ghi chú theo kiến trúc hiện tại

Theo báo cáo kỹ thuật HVNH Hub, hệ thống đã có một phần cơ chế như kiểm tra URL/SSRF trong crawler, kiểm soát quyền tài liệu, rate limiting bằng Redis, quản lý phiên bản và citation verifier dựa trên quy tắc. Vì vậy, cần **rà soát, kiểm thử và hoàn thiện** các phần này trước khi quyết định xây dựng mới.
