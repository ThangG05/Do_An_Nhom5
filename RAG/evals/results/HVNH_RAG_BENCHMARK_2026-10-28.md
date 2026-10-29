# Báo cáo benchmark hệ thống HVNH RAG

**Ngày chạy:** 28/10/2026  
**Cấu hình:** Gemini `gemini-3.5-flash-lite`; Modal BGE-M3 (`BAAI/bge-m3`, 1.024 chiều); Qdrant collection `hvnh_documents`; RAGAS 0.4.2.

## Tóm tắt

| Phép đo | Kết quả |
|---|---:|
| End-to-end, gold đã duyệt | 27/30 đạt (90,00%) |
| Đúng nguồn trích dẫn kỳ vọng | 29/30 (96,67%) |
| Quyết định từ chối đúng | 29/30 (96,67%) |
| Required facts đạt | 27/30 (90,00%) |
| Retrieval Hit@5 | 54/55 truy vấn dương (98,18%) |
| Retrieval MRR | 0,912 |
| Truy vấn âm trả rỗng đúng | 5/5 (100%) |
| RAGAS answer correctness | 0,707 |
| RAGAS faithfulness | 0,942 |
| End-to-end latency trung bình / p50 / p95 / max | 4.076 / 3.622 / 8.527 / 8.916 ms |
| Lỗi runtime end-to-end | 0/30 |

**Nhận định:** Retrieval có độ bao phủ top-5 tốt trên tập kiểm thử, nhưng còn một truy vấn không tìm được tài liệu kỳ vọng. End-to-end chưa đạt toàn bộ gold: có một false refusal được tái hiện khi chạy lại và hai câu trả lời thiếu required facts. RAGAS cho điểm faithfulness/context cao, nhưng answer correctness 0,707 cho thấy độ đầy đủ/chính xác theo reference còn cần cải thiện. Chưa nên kết luận hệ thống đạt độ chính xác production chỉ từ các kết quả này.

## 1. End-to-end có nhãn tham chiếu

Đã chạy 30 case `APPROVED` qua pipeline hiện tại. Tiêu chí pass gồm refusal đúng, citation đúng nguồn kỳ vọng, keywords và độ phủ required facts.

| Chỉ số | Kết quả |
|---|---:|
| Số case | 30 |
| Pass | 27 (90,00%) |
| Citation/expected-source accuracy | 29/30 (96,67%) |
| Refusal decision accuracy | 29/30 (96,67%) |
| Keyword check | 30/30 (100%) |
| Required facts đạt | 27/30 (90,00%) |
| Runtime errors | 0 |
| Latency mean | 4.076 ms |
| Latency p50 | 3.622 ms |
| Latency p95 | 8.527 ms |
| Latency max | 8.916 ms |

Không có case-level runtime error. Khi Python đóng event loop sau benchmark, có xuất hiện cảnh báo cleanup `StreamWriter.__del__: RuntimeError: Event loop is closed`; cảnh báo này không làm mất artifact/kết quả nhưng nên xử lý riêng trước khi coi việc teardown là sạch hoàn toàn.

### Các case chưa đạt

| Case | Lỗi quan sát được | Ý nghĩa |
|---|---|---|
| `hvnh-011` | Đúng citation và keywords, nhưng fact coverage 0,5 | Câu trả lời nêu xác nhận nhập học và nơi xem hướng dẫn, nhưng thiếu thời điểm tra cứu kết quả cùng điều kiện/thông tin trong reference. |
| `hvnh-021` | False refusal; không có citation/context | Hệ thống trả “chưa thể tạo câu trả lời có trích dẫn hợp lệ” dù bộ gold có câu trả lời. Chạy lại riêng case này vẫn từ chối và có ba lần retry hợp đồng câu trả lời; lỗi được tái hiện, không chỉ là một lần ngẫu nhiên. |
| `hvnh-027` | Đúng citation và keywords, nhưng fact coverage 0,5 | Câu trả lời mô tả năm đầu học MIS nhưng bỏ ý người viết chọn MIS vì yêu công nghệ và không hối tiếc. |

## 2. Retrieval

Đã chạy 60 truy vấn phân tầng: 55 truy vấn dương và 5 truy vấn kỳ vọng không có kết quả.

| Metric | Kết quả |
|---|---:|
| Hit@5 | 54/55 = 0,982 |
| MRR | 0,912 |
| Correct-empty accuracy | 5/5 = 1,000 |

Case retrieval bị trượt là `strat-050-microsoft-word-quy-che-dao-tao-dhcd`: truy vấn yêu cầu tài liệu quy chế đào tạo được đặt tên theo `Microsoft Word - quy che dao tao dhcd26-6.doc`, nhưng top 5 trả về các tài liệu quy định khác. Cần xác minh alias/tên tài liệu kỳ vọng có được index trong kho hay không trước khi kết luận đây chỉ là lỗi xếp hạng.

Trong lần chạy có log cảnh báo nhánh lexical retrieval không khả dụng và chuyển sang vector results. Retrieval vẫn hoàn tất; cần theo dõi nhánh PostgreSQL lexical vì hybrid retrieval có thể mất lợi thế khi nhánh này lỗi.

## 3. RAGAS trên toàn bộ mẫu có reference

RAGAS 0.4.2 đã chấm **24/24** câu trả lời có reference và không phải refusal, với 5 metric mỗi mẫu.

| Metric | Trung bình | Min | Max |
|---|---:|---:|---:|
| Faithfulness | 0,942 | 0,000 | 1,000 |
| Answer relevancy | 0,866 | 0,604 | 0,992 |
| Answer correctness | 0,707 | 0,199 | 0,992 |
| Context precision | 0,974 | 0,500 | 1,000 |
| Context recall | 0,958 | 0,000 | 1,000 |

### Diễn giải và giới hạn

- Context precision/recall cao cho thấy context thường có nguồn đúng và bao phủ nội dung reference trong tập đã chọn; đây không phải bằng chứng rằng kho tri thức bao phủ mọi câu hỏi.
- Answer correctness thấp hơn faithfulness đáng kể. Một câu trả lời có thể được context hỗ trợ nhưng vẫn thiếu ý hoặc khác phạm vi của reference.
- `hvnh-013`, `hvnh-033` và `hvnh-041` có answer correctness thấp nhất (xấp xỉ 0,20–0,22). Một số reference có phạm vi hẹp hơn câu hỏi hoặc response; riêng `hvnh-041`, response nêu “khối ngành II” trong khi reference ghi “khối III”. Cần đối chiếu nguồn học phí chính thức để phân biệt lỗi trả lời với lỗi nhãn trước khi hiệu chỉnh model.
- `hvnh-006` có faithfulness/context recall bằng 0 nhưng answer correctness gần 0,992; sự lệch giữa các metric judge này cần được kiểm tra thủ công, không nên xem một metric riêng lẻ là chân lý.
- Judge dùng cùng provider/model Gemini với model sinh câu trả lời (`independent_from_answer_model=false`), nên có nguy cơ self-evaluation bias. Bộ số này phù hợp làm đánh giá nội bộ, chưa phải kiểm định độc lập.

## 4. Latency và Modal

Trước benchmark đã gọi smoke test `scripts.check_modal_embedding`: Modal app `hvnh_rag` trả thành công một vector BGE-M3 1.024 chiều. Cấu hình app hiện scale GPU về 0 khi rảnh và tự khởi động khi có request; benchmark không bật GPU thường trực.

Latency bên trên lấy từ `latency_ms` lưu bởi pipeline trên 30 request. Vì đây không phải phép đo nhiều tải đồng thời và không tách p95 cold-start khỏi warm-start, không dùng các số này làm SLA. Lượt benchmark retrieval ban đầu trước smoke test đã bị chờ ở embedding Modal; sau khi xác nhận Modal và cho phép kết nối cloud, lượt đo hoàn tất. Cần đo cold-start riêng nếu báo cáo yêu cầu đặc tính khởi động sau thời gian idle.

## 5. Giới hạn và kết luận sử dụng trong báo cáo

1. Bộ gold end-to-end có 30 câu; retrieval có 60 truy vấn. Đây là benchmark nội bộ có kiểm soát, chưa đại diện toàn bộ domain, học kỳ, loại tài liệu, câu hỏi đa lượt hoặc truy vấn đối kháng.
2. RAGAS là LLM-as-judge; có thể dao động theo model/prompt và cùng model sinh câu trả lời làm giảm tính độc lập.
3. Tham chiếu `reference_answer` có thể chưa cùng độ chi tiết hoặc chưa chuẩn hóa thuật ngữ với câu hỏi. Cần rà lại các case correctness thấp bằng người đánh giá và bằng nguồn gốc.
4. Latency không phải tải stress; chưa đo throughput, concurrent users, p99 ổn định, cold-start tách riêng hoặc resilience khi DB/Qdrant/Modal lỗi.
5. Có một cảnh báo fallback lexical trong lượt retrieval; nên kiểm tra PostgreSQL lexical trước khi phát biểu hybrid retrieval luôn hoạt động đầy đủ.
6. Kết quả 90% pass theo bộ rule-based không đồng nghĩa độ chính xác tổng quát 90%, và 100% metric nào trên mẫu nhỏ cũng không chứng minh hệ thống không hallucinate.

**Kết luận:** Với bộ kiểm thử hiện tại, RAG đạt mức tốt về tìm nguồn trong top-5 và độ bám context, nhưng còn lỗi false refusal có thể tái hiện, thiếu facts ở một số câu và answer correctness trung bình 0,707. Có thể trình bày đây là kết quả benchmark nội bộ cùng phạm vi/giới hạn nêu trên; chưa nên gọi là chứng nhận production-ready hay độ chính xác tuyệt đối.

## 6. Artifacts tái lập

- `evals/results/retrieval-benchmark-2026-10-28.json`
- `evals/results/rag-benchmark-2026-10-28.json`
- `evals/results/ragas-dataset-2026-10-28.json`
- `evals/results/ragas-benchmark-2026-10-28.json`
- `evals/results/recheck-hvnh-021-2026-10-28.json`
- Bộ nhãn: `evals/rag-gold.json`, `evals/retrieval-stratified.json`

Benchmark end-to-end ghi các conversation/message đánh dấu `evaluation` vào DB để có thể đối chiếu kết quả với lịch sử pipeline.
