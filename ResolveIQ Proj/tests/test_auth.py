import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import UserRegister, UserLogin
from app.services.auth_service import AuthService, hash_password, verify_password

client = TestClient(app)


def test_password_hashing_security():
    """Verify PBKDF2 HMAC SHA-256 password hashing with salt and constant-time comparison."""
    pwd = "superSecretPassword123"
    pwd_hash, salt = hash_password(pwd)

    # Must not store plaintext
    assert pwd not in pwd_hash
    assert len(salt) >= 16
    assert len(pwd_hash) == 64  # hex representation of 32-byte sha256 output

    # Verification must succeed with correct password
    assert verify_password(pwd, salt, pwd_hash) is True

    # Verification must fail with incorrect password
    assert verify_password("wrongPassword", salt, pwd_hash) is False


def test_user_registration_success():
    """Verify registering a new ResolveIQ user with basic account details (Name, Email, Password)."""
    email = f"ops_{uuid.uuid4().hex[:8]}@resolveiq.io"
    payload = {
        "name": "DevOps Engineer",
        "email": email,
        "password": "SecurePassword999!"
    }

    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["email"] == email
    assert data["name"] == "DevOps Engineer"
    assert "token" in data and data["token"].startswith("riq_")
    assert "id" in data
    assert "password" not in data
    assert "pwd_hash" not in data
    assert "salt" not in data


def test_user_registration_duplicate_email():
    """Verify duplicate email registration is rejected with 400 Bad Request."""
    email = f"dup_{uuid.uuid4().hex[:8]}@resolveiq.io"
    payload = {
        "name": "Original User",
        "email": email,
        "password": "Password123"
    }

    # Register first time
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt to register again with same email
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_user_registration_invalid_inputs():
    """Verify validation on registration (invalid email or short password)."""
    # Short password
    res1 = client.post("/api/v1/auth/register", json={
        "name": "Test",
        "email": f"valid_{uuid.uuid4().hex[:8]}@email.com",
        "password": "12"
    })
    assert res1.status_code in (400, 422)

    # Missing/invalid email
    res2 = client.post("/api/v1/auth/register", json={
        "name": "Test",
        "email": "not-an-email",
        "password": "ValidPassword123"
    })
    assert res2.status_code in (400, 422)


def test_user_login_success():
    """Verify successful login with valid credentials returns session token and profile."""
    email = f"login_{uuid.uuid4().hex[:8]}@resolveiq.io"
    password = "MyStrongPassword456"

    # Register user first
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Login Tester",
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["email"] == email
    assert data["name"] == "Login Tester"
    assert "token" in data and data["token"].startswith("riq_")
    assert "password" not in data


def test_user_login_invalid_password():
    """Verify login with incorrect password returns 401 Unauthorized."""
    email = f"bad_pwd_{uuid.uuid4().hex[:8]}@resolveiq.io"
    client.post("/api/v1/auth/register", json={
        "name": "Bad Pwd Tester",
        "email": email,
        "password": "CorrectPassword123"
    })

    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword999"
    })
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_user_login_nonexistent_email():
    """Verify login with unregistered email returns 401 Unauthorized."""
    res = client.post("/api/v1/auth/login", json={
        "email": f"ghost_{uuid.uuid4().hex[:8]}@resolveiq.io",
        "password": "AnyPassword123"
    })
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_authenticated_access_me_endpoint():
    """Verify accessing /auth/me with valid session token returns the current user profile."""
    email = f"session_{uuid.uuid4().hex[:8]}@resolveiq.io"
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Session User",
        "email": email,
        "password": "SessionPassword123"
    })
    token = reg_res.json()["token"]

    # Call /auth/me with Bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == email
    assert data["name"] == "Session User"
    assert data["token"] == token


def test_unauthenticated_access_me_endpoint_rejected():
    """Verify accessing /auth/me without authorization header returns 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "authentication required" in res.json()["detail"].lower()


def test_invalid_token_rejected():
    """Verify accessing /auth/me with a fabricated or expired token returns 401."""
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake_token_xyz_12345"})
    assert res.status_code == 401
    assert "invalid or expired session token" in res.json()["detail"].lower()


def test_jira_connection_endpoint_does_not_leak_secrets():
    """Verify /auth/jira-connection returns status without exposing backend API tokens or secrets."""
    res = client.get("/api/v1/auth/jira-connection")
    assert res.status_code == 200
    data = res.json()
    assert "connected" in data
    assert "api_token" not in data
    assert "password" not in data
    assert "secret" not in data
