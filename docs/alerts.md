# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: high_latency_p95
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack (#ai-alerts)
- SLI/SLO liên quan: Primary SLO - fast_successful_requests (Latency P95 <= 2000ms)
- Điều kiện và thời gian duy trì: `p95_latency_ms > 2000` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng chờ phản hồi câu trả lời lâu hơn bình thường, trải nghiệm chat bị gián đoạn.
- Ba bước kiểm tra đầu tiên:
  1. **Kiểm tra Dashboard**: Xác định thời điểm bắt đầu trễ và xem phân rã latency (TTFT vs generation latency).
  2. **Lọc Log**: Mở `data/logs.jsonl`, lọc các sự kiện `response_sent` có `latency_ms > 2000` để lấy `correlation_id` cụ thể.
  3. **Kiểm tra Trace**: Vào Langfuse tìm trace có cùng `correlation_id`, xem waterfall span để xác định bước chậm là do `retrieve` (vector search) hay `FakeLLM.generate`.
- Mitigation tạm thời:
  - Nếu bước `retrieve` chậm: kích hoạt cache tài liệu hoặc chuyển sang fallback keyword search.
  - Nếu LLM model chậm: chuyển routing sang model dự phòng hoặc scale-out instance.
- Owner: platform-team

---

## Alert 2

- Tên: high_error_rate
- Severity: critical
- Duration: 3m
- Kênh thông báo: Slack (#ai-critical-incidents)
- SLI/SLO liên quan: Guardrail - Error Rate <= 2.0%
- Điều kiện và thời gian duy trì: `error_rate_pct > 2.0` liên tục trong 3 phút
- Ảnh hưởng tới người dùng: Người dùng nhận mã lỗi HTTP 500 hoặc thông báo hệ thống không thể xử lý yêu cầu.
- Ba bước kiểm tra đầu tiên:
  1. **Kiểm tra Dashboard**: Quan sát panel Errors để phân loại nhóm lỗi chính (`error_type`).
  2. **Lọc Log**: Lọc các dòng log `request_failed` trong `data/logs.jsonl` để trích xuất `correlation_id` và stacktrace (`payload.detail`).
  3. **Kiểm tra Trace**: Mở Langfuse trace tương ứng để xem span nào ném ra Exception.
- Mitigation tạm thời:
  - Bật chế độ degraded/safe-mode trả về câu trả lời mặc định nếu service phụ thuộc bị sập.
  - Khởi động lại service hoặc rollback phiên bản release gần nhất nếu phát hiện bug mới triển khai.
- Owner: ai-ops-team

---

## Alert 3

- Tên: retrieval_failure_spike
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack (#rag-engineers)
- SLI/SLO liên quan: Guardrail - Retrieval Success Rate >= 90.0%
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90.0` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Agent không truy xuất được tài liệu kiến thức chuyên ngành, dẫn đến câu trả lời thiếu chính xác hoặc bị từ chối trả lời.
- Ba bước kiểm tra đầu tiên:
  1. **Kiểm tra Dashboard**: Xem panel Errors/Retrieval xem tỉ lệ `tool_success == false` bắt đầu tăng từ lúc nào.
  2. **Lọc Log**: Tìm các log có `tool_name == "retrieval"` và `tool_success == false` để lấy mã lỗi (`RuntimeError: Vector store timeout`).
  3. **Kiểm tra Trace**: Mở trace trên Langfuse, kiểm tra span `retrieve` xem kết nối mạng hoặc database vector có bị timeout không.
- Mitigation tạm thời:
  - Tự động chuyển truy vấn sang domain corpus dự phòng hoặc cơ chế full-text search.
  - Tăng timeout tạm thời hoặc restart vector store pod.
- Owner: rag-ops-team
