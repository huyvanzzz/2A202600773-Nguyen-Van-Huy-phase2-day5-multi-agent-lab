import logging
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        logger.info("WriterAgent running.")
        
        with trace_span(self.name) as span:
            try:
                system_prompt = (
                    f"You are a Writer agent. Your task is to synthesize the provided research notes "
                    f"and analysis notes into a comprehensive, final report. Structure your report "
                    f"using markdown headings, list items, or bold text. Format the final output "
                    f"specifically for the audience: '{state.request.audience}'. You MUST include "
                    f"inline citations (e.g. [1], [2]) that link facts back to the source documents "
                    f"originally captured by the researcher."
                )
                
                user_prompt = (
                    f"Query: {state.request.query}\n\n"
                    f"Research Notes:\n{state.research_notes or 'None'}\n\n"
                    f"Analysis Notes:\n{state.analysis_notes or 'None'}"
                )
                
                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                state.final_answer = response.content
                
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "duration_seconds": span.get("duration_seconds")
                }
            except Exception as e:
                logger.error(f"Writer execution failed: {e}")
                state.errors.append(f"Writer error: {e}")
                state.final_answer = f"Error during final answer generation: {e}"
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "error": str(e)
                }

            state.agent_results.append(AgentResult(
                agent=AgentName.WRITER,
                content=state.final_answer,
                metadata=metadata
            ))
            state.add_trace_event("writing_completed", {"system_prompt": system_prompt, "user_prompt": user_prompt, "metadata": metadata})

        return state

