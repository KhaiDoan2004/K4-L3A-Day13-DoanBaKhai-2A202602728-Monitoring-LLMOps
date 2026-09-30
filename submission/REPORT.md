# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đoàn Bá Khải
- **MSSV:** 2A202602728
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/KhaiDoan2004/K4-L3A-Day13-DoanBaKhai-2A202602728-Monitoring-LLMOps.git
- **Commit SHA cuối:** `46f152600f86785a14219550ba0edd5315b3cfcb`
- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602728`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.txt` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.txt` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt 100/100, đầy đủ required fields, correlation_id, enrichment và PII scrubbing |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Đạt cấu trúc contract 6/6 panel |
| `pytest` | 22 passed | 24 passed | Bổ sung 2 bài test PII cho CCCD và thẻ ngân hàng |
| Số traces hợp lệ | 0 | 27 | Đạt yêu cầu (tối thiểu 10 traces, thực tế tạo 27 traces tương ứng 27 correlation IDs) |
| Số PII leak | 0 | 0 | Đã kích hoạt PII scrubber đệ quy và kiểm chứng không rò rỉ |
| Latency P95 / TTFT P95 | ~159ms / N/A | ~151ms / 50ms (baseline) | Baseline đáp ứng tốt SLO <= 2000ms; trong challenge P95 tăng lên 2652ms do incident |
| Retrieval success rate | 100% | 100% | Toàn bộ 100% request thực hiện truy xuất thành công |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware`, trước mỗi request gọi `clear_contextvars()` để tránh rò rỉ context. Kiểm tra header `x-request-id`, nếu có thì nhận, nếu thiếu thì tự sinh theo format `req-<8-hex>` (`f"req-{uuid.uuid4().hex[:8]}"`). Sau đó gọi `bind_contextvars(correlation_id=correlation_id)` và gán `request.state.correlation_id`. Khi trả về response, gắn header `x-request-id` và `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Tại endpoint `/chat`, gọi `bind_contextvars` bổ sung ngay các trường: `user_id_hash` (băm sha256 12 ký tự), `session_id`, `feature`, `model` (model của agent), và `env` (APP_ENV).
- **Cách bảo đảm PII được scrub trước khi ghi:** Xây dựng hàm `_scrub_value` duyệt đệ quy (hỗ trợ dict, list, str) và áp dụng các regex trong `app/pii.py` (email, phone_vn, cccd 12 số, credit card) để thay thế bằng `[REDACTED_<TYPE>]`. Hàm `scrub_event` được đặt trong chuỗi processors của structlog ngay trước `JsonlFileProcessor` và `JSONRenderer`, bảo đảm dữ liệu được tẩy sạch trước khi render JSON và ghi xuống `data/logs.jsonl`.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt điểm tuyệt đối 100/100 (đủ required fields, 10 correlation IDs duy nhất, đủ enrichment fields, 0 PII leak). Bộ unit test `tests/test_pii.py` pass 100% (4/4 tests).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Project trên Langfuse Cloud mang tên `day13-k4-l3a-2A202602728`, sử dụng key pair cá nhân được cấu hình trong `.env`. Mọi trace đều mang environment `dev`, tags `["lab", feature, model]` và metadata khớp với các phiên load test từ máy cá nhân.
- **Cấu trúc root/retrieval/generation observations:**
  - Root observation: `lab-agent-run` (type: `agent`) bao bọc toàn bộ chu trình xử lý request.
  - Child 1: `retrieve` (type: `retriever`) thực hiện tìm kiếm tài liệu trong corpus, ghi nhận metadata `doc_count` và preview truy vấn đã redact PII.
  - Child 2: `FakeLLM.generate` (type: `generation`) thực hiện sinh câu trả lời, ghi nhận `model`, `prompt`, `usage_details` (input, output, total tokens), `cost_details` (total USD) và câu trả lời tóm tắt.
- **Cách nối trace với log:** Ghi nhận `correlation_id` vào trường `metadata.correlation_id` của trace (thông qua `propagate_attributes`). Nhờ đó, từ một dòng log trong `data/logs.jsonl` có thể lấy `correlation_id` tra cứu trực tiếp ra trace trên Langfuse.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1, labels `["baseline", "production"]`. Template: `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}`
- **Version/label candidate:** Version 2, labels `["candidate"]`. Template có thêm hướng dẫn: `Instruction: Provide an accurate, concise answer under 3 sentences.`
- **Trace ID của mỗi version:** Được ghi nhận khi chạy test với từng nhãn prompt tương ứng.
- **Cách promote và rollback `production`:**
  - Promote: Trên Langfuse Cloud (hoặc script `setup_prompts.py`), gán label `production` cho Version 2 (`candidate`).
  - Rollback: Khi phát hiện hồi quy chất lượng hoặc sự cố, gán lại label `production` về Version 1. App tự động nhận version mới theo label `production` sau khi hết TTL cache (60s).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Xây dựng đầy đủ 6 panels theo đúng contract `config/dashboard.yaml`:
  1. *Latency*: P50, P95, P99 và TTFT P95 (đơn vị: ms, threshold P95 $\le$ 2000ms).
  2. *Traffic*: Số lượng request xử lý theo cửa sổ 60 phút.
  3. *Errors*: Tỷ lệ lỗi (error rate $\le$ 2.0%) và tỷ lệ thành công của retrieval ($\ge$ 90.0%).
  4. *Cost*: Chi phí tích lũy theo USD (tỷ lệ $3/M input, $15/M output, ngưỡng $\le$ $2.50/ngày).
  5. *Tokens*: Tổng token in và token out.
  6. *Quality*: Điểm đánh giá chất lượng trung bình theo heuristic (ngưỡng $\ge$ 0.75 / 1.0).
- **SLO và lý do chọn:** Primary SLO: `fast_successful_requests` với mục tiêu 99.5% request thành công và có `latency_ms <= 2000` trên cửa sổ 28 ngày. Ngưỡng 2000ms được chọn dựa trên baseline P95 đo được (~151ms–160ms), cho phép độ trễ dự phòng hợp lý khi có truy vấn phức tạp hoặc mạng chậm mà vẫn đảm bảo tính phản hồi nhanh cho người dùng.
- **Cách tính error budget:** Error budget = $100\% - 99.5\% = 0.5\%$. Trong khoảng thời gian 28 ngày, hệ thống chỉ được phép có tối đa 0.5% tổng số request bị lỗi (HTTP 500) hoặc có độ trễ vượt quá 2000ms.
- **Ba alert và runbook tương ứng:** Cấu hình trong `config/alert_rules.yaml` và `docs/alerts.md`:
  1. `high_latency_p95`: Cảnh báo khi P95 latency > 2000ms kéo dài 5 phút (Warning, Slack, platform-team).
  2. `high_error_rate`: Báo động khi Error rate > 2.0% kéo dài 3 phút (Critical, Slack, ai-ops-team).
  3. `retrieval_failure_spike`: Báo động khi Retrieval success rate < 90.0% kéo dài 5 phút (Critical, Slack, rag-ops-team).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29 09:10:00 UTC – 2026-09-29 09:12:30 UTC
- **Triệu chứng từ metrics:** Trên Dashboard (Panel 1: Latency), độ trễ P95 tăng vọt từ baseline ~151ms lên **2652.0 ms** và P99 đạt **3638.5 ms**, vi phạm nghiêm trọng Primary SLO `fast_successful_requests` (ngưỡng quy định $\le$ 2000ms). Trong khi đó, Error rate vẫn 0% và Retrieval success rate vẫn 100%, cho thấy hệ thống không bị lỗi crash mà bị nghẽn độ trễ nghiêm trọng.
- **Log line và correlation ID liên quan:**
  - Correlation ID: `req-508f6a5f`
  - Dòng log `response_sent`:
    ```json
    {"service": "api", "latency_ms": 2652, "ttft_ms": 50, "tokens_in": 35, "tokens_out": 101, "cost_usd": 0.00162, "quality_score": 0.8, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "user_id_hash": "dc9b2ec8da9d", "env": "dev", "model": "claude-sonnet-4-5", "session_id": "k4-l3a-challenge-s03", "feature": "monitoring", "correlation_id": "req-508f6a5f", "level": "info", "ts": "2026-09-29T09:11:17.658460Z"}
    ```
- **Trace ID và span gây ảnh hưởng:**
  - Tìm kiếm trên Langfuse Cloud theo `correlation_id: req-508f6a5f`.
  - Phân rã thời gian waterfall: Root `lab-agent-run` mất 2652 ms, trong đó span `retrieve` (retriever) tiêu tốn **~2500 ms** (chiếm 94.3% toàn bộ thời gian), còn span `FakeLLM.generate` chỉ mất **152 ms** (TTFT: 50 ms).
  - Kết luận: Span gây ảnh hưởng trực tiếp là **`retrieve`**.
- **Root cause:** Bước truy xuất tài liệu `retrieve` bị nghẽn độ trễ (mô phỏng tình huống vector database bị quá tải hoặc mạng chập chờn gây trễ ~2.5s mỗi request), khiến tổng độ trễ vượt xa ngưỡng SLO 2000ms.
- **Fix action:** Tức thời: Kích hoạt cache cho các truy vấn retrieval thường gặp, tạm thời định tuyến sang tìm kiếm keyword search fallback nếu vector store bị suy giảm hiệu năng; mở rộng tài nguyên tính toán cho vector database pod.
- **Preventive measure:**
  1. Thiết lập Circuit Breaker và giới hạn timeout tối đa cho bước retrieval (ví dụ 1000ms) để fail-safe chuyển sang fallback docs thay vì để treo request.
  2. Đặt alert sớm cho span: cảnh báo khi `retrieval_latency_p95 > 1000ms` kéo dài trên 2 phút.
  3. Đánh index lại vector store và thực hiện load testing định kỳ.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Quyết định thực hiện PII scrubbing đệ quy (`_scrub_value`) trên toàn bộ cây dữ liệu (dict, list, str) của structlog event_dict ngay trước bước render JSON và ghi file. Lý do: đảm bảo tuyệt đối không có dữ liệu nhạy cảm (email, sđt, cccd, thẻ) nào lọt vào log file hoặc terminal, bảo vệ an toàn thông tin người dùng theo quy định GDPR/chính sách bảo mật mà không phụ thuộc vào việc lập trình viên có nhớ scrub thủ công ở từng hàm hay không.
- **Một lỗi/blocker đã gặp:** Gặp lỗi mã hóa ký tự `UnicodeEncodeError: 'charmap' codec can't encode character` khi chạy script in tiếng Việt trên console Windows (do encoding mặc định là cp1252).
- **Cách tìm nguyên nhân và xử lý:** Nhận diện traceback từ thư viện `codecs.charmap_encode` trên Windows; xử lý bằng cách cấu hình `$env:PYTHONIOENCODING="utf-8"` trong PowerShell và tích hợp `app.cli.configure_utf8_stdio()` vào đầu các script thực thi.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - *Metrics* là bảng đồng hồ báo động tổng thể, cho biết **"hệ thống đang gặp vấn đề gì và bắt đầu từ khi nào"** (ví dụ: Latency P95 tăng vọt lúc 09:11).
  - *Logs* là nhật ký chi tiết có cấu trúc, giúp tìm ra **"request cụ thể nào bị ảnh hưởng"** bằng cách lọc theo ngưỡng độ trễ và lấy mã định danh duy nhất `correlation_id`.
  - *Traces* là kính hiển vi phân rã từng bước thực thi, dựa vào `correlation_id` để mở cây span và chỉ ra chính xác **"bước nào/thành phần nào là nguyên nhân gốc rễ"** (bước `retrieve` chậm 2.5s chứ không phải do LLM).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - *Prompt version & Rollback*: Prompt đóng vai trò như mã nguồn trong LLMOps; việc versioning và gắn nhãn (baseline, candidate, production) cho phép thử nghiệm an toàn và khôi phục (rollback) ngay lập tức về phiên bản ổn định nếu prompt mới gây ảo giác, tăng chi phí hoặc suy giảm chất lượng.
  - *Token & Cost*: Chi phí LLM tăng tuyến tính theo số lượng token; theo dõi sát sao giúp phát hiện prompt injection, vòng lặp vô tận hoặc incident token spike.
  - *SLO & Error Budget*: Là cam kết chất lượng dịch vụ với người dùng và ranh giới định lượng giữa độ tin cậy và tốc độ phát triển tính năng mới.
  - **Điều quan trọng nhất đã học:** Nắm vững trọn vẹn quy trình Observability thực chiến cho hệ sinh thái GenAI/LLM, từ việc chuẩn hóa log JSON, bảo vệ PII, truy vết phân tán bằng OpenTelemetry/Langfuse, cho đến tư duy điều tra sự cố bài bản từ vĩ mô (Metrics) xuống vi mô (Traces).
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Các kiểm thử hiện tại chủ yếu chạy trên mô hình fake LLM và dữ liệu mẫu cục bộ; trong môi trường sản xuất thực tế cần tích hợp LLM thật (như OpenAI, Anthropic, Gemini) với streaming responses và giám sát cả độ trễ First Chunk (TTFT) thực tế qua mạng.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
