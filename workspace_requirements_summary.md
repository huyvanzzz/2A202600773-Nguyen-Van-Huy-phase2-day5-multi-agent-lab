# Tóm tắt Yêu cầu và Công việc của Dự án (Lab Multi-Agent Research System)

Tài liệu này tóm tắt toàn bộ yêu cầu, kiến trúc hệ thống và danh sách công việc cần làm (**TODOs**) được tổng hợp từ các file tài liệu định dạng `.md` trong repo.

---

## 🎯 Mục tiêu Dự án
Xây dựng một hệ thống nghiên cứu tự động (**Research Assistant**) có khả năng nhận câu hỏi dài, tìm kiếm thông tin, phân tích và đưa ra câu trả lời cuối cùng có trích dẫn nguồn.
Dự án yêu cầu so sánh (benchmark) hai cách tiếp cận:
1. **Single-agent baseline:** Một agent duy nhất thực hiện toàn bộ tác vụ.
2. **Multi-agent workflow:** Hệ thống phân vai điều phối gồm **Supervisor** điều phối các worker agents (**Researcher**, **Analyst**, **Writer** và tùy chọn **Critic**).

---

## 🏗️ Kiến trúc Hệ thống

```text
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes + sources
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

---

## 📋 Danh sách Công việc Cần làm (TODOs)

Dưới đây là chi tiết các phần việc cần tự triển khai được đánh dấu bằng `TODO(student)` trong mã nguồn:

### 1. Dịch vụ Cơ sở (Services)
*   **LLM Client** ([llm_client.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/services/llm_client.py)):
    *   Kết nối với OpenAI, Azure OpenAI hoặc nhà cung cấp khác.
    *   Tích hợp các cơ chế xử lý lỗi (retry, timeout) và thu thập thông tin token sử dụng.
*   **Search Client** ([search_client.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/services/search_client.py)):
    *   Hiện thực hóa phương thức tìm kiếm tài liệu từ API thật (Tavily, Bing, SerpAPI...) hoặc nguồn dữ liệu giả lập (mock).

### 2. Single-Agent Baseline
*   **Baseline Client** ([cli.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/cli.py)):
    *   Thay thế placeholder hiện tại bằng cuộc gọi LLM thật để thực hiện truy vấn trực tiếp và ghi lại kết quả (latency, cost, quality) làm dữ liệu so sánh cơ sở.

### 3. Hệ thống Multi-Agent & Định tuyến
*   **SupervisorAgent** ([supervisor.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/agents/supervisor.py)):
    *   Kiểm tra yêu cầu, ghi chú hiện có và xác định thông tin còn thiếu.
    *   Lựa chọn agent tiếp theo sẽ thực thi (`researcher`, `analyst`, `writer`, `done`).
    *   Áp dụng các cơ chế kiểm soát: số vòng lặp tối đa (`max_iterations`) và phương án dự phòng khi gặp lỗi (`fallback`).
*   **ResearcherAgent** ([researcher.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/agents/researcher.py)):
    *   Thực hiện tìm kiếm, lọc các nguồn tài liệu, lưu thông tin trích dẫn (`state.sources`) và ghi chú nghiên cứu (`state.research_notes`).
*   **AnalystAgent** ([analyst.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/agents/analyst.py)):
    *   Đọc và chuyển đổi ghi chú nghiên cứu thành các thông tin phân tích chuyên sâu (`state.analysis_notes`).
    *   So sánh các quan điểm khác nhau và đánh giá mức độ tin cậy của thông tin tìm được.
*   **WriterAgent** ([writer.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/agents/writer.py)):
    *   Tổng hợp thông tin từ ghi chú nghiên cứu và ghi chú phân tích để tạo câu trả lời cuối cùng (`state.final_answer`), đảm bảo định dạng chuyên nghiệp có nguồn trích dẫn cụ thể.
*   **CriticAgent (Tùy chọn)** ([critic.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/agents/critic.py)):
    *   Đánh giá chéo kết quả để tránh hiện tượng ảo giác (hallucination) hoặc kiểm tra độ phủ trích dẫn trước khi trả về người dùng.

### 4. Thiết lập Luồng Công việc (LangGraph Workflow)
*   **Workflow Design** ([workflow.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/graph/workflow.py)):
    *   Xây dựng các node, cạnh nối (edges), logic định tuyến có điều kiện (conditional routing) và điều kiện dừng đồ thị.
    *   Biên dịch và chạy luồng dữ liệu, cập nhật kết quả trả về đúng định dạng của `ResearchState`.

### 5. Giám sát & Đánh giá (Observability & Benchmarking)
*   **Observability** ([tracing.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/observability/tracing.py)):
    *   Tích hợp nền tảng trace chuyên dụng như LangSmith, Langfuse hoặc OpenTelemetry để giám sát chi tiết hành động và thời gian của từng agent.
*   **Evaluation & Benchmark** ([benchmark.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/evaluation/benchmark.py)):
    *   Đo lường thời gian chạy, ước lượng chi phí token, chất lượng phản hồi (quality score), tỉ lệ lỗi và lưu lại kết quả benchmark.
*   **Report Generation** ([report.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/evaluation/report.py)):
    *   Render kết quả so sánh thành báo cáo Markdown hoàn chỉnh, có phân tích ưu nhược điểm của từng phương pháp.

---

## 🛠️ Quy chuẩn Kỹ thuật
*   **Stateful Design:** Đảm bảo `Shared State` ([state.py](file:///d:/Vin/2A202600773-Nguyen-Van-Huy-phase2-day5-multi-agent-lab/src/multi_agent_research_lab/core/state.py)) có đủ thông tin để handoff (chuyển giao giữa các agent) mà không mất context.
*   **Guardrails:** Bắt buộc thiết lập `max_iterations` (mặc định: 6) và `timeout_seconds` (mặc định: 60s) để tránh vòng lặp vô hạn gây tốn chi phí.
*   **Environment Validation:** Không hardcode API key. Sử dụng tệp `.env` cấu hình các biến như `OPENAI_API_KEY`, `TAVILY_API_KEY`, và `LANGSMITH_API_KEY`.

---

## 📦 Sản phẩm Bàn giao
1.  **Mã nguồn trên kho chứa cá nhân (GitHub)** đã hoàn thiện đầy đủ các TODOs.
2.  **Screenshot/Link trace** luồng thực thi thành công từ LangSmith/Langfuse.
3.  Tệp báo cáo **`reports/benchmark_report.md`** so sánh chi tiết hiệu năng và chất lượng giữa Single-Agent và Multi-Agent.
4.  Đoạn giải thích về các **Failure Modes** gặp phải và chiến lược xử lý.
Trong report phải lồng cả single agent và multi-agent để có thể compare dễ hơn.
Submit 1 file có cái trace chi tiết bằng html.
Show cả prompt dùng.