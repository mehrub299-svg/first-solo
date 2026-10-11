import asyncio

from app.api.ratelimit import ASK_MINUTE, LOGIN, REGISTER
from tests.helpers import API, register_and_login


async def login(client, email, password):
    return await client.post(
        f"{API}/auth/login", data={"username": email, "password": password}
    )


async def test_login_is_limited_per_client(client):
    await register_and_login(client, "a@example.com")
    LOGIN.reset()
    LOGIN.limit = 3

    for _ in range(3):
        assert (await login(client, "a@example.com", "wrong-password")).status_code == 401

    blocked = await login(client, "a@example.com", "wrong-password")
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) >= 1
    assert "Too many requests" in blocked.json()["detail"]
    assert (await client.get(f"{API}/health")).status_code == 200  # other routes unaffected


async def test_register_is_limited_per_client(client):
    REGISTER.limit = 2
    for number in range(2):
        response = await client.post(
            f"{API}/auth/register",
            json={"email": f"u{number}@example.com", "password": "password123"},
        )
        assert response.status_code == 201

    blocked = await client.post(
        f"{API}/auth/register", json={"email": "u9@example.com", "password": "password123"}
    )
    assert blocked.status_code == 429


async def test_ask_limit_is_per_user(client):
    headers_a = await register_and_login(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    ASK_MINUTE.reset()
    ASK_MINUTE.limit = 2

    async def ask(headers):
        return await client.post(
            f"{API}/chat/ask", json={"question": "hello", "top_k": 3}, headers=headers
        )

    assert (await ask(headers_a)).status_code == 200
    assert (await ask(headers_a)).status_code == 200
    assert (await ask(headers_a)).status_code == 429
    assert (await ask(headers_b)).status_code == 200  # another user is not affected


async def test_limit_lifts_after_the_window(client):
    LOGIN.limit = 1
    LOGIN.window = 0.2

    assert (await login(client, "nobody@example.com", "x")).status_code == 401
    assert (await login(client, "nobody@example.com", "x")).status_code == 429
    await asyncio.sleep(0.3)
    assert (await login(client, "nobody@example.com", "x")).status_code == 401