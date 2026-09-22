from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.jira import IngestionReceiptSchema
from app.services.jira_ingestion import JiraIngestionService

router = APIRouter(prefix="/jira", tags=["jira"])


def get_jira_ingestion_service() -> JiraIngestionService:
    return JiraIngestionService()


@router.post(
    "/webhook",
    response_model=IngestionReceiptSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Receive and store raw Jira webhook event"
)
async def receive_jira_webhook(
    payload: Dict[str, Any],
    service: JiraIngestionService = Depends(get_jira_ingestion_service)
) -> IngestionReceiptSchema:
    """Endpoint for receiving incoming webhook payloads from Jira."""
    try:
        return await service.ingest_webhook_event(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest Jira webhook event: {str(e)}"
        )


@router.post(
    "/fetch/{issue_key}",
    response_model=IngestionReceiptSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Fetch and store raw issue data from Jira REST API"
)
async def fetch_and_ingest_jira_issue(
    issue_key: str,
    service: JiraIngestionService = Depends(get_jira_ingestion_service)
) -> IngestionReceiptSchema:
    """Endpoint to trigger issue fetch from Jira API and save raw payload."""
    try:
        return await service.fetch_and_ingest_issue(issue_key)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching issue from Jira: {str(e)}"
        )


@router.post(
    "/sync",
    status_code=status.HTTP_200_OK,
    summary="Trigger read-only synchronization of all Jira issues"
)
async def sync_all_jira_issues(
    service: JiraIngestionService = Depends(get_jira_ingestion_service)
) -> Dict[str, Any]:
    """Synchronize all accessible issues from Jira API into ResolveIQ using read-only GET requests."""
    try:
        return await service.sync_all_jira_issues()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to synchronize Jira issues: {str(e)}"
        )


@router.get(
    "/connection",
    status_code=status.HTTP_200_OK,
    summary="Check read-only Jira connection status"
)
async def check_jira_connection(
    service: JiraIngestionService = Depends(get_jira_ingestion_service)
) -> Dict[str, Any]:
    """Verify read-only Jira connection and return authenticated user details."""
    return await service.jira_client.verify_connection()

