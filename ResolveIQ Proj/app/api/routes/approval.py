from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from app.schemas.approval import ApprovalPackage, HumanApprovalInput, FinalWorkflowOutput
from app.schemas.auth import UserResponse
from app.api.routes.auth import require_authenticated_user
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approval", tags=["approval"])


class SubmitApprovalRequest(BaseModel):
    package: ApprovalPackage
    decision: HumanApprovalInput


def get_approval_service() -> ApprovalService:
    return ApprovalService()


@router.post(
    "/submit",
    response_model=FinalWorkflowOutput,
    status_code=status.HTTP_200_OK,
    summary="Submit human approval or rejection decision"
)
async def submit_human_approval(
    req: SubmitApprovalRequest,
    current_user: UserResponse = Depends(require_authenticated_user),
    service: ApprovalService = Depends(get_approval_service)
) -> FinalWorkflowOutput:
    """
    Submits human approval decision (Requires authenticated ResolveIQ user):
    - Status 'approved' triggers controlled Jira writeback & verification.
    - Status 'rejected' ends workflow in REJECTED state without updating Jira.
    """
    # Ensure reviewer is set from authenticated user if not provided
    if not req.decision.reviewer or req.decision.reviewer == "Human Operator":
        req.decision.reviewer = current_user.name or current_user.email

    try:
        return await service.process_approval(package=req.package, user_input=req.decision)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


