# Báo cáo benchmark hệ thống HVNH RAG

- Thời điểm đo: `2026-09-09T17:16:37+07:00`
- LLM sinh câu trả lời/judge: `gemini` / `gemini-3.5-flash-lite`
- Embedding: `modal` / `BAAI/bge-m3` (1024 chiều)
- Collection: `hvnh_documents`
- Phạm vi: pipeline thật từ query → retrieval → LLM → citation → persistence; không ghi khóa API hoặc URL kết nối bí mật.

## Kết luận điều hành

Rule-based end-to-end đạt **29/31 (93,55%)**, không có lỗi hạ tầng. Retrieval đạt Hit@5 **1,000** và MRR **1,000** trên 6 ca. RAGAS cho thấy điểm mạnh là answer relevancy (0,885) và context precision (0,800); điểm cần ưu tiên là answer correctness (0,487), faithfulness (0,750) và context recall (0,774).

Hệ thống đã đủ tốt để demo và tiếp tục mở rộng dữ liệu có kiểm soát, nhưng chưa nên coi là đạt chuẩn production cuối cùng cho câu hỏi học vụ quan trọng. Ngưỡng cải tiến hợp lý cho vòng tới là ≥0,80 ở từng metric RAGAS, không chỉ điểm trung bình.

## 1. Benchmark end-to-end có gold label

| Chỉ số | Kết quả |
|---|---:|
| Gold case đã duyệt | 31 |
| Passed | 29 |
| Pass rate | 93,55% |
| Refusal decision accuracy | 93,55% |
| Citation/expected-source accuracy | 93,55% |
| Lỗi runtime | 0 |
| Latency mean | 5210.9 ms |
| Latency p50 | 4300.0 ms |
| Latency p95 | 5322 ms |
| Latency max | 39422 ms |

### Ca chưa đạt

| Case | Câu hỏi | Refusal | Citation | Keyword |
|---|---|---:|---:|---:|
| `hvnh-008` | Sinh viên K25 đã được trải nghiệm những gì trong chuyến tham quan FPT Software năm 2023? | Không đạt | Không đạt | Đạt |
| `hvnh-034` | Thông báo tuyển sinh khóa 2 chương trình Tiến sĩ PhD của UWE Bristol có nội dung gì? | Không đạt | Không đạt | Đạt |

Hai ca trên đều là từ chối nhầm trong khi kiểm tra keyword không phát hiện sai nội dung. Cần điều chỉnh ngưỡng đủ-context/guard để giảm false refusal mà không làm tăng hallucination.

## 2. Retrieval benchmark

| Chỉ số | Kết quả |
|---|---:|
| Số ca | 6 |
| Hit@5 | 1,000 |
| MRR | 1,000 |
| Correct-empty accuracy | 1,000 |

Tất cả truy vấn dương tìm đúng tài liệu ở hạng 1 và truy vấn âm trả rỗng đúng. Tuy nhiên tập 6 ca còn nhỏ, nên chưa chứng minh được độ ổn định trên mọi domain/tài liệu mới.

## 3. RAGAS

RAGAS 0.4.2 chấm **10/24** câu trả lời có reference (5 metric mỗi mẫu). Các refusal được đánh giá ở benchmark rule-based và bị loại khỏi tập RAGAS answer-quality.

| Metric | Trung bình | Min | Max |
|---|---:|---:|---:|
| Faithfulness | 0,750 | 0,333 | 1,000 |
| Answer relevancy | 0,885 | 0,781 | 0,985 |
| Answer correctness | 0,487 | 0,193 | 0,804 |
| Context precision | 0,800 | 0,000 | 1,000 |
| Context recall | 0,774 | 0,000 | 1,000 |

Diễn giải:

- Answer relevancy cao: câu trả lời nhìn chung bám câu hỏi.
- Context precision khá: phần lớn context đưa vào có ích, nhưng hai mẫu có precision bằng 0 cho thấy vẫn có retrieval/citation không khớp reference.
- Context recall 0,774: context chưa luôn bao phủ đủ thông tin trong reference.
- Faithfulness 0,750: một số mệnh đề trong câu trả lời chưa được context trích dẫn hỗ trợ đầy đủ dù URL citation đúng.
- Answer correctness 0,487 là điểm yếu chính: câu trả lời thường đúng hướng nhưng thiếu nhiều chi tiết so với reference hoặc reference hiện quá rộng so với câu hỏi.

## 4. Chất lượng kho tri thức

| Chỉ số | Kết quả |
|---|---:|
| Sources | 10 (9 enabled) |
| Documents | 350 |
| Versions | 541 |
| Chunks | 1577 |
| INDEXED / ARCHIVED | 346 / 195 |
| FAILED / quarantined | 0 / 0 |
| Indexed không có chunk | 0 |
| Thiếu academic_year | 305 (87,14%) |
| Thiếu published_at | 223 (63,71%) |
| Thiếu issuer | 0 |
| Source enabled quá hạn lịch crawl | 9/9 |
| Latest crawl PARTIAL | 5/9 |

Strict audit đạt vì không có version FAILED, quarantine hoặc indexed-version thiếu chunk. Một file danh sách sinh viên nợ học phí đã bị loại đúng bằng `PII_EXCLUDED`. Rủi ro vận hành còn lại là metadata thời gian thiếu nhiều và toàn bộ source enabled đang quá hạn lịch crawl; điều này ảnh hưởng trực tiếp câu hỏi “mới nhất” và truy vấn lịch sử.

## 5. Kiểm thử kỹ thuật

- Pytest: **103/103 test qua trong 10.20 giây**.
- Dependency eval: `pip check` không phát hiện xung đột.
- RAGAS chạy trong `.venv-eval` tách khỏi môi trường production.
- Benchmark cloud không có runtime error; một latency outlier cần được theo dõi bằng p95/p99 nhiều vòng.

## 6. Giới hạn phép đo

- Gold end-to-end gồm 31 ca và retrieval chỉ 6 ca; cần mở rộng theo từng intent, năm học, loại file và domain.
- RAGAS chỉ lấy 10 mẫu đầu trong 24 câu answerable do quota Gemini miễn phí 15 request/phút; đây không phải ước lượng toàn bộ tập.
- Gemini vừa sinh câu trả lời vừa làm judge nên có nguy cơ self-evaluation bias. Khi có ngân sách, nên dùng judge khác họ model (ví dụ DeepSeek/OpenAI) và chạy lặp ít nhất 3 seed.
- Reference answer có trường hợp dài/rộng hơn phạm vi câu hỏi, có thể kéo AnswerCorrectness xuống; cần chuẩn hóa reference thành câu trả lời tối thiểu nhưng đầy đủ.
- Đây là snapshot tại thời điểm đo; dữ liệu web và kết quả LLM có thể thay đổi ở lần chạy sau.

## 7. Thứ tự cải thiện đề xuất

1. Sửa hai false refusal và bổ sung regression case cho đúng intent tương ứng.
2. Chuẩn hóa reference answer, thêm claim-level citation verification và yêu cầu câu trả lời phủ các facts bắt buộc.
3. Backfill `published_at`/`academic_year`, xử lý các source PARTIAL và khôi phục scheduler đang overdue.
4. Mở rộng retrieval benchmark lên tối thiểu 50–100 câu phân tầng; RAGAS lên toàn bộ 24 mẫu rồi ≥100 mẫu.
5. Đo lặp latency và RAGAS bằng judge độc lập trước khi chốt SLA/production readiness.

## 8. Artifacts tái lập

- `evals/results/rag-benchmark.json`
- `evals/results/retrieval-benchmark.json`
- `evals/results/ragas-benchmark.json`
- `evals/results/knowledge-audit-benchmark.json`
- `evals/results/ragas-dataset.json`
