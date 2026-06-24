import logging
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        settings = get_settings()
        
        # Enforce loop guardrails first
        if state.iteration >= settings.max_iterations:
            logger.warning(f"Max iterations ({settings.max_iterations}) reached. Forcing route to 'done'.")
            state.record_route("done")
            state.agent_results.append(AgentResult(
                agent=AgentName.SUPERVISOR,
                content="done",
                metadata={"reason": "max_iterations_reached"}
            ))
            return state

        with trace_span(self.name, {"iteration": state.iteration}) as span:
            system_prompt = (
                "You are a Supervisor agent. Your task is to inspect the current state of a research project "
                "and choose the next worker agent to run. The possible options are: 'researcher', 'analyst', 'writer', or 'done'.\n"
                "Rules:\n"
                "- Choose 'researcher' if research_notes is empty/None.\n"
                "- Choose 'analyst' if research_notes is present but analysis_notes is empty/None.\n"
                "- Choose 'writer' if analysis_notes is present but final_answer is empty/None.\n"
                "- Choose 'done' if all fields are populated or if there's no more work to do.\n"
                "Answer with exactly one word (the name of the worker or 'done')."
            )
            
            user_prompt = (
                f"Query: {state.request.query}\n"
                f"Current iteration: {state.iteration}\n"
                f"research_notes: {state.research_notes or 'None'}\n"
                f"analysis_notes: {state.analysis_notes or 'None'}\n"
                f"final_answer: {state.final_answer or 'None'}"
            )
            
            try:
                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                route = response.content.strip().lower()
                
                # Validation & Fallback
                valid_routes = {"researcher", "analyst", "writer", "done"}
                if route not in valid_routes:
                    logger.warning(f"Supervisor returned invalid route: '{route}'. Falling back based on state.")
                    if not state.research_notes:
                        route = "researcher"
                    elif not state.analysis_notes:
                        route = "analyst"
                    elif not state.final_answer:
                        route = "writer"
                    else:
                        route = "done"
                        
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "duration_seconds": span.get("duration_seconds")
                }
            except Exception as e:
                logger.error(f"Supervisor LLM call failed: {e}. Falling back based on state.")
                state.errors.append(f"Supervisor error: {e}")
                # Fallback rule
                if not state.research_notes:
                    route = "researcher"
                elif not state.analysis_notes:
                    route = "analyst"
                elif not state.final_answer:
                    route = "writer"
                else:
                    route = "done"
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "error": str(e),
                    "fallback": True
                }
            
            logger.info(f"Supervisor routed to: '{route}' (Iteration: {state.iteration})")
            state.record_route(route)
            state.agent_results.append(AgentResult(
                agent=AgentName.SUPERVISOR,
                content=route,
                metadata=metadata
            ))
            state.add_trace_event("supervisor_decision", {"route": route, "system_prompt": system_prompt, "user_prompt": user_prompt, "metadata": metadata})
            
        return state

