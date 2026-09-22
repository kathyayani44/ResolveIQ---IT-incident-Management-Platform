import hashlib
import os
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.schemas.auth import UserLogin, UserRegister, UserResponse, JiraConnectionResponse
from app.integrations.jira.client import AbstractJiraClient, JiraClient
from app.integrations.supabase.client import AbstractSupabaseClient, SupabaseClient


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password using PBKDF2 HMAC SHA-256 with 100,000 iterations and per-user salt."""
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pwd_hash, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Verify password against expected hash using constant-time comparison."""
    pbkdf2_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    if secrets.compare_digest(pbkdf2_hash, expected_hash):
        return True
    # Backward compatibility with legacy SHA256 hashes
    legacy_hash = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(legacy_hash, expected_hash)


class AuthService:
    """Authentication and Jira Connection verification service for ResolveIQ."""

    _users_db: Dict[str, Dict[str, Any]] = {}
    _tokens_db: Dict[str, str] = {}  # token -> user_email

    def __init__(
        self,
        jira_client: Optional[AbstractJiraClient] = None,
        supabase_client: Optional[AbstractSupabaseClient] = None
    ):
        self.jira_client = jira_client or JiraClient()
        self.supabase_client = supabase_client or SupabaseClient()
        self._seed_default_user()

    def _seed_default_user(self):
        # Sync from Supabase client in-memory cache
        if hasattr(self.supabase_client, "_in_memory_users"):
            for email, u in self.supabase_client._in_memory_users.items():
                self._users_db[email] = u

        if "usravya1@gmail.com" not in self._users_db:
            pwd_hash, salt = hash_password("password123")
            user_record = {
                "id": "usr-default-001",
                "email": "usravya1@gmail.com",
                "name": "Sravya Ullamgunta",
                "pwd_hash": pwd_hash,
                "salt": salt,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self._users_db["usravya1@gmail.com"] = user_record
            if hasattr(self.supabase_client, "_in_memory_users"):
                self.supabase_client._in_memory_users["usravya1@gmail.com"] = user_record
                self.supabase_client._save_users_cache()

        self._tokens_db["riq_default"] = "usravya1@gmail.com"

    async def register(self, reg_data: UserRegister) -> UserResponse:
        email = reg_data.email.strip().lower()
        if not email or "@" not in email:
            raise ValueError("A valid email address is required.")
        if len(reg_data.password) < 4:
            raise ValueError("Password must be at least 4 characters long.")

        existing = self._users_db.get(email)
        if not existing and hasattr(self.supabase_client, "get_user_by_email"):
            existing = await self.supabase_client.get_user_by_email(email)

        if existing:
            raise ValueError(f"Account with email '{email}' already exists.")

        user_id = f"usr-{secrets.token_hex(6)}"
        pwd_hash, salt = hash_password(reg_data.password)
        name = reg_data.name.strip() if reg_data.name else email.split("@")[0].title()

        now_iso = datetime.now(timezone.utc).isoformat()
        user_record = {
            "id": user_id,
            "email": email,
            "name": name,
            "pwd_hash": pwd_hash,
            "salt": salt,
            "created_at": now_iso
        }

        if hasattr(self.supabase_client, "save_user"):
            await self.supabase_client.save_user(user_record)
        self._users_db[email] = user_record

        token = f"riq_{secrets.token_urlsafe(32)}"
        self._tokens_db[token] = email

        return UserResponse(
            id=user_id,
            email=email,
            name=name,
            token=token,
            created_at=datetime.fromisoformat(now_iso)
        )

    async def login(self, login_data: UserLogin) -> UserResponse:
        email = login_data.email.strip().lower()
        user_record = self._users_db.get(email)
        if not user_record and hasattr(self.supabase_client, "get_user_by_email"):
            user_record = await self.supabase_client.get_user_by_email(email)

        if not user_record:
            raise ValueError("Invalid email or password.")

        if not verify_password(login_data.password, user_record["salt"], user_record["pwd_hash"]):
            raise ValueError("Invalid email or password.")

        token = f"riq_{secrets.token_urlsafe(32)}"
        self._tokens_db[token] = email

        created = user_record.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except Exception:
                created = datetime.now(timezone.utc)
        elif not created:
            created = datetime.now(timezone.utc)

        return UserResponse(
            id=user_record["id"],
            email=user_record["email"],
            name=user_record["name"],
            token=token,
            created_at=created
        )

    def get_user_by_token(self, token: str) -> Optional[UserResponse]:
        email = self._tokens_db.get(token)
        if not email:
            return None
        user_record = self._users_db.get(email)
        if not user_record and hasattr(self.supabase_client, "_in_memory_users"):
            user_record = self.supabase_client._in_memory_users.get(email)
        if not user_record:
            return None

        created = user_record.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except Exception:
                created = datetime.now(timezone.utc)
        elif not created:
            created = datetime.now(timezone.utc)

        return UserResponse(
            id=user_record["id"],
            email=user_record["email"],
            name=user_record["name"],
            token=token,
            created_at=created
        )

    async def get_jira_connection_status(self) -> JiraConnectionResponse:
        """Verifies connected Jira account using read-only API and returns sanitized status."""
        conn = await self.jira_client.verify_connection()
        return JiraConnectionResponse(
            connected=conn.get("connected", False),
            domain=conn.get("domain"),
            displayName=conn.get("displayName"),
            emailAddress=conn.get("emailAddress"),
            error=conn.get("error")
        )

