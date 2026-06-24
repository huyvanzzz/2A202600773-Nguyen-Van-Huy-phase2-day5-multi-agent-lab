import re
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return a benchmark metric object containing cost, quality, and citations."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    # Calculate estimated token cost from all agent interactions
    estimated_cost = 0.0
    for res in state.agent_results:
        cost = res.metadata.get("cost_usd")
        if cost is not None:
            estimated_cost += cost

    # Calculate citation coverage
    citations = set(re.findall(r"\[(\d+)\]", state.final_answer or ""))
    citation_count = len(citations)
    source_count = len(state.sources)
    citation_ratio = (citation_count / source_count) if source_count > 0 else 0.0

    # Quality scoring heuristic based on length and citation behavior
    quality = 0.0
    if state.final_answer and len(state.final_answer) > 50:
        quality = 5.0
        if citation_ratio > 0.5:
            quality += 3.0
        elif citation_ratio > 0:
            quality += 1.5
        if len(state.final_answer) > 400:
            quality += 2.0
    
    quality_score = min(quality, 10.0)

    error_count = len(state.errors)
    notes = f"Iters: {state.iteration} | Citations: {citation_count}/{source_count} ({citation_ratio*100:.0f}%) | Errors: {error_count}"

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost if estimated_cost > 0 else None,
        quality_score=quality_score if quality_score > 0 else None,
        notes=notes
    )
    return state, metrics

