Giai đoạn 1 — Gemini LLM service
Mục tiêu: xác nhận ứng dụng gọi được Gemini ổn định mà chưa liên quan RAG.
Công việc:
- Cài google-genai.
- Hoàn thiện app/services/llm.py.
- Tạo provider abstraction để sau này đổi Gemini/OpenAI/local LLM.
- Timeout, retry cho 429 và 5xx.
- Không log prompt, API key hoặc dữ liệu nhạy cảm.
- Endpoint thử nghiệm nội bộ.
- Unit test bằng mock, không gọi Gemini trong mỗi lần pytest.
Tiêu chí hoàn thành:
FastAPI → Gemini → nhận câu trả lời
Giai đoạn 2 — Knowledge ingestion
Mục tiêu: đưa tài liệu chính thức vào PostgreSQL nhưng chưa embedding.
Nguồn đầu tiên chỉ nên gồm:
- Quy chế năm học 2025/2026.
- Thông báo mới của Học viện.
- FAQ hoặc hướng dẫn chính thức.
- PDF và URL được phép sử dụng.
Pipeline:
PDF/URL
→ tải nội dung
→ làm sạch
→ SHA-256
→ ai_documents
→ ai_document_versions
Cần triển khai:
- PDF loader.
- Website loader có giới hạn domain.
- Phát hiện tài liệu trùng bằng content_hash.
- Versioning khi nội dung thay đổi.
- Trạng thái PENDING/PROCESSING/INDEXED/FAILED.
- Lưu file gốc trên R2 nếu cần.
- Chưa crawl toàn bộ website tự động; bắt đầu bằng danh sách URL được duyệt.
Giai đoạn 3 — Chunking
Mục tiêu: biến tài liệu thành những đoạn có thể retrieval và citation.
Chunk cần giữ:
- document_version_id
- chunk_index
- content
- token_count
- page_start/page_end
- section_title
- heading_path
- content_hash
Không nên chỉ cắt cố định từng N ký tự. Với quy chế, cần ưu tiên ranh giới:
Chương → Mục → Điều → Khoản
Với thông báo:
Tiêu đề → ngày ban hành → nội dung → đơn vị phát hành
Giai đoạn 4 — Embedding và Qdrant indexing
Mục tiêu:
ai_document_chunks → embedding → Qdrant
Nếu giữ đúng đề cương:
- Model: BAAI/bge-m3
- Vector dimension: 1024
- Distance: Cosine
- Qdrant point ID: dùng chính ai_document_chunks.id
Payload Qdrant:
{
  "chunk_id": "...",
  "document_id": "...",
  "document_version_id": "...",
  "document_type": "REGULATION",
  "academic_year": "2025/2026",
  "published_at": "...",
  "is_current": true,
  "visibility": "PUBLIC",
  "group_id": null,
  "page_start": 12,
  "page_end": 13,
  "section_title": "Điều kiện tốt nghiệp"
}
Cần tạo payload index cho các trường thường filter:
- document_type
- academic_year
- is_current
- visibility
- group_id
- document_id
Một quyết định phải chốt: bge-m3 chạy ở đâu khi deploy. Model này tương đối nặng, khó chạy trên hosting miễn phí nhỏ. Giai đoạn phát triển có thể chạy local và đẩy vector lên Qdrant Cloud.
Giai đoạn 5 — Retrieval
Mục tiêu: tìm đúng chunk trước khi gọi Gemini.
Retrieval phải xử lý ba trường hợp:
1. Quy chế hiện hành
document_type = REGULATION
academic_year = 2025/2026
is_current = true
2. Thông báo mới
document_type = ANNOUNCEMENT
sort/filter theo published_at
3. Thông tin lịch sử
lọc đúng academic_year/thời điểm
không ép is_current = true
Cần có:
- Query normalization.
- Temporal filter.
- Access filter.
- Top-K retrieval.
- Score threshold.
- Optional reranking.
- Trả “không tìm thấy thông tin” nếu context không đủ.
Giai đoạn 6 — RAG answer và citation
Luồng hoàn chỉnh:
Câu hỏi
→ rewrite query
→ retrieval
→ context
→ Gemini
→ câu trả lời
→ citation
→ lưu PostgreSQL
Gemini phải được yêu cầu:
- Chỉ trả lời từ context.
- Không tự suy đoán quy chế.
- Nói rõ khi không đủ dữ liệu.
- Gắn citation dạng [1], [2].
- Không tự tạo URL hoặc số trang.
Citation phải được lưu vào ai_message_citations, không chỉ trả tạm cho frontend.
Giai đoạn 7 — Hội thoại nhiều lượt
Sau khi RAG một lượt chạy đúng mới thêm memory:
- Tạo ai_conversations.
- Lưu ai_messages theo sequence_number.
- Viết lại câu hỏi phụ thuộc ngữ cảnh.
- Chỉ gửi các lượt gần nhất.
- Tóm tắt lịch sử dài vào summary.
- Không dùng lịch sử hội thoại làm nguồn kiến thức thay cho tài liệu.
Ví dụ:
User: Điều kiện tốt nghiệp năm 2025/2026 là gì?
User: Còn chứng chỉ ngoại ngữ thì sao?
Câu thứ hai được viết lại thành:
Yêu cầu chứng chỉ ngoại ngữ để tốt nghiệp năm học 2025/2026 là gì?
Giai đoạn 8 — Đánh giá và triển khai
Tạo một bộ câu hỏi chuẩn, ví dụ:
- Quy chế đào tạo.
- Điều kiện tốt nghiệp.
- Học phí.
- Lịch thi.
- Thông báo mới.
- Câu hỏi lịch sử.
- Câu hỏi không có trong tài liệu.
- Câu hỏi nối tiếp nhiều lượt.
Đánh giá:
- Recall@K/MRR cho retrieval.
- Độ đúng câu trả lời.
- Faithfulness.
- Độ đúng citation.
- Tỷ lệ từ chối đúng khi thiếu nguồn.
- Latency.
- Gemini/Qdrant rate limit.
Sprint tiếp theo nên làm
Phạm vi hợp lý nhất cho vòng kế tiếp:
1. Gemini provider.
2. API schema cho chat.
3. PDF loader.
4. Ingestion một tài liệu thủ công.
5. Chunker có page/section metadata.
6. Unit test.
Chưa cần crawler diện rộng hoặc LangGraph. Sau sprint này, hệ thống phải đạt:
Một PDF chính thức
→ PostgreSQL document/version/chunks
→ chưa cần vector search
→ có thể kiểm tra đầy đủ dữ liệu đã ingest
Đây là nền tảng an toàn nhất trước khi đưa bge-m3 và Qdrant indexing vào.