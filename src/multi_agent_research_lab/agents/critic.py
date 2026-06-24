import logging
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        logger.info("CriticAgent running.")
        
        if not state.final_answer:
            logger.warning("No final answer found to review. Skipping.")
            return state

        with trace_span(self.name) as span:
            try:
                system_prompt = (
                    "You are a Critic agent. Your task is to fact-check the final report "
                    "against the gathered research notes. Verify that the citations are correct "
                    "and there are no hallucinations. End your response with 'APPROVED' if the report "
                    "is satisfactory, or provide detailed feedback."
                )
                
                user_prompt = (
                    f"Final Report:\n{state.final_answer}\n\n"
                    f"Research Notes:\n{state.research_notes or 'None'}"
                )
                
                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                
                metadata = {
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "duration_seconds": span.get("duration_seconds")
                }
                
                # Append critique findings to state trace or errors if rejected
                if "approved" in response.content.lower():
                    logger.info("Critic approved the final report.")
                else:
                    logger.warning("Critic requested revisions.")
                    
            except Exception as e:
                logger.error(f"Critic execution failed: {e}")
                state.errors.append(f"Critic error: {e}")
                response_content = f"Error during critic verification: {e}"
                metadata = {"error": str(e)}
                response = type("MockResponse", (), {"content": response_content})()

            state.agent_results.append(AgentResult(
                agent=AgentName.CRITIC,
                content=response.content,
                metadata=metadata
            ))
            state.add_trace_event("critic_completed", {"metadata": metadata})

        return state

