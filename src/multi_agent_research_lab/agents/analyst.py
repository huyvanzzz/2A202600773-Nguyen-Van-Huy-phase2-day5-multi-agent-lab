import logging
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        logger.info("AnalystAgent running.")
        
        if not state.research_notes:
            logger.warning("No research notes found for analysis. Skipping.")
            return state

        with trace_span(self.name) as span:
            try:
                system_prompt = (
                    "You are an Analyst agent. Your task is to analyze the provided research notes.\n"
                    "Extract the key claims, compare differing viewpoints if any, and flag any "
                    "weak or unsupported evidence. Make sure your analysis is highly structured."
                )
                
                user_prompt = f"Research Notes:\n{state.research_notes}"
                
                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                state.analysis_notes = response.content
                
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "duration_seconds": span.get("duration_seconds")
                }
            except Exception as e:
                logger.error(f"Analyst execution failed: {e}")
                state.errors.append(f"Analyst error: {e}")
                state.analysis_notes = f"Error during analysis generation: {e}"
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "error": str(e)
                }

            state.agent_results.append(AgentResult(
                agent=AgentName.ANALYST,
                content=state.analysis_notes,
                metadata=metadata
            ))
            state.add_trace_event("analysis_completed", {"system_prompt": system_prompt, "user_prompt": user_prompt, "metadata": metadata})

        return state

