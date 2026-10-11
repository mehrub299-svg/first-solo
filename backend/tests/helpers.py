from httpx import AsyncClient
from sqlalchemy import text

from app.db.engine import engine

API = "/api/v1"

REACTOR_TEXT = (
    "The Zorblax-7 reactor was commissioned in 2031 in the city of Quillham. "
    "It uses liquid helium as coolant and produces 480 megawatts of power."
)
GARDEN_TEXT = (
    "Tomato plants need at least six hours of sun per day. "
    "Water them deeply twice a week and stake the tall varieties."
)
# Deliberately does not contain "Quillham" or "helium", so tests can check
# that those words never reach the LLM for a user who doesn't own that document.
REACTOR_QUESTION = "Where was the reactor commissioned?"


async def register_and_login(
    client: AsyncClient, email: str, password: str = "password123"
) -> dict[str, str]:
    response = await client.post(
        f"{API}/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201, response.text
    response = await client.post(
        f"{API}/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def create_document(
    client: AsyncClient, headers: dict[str, str], title: str, body: str
) -> dict:
    response = await client.post(
        f"{API}/documents", json={"title": title, "text": body}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()


async def db_scalar(query: str):
    async with engine.connect() as connection:
        result = await connection.execute(text(query))
        return result.scalar_one()