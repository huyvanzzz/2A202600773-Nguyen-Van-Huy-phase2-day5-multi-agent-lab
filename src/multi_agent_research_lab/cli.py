"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a real single-agent baseline calling the LLM client."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    
    from multi_agent_research_lab.services.llm_client import LLMClient
    from multi_agent_research_lab.services.search_client import SearchClient
    from multi_agent_research_lab.core.schemas import AgentName, AgentResult
    from time import perf_counter
    
    console.print(f"[bold green]Running Single-Agent Baseline for query: '{query}'...[/bold green]")
    started = perf_counter()
    
    try:
        search_client = SearchClient()
        sources = search_client.search(query, max_results=request.max_sources)
        state.sources = sources
        
        sources_str = ""
        for i, doc in enumerate(sources, 1):
            sources_str += f"[{i}] {doc.title}: {doc.snippet}\n"
            
        system_prompt = (
            "You are an expert research assistant. Your task is to analyze the user's query "
            "and the provided search results to write a comprehensive, well-structured synthesis "
            "answering the query. You MUST cite your sources using inline citation numbers (e.g. [1], [2])."
        )
        user_prompt = f"Query: {query}\n\nSearch Results:\n{sources_str}"
        
        llm = LLMClient()
        response = llm.complete(system_prompt, user_prompt)
        state.final_answer = response.content
        
        latency = perf_counter() - started
        state.agent_results.append(AgentResult(
            agent=AgentName.WRITER,
            content=response.content,
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "latency_seconds": latency
            }
        ))
        
        console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))
        console.print(f"[dim]Latency: {latency:.2f}s | Est. Cost: ${response.cost_usd or 0.0:.6f}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Baseline failed: {e}[/bold red]")



@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        console.print(f"[bold green]Running Multi-Agent Workflow for query: '{query}'...[/bold green]")
        result = workflow.run(state)
        console.print(Panel.fit(result.final_answer or "No final answer generated.", title="Multi-Agent Final Answer"))
        console.print(f"[bold blue]Routing history:[/bold blue] {' -> '.join(result.route_history)}")
        
        # Save HTML trace report
        from multi_agent_research_lab.observability.tracing import save_html_trace
        from pathlib import Path
        trace_path = Path("reports/trace_report.html")
        save_html_trace(result, str(trace_path))
        console.print(f"[bold green]HTML Trace Report successfully saved to: {trace_path.resolve()}[/bold green]")
        
        console.print(f"[dim]Total Iterations: {result.iteration} | Errors: {len(result.errors)}[/dim]")
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    except Exception as e:
        console.print(f"[bold red]Workflow execution failed: {e}[/bold red]")


def run_baseline_workflow(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    from multi_agent_research_lab.services.llm_client import LLMClient
    from multi_agent_research_lab.services.search_client import SearchClient
    from multi_agent_research_lab.core.schemas import AgentName, AgentResult
    
    search_client = SearchClient()
    sources = search_client.search(query, max_results=request.max_sources)
    state.sources = sources
    
    sources_str = "".join(f"[{i}] {doc.title}: {doc.snippet}\n" for i, doc in enumerate(sources, 1))
    system_prompt = (
        "You are an expert research assistant. Your task is to analyze the user's query "
        "and the provided search results to write a comprehensive, well-structured synthesis "
        "answering the query. You MUST cite your sources using inline citation numbers (e.g. [1], [2])."
    )
    user_prompt = f"Query: {query}\n\nSearch Results:\n{sources_str}"
    
    llm = LLMClient()
    response = llm.complete(system_prompt, user_prompt)
    state.final_answer = response.content
    state.agent_results.append(AgentResult(
        agent=AgentName.WRITER,
        content=response.content,
        metadata={
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd
        }
    ))
    return state


def run_multi_agent_workflow(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@app.command("benchmark")
def benchmark(
    config_path: Annotated[str, typer.Option("--config", "-c", help="Path to config YAML")] = "configs/lab_default.yaml",
) -> None:
    """Run comparative benchmark of single-agent and multi-agent workflows."""
    _init()
    
    import yaml
    from pathlib import Path
    from multi_agent_research_lab.evaluation.benchmark import run_benchmark
    from multi_agent_research_lab.evaluation.report import render_markdown_report
    
    yaml_path = Path(config_path)
    if not yaml_path.exists():
        console.print(f"[bold red]Config file not found at {config_path}[/bold red]")
        raise typer.Exit(code=1)
        
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    queries = config.get("benchmark", {}).get("queries", [])
    if not queries:
        console.print("[bold yellow]No benchmark queries found in config.[/bold yellow]")
        return
        
    console.print(f"[bold green]Starting Benchmark on {len(queries)} queries...[/bold green]")
    
    metrics_list = []
    
    for idx, query in enumerate(queries, 1):
        console.print(f"\n[bold cyan]Query #{idx}: {query}[/bold cyan]")
        
        # 1. Run Baseline
        console.print("  Running Single-Agent Baseline...")
        try:
            _, base_metrics = run_benchmark(f"Single-Agent (Q{idx})", query, run_baseline_workflow)
            metrics_list.append(base_metrics)
            console.print(f"    Latency: {base_metrics.latency_seconds:.2f}s | Quality: {base_metrics.quality_score or 'N/A'}")
        except Exception as e:
            console.print(f"    [bold red]Baseline failed: {e}[/bold red]")
            
        # 2. Run Multi-Agent
        console.print("  Running Multi-Agent Workflow...")
        try:
            _, multi_metrics = run_benchmark(f"Multi-Agent (Q{idx})", query, run_multi_agent_workflow)
            metrics_list.append(multi_metrics)
            console.print(f"    Latency: {multi_metrics.latency_seconds:.2f}s | Quality: {multi_metrics.quality_score or 'N/A'}")
        except Exception as e:
            console.print(f"    [bold red]Multi-Agent failed: {e}[/bold red]")
            
    # Generate report
    report_content = render_markdown_report(metrics_list)
    
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / "benchmark_report.md"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    console.print(f"\n[bold green]Benchmark completed successfully![/bold green]")
    console.print(f"Report saved to: [underline]{report_file.resolve()}[/underline]")


if __name__ == "__main__":
    app()

