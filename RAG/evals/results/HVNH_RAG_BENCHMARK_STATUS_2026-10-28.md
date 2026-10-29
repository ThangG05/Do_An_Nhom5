# Đánh giá RAG HVNH Hub — trạng thái ban đầu ngày 28/10/2026

> **Đã được cập nhật:** Sau khi kết nối Modal thành công, benchmark ngày 28/10/2026 đã chạy xong. Xem [báo cáo kết quả đầy đủ](HVNH_RAG_BENCHMARK_2026-10-28.md) và các artifact `*-2026-10-28.json`. Nội dung bên dưới ghi lại baseline cũ và lần chạy bị treo ban đầu, không còn là trạng thái cuối cùng.

## Kết luận ngắn

Chưa có điểm benchmark mới hoàn tất trong lần kiểm tra ngày 28/10/2026. Lượt chạy retrieval mới bị chờ ở bước tạo embedding qua Modal quá 2 phút và được dừng để tránh treo lâu. Vì vậy các chỉ số bên dưới là **baseline hoàn chỉnh gần nhất ngày 11/09/2026**, không được diễn giải là số đo của code, dữ liệu hoặc cấu hình đang chạy ngày 28/10.

## Baseline gần nhất đã hoàn tất — 11/09/2026

### End-to-end trên bộ câu hỏi có nhãn đã duyệt

| Chỉ số | Kết quả |
|---|---:|
| Số câu hỏi | 30 |
| Đạt theo bộ tiêu chí rule-based | 30/30 (100%) |
| Độ chính xác quyết định từ chối | 100% |
| Tìm đúng nguồn trích dẫn kỳ vọng | 100% |
| Lỗi runtime | 0 |
| Độ trễ trung bình | 3.653,5 ms |
| p50 | 3.566 ms |
| p95 | 4.570 ms |
| Lớn nhất | 9.295 ms |

“Đạt” ở đây là kết hợp các tiêu chí trong benchmark: refusal đúng, nguồn kỳ vọng có trong citations, keyword và required facts. Đây không phải đánh giá thủ công toàn diện từng câu trả lời.

### Retrieval trên tập phân tầng

| Chỉ số | Kết quả |
|---|---:|
| Số truy vấn | 60 |
| Hit@5 | 0,982 |
| MRR | 0,900 |
| Độ chính xác truy vấn kỳ vọng không có kết quả | 1,000 |

Kết quả cho thấy tài liệu liên quan thường lọt vào top 5; MRR 0,900 cho thấy vẫn có truy vấn tài liệu đúng không nằm ở hạng đầu. Tập 60 ca còn nhỏ so với toàn bộ chủ đề, năm học và dạng câu hỏi trong hệ thống.

### RAGAS — artifact ngày 09/09/2026

RAGAS đã chấm **10 trong 24 câu có reference**; đây là mẫu một phần, không phải toàn bộ tập answerable.

| Metric | Điểm trung bình |
|---|---:|
| Faithfulness | 0,750 |
| Answer relevancy | 0,885 |
| Answer correctness | 0,487 |
| Context precision | 0,800 |
| Context recall | 0,774 |

Answer relevancy là điểm mạnh tương đối: câu trả lời nhìn chung đúng hướng câu hỏi. Answer correctness là hạn chế lớn nhất; câu trả lời có thể thiếu chi tiết so với reference. Faithfulness và context recall cũng còn khoảng cách để khẳng định độ tin cậy cao, đặc biệt với câu hỏi nhiều điều kiện hoặc đòi hỏi đủ ý.

### Độ trễ qua các lượt lặp — artifact ngày 09/09/2026

| Chỉ số | Kết quả |
|---|---:|
| Số request | 15 (5 ca × 3 lượt) |
| Tỷ lệ request thành công | 100% |
| Trung bình | 6.118,3 ms |
| p50 | 5.149 ms |
| p95 | 13.371 ms |
| p99 | 13.376 ms |

Đây là một mẫu rất nhỏ và có outlier; không đủ để công bố SLA hoặc dự đoán tải đồng thời.

## Lần kiểm tra mới ngày 28/10/2026

- Đã khởi chạy `scripts.evaluate_retrieval` trên `evals/retrieval-stratified.json`.
- Không nhận được kết quả; quá trình chờ tại lời gọi embedding Modal trên hai phút và được dừng.
- Không tạo artifact kết quả mới, do đó **không có số đo mới để so sánh**.
- Đây mới là bằng chứng về sự cố/độ trễ của lần gọi embedding trong môi trường benchmark hiện tại; chưa đủ để kết luận nguyên nhân gốc là app Modal, xác thực, cold start hay kết nối mạng.

## Giới hạn và cách diễn giải cho báo cáo

1. Baseline trên được đo ngày 11/09/2026, trong khi benchmark rerun ngày 28/10 chưa hoàn tất. Cần ghi ngày rõ ràng và không trình bày baseline cũ như trạng thái hiện hành.
2. Bộ end-to-end 30 câu và retrieval 60 câu chưa đủ đại diện toàn bộ miền dữ liệu HVNH.
3. RAGAS chỉ chấm 10/24 mẫu do quota lúc chạy; mỗi câu có reference nhưng reference chưa chắc bao phủ mọi biến thể đáp án hợp lệ.
4. Judge dùng cùng nhà cung cấp/model Gemini với luồng tạo câu trả lời ở lần đo cũ, có nguy cơ thiên lệch tự đánh giá.
5. Latency phụ thuộc thời điểm, cache, cold start Modal, tình trạng mạng, DB và Qdrant. Một lần đo nhỏ không phải cam kết hiệu năng production.
6. Kết quả “30/30” là pass theo bộ luật benchmark, không đồng nghĩa độ chính xác tổng quát 100% hay không hallucination.

## Artifact nguồn của baseline

- `rag-current-2026-09-11-v3.json`
- `retrieval-stratified-current-v2.json`
- `ragas-benchmark.json`
- `latency-repeated.json`
- `HVNH_RAG_BENCHMARK_2026-09-11.md`

## Để có bộ số liệu mới có thể công bố

1. Khôi phục/kiểm tra lời gọi Modal embedding từ đúng profile/workspace và xác nhận request embedding trả về trong thời gian hữu hạn.
2. Chạy lại retrieval stratified và lưu artifact có ngày chạy mới.
3. Chạy lại end-to-end trên toàn bộ 30 câu gold đã duyệt; ghi lại response, citations, required-fact coverage và latency.
4. Chấm RAGAS trên toàn bộ 24 câu answerable, hoặc báo rõ mẫu nếu quota buộc phải giới hạn; ưu tiên judge khác model sinh.
5. Chạy latency lặp nhiều lượt và báo p50/p95/p99 riêng cold-start/warm-start.
6. Lưu mã commit, cấu hình model/embedding, kích thước dữ liệu và ngày chạy bên cạnh mỗi artifact để benchmark có thể tái lập.
