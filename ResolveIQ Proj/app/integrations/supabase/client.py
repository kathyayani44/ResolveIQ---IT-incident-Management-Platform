from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings
from app.schemas.incident import CanonicalIncident


class AbstractSupabaseClient(ABC):
    """Abstract interface for Supabase database operations."""

    @abstractmethod
    async def save_raw_event(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Save raw event payload to raw_events table."""
        pass

    @abstractmethod
    async def save_incident(self, incident: CanonicalIncident) -> CanonicalIncident:
        """Save or update normalized incident in incidents table."""
        pass

    @abstractmethod
    async def get_incident(self, issue_key: str) -> Optional[CanonicalIncident]:
        """Retrieve normalized incident by issue key."""
        pass

    @abstractmethod
    async def list_incidents(self) -> List[CanonicalIncident]:
        """Retrieve all normalized incidents."""
        pass

    @abstractmethod
    async def save_user(self, user_record: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update user in users table."""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by email address."""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by unique user ID."""
        pass


import json
import os
from pathlib import Path

CACHE_FILE = Path("data/incidents_cache.json")
USERS_CACHE_FILE = Path("data/users_cache.json")


class SupabaseClient(AbstractSupabaseClient):
    """Supabase REST API Client for raw events, normalized incidents, and users."""

    _shared_in_memory_raw: Dict[str, Dict[str, Any]] = {}
    _shared_in_memory_incidents: Dict[str, CanonicalIncident] = {}
    _shared_in_memory_users: Dict[str, Dict[str, Any]] = {}
    _cache_loaded: bool = False

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None
    ):
        self.url = (url or settings.SUPABASE_URL or "").rstrip("/")
        self.key = key or settings.SUPABASE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self._in_memory_raw = SupabaseClient._shared_in_memory_raw
        self._in_memory_incidents = SupabaseClient._shared_in_memory_incidents
        self._in_memory_users = SupabaseClient._shared_in_memory_users
        self._load_cache_if_needed()

    def _load_cache_if_needed(self):
        if not SupabaseClient._cache_loaded:
            SupabaseClient._cache_loaded = True
            if CACHE_FILE.exists():
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data:
                            inc = CanonicalIncident(**item)
                            SupabaseClient._shared_in_memory_incidents[inc.issue_key] = inc
                except Exception:
                    pass
            if USERS_CACHE_FILE.exists():
                try:
                    with open(USERS_CACHE_FILE, "r", encoding="utf-8") as f:
                        users_data = json.load(f)
                        for u in users_data:
                            email = u.get("email", "").lower()
                            if email:
                                SupabaseClient._shared_in_memory_users[email] = u
                except Exception:
                    pass

    def _save_cache(self):
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    [inc.model_dump(mode="json") for inc in SupabaseClient._shared_in_memory_incidents.values()],
                    f,
                    indent=2,
                    default=str
                )
        except Exception:
            pass

    def _save_users_cache(self):
        try:
            USERS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(USERS_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    list(SupabaseClient._shared_in_memory_users.values()),
                    f,
                    indent=2,
                    default=str
                )
        except Exception:
            pass

    def _has_credentials(self) -> bool:
        return bool(self.url and self.key)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key or "",
            "Authorization": f"Bearer {self.key or ''}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def save_raw_event(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        event_id = raw_record.get("event_id") or raw_record.get("id")
        if not event_id:
            import uuid
            event_id = str(uuid.uuid4())
            raw_record["id"] = event_id

        if "id" not in raw_record:
            raw_record["id"] = event_id

        if not self._has_credentials():
            self._in_memory_raw[event_id] = raw_record
            return raw_record

        endpoint = f"{self.url}/rest/v1/raw_events"
        payload = {
            "id": event_id,
            "source": raw_record.get("source", "jira"),
            "issue_key": raw_record.get("issue_key"),
            "raw_payload": raw_record.get("raw_payload", raw_record),
            "received_at": str(raw_record.get("received_at")) if raw_record.get("received_at") else None
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(endpoint, json=payload, headers=self._get_headers())
            if res.status_code in (200, 201):
                data = res.json()
                return data[0] if isinstance(data, list) and len(data) > 0 else payload
            # Fallback to local memory on API error in un-provisioned dev env
            self._in_memory_raw[event_id] = raw_record
            return raw_record

    async def save_incident(self, incident: CanonicalIncident) -> CanonicalIncident:
        if not self._has_credentials():
            self._in_memory_incidents[incident.issue_key] = incident
            self._save_cache()
            return incident

        endpoint = f"{self.url}/rest/v1/incidents?on_conflict=issue_key"
        payload = incident.model_dump(mode="json")
        headers = self._get_headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(endpoint, json=payload, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        saved = CanonicalIncident(**data[0])
                        self._in_memory_incidents[incident.issue_key] = saved
                        self._save_cache()
                        return saved
            except Exception:
                pass
            self._in_memory_incidents[incident.issue_key] = incident
            self._save_cache()
            return incident

    async def get_incident(self, issue_key: str) -> Optional[CanonicalIncident]:
        if not self._has_credentials():
            return self._in_memory_incidents.get(issue_key)

        endpoint = f"{self.url}/rest/v1/incidents?issue_key=eq.{issue_key}&select=*"
        async with httpx.AsyncClient() as client:
            res = await client.get(endpoint, headers=self._get_headers())
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return CanonicalIncident(**data[0])
            return self._in_memory_incidents.get(issue_key)

    async def list_incidents(self) -> List[CanonicalIncident]:
        if not self._has_credentials():
            return list(self._in_memory_incidents.values())

        endpoint = f"{self.url}/rest/v1/incidents?select=*&order=created_at.desc"
        async with httpx.AsyncClient() as client:
            res = await client.get(endpoint, headers=self._get_headers())
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return [CanonicalIncident(**item) for item in data]
            return list(self._in_memory_incidents.values())

    async def save_user(self, user_record: Dict[str, Any]) -> Dict[str, Any]:
        """Save user to Supabase users table and persist in cache."""
        email = user_record.get("email", "").strip().lower()
        if not email:
            raise ValueError("Email is required to save user.")

        # Ensure ISO formatted strings for JSON serialization
        record_to_save = dict(user_record)
        if "created_at" in record_to_save and hasattr(record_to_save["created_at"], "isoformat"):
            record_to_save["created_at"] = record_to_save["created_at"].isoformat()

        # Update local memory and file cache
        self._in_memory_users[email] = record_to_save
        self._save_users_cache()

        if not self._has_credentials():
            return record_to_save

        endpoint = f"{self.url}/rest/v1/users?on_conflict=email"
        headers = self._get_headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(endpoint, json=record_to_save, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        saved = data[0]
                        self._in_memory_users[email] = saved
                        self._save_users_cache()
                        return saved
        except Exception:
            pass

        return record_to_save

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by email address."""
        clean_email = email.strip().lower()
        if clean_email in self._in_memory_users:
            return self._in_memory_users[clean_email]

        if not self._has_credentials():
            return None

        endpoint = f"{self.url}/rest/v1/users?email=eq.{clean_email}&select=*"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(endpoint, headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        user = data[0]
                        self._in_memory_users[clean_email] = user
                        self._save_users_cache()
                        return user
        except Exception:
            pass

        return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by user ID."""
        for u in self._in_memory_users.values():
            if u.get("id") == user_id:
                return u

        if not self._has_credentials():
            return None

        endpoint = f"{self.url}/rest/v1/users?id=eq.{user_id}&select=*"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(endpoint, headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        user = data[0]
                        email = user.get("email", "").lower()
                        if email:
                            self._in_memory_users[email] = user
                            self._save_users_cache()
                        return user
        except Exception:
            pass

        return None

