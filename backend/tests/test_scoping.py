from tests.helpers import (
    API,
    GARDEN_TEXT,
    REACTOR_QUESTION,
    REACTOR_TEXT,
    create_document,
    register_and_login,
)


async def ask(client, headers, **extra):
    payload = {"question": REACTOR_QUESTION, "top_k": 5, **extra}
    return await client.post(f"{API}/chat/ask", json=payload, headers=headers)


async def two_documents(client, headers):
    reactor = await create_document(client, headers, "Reactor facts", REACTOR_TEXT)
    garden = await create_document(client, headers, "Garden facts", GARDEN_TEXT)
    return reactor["id"], garden["id"]


def titles(response):
    return {source["document_title"] for source in response.json()["sources"]}


async def test_selecting_a_document_restricts_the_sources(client, fake_llm):
    headers = await register_and_login(client, "a@example.com")
    _, garden_id = await two_documents(client, headers)

    response = await ask(client, headers, document_ids=[garden_id])
    assert response.status_code == 200
    assert titles(response) == {"Garden facts"}
    assert "Quillham" not in str(fake_llm.calls[0])


async def test_selecting_several_documents_searches_all_of_them(client):
    headers = await register_and_login(client, "a@example.com")
    reactor_id, garden_id = await two_documents(client, headers)

    response = await ask(client, headers, document_ids=[reactor_id, garden_id])
    assert response.status_code == 200
    assert titles(response) == {"Reactor facts", "Garden facts"}


async def test_no_selection_means_all_documents(client):
    headers = await register_and_login(client, "a@example.com")
    await two_documents(client, headers)

    for extra in ({}, {"document_ids": None}, {"document_ids": []}):
        response = await ask(client, headers, **extra)
        assert response.status_code == 200, extra
        assert titles(response) == {"Reactor facts", "Garden facts"}, extra


async def test_another_users_document_id_is_rejected_without_calling_the_llm(
    client, fake_llm
):
    headers_a = await register_and_login(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    reactor_a = await create_document(client, headers_a, "Reactor facts", REACTOR_TEXT)
    await create_document(client, headers_b, "Garden facts", GARDEN_TEXT)

    response = await ask(client, headers_b, document_ids=[reactor_a["id"]])
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}
    assert fake_llm.calls == []


async def test_unknown_document_id_is_rejected(client, fake_llm):
    headers = await register_and_login(client, "a@example.com")
    await two_documents(client, headers)

    response = await ask(client, headers, document_ids=[9999])
    assert response.status_code == 404
    assert fake_llm.calls == []


async def test_mixed_valid_and_foreign_ids_are_rejected_entirely(client, fake_llm):
    headers_a = await register_and_login(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    reactor_a = await create_document(client, headers_a, "Reactor facts", REACTOR_TEXT)
    garden_b = await create_document(client, headers_b, "Garden facts", GARDEN_TEXT)

    response = await ask(client, headers_b, document_ids=[garden_b["id"], reactor_a["id"]])
    assert response.status_code == 404
    assert fake_llm.calls == []


async def test_duplicate_ids_are_accepted(client):
    headers = await register_and_login(client, "a@example.com")
    _, garden_id = await two_documents(client, headers)

    response = await ask(client, headers, document_ids=[garden_id, garden_id])
    assert response.status_code == 200
    assert titles(response) == {"Garden facts"}


async def test_invalid_selection_is_a_validation_error(client):
    headers = await register_and_login(client, "a@example.com")
    assert (await ask(client, headers, document_ids=["x"])).status_code == 422
    assert (await ask(client, headers, document_ids=list(range(1, 52)))).status_code == 422