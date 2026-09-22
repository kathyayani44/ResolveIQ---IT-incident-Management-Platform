from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.incident import CanonicalIncident
from app.schemas.auth import UserResponse
from app.api.routes.auth import require_authenticated_user
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_incident_service() -> IncidentService:
    return IncidentService()


@router.get(
    "",
    response_model=List[CanonicalIncident],
    status_code=status.HTTP_200_OK,
    summary="List all normalized CanonicalIncident records"
)
async def list_incidents(
    sync: bool = False,
    service: IncidentService = Depends(get_incident_service)
) -> List[CanonicalIncident]:
    """Retrieve all normalized CanonicalIncident records. If sync=True, syncs fresh issues from Jira first."""
    if sync:
        try:
            from app.services.jira_ingestion import JiraIngestionService
            jira_ingest = JiraIngestionService(storage=service.raw_storage, incident_service=service)
            await jira_ingest.sync_all_jira_issues()
        except Exception as e:
            import logging
            logging.getLogger("resolveiq.incidents").warning(f"Jira sync failed on list: {e}")

    return await service.list_incidents()


@router.get(
    "/{issue_key}",
    response_model=CanonicalIncident,
    status_code=status.HTTP_200_OK,
    summary="Get normalized CanonicalIncident by issue key"
)
async def get_incident(
    issue_key: str,
    service: IncidentService = Depends(get_incident_service)
) -> CanonicalIncident:
    """Retrieve normalized CanonicalIncident record by Jira issue key."""
    incident = await service.get_incident_by_key(issue_key)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with issue key '{issue_key}' not found."
        )
    return incident


@router.post(
    "/{issue_key}/process",
    response_model=CanonicalIncident,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-agent resolution pipeline on an incident"
)
async def process_incident(
    issue_key: str,
    service: IncidentService = Depends(get_incident_service)
) -> CanonicalIncident:
    """Trigger Classification -> RAG -> RCA -> Resolution pipeline and return updated CanonicalIncident."""
    try:
        return await service.process_incident_pipeline(issue_key)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing incident pipeline: {str(e)}"
        )


@router.post(
    "/{issue_key}/retry-writeback",
    status_code=status.HTTP_200_OK,
    summary="Retry Jira writeback and verification for an approved incident"
)
async def retry_jira_writeback(
    issue_key: str,
    current_user: UserResponse = Depends(require_authenticated_user)
):
    """
    Retries Jira writeback and verification for an already-approved incident without
    rerunning AI analysis stages. Safe against duplicate comments or transitions.
    Requires authenticated ResolveIQ user.
    """
    from app.services.approval_service import ApprovalService
    approval_svc = ApprovalService()
    try:
        reviewer_name = current_user.name or current_user.email or "IT Ops Operator"
        return await approval_svc.retry_writeback(issue_key=issue_key, reviewer=reviewer_name)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrying Jira writeback: {str(e)}"
        )




