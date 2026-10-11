import hashlib

from sqlalchemy import text

from app.db.engine import engine
from tests.helpers import API, db_scalar, register_and_login

COOKIE = "refresh_token"


async def db_execute(statement: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(statement))


async def sign_in(client, email: str = "a@example.com"):
    headers = await register_and_login(client, email)
    return headers, client.cookies.get(COOKIE)


async def refresh_with(client, raw_token: str):
    """Send a specific refresh token, ignoring whatever is in the cookie jar."""
    client.cookies.clear()
    return await client.post(
        f"{API}/auth/refresh", headers={"Cookie": f"{COOKIE}={raw_token}"}
    )


async def test_login_sets_http_only_refresh_cookie(client):
    await client.post(
        f"{API}/auth/register", json={"email": "a@example.com", "password": "password123"}
    )
    response = await client.post(
        f"{API}/auth/login", data={"username": "a@example.com", "password": "password123"}
    )
    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith("refresh_token=")
    assert "httponly" in cookie
    assert "path=/api/v1/auth" in cookie
    assert "samesite=lax" in cookie
    assert "refresh_token" not in response.json()


async def test_refresh_issues_working_access_token_and_rotates_cookie(client):
    _, old = await sign_in(client)

    response = await client.post(f"{API}/auth/refresh")
    assert response.status_code == 200
    me = await client.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert client.cookies.get(COOKIE) != old


async def test_refresh_without_cookie_is_rejected_and_cookie_cleared(client):
    response = await client.post(f"{API}/auth/refresh")
    assert response.status_code == 401
    assert "max-age=0" in response.headers["set-cookie"].lower()


async def test_logout_revokes_the_refresh_token(client):
    _, old = await sign_in(client)
    response = await client.post(f"{API}/auth/logout")
    assert response.status_code == 204
    assert (await refresh_with(client, old)).status_code == 401


async def test_old_token_replayed_after_grace_revokes_the_whole_family(client):
    _, first = await sign_in(client)
    assert (await client.post(f"{API}/auth/refresh")).status_code == 200
    second = client.cookies.get(COOKIE)

    await db_execute(
        "UPDATE refresh_tokens SET rotated_at = now() - interval '1 minute' "
        "WHERE rotated_at IS NOT NULL"
    )
    assert (await refresh_with(client, first)).status_code == 401
    assert (await refresh_with(client, second)).status_code == 401


async def test_old_token_replayed_within_grace_is_tolerated(client):
    _, first = await sign_in(client)
    assert (await client.post(f"{API}/auth/refresh")).status_code == 200
    assert (await refresh_with(client, first)).status_code == 200


async def test_expired_refresh_token_is_rejected(client):
    _, token = await sign_in(client)
    await db_execute("UPDATE refresh_tokens SET expires_at = now() - interval '1 minute'")
    assert (await refresh_with(client, token)).status_code == 401


async def test_refresh_tokens_are_stored_hashed(client):
    _, raw = await sign_in(client)
    stored = await db_scalar("SELECT token_hash FROM refresh_tokens")
    assert stored != raw
    assert stored == hashlib.sha256(raw.encode()).hexdigest()