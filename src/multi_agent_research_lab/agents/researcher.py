import logging
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        logger.info(f"ResearcherAgent running for query: '{state.request.query}'")
        
        with trace_span(self.name) as span:
            try:
                # 1. Search for sources
                search_client = SearchClient()
                sources = search_client.search(
                    query=state.request.query, 
                    max_results=state.request.max_sources
                )
                state.sources = sources
                
                # 2. Formulate prompts for LLM
                system_prompt = (
                    "You are a Researcher agent. Your task is to analyze the search results "
                    "and synthesize concise, fact-based research notes. You MUST reference "
                    "the source documents by citation numbers (e.g. [1], [2]) matching their "
                    "index in the provided search results list."
                )
                
                sources_str = ""
                for idx, doc in enumerate(sources, 1):
                    sources_str += f"[{idx}] Title: {doc.title}\n    Snippet: {doc.snippet}\n\n"
                    
                user_prompt = (
                    f"Query: {state.request.query}\n\n"
                    f"Search Results:\n{sources_str}"
                )
                
                # 3. Call LLM to summarize
                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                state.research_notes = response.content
                
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "duration_seconds": span.get("duration_seconds")
                }
            except Exception as e:
                logger.error(f"Researcher execution failed: {e}")
                state.errors.append(f"Researcher error: {e}")
                state.research_notes = f"Error during research collection: {e}"
                metadata = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "error": str(e)
                }

            state.agent_results.append(AgentResult(
                agent=AgentName.RESEARCHER,
                content=state.research_notes,
                metadata=metadata
            ))
            state.add_trace_event("research_completed", {"system_prompt": system_prompt, "user_prompt": user_prompt, "metadata": metadata})

        return state

