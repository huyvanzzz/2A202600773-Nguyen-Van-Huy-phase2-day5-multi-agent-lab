import logging
from langgraph.graph import StateGraph, END
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def build(self) -> object:
        """Create a LangGraph graph."""
        builder = StateGraph(ResearchState)
        
        # Add nodes wrapping our agents
        builder.add_node("supervisor", lambda state: SupervisorAgent().run(state))
        builder.add_node("researcher", lambda state: ResearcherAgent().run(state))
        builder.add_node("analyst", lambda state: AnalystAgent().run(state))
        builder.add_node("writer", lambda state: WriterAgent().run(state))
        
        # The flow starts at the supervisor
        builder.set_entry_point("supervisor")
        
        # Routing decision handler
        def route_next(state: ResearchState) -> str:
            if not state.route_history:
                logger.error("Supervisor did not record any route. Ending workflow.")
                return "done"
            
            last_route = state.route_history[-1]
            if last_route == "done":
                return "done"
            return last_route
            
        # Wire up supervisor's routing decisions
        builder.add_conditional_edges(
            "supervisor",
            route_next,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END
            }
        )
        
        # Every worker routes back to the supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")
        
        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        compiled_graph = self.build()
        logger.info("Starting Multi-Agent Workflow execution.")
        
        result = compiled_graph.invoke(state)
        
        if isinstance(result, ResearchState):
            return result
        elif isinstance(result, dict):
            return ResearchState(**result)
        else:
            logger.error(f"Unexpected graph invocation result type: {type(result)}")
            return state

