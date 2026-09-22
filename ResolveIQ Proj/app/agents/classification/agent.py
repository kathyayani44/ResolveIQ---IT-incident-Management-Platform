from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult
from app.agents.classification.prompts import SYSTEM_PROMPT, format_classification_user_prompt
from app.core.llm_client import execute_llm_request


async def run_classification(incident: CanonicalIncident) -> ClassificationResult:
    """
    Analyzes an incident's title, description, severity, and optional comments to identify:
    - category
    - affected service

    Does NOT receive retrieved chunks, RCA results, resolution, or workflow state.
    """
    user_prompt = format_classification_user_prompt(incident)

    result = await execute_llm_request(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=ClassificationResult,
        operation_name="Classification Agent",
    )
    return result
