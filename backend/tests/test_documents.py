from tests.helpers import (
    API,
    REACTOR_TEXT,
    create_document,
    db_scalar,
    register_and_login,
)


async def test_documents_require_login(client):
    assert (await client.get(f"{API}/documents")).status_code == 401
    response = await client.post(f"{API}/documents", json={"title": "x", "text": "y"})
    assert response.status_code == 401


async def test_create_and_list_document(client):
    headers = await register_and_login(client, "a@example.com")
    created = await create_document(client, headers, "Reactor facts", REACTOR_TEXT)
    assert created["title"] == "Reactor facts"
    assert created["chunk_count"] >= 1

    listing = await client.get(f"{API}/documents", headers=headers)
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [created["id"]]
    assert listing.json()[0]["chunk_count"] == created["chunk_count"]


async def test_whitespace_only_text_is_rejected(client):
    headers = await register_and_login(client, "a@example.com")
    response = await client.post(
        f"{API}/documents", json={"title": "x", "text": "   "}, headers=headers
    )
    assert response.status_code == 422


async def test_nul_only_text_is_rejected_as_empty(client):
    headers = await register_and_login(client, "a@example.com")
    response = await client.post(
        f"{API}/documents", json={"title": "x", "text": "\u0000\u0000"}, headers=headers
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Document has no readable text"}


async def test_delete_removes_document_and_chunks(client):
    headers = await register_and_login(client, "a@example.com")
    created = await create_document(client, headers, "Reactor facts", REACTOR_TEXT)
    assert await db_scalar("SELECT count(*) FROM chunks") >= 1

    response = await client.delete(f"{API}/documents/{created['id']}", headers=headers)
    assert response.status_code == 204
    assert (await client.get(f"{API}/documents", headers=headers)).json() == []
    assert await db_scalar("SELECT count(*) FROM chunks") == 0


async def test_delete_unknown_document_returns_404(client):
    headers = await register_and_login(client, "a@example.com")
    response = await client.delete(f"{API}/documents/9999", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}