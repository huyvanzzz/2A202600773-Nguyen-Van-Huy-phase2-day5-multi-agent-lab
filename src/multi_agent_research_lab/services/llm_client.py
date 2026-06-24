import logging
import time
from dataclasses import dataclass
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion."""
        settings = get_settings()

        if settings.use_mock:
            # Simulate slight latency
            time.sleep(0.5)
            
            prompt_combined = (system_prompt + " " + user_prompt).lower()
            logger.info(f"[MockLLM] complete called. Input prompt size: {len(prompt_combined)} chars.")
            
            # 1. Determine if this is a Supervisor routing request
            if "supervisor" in prompt_combined or "route" in prompt_combined or "router" in prompt_combined:
                # Decide route based on current state mentioned in prompts
                if "research_notes: none" in prompt_combined or "research_notes=none" in prompt_combined or "research_notes: ''" in prompt_combined or "research_notes: \"\"" in prompt_combined:
                    content = "researcher"
                elif "analysis_notes: none" in prompt_combined or "analysis_notes=none" in prompt_combined or "analysis_notes: ''" in prompt_combined or "analysis_notes: \"\"" in prompt_combined:
                    content = "analyst"
                elif "final_answer: none" in prompt_combined or "final_answer=none" in prompt_combined or "final_answer: ''" in prompt_combined or "final_answer: \"\"" in prompt_combined:
                    content = "writer"
                else:
                    content = "done"
                logger.info(f"[MockLLM] Supervisor routing decision: '{content}'")
            
            # 2. Determine if this is Writer / Synthesis request
            elif "writer" in prompt_combined or "write" in prompt_combined or "synthesis" in prompt_combined:
                if "graphrag" in prompt_combined:
                    content = (
                        "# Summary of GraphRAG State-of-the-Art\n\n"
                        "GraphRAG represents a major evolution in Retrieval-Augmented Generation [1]. By structuring private text data into a semantic knowledge graph (identifying entities, attributes, and relationships), it enables rich hierarchical indexing before the LLM is queried [2].\n\n"
                        "### Core Methodology\n"
                        "- **Community Detection:** Leverages Leiden clustering to group entities hierarchically [2].\n"
                        "- **Query-Time Synthesis:** Generates multi-level community summaries to answer global queries [3].\n\n"
                        "### Trade-offs\n"
                        "While offering exceptional context coverage and claim accuracy [1], GraphRAG requires significantly higher token costs and pre-processing latency than traditional naive RAG [2]."
                    )
                elif "customer support" in prompt_combined or "support" in prompt_combined:
                    content = (
                        "# Multi-Agent Support Workflows vs. Single-Agent\n\n"
                        "Modern enterprise customer support benefits from dividing labor among multiple specialized agents (e.g., Billing, Support) [1]. A central Router redirects the user query based on intent [2].\n\n"
                        "### Key Advantages\n"
                        "- **Prompt Isolation:** Isolates specialized tools and prompts, reducing injection risks [1].\n"
                        "- **Handoff Efficiency:** Structured state transition prevents context loss [2].\n\n"
                        "### Core Challenges\n"
                        "Orchestration latency is higher, and loop guardrails must be active to terminate circular routing [1]."
                    )
                elif "guardrail" in prompt_combined:
                    content = (
                        "# Production Guardrails for LLM Agents\n\n"
                        "To build reliable, cost-predictable agentic systems, several guardrails must be applied at different stages [1].\n\n"
                        "### Main Guardrail Types\n"
                        "1. **Execution Limits:** Strict constraints on maximum iterations and total execution timeouts [1].\n"
                        "2. **Schema Validation:** Verifying JSON/Pydantic output schemas, with predefined fallback routines [2].\n"
                        "3. **Input Guardrails:** Safeguarding prompts using classifiers or safety checks before LLM execution [2]."
                    )
                else:
                    content = f"# Synthesis Report\n\nFinal mock response synthesized based on research and analysis notes with citations [1][2]."
                logger.info("[MockLLM] Writer report generated.")
                
            # 3. Determine if this is Analyst agent request
            elif "analyst" in prompt_combined:
                if "graphrag" in prompt_combined:
                    content = (
                        "Analysis Notes - GraphRAG:\n"
                        "1. Key Claim: GraphRAG enables global understanding of private corpora, which naive RAG cannot do.\n"
                        "2. Viewpoint Comparison: GraphRAG provides superior quality and diversity of claims, but has an order of magnitude higher token consumption than naive RAG during indexing.\n"
                        "3. Evidence Validation: The claim of outperforming standard RAG on global queries is well-supported by benchmarks, but practical adoption is constrained by high setup complexity and pricing."
                    )
                elif "customer support" in prompt_combined or "support" in prompt_combined:
                    content = (
                        "Analysis Notes - Customer Support:\n"
                        "1. Key Claim: Isolating tools in sub-agents reduces the surface area for prompt injections.\n"
                        "2. Trade-offs: Lower prompt size per agent vs. increased total system orchestration overhead.\n"
                        "3. Risk: Handoff logic can fail if state context is lost or if agents recursively redirect to one another."
                    )
                elif "guardrail" in prompt_combined:
                    content = (
                        "Analysis Notes - Production Guardrails:\n"
                        "1. Key Claim: Hard limits like iteration ceilings and timeouts are essential for cost predictability.\n"
                        "2. Design Pattern: Defensive validation (Pydantic schema validation) is superior to raw LLM retries.\n"
                        "3. Risk: Overly aggressive input filtering might block valid user queries."
                    )
                else:
                    content = "Mock Analysis Notes: Extracted 3 key claims and validated them against search evidence."
                logger.info("[MockLLM] Analyst insights generated.")
                
            # 4. Determine if this is Researcher agent request
            elif "researcher" in prompt_combined:
                if "graphrag" in prompt_combined:
                    content = (
                        "Research Notes - GraphRAG:\n"
                        "- Microsoft's GraphRAG builds a knowledge graph from unstructured source text to capture entities, attributes, and relationships [1].\n"
                        "- Uses Leiden hierarchical community detection to cluster related entities into semantic 'communities' [2].\n"
                        "- Provides 'global search' capability by summarizing these communities, allowing LLMs to answer high-level questions that standard RAG fails [3].\n"
                        "- A key trade-off is the high cost and latency associated with graph construction and extensive summarization [2]."
                    )
                elif "customer support" in prompt_combined or "support" in prompt_combined:
                    content = (
                        "Research Notes - Customer Support:\n"
                        "- Multi-agent support workflows route user queries to specialized sub-agents (billing, tech, refunds) to isolate prompts and tools [1].\n"
                        "- Requires a clear handoff schema to pass state without context loss [2].\n"
                        "- Implementing state-machine guardrails prevents infinite redirection loops between agents [1]."
                    )
                elif "guardrail" in prompt_combined:
                    content = (
                        "Research Notes - Production Guardrails:\n"
                        "- Key guardrails include hard limits on iterations (max_iterations) and execution timeout thresholds to prevent runaway loops [1].\n"
                        "- Input guardrails validate incoming prompts to detect injection attacks or jailbreaks [2].\n"
                        "- Output guardrails validate LLM outputs against strict JSON/Pydantic schemas and invoke fallbacks on failure [2]."
                    )
                else:
                    content = f"Mock Research Notes on the query. Found key details in simulated documents [1][2]."
                logger.info("[MockLLM] Researcher notes generated.")
                
            # 5. Default/Critic / Other
            else:
                content = "Mock LLM output: Operation completed successfully."
                
            # Mock tokens & cost estimation
            input_tokens = len(system_prompt + user_prompt) // 4
            output_tokens = len(content) // 4
            cost_usd = (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
            
            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd
            )

        # Real LLM call
        if settings.llm_provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValidationError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter.")
            api_key = settings.openrouter_api_key
            base_url = settings.openrouter_base_url
            model = settings.openrouter_model
        else:
            if not settings.openai_api_key:
                raise ValidationError("OPENAI_API_KEY is required for real LLM completions. Set USE_MOCK=true in .env to run without it.")
            api_key = settings.openai_api_key
            base_url = None
            model = settings.openai_model

        try:
            import openai
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = completion.choices[0].message.content or ""
            input_tokens = completion.usage.prompt_tokens if completion.usage else None
            output_tokens = completion.usage.completion_tokens if completion.usage else None
            
            # Simple pricing model (standard rates for gpt-4o-mini)
            cost_usd = None
            if input_tokens is not None and output_tokens is not None:
                cost_usd = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000

            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd
            )
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise ValidationError(f"LLM API failed: {e}")

