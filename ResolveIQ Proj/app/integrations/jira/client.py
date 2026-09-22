from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings


class AbstractJiraClient(ABC):
    """Abstract interface for Jira API Integration."""

    @abstractmethod
    async def fetch_issue(self, issue_key: str) -> Dict[str, Any]:
        """Fetch Jira issue data by issue key."""
        pass

    @abstractmethod
    async def fetch_all_issues(self, jql: Optional[str] = None, max_results: int = 50) -> list[Dict[str, Any]]:
        """Fetch all issues accessible to authenticated Jira account using pagination."""
        pass

    @abstractmethod
    async def verify_connection(self) -> Dict[str, Any]:
        """Verify Jira credentials and return authenticated user details."""
        pass

    @abstractmethod
    @abstractmethod
    async def add_comment_to_issue(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add resolution comment to Jira issue."""
        pass

    @abstractmethod
    async def get_transitions(self, issue_key: str) -> list[Dict[str, Any]]:
        """Get available transitions for an issue."""
        pass

    @abstractmethod
    async def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        """Apply a workflow transition to a Jira issue."""
        pass


class JiraClient(AbstractJiraClient):
    """Jira REST API v3 Client."""

    def __init__(
        self,
        domain: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        self.domain = domain or settings.JIRA_DOMAIN or settings.JIRA_BASE_URL
        self.email = email if email is not None else (settings.JIRA_EMAIL if domain is None else None)
        self.api_token = api_token if api_token is not None else (settings.JIRA_API_TOKEN if domain is None else None)

    def _get_base_url(self) -> str:
        if not self.domain:
            raise ValueError("Jira domain is not configured (set JIRA_DOMAIN or JIRA_BASE_URL environment variable).")
        domain = self.domain.strip()
        if not domain.startswith("http://") and not domain.startswith("https://"):
            return f"https://{domain}"
        return domain

    async def verify_connection(self) -> Dict[str, Any]:
        """Verify Jira credentials and return authenticated user details."""
        if not self.email or not self.api_token or not self.domain:
            return {
                "connected": False,
                "domain": self.domain,
                "error": "Jira credentials are not fully configured (set JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN)."
            }

        base_url = self._get_base_url()
        url = f"{base_url}/rest/api/3/myself"

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.get(
                    url,
                    auth=(self.email, self.api_token),
                    headers={"Accept": "application/json"}
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "connected": True,
                        "domain": self.domain,
                        "displayName": data.get("displayName"),
                        "emailAddress": data.get("emailAddress"),
                        "accountId": data.get("accountId"),
                        "active": data.get("active", True),
                    }
                return {
                    "connected": False,
                    "domain": self.domain,
                    "error": f"Jira authentication failed (HTTP {response.status_code}): {response.text}"
                }
        except Exception as exc:
            return {
                "connected": False,
                "domain": self.domain,
                "error": f"Failed to connect to Jira API: {str(exc)}"
            }

    async def fetch_all_issues(self, jql: Optional[str] = None, max_results: int = 50) -> list[Dict[str, Any]]:
        """Fetch all issues accessible to authenticated Jira account using token-based pagination."""
        if not self.email or not self.api_token:
            raise ValueError("Jira credentials are missing (set JIRA_EMAIL and JIRA_API_TOKEN).")

        base_url = self._get_base_url()
        url = f"{base_url}/rest/api/3/search/jql"
        effective_jql = jql.strip() if jql and jql.strip() else "issueKey is not EMPTY order by created DESC"

        all_issues: list[Dict[str, Any]] = []
        next_page_token: Optional[str] = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params: Dict[str, Any] = {
                    "jql": effective_jql,
                    "maxResults": max_results,
                    "fields": "*all"
                }
                if next_page_token:
                    params["nextPageToken"] = next_page_token

                response = await client.get(
                    url,
                    params=params,
                    auth=(self.email, self.api_token),
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                page_issues = data.get("issues", [])
                all_issues.extend(page_issues)

                is_last = data.get("isLast", True)
                next_page_token = data.get("nextPageToken")
                if is_last or not next_page_token or len(page_issues) == 0:
                    break

        return all_issues

    async def fetch_issue(self, issue_key: str) -> Dict[str, Any]:
        if not self.email or not self.api_token:
            raise ValueError("Jira credentials are missing (set JIRA_EMAIL and JIRA_API_TOKEN).")

        base_url = self._get_base_url()
        url = f"{base_url}/rest/api/3/issue/{issue_key}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()

    async def add_comment_to_issue(self, issue_key: str, comment: str) -> Dict[str, Any]:
        if not self.email or not self.api_token:
            raise ValueError("Jira credentials are missing (set JIRA_EMAIL and JIRA_API_TOKEN).")

        base_url = self._get_base_url()
        url = f"{base_url}/rest/api/3/issue/{issue_key}/comment"

        # Atlassian Document Format (ADF) body payload
        payload = {
            "body": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                auth=(self.email, self.api_token),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_transitions(self, issue_key: str) -> list[Dict[str, Any]]:
        """Get available transitions for a Jira issue."""
        if not self.email or not self.api_token:
            raise ValueError("Jira credentials are missing (set JIRA_EMAIL and JIRA_API_TOKEN).")

        base_url = self._get_base_url()
        url = f"{base_url}/rest/api/3/issue/{issue_key}/transitions"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("transitions", [])

    async def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        """Apply a workflow transition to a Jira issue."""
        if not self.email or not self.api_token:
            raise ValueError("Jira credentials are missing (set JIRA_EMAIL and JIRA_API_TOKEN).")

        base_url = self._get_base_url()
        url = f"{base_url}/rest/api/3/issue/{issue_key}/transitions"
        payload = {
            "transition": {
                "id": str(transition_id)
            }
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                url,
                json=payload,
                auth=(self.email, self.api_token),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return {"status": "success", "transition_id": transition_id}
            return response.json()
