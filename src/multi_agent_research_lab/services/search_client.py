import logging
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        settings = get_settings()

        if settings.use_mock:
            logger.info(f"[MockSearch] Searching for query: '{query}'")
            query_lower = query.lower()
            
            # Simulated search results database
            if "graphrag" in query_lower:
                results = [
                    SourceDocument(
                        title="GraphRAG: Unlocking LLM Discovery on Private Data",
                        url="https://example.com/graphrag-paper",
                        snippet="Microsoft's GraphRAG uses knowledge graphs to structure private data before prompting LLMs. It consists of entity extraction, hierarchical community detection, and query-time summarization, outperforming standard RAG on global questions."
                    ),
                    SourceDocument(
                        title="GraphRAG vs Naive RAG Benchmark",
                        url="https://example.com/graphrag-vs-naive-rag",
                        snippet="In benchmarking GraphRAG vs naive RAG, GraphRAG demonstrates superior comprehensiveness and diversity of results by clustering entities and summarizing clusters, though it incurs higher token cost due to community summary generation."
                    ),
                    SourceDocument(
                        title="Knowledge Graphs in RAG Systems",
                        url="https://example.com/knowledge-graphs-rag",
                        snippet="Integrating knowledge graphs into RAG systems allows LLMs to query structured entity-relation triples. This approach enables multi-hop reasoning and provides better grounding for answers, reducing factual errors."
                    )
                ]
            elif "customer support" in query_lower or "support" in query_lower:
                results = [
                    SourceDocument(
                        title="Orchestrating Multi-Agent Customer Support Workflows",
                        url="https://example.com/multi-agent-support",
                        snippet="Customer support systems benefit from multi-agent setups where a Router directs queries to Billing, Technical, or Refund agents. This isolates prompts and tools, improving accuracy and reducing prompt injection risks."
                    ),
                    SourceDocument(
                        title="Handoff Patterns in Support Agents",
                        url="https://example.com/agent-handoffs",
                        snippet="A core pattern in support agents is state handoff: transferring state between specialized agents. Proper routing policies prevent circular handoffs and ensure a fallback agent handles unsupported queries."
                    )
                ]
            elif "guardrail" in query_lower or "production guardrail" in query_lower:
                results = [
                    SourceDocument(
                        title="Production Guardrails for LLM Agents",
                        url="https://example.com/llm-guardrails",
                        snippet="Building production agents requires implementing strict guardrails: setting maximum iteration limits to prevent endless loops, utilizing timeout boundaries, caching LLM responses, and doing schema validation on outputs."
                    ),
                    SourceDocument(
                        title="Input-Output Validation in LLM Pipelines",
                        url="https://example.com/io-validation",
                        snippet="Validating inputs via regex or LLM classifiers prevents prompt injection. Validating output JSON schemas ensures structured response compatibility. Fallbacks should execute when validation fails."
                    )
                ]
            else:
                results = [
                    SourceDocument(
                        title=f"General Research on: {query}",
                        url="https://example.com/general-search",
                        snippet=f"This mock document analyzes the state-of-the-art developments in '{query}' and proposes a structured framework to address current limitations."
                    ),
                    SourceDocument(
                        title=f"Comprehensive Overview of {query}",
                        url="https://example.com/overview",
                        snippet=f"A reference document detailing the core concepts, methodologies, and practical applications of '{query}'."
                    )
                ]
            
            return results[:max_results]

        # Actual search logic
        if not settings.tavily_api_key:
            raise ValidationError("TAVILY_API_KEY is required for real search. Set USE_MOCK=true in .env to run without it.")
        
        try:
            import requests
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            docs = []
            for result in data.get("results", []):
                docs.append(SourceDocument(
                    title=result.get("title", "Untitled"),
                    url=result.get("url"),
                    snippet=result.get("content", "")
                ))
            return docs
        except Exception as e:
            logger.error(f"Search API call failed: {e}")
            raise ValidationError(f"Search failed: {e}")

