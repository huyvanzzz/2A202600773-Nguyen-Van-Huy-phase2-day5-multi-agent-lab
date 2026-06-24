"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton.

    TODO(student): Replace or augment with LangSmith/Langfuse provider spans.
    """

    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started


def save_html_trace(state: Any, filepath: str) -> None:
    """Generate a highly stylized premium light-mode HTML trace of the execution graph and prompt logs."""
    import html
    import re
    from pathlib import Path

    # Helper function to format markdown in cells
    def format_cell(text: str) -> str:
        escaped = html.escape(text)
        # Bold: **text**
        escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
        # Italic: *text*
        escaped = re.sub(r'\*(.*?)\*', r'<em>\1</em>', escaped)
        # Handle some custom badges
        escaped = escaped.replace("Single-Agent", '<span class="badge-type single">Single-Agent</span>')
        escaped = escaped.replace("Multi-Agent", '<span class="badge-type multi">Multi-Agent</span>')
        return escaped

    # Extract benchmark tables from reports/benchmark_report.md
    benchmark_tables_html = ""
    benchmark_path = Path("reports/benchmark_report.md")
    if benchmark_path.exists():
        try:
            with open(benchmark_path, "r", encoding="utf-8") as f:
                bm_content = f.read()
            
            lines = bm_content.splitlines()
            current_table = []
            tables = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("|"):
                    current_table.append(stripped)
                else:
                    if current_table:
                        tables.append(current_table)
                        current_table = []
            if current_table:
                tables.append(current_table)
                
            for idx_table, t_lines in enumerate(tables):
                if len(t_lines) >= 2:
                    headers = [c.strip() for c in t_lines[0].split("|")[1:-1]]
                    rows = []
                    for r in t_lines[2:]:
                        cells = [c.strip() for c in r.split("|")[1:-1]]
                        if cells:
                            rows.append(cells)
                    
                    if headers:
                        # Build Table HTML
                        th_html = "".join(f"<th>{format_cell(h)}</th>" for h in headers)
                        tr_html = ""
                        for row in rows:
                            td_html = "".join(f"<td>{format_cell(c)}</td>" for c in row)
                            tr_html += f"<tr>{td_html}</tr>"
                        
                        title = "Bảng So Sánh Hiệu Năng (Benchmark)" if idx_table == 0 else f"Bảng So Sánh Phụ #{idx_table + 1}"
                        benchmark_tables_html += f"""
                        <div class="benchmark-container">
                            <h3 class="section-subtitle">📈 {title}</h3>
                            <div class="table-responsive">
                                <table class="custom-table">
                                    <thead>
                                        <tr>{th_html}</tr>
                                    </thead>
                                    <tbody>
                                        {tr_html}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        """
        except Exception as e:
            benchmark_tables_html = f"<div class='error-msg'>Không thể tải dữ liệu so sánh từ benchmark_report.md: {html.escape(str(e))}</div>"
    else:
        benchmark_tables_html = "<div class='info-msg'>Chưa có dữ liệu so sánh từ benchmark_report.md. Hãy chạy lệnh benchmark trước.</div>"

    # Render agents timeline cards
    cards_html = ""
    for idx, result in enumerate(state.agent_results, 1):
        agent_name = result.agent.upper()
        content = html.escape(result.content)
        metadata = result.metadata
        
        sys_prompt = html.escape(metadata.get("system_prompt", "N/A"))
        user_prompt = html.escape(metadata.get("user_prompt", "N/A"))
        input_tokens = metadata.get("input_tokens", "N/A")
        output_tokens = metadata.get("output_tokens", "N/A")
        cost = metadata.get("cost_usd", 0.0)
        cost_str = f"${cost:.5f}" if isinstance(cost, (int, float)) else "N/A"
        duration = metadata.get("duration_seconds", "N/A")
        # Check fallback latency key if duration is missing
        if duration == "N/A":
            duration = metadata.get("latency_seconds", "N/A")
        duration_str = f"{duration:.2f}s" if isinstance(duration, (int, float)) else "N/A"
        
        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <div class="header-left">
                    <span class="agent-badge {result.agent}">{agent_name}</span>
                    <span class="step-tag">Bước #{idx}</span>
                </div>
                <div class="header-right">
                    <span class="time-stamp">⏱️ {duration_str}</span>
                </div>
            </div>
            <div class="card-body">
                <div class="metrics-grid">
                    <div class="metric-item">
                        <span class="metric-label">Chi phí</span>
                        <span class="metric-value cost-value">{cost_str}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Input Tokens</span>
                        <span class="metric-value">{input_tokens}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Output Tokens</span>
                        <span class="metric-value">{output_tokens}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Thời gian</span>
                        <span class="metric-value">{duration_str}</span>
                    </div>
                </div>
                
                <div class="accordion-section">
                    <button class="accordion-btn" onclick="toggleAccordion(this)">
                        <span>⚙️ Xem Chi Tiết Prompt (System & User)</span>
                        <span class="arrow">▼</span>
                    </button>
                    <div class="accordion-content">
                        <div class="prompt-box">
                            <span class="prompt-title system">System Prompt:</span>
                            <pre><code>{sys_prompt}</code></pre>
                        </div>
                        <div class="prompt-box">
                            <span class="prompt-title user">User Prompt:</span>
                            <pre><code>{user_prompt}</code></pre>
                        </div>
                    </div>
                </div>
                
                <div class="accordion-section active">
                    <button class="accordion-btn" onclick="toggleAccordion(this)">
                        <span>📝 Xem Kết Quả Trả Về (Agent Response)</span>
                        <span class="arrow">▼</span>
                    </button>
                    <div class="accordion-content" style="display: block;">
                        <pre class="response-pre"><code>{content}</code></pre>
                    </div>
                </div>
            </div>
        </div>
        """
        
    # Render sources list
    sources_html = ""
    for idx, doc in enumerate(state.sources, 1):
        url_tag = f'<a href="{doc.url}" target="_blank" class="source-link">{doc.url}</a>' if doc.url else "Không có liên kết"
        sources_html += f"""
        <div class="source-card">
            <div class="source-header">
                <span class="source-idx">[{idx}]</span>
                <span class="source-title">{html.escape(doc.title)}</span>
            </div>
            <div class="source-body">
                <p class="source-snippet">"{html.escape(doc.snippet)}"</p>
                <div class="source-footer">
                    🔗 Nguồn: {url_tag}
                </div>
            </div>
        </div>
        """
        
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bản Ghi Chi Tiết Thực Thi - Multi-Agent Research System</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient-start: #f8fafc;
            --bg-gradient-end: #f1f5f9;
            --card-bg: #ffffff;
            --text-main: #334155;
            --text-heading: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --primary: #2563eb;
            --primary-light: #eff6ff;
            --success: #16a34a;
            --success-light: #f0fdf4;
            --warning: #ca8a04;
            --warning-light: #fefbeb;
            --danger: #dc2626;
            --danger-light: #fef2f2;
            
            --badge-supervisor-bg: #fef3c7;
            --badge-supervisor-text: #b45309;
            --badge-researcher-bg: #dbeafe;
            --badge-researcher-text: #1d4ed8;
            --badge-analyst-bg: #f3e8ff;
            --badge-analyst-text: #7e22ce;
            --badge-writer-bg: #dcfce7;
            --badge-writer-text: #15803d;
            --badge-critic-bg: #fee2e2;
            --badge-critic-text: #b91c1c;
        }}
        
        * {{
            box-sizing: border-box;
            transition: all 0.2s ease;
        }}
        
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-start), var(--bg-gradient-end));
            color: var(--text-main);
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        
        /* Header & Info */
        header {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .header-title-section h1 {{
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--text-heading);
            margin: 0 0 8px 0;
            letter-spacing: -0.025em;
            background: linear-gradient(to right, #1e3a8a, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .header-title-section p {{
            margin: 0;
            color: var(--text-muted);
            font-size: 1rem;
        }}
        
        .student-badge-card {{
            background: var(--primary-light);
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 15px 20px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .student-badge-card .student-title {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--primary);
            font-weight: 700;
        }}
        
        .student-badge-card .student-name {{
            font-size: 1.1rem;
            font-weight: 800;
            color: #1e3a8a;
        }}
        
        .student-badge-card .student-id {{
            font-size: 0.85rem;
            color: #2563eb;
            font-weight: 500;
        }}
        
        /* Section styling */
        h2 {{
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--text-heading);
            margin-top: 40px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-left: 5px solid var(--primary);
            padding-left: 12px;
        }}
        
        /* General Info Panel */
        .info-panel {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .info-label {{
            font-size: 0.85rem;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .info-value {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-heading);
        }}
        
        .info-value.sequence {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            color: var(--primary);
        }}
        
        /* Tables (Benchmark) */
        .benchmark-container {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        }}
        
        .section-subtitle {{
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.1rem;
            color: var(--text-heading);
            font-weight: 700;
        }}
        
        .table-responsive {{
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }}
        
        .custom-table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.95rem;
        }}
        
        .custom-table th {{
            background: #f1f5f9;
            color: var(--text-heading);
            font-weight: 700;
            padding: 14px 18px;
            border-bottom: 2px solid var(--border-color);
            white-space: nowrap;
        }}
        
        .custom-table td {{
            padding: 14px 18px;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-main);
            vertical-align: middle;
        }}
        
        .custom-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        .custom-table tbody tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        
        .custom-table tbody tr:hover {{
            background-color: #f1f5f9;
        }}
        
        /* Badges for single-agent and multi-agent inside tables */
        .badge-type {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-type.single {{
            background: #e0f2fe;
            color: #0369a1;
            border: 1px solid #bae6fd;
        }}
        .badge-type.multi {{
            background: #fae8ff;
            color: #a21caf;
            border: 1px solid #f5d0fe;
        }}
        
        /* Final Answer Card */
        .final-answer-panel {{
            background: #ffffff;
            border: 1px solid #bfdbfe;
            border-top: 5px solid var(--primary);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.06);
            white-space: pre-wrap;
            font-family: inherit;
            font-size: 1.05rem;
            color: #1e293b;
        }}
        
        /* Execution Cards & Accordion */
        .timeline {{
            display: flex;
            flex-direction: column;
            gap: 25px;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        }}
        
        .card:hover {{
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);
            border-color: #cbd5e1;
        }}
        
        .card-header {{
            background: #f8fafc;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .header-left, .header-right {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .agent-badge {{
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 0.85em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        }}
        
        .agent-badge.supervisor {{ background-color: var(--badge-supervisor-bg); color: var(--badge-supervisor-text); border: 1px solid #fde68a; }}
        .agent-badge.researcher {{ background-color: var(--badge-researcher-bg); color: var(--badge-researcher-text); border: 1px solid #bfdbfe; }}
        .agent-badge.analyst {{ background-color: var(--badge-analyst-bg); color: var(--badge-analyst-text); border: 1px solid #e9d5ff; }}
        .agent-badge.writer {{ background-color: var(--badge-writer-bg); color: var(--badge-writer-text); border: 1px solid #bbf7d0; }}
        .agent-badge.critic {{ background-color: var(--badge-critic-bg); color: var(--badge-critic-text); border: 1px solid #fecaca; }}
        
        .step-tag {{
            font-weight: 700;
            font-size: 0.9rem;
            color: var(--text-muted);
        }}
        
        .time-stamp {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-muted);
        }}
        
        .card-body {{
            padding: 24px;
        }}
        
        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .metric-item {{
            background: #f8fafc;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 12px 15px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .metric-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .metric-value {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-heading);
        }}
        
        .metric-value.cost-value {{
            color: var(--success);
        }}
        
        /* Accordions */
        .accordion-section {{
            border: 1px solid var(--border-color);
            border-radius: 10px;
            margin-bottom: 15px;
            overflow: hidden;
            background: #ffffff;
        }}
        
        .accordion-section.active {{
            border-color: #cbd5e1;
        }}
        
        .accordion-btn {{
            width: 100%;
            background: #f8fafc;
            border: none;
            padding: 14px 20px;
            text-align: left;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-heading);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .accordion-btn:hover {{
            background: #f1f5f9;
        }}
        
        .accordion-content {{
            display: none;
            padding: 20px;
            border-top: 1px solid var(--border-color);
            background: #fafafa;
        }}
        
        .arrow {{
            font-size: 0.8rem;
            color: var(--text-muted);
            transition: transform 0.2s ease;
        }}
        
        .accordion-section.active .arrow {{
            transform: rotate(180deg);
        }}
        
        pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            background: #f1f5f9;
            color: #334155;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .response-pre {{
            max-height: 600px;
            background: #ffffff;
        }}
        
        .prompt-box {{
            margin-bottom: 20px;
        }}
        
        .prompt-box:last-child {{
            margin-bottom: 0;
        }}
        
        .prompt-title {{
            display: inline-block;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 4px;
            margin-bottom: 8px;
        }}
        
        .prompt-title.system {{
            background: #eff6ff;
            color: var(--primary);
        }}
        
        .prompt-title.user {{
            background: #f0fdf4;
            color: var(--success);
        }}
        
        /* Sources list */
        .source-grid {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .source-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
        }}
        
        .source-header {{
            display: flex;
            gap: 10px;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        
        .source-idx {{
            background: var(--primary-light);
            color: var(--primary);
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.85rem;
        }}
        
        .source-title {{
            font-weight: 700;
            font-size: 1.05rem;
            color: var(--text-heading);
        }}
        
        .source-snippet {{
            font-style: italic;
            color: var(--text-muted);
            margin: 0 0 12px 0;
            font-size: 0.95rem;
            line-height: 1.5;
        }}
        
        .source-footer {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        
        .source-link {{
            color: var(--primary);
            text-decoration: none;
            word-break: break-all;
        }}
        
        .source-link:hover {{
            text-decoration: underline;
        }}
        
        /* Warnings & Infos */
        .error-msg {{
            background: var(--danger-light);
            color: var(--danger);
            border: 1px solid #fca5a5;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 0.95rem;
        }}
        
        .info-msg {{
            background: var(--primary-light);
            color: var(--primary);
            border: 1px solid #93c5fd;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 0.95rem;
        }}
    </style>
    <script>
        function toggleAccordion(btn) {{
            const section = btn.parentElement;
            const content = btn.nextElementSibling;
            
            if (content.style.display === "block") {{
                content.style.display = "none";
                section.classList.remove("active");
            }} else {{
                content.style.display = "block";
                section.classList.add("active");
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title-section">
                <h1>🔮 Trình Vết Multi-Agent Research System</h1>
                <p>Nhật ký vết chi tiết chạy thực tế từ OpenRouter LLM APIs</p>
            </div>
            <div class="student-badge-card">
                <span class="student-title">Học Viên Thực Hiện</span>
                <span class="student-name">Nguyễn Văn Huy</span>
                <span class="student-id">MSSV: 2A202600773</span>
            </div>
        </header>
        
        <div class="info-panel">
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Câu hỏi truy vấn (Query)</span>
                    <span class="info-value">"{html.escape(state.request.query)}"</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Đối tượng độc giả</span>
                    <span class="info-value">"{html.escape(state.request.audience)}"</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Dòng chuyển hướng (Routing Sequence)</span>
                    <span class="info-value sequence">{html.escape(" ➔ ".join(state.route_history))}</span>
                </div>
            </div>
        </div>
        
        {benchmark_tables_html}
        
        <h2>🏁 Kết Quả Bài Tổng Hợp Cuối Cùng (Final Answer)</h2>
        <div class="final-answer-panel">{html.escape(state.final_answer or "Không có câu trả lời cuối cùng nào được tạo ra.")}</div>
        
        <h2>📜 Dòng Thời Gian Thực Thi (Execution Timeline)</h2>
        <div class="timeline">
            {cards_html}
        </div>
        
        <h2>📚 Các Tài Liệu Nguồn Tham Khảo (Source Documents)</h2>
        <div class="source-grid">
            {sources_html}
        </div>
    </div>
</body>
</html>
"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

