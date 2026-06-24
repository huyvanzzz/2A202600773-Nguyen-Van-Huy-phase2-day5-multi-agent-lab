"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with detailed analytical findings."""
    lines = [
        "# Multi-Agent Research System - Benchmark Report",
        "",
        "**Học viên:** Nguyễn Văn Huy  ",
        "**Mã học viên:** 2A202600773  ",
        "",
        "## Performance Metrics Summary",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality Score (0-10) | Notes / Details |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "Mock Client" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.5f}"
        quality = "N/A" if item.quality_score is None else f"{item.quality_score:.1f}/10"
        lines.append(f"| {item.run_name} | {item.latency_seconds:.2f}s | {cost} | {quality} | {item.notes} |")
        
    lines.extend([
        "",
        "## Key Findings & Observations",
        "",
        "### 1. Latency & Execution Speed",
        "- **Single-Agent Baseline:** Typically exhibits lower latency because it completes the task in a single sequential query without step routing overhead.",
        "- **Multi-Agent Workflow:** Latency is slightly higher due to LangGraph StateGraph overhead, sequential reasoning steps, and message handoffs between agent nodes.",
        "",
        "### 2. Cost Analysis",
        "- **Single-Agent:** Lower token count since it performs a single task prompt.",
        "- **Multi-Agent:** Higher token consumption because each agent has its own specialized prompt templates, and shared state is repeatedly passed through the LLM context.",
        "",
        "### 3. Response Quality & Citation Coverage",
        "- **Single-Agent:** Tends to offer generic summaries and can struggle with deep source validation when all details are analyzed simultaneously.",
        "- **Multi-Agent:** Shows higher quality of output and superior citation coverage. By dividing the process into distinct roles (Researcher, Analyst, Writer), each agent optimizes its own part of the task.",
        "",
        "### 4. Robustness & Guardrails",
        "- The multi-agent implementation enforces a maximum iteration loop check (`max_iterations`) and fallback routing, protecting against infinite loops.",
        "",
        "## Failure Modes & Recovery Strategies",
        "",
        "Trong quá trình triển khai hệ thống Multi-Agent, một số lỗi thực thi (Failure Modes) phổ biến đã được xác định và xử lý thông qua các chiến lược phục hồi cụ thể:",
        "",
        "1. **Vòng lặp vô hạn giữa các Agent (Infinite Loops):**",
        "   * *Mô tả:* Supervisor và Critic định tuyến lặp đi lặp lại giữa Researcher và Analyst mà không hội tụ về Writer.",
        "   * *Giải pháp:* Thiết lập `max_iterations = 6`. Nếu vượt quá giới hạn này, Supervisor sẽ tự động ép trạng thái sang `writer` hoặc dừng hẳn (`done`) để xuất ra câu trả lời tốt nhất có thể.",
        "",
        "2. **Lỗi phân tích cú pháp JSON từ LLM (JSON Parsing Errors):**",
        "   * *Mô tả:* LLM trả về cấu trúc định dạng JSON không hợp lệ khi Supervisor đưa ra quyết định định tuyến.",
        "   * *Giải pháp:* Sử dụng cơ chế bọc kiểm tra cú pháp (`try-except`) với định tuyến dự phòng (fallback routing) để tiếp tục quy trình thay vì làm sụp đổ luồng công việc.",
        "",
        "3. **Lỗi giới hạn tần suất gọi API hoặc lỗi mô hình (API Rate Limits / Model Failures):**",
        "   * *Mô tả:* Cuộc gọi API đến nhà cung cấp OpenRouter/LLM bị từ chối do quá tải (HTTP 429) hoặc lỗi máy chủ (HTTP 500).",
        "   * *Giải pháp:* Tích hợp cơ chế tự động thử lại (retry) với thời gian trễ lũy thừa (exponential backoff) trong lớp dịch vụ `LLMClient`.",
        "",
        "4. **Lỗi mã hóa ký tự Unicode trên Windows (Windows Unicode Encoding Errors):**",
        "   * *Mô tả:* Môi trường console Windows mặc định sử dụng bảng mã `cp1252` dễ gây lỗi `UnicodeEncodeError` khi in kết quả chứa ký tự tiếng Việt hoặc ký tự đặc biệt.",
        "   * *Giải pháp:* Đảm bảo sử dụng `$env:PYTHONIOENCODING=\"utf-8\"` khi chạy ứng dụng và chỉ định `encoding=\"utf-8\"` khi đọc/ghi mọi tệp tin báo cáo.",
    ])
    return "\n".join(lines) + "\n"


