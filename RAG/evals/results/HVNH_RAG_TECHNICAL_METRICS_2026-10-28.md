# HVNH RAG — Bảng thông số kỹ thuật benchmark

| Nhóm | Thông số | Giá trị |
|---|---|---:|
| Thời điểm | Ngày benchmark | 28/10/2026 |
| LLM | Provider | Gemini |
| LLM | Model sinh câu trả lời | `gemini-3.5-flash-lite` |
| LLM judge | Provider / model | Gemini / `gemini-3.5-flash-lite` |
| LLM judge | Độc lập với model sinh | Không |
| Embedding | Provider | Modal |
| Embedding | Model | `BAAI/bge-m3` |
| Embedding | Vector dimension | 1.024 |
| GPU embedding | Modal class | `hvnh_rag/BgeM3` |
| GPU embedding | GPU | NVIDIA T4 |
| GPU embedding | Min containers | 0 |
| Vector database | Engine | Qdrant |
| Vector database | Collection | `hvnh_documents` |
| Persistence / retrieval | Database | PostgreSQL (Neon) |
| End-to-end | Gold cases đã duyệt | 30 |
| End-to-end | Pass | 27/30 (90,00%) |
| End-to-end | Expected citation accuracy | 29/30 (96,67%) |
| End-to-end | Refusal decision accuracy | 29/30 (96,67%) |
| End-to-end | Keyword check pass | 30/30 (100%) |
| End-to-end | Required facts pass | 27/30 (90,00%) |
| End-to-end | Runtime errors | 0/30 |
| End-to-end latency | Mean | 4.076 ms |
| End-to-end latency | p50 | 3.622 ms |
| End-to-end latency | p95 | 8.527 ms |
| End-to-end latency | Maximum | 8.916 ms |
| Retrieval | Tổng số truy vấn | 60 |
| Retrieval | Truy vấn dương | 55 |
| Retrieval | Truy vấn âm | 5 |
| Retrieval | Hit@5 | 54/55 (98,18%) |
| Retrieval | MRR | 0,912 |
| Retrieval | Correct-empty accuracy | 5/5 (100%) |
| RAGAS | Version | 0.4.2 |
| RAGAS | Scored answerable samples | 24/24 |
| RAGAS | Faithfulness | 0,942 |
| RAGAS | Answer relevancy | 0,866 |
| RAGAS | Answer correctness | 0,707 |
| RAGAS | Context precision | 0,974 |
| RAGAS | Context recall | 0,958 |
| RAGAS | Faithfulness range | 0,000–1,000 |
| RAGAS | Answer relevancy range | 0,604–0,992 |
| RAGAS | Answer correctness range | 0,199–0,992 |
| RAGAS | Context precision range | 0,500–1,000 |
| RAGAS | Context recall range | 0,000–1,000 |
| Repeat check | `hvnh-021` false refusal reproduced | Có; 2/2 lần |
| Retrieval miss | Failed positive query | 1/55 |
| Runtime observation | PostgreSQL lexical retrieval fallback warning | Có; vector retrieval tiếp tục |
| Runtime observation | Python async stream cleanup warning at process shutdown | Có; không làm mất benchmark artifact |

## Artifact benchmark

| Artifact | Đường dẫn |
|---|---|
| Retrieval result | `evals/results/retrieval-benchmark-2026-10-28.json` |
| End-to-end result | `evals/results/rag-benchmark-2026-10-28.json` |
| RAGAS dataset | `evals/results/ragas-dataset-2026-10-28.json` |
| RAGAS result | `evals/results/ragas-benchmark-2026-10-28.json` |
| Recheck `hvnh-021` | `evals/results/recheck-hvnh-021-2026-10-28.json` |
| Gold dataset | `evals/rag-gold.json` |
| Retrieval dataset | `evals/retrieval-stratified.json` |

## Định nghĩa metric

| Metric | Định nghĩa sử dụng trong benchmark |
|---|---|
| Hit@5 | Tỷ lệ truy vấn dương có tài liệu kỳ vọng xuất hiện trong 5 kết quả đầu |
| MRR | Trung bình nghịch đảo thứ hạng của tài liệu liên quan trên truy vấn dương |
| Correct-empty accuracy | Tỷ lệ truy vấn được gán `expected_empty` mà retrieval trả về rỗng |
| Expected citation accuracy | Tỷ lệ case có citation khớp URL hoặc tiêu đề nguồn kỳ vọng |
| Refusal decision accuracy | Tỷ lệ quyết định từ chối khớp `expected_refused` |
| Faithfulness | Mức độ các khẳng định trong câu trả lời được context hỗ trợ |
| Answer relevancy | Mức độ câu trả lời phù hợp với câu hỏi |
| Answer correctness | Mức độ câu trả lời tương đồng/chính xác so với reference |
| Context precision | Tỷ lệ context được truy xuất có liên quan tới reference |
| Context recall | Mức độ context bao phủ thông tin trong reference |
