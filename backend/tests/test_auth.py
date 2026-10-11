from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings
from app.core.security import create_access_token
from tests.helpers import API, db_scalar, register_and_login


async def test_register_returns_user_without_password(client):
    response = await client.post(
        f"{API}/auth/register", json={"email": "a@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "a@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_duplicate_email_is_rejected(client):
    payload = {"email": "a@example.com", "password": "password123"}
    assert (await client.post(f"{API}/auth/register", json=payload)).status_code == 201
    response = await client.post(f"{API}/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


async def test_email_is_case_insensitive(client):
    await client.post(
        f"{API}/auth/register", json={"email": "Mixed@Example.com", "password": "password123"}
    )
    response = await client.post(
        f"{API}/auth/login", data={"username": "mixed@example.com", "password": "password123"}
    )
    assert response.status_code == 200


async def test_short_password_is_rejected(client):
    response = await client.post(
        f"{API}/auth/register", json={"email": "a@example.com", "password": "short"}
    )
    assert response.status_code == 422


async def test_password_is_stored_as_argon2_hash(client):
    await register_and_login(client, "a@example.com")
    stored = await db_scalar("SELECT hashed_password FROM users")
    assert stored.startswith("$argon2id$")
    assert "password123" not in stored


async def test_wrong_password_and_unknown_email_look_the_same(client):
    await register_and_login(client, "a@example.com")
    wrong = await client.post(
        f"{API}/auth/login", data={"username": "a@example.com", "password": "wrong-password"}
    )
    unknown = await client.post(
        f"{API}/auth/login", data={"username": "nobody@example.com", "password": "password123"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_me_returns_current_user(client):
    headers = await register_and_login(client, "a@example.com")
    response = await client.get(f"{API}/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "a@example.com"


async def test_me_requires_a_valid_token(client):
    assert (await client.get(f"{API}/auth/me")).status_code == 401
    bad = await client.get(f"{API}/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert bad.status_code == 401


async def test_expired_token_is_rejected(client):
    await register_and_login(client, "a@example.com")
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401


async def test_token_for_missing_user_is_rejected(client):
    token = create_access_token("9999")
    response = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_token_signed_with_wrong_key_is_rejected(client):
    await register_and_login(client, "a@example.com")
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "x" * 32,
        algorithm="HS256",
    )
    response = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {forged}"}
    )
    assert response.status_code == 401