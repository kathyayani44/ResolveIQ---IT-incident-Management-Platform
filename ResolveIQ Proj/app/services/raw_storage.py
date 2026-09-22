from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid
from app.integrations.supabase.client import AbstractSupabaseClient, SupabaseClient


class AbstractRawStorage(ABC):
    """Abstract Interface for Raw Event Storage."""

    @abstractmethod
    async def save_raw_event(self, raw_payload: Dict[str, Any], source: str = "jira", issue_key: Optional[str] = None) -> Dict[str, Any]:
        """Store raw event payload and return event metadata record."""
        pass

    @abstractmethod
    async def get_raw_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored raw event record by event_id."""
        pass


class InMemoryRawStorage(AbstractRawStorage):
    """In-memory implementation of raw event storage."""

    def __init__(self):
        self._records: Dict[str, Dict[str, Any]] = {}

    async def save_raw_event(self, raw_payload: Dict[str, Any], source: str = "jira", issue_key: Optional[str] = None) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        record = {
            "event_id": event_id,
            "id": event_id,
            "source": source,
            "issue_key": issue_key,
            "raw_payload": raw_payload,
            "received_at": datetime.now(timezone.utc),
            "status": "stored"
        }
        self._records[event_id] = record
        return record

    async def get_raw_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self._records.get(event_id)


class SupabaseRawStorage(AbstractRawStorage):
    """Supabase-backed raw event storage."""

    def __init__(self, supabase_client: Optional[AbstractSupabaseClient] = None):
        self.supabase_client = supabase_client or SupabaseClient()
        self.fallback = InMemoryRawStorage()

    async def save_raw_event(self, raw_payload: Dict[str, Any], source: str = "jira", issue_key: Optional[str] = None) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        record = {
            "event_id": event_id,
            "id": event_id,
            "source": source,
            "issue_key": issue_key,
            "raw_payload": raw_payload,
            "received_at": datetime.now(timezone.utc),
            "status": "stored"
        }
        saved = await self.supabase_client.save_raw_event(record)
        await self.fallback.save_raw_event(raw_payload=raw_payload, source=source, issue_key=issue_key)
        return saved if isinstance(saved, dict) else record

    async def get_raw_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return await self.fallback.get_raw_event(event_id)


# Global default raw storage instance
raw_storage_instance = InMemoryRawStorage()
