from tests.fakes import FAKE_ANSWER
from tests.helpers import (
    API,
    GARDEN_TEXT,
    REACTOR_QUESTION,
    REACTOR_TEXT,
    create_document,
    register_and_login,
)


async def ask(client, headers, question=REACTOR_QUESTION, top_k=5):
    return await client.post(
        f"{API}/chat/ask", json={"question": question, "top_k": top_k}, headers=headers
    )


async def test_users_only_see_their_own_documents(client):
    headers_a = await register_and_login(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    await create_document(client, headers_a, "Reactor facts", REACTOR_TEXT)

    listing_b = await client.get(f"{API}/documents", headers=headers_b)
    assert listing_b.json() == []


async def test_user_cannot_delete_another_users_document(client):
    headers_a = await register_and_login(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    created = await create_document(client, headers_a, "Reactor facts", REACTOR_TEXT)

    response = await client.delete(f"{API}/documents/{created['id']}", headers=headers_b)
    assert response.status_code == 404

    listing_a = await client.get(f"{API}/documents", headers=headers_a)
    assert [item["id"] for item in listing_a.json()] == [created["id"]]


async def test_asking_without_own_documents_never_reaches_the_llm(client, fake_llm):
    headers_a = await register_and_login(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    await create_document(client, headers_a, "Reactor facts", REACTOR_TEXT)

    response = await ask(client, headers_b)
    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("I don't have any documents")
    assert body["sources"] == []
    assert fake_llm.calls == []


async def test_answers_only_use_the_askers_documents(client, fake_llm):
    headers_a = await register_and_login(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    await create_document(client, headers_a, "Reactor facts", REACTOR_TEXT)
    await create_document(client, headers_b, "Garden facts", GARDEN_TEXT)

    response_b = await ask(client, headers_b)
    assert response_b.status_code == 200
    assert {source["document_title"] for source in response_b.json()["sources"]} == {
        "Garden facts"
    }
    sent_for_b = str(fake_llm.calls[0])
    assert "Quillham" not in sent_for_b
    assert "helium" not in sent_for_b

    response_a = await ask(client, headers_a)
    assert {source["document_title"] for source in response_a.json()["sources"]} == {
        "Reactor facts"
    }


async def test_ask_returns_answer_and_sources(client):
    headers = await register_and_login(client, "a@example.com")
    await create_document(client, headers, "Reactor facts", REACTOR_TEXT)
    await create_document(client, headers, "Garden facts", GARDEN_TEXT)

    response = await ask(client, headers, top_k=3)
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == FAKE_ANSWER
    assert body["sources"][0]["document_title"] == "Reactor facts"
    assert set(body["sources"][0]) == {
        "document_id",
        "document_title",
        "chunk_index",
        "content",
        "score",
    }


async def test_ask_requires_login(client):
    response = await client.post(
        f"{API}/chat/ask", json={"question": "hello", "top_k": 3}
    )
    assert response.status_code == 401


async def test_ask_validates_input(client):
    headers = await register_and_login(client, "a@example.com")
    for payload in (
        {"question": "", "top_k": 3},
        {"question": "hello", "top_k": 0},
        {"question": "hello", "top_k": 11},
    ):
        response = await client.post(f"{API}/chat/ask", json=payload, headers=headers)
        assert response.status_code == 422, payload