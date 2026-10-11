from tests.helpers import (
    API,
    REACTOR_QUESTION,
    REACTOR_TEXT,
    create_document,
    db_scalar,
    register_and_login,
)


async def ask(client, headers, question=REACTOR_QUESTION, **extra):
    payload = {"question": question, "top_k": 3, **extra}
    return await client.post(f"{API}/chat/ask", json=payload, headers=headers)


async def user_with_document(client, email="a@example.com"):
    headers = await register_and_login(client, email)
    await create_document(client, headers, "Reactor facts", REACTOR_TEXT)
    return headers


async def test_first_question_creates_a_chat_and_stores_both_messages(client):
    headers = await user_with_document(client)
    response = await ask(client, headers)
    assert response.status_code == 200
    chat_id = response.json()["chat_id"]

    chats = (await client.get(f"{API}/chats", headers=headers)).json()
    assert [chat["id"] for chat in chats] == [chat_id]
    assert chats[0]["title"] == REACTOR_QUESTION

    messages = (await client.get(f"{API}/chats/{chat_id}/messages", headers=headers)).json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["sources"] is None
    assert messages[1]["sources"][0]["document_title"] == "Reactor facts"


async def test_follow_up_in_same_chat_uses_history(client, fake_llm):
    headers = await user_with_document(client)
    first = await ask(client, headers)
    chat_id = first.json()["chat_id"]

    second = await ask(client, headers, "And in what year?", chat_id=chat_id)
    assert second.status_code == 200
    assert second.json()["chat_id"] == chat_id

    messages = (await client.get(f"{API}/chats/{chat_id}/messages", headers=headers)).json()
    assert len(messages) == 4

    # 1 answer call, then 1 question-rewrite call + 1 answer call.
    assert len(fake_llm.calls) == 3
    assert fake_llm.calls[1][0]["content"].startswith("Rewrite the user's last question")
    final_prompt = fake_llm.calls[2][1]["content"]
    assert "Conversation so far" in final_prompt
    assert f"User: {REACTOR_QUESTION}" in final_prompt
    assert "Assistant: Based on the documents." in final_prompt  # [1] stripped


async def test_questions_without_chat_id_start_separate_chats(client):
    headers = await user_with_document(client)
    first = (await ask(client, headers)).json()["chat_id"]
    second = (await ask(client, headers)).json()["chat_id"]
    assert first != second

    chats = (await client.get(f"{API}/chats", headers=headers)).json()
    assert [chat["id"] for chat in chats] == [second, first]  # newest first


async def test_chats_are_private(client, fake_llm):
    headers_a = await user_with_document(client, "a@example.com")
    headers_b = await register_and_login(client, "b@example.com")
    chat_id = (await ask(client, headers_a)).json()["chat_id"]
    calls_before = len(fake_llm.calls)

    assert (await client.get(f"{API}/chats", headers=headers_b)).json() == []
    assert (await client.get(f"{API}/chats/{chat_id}/messages", headers=headers_b)).status_code == 404
    assert (await client.delete(f"{API}/chats/{chat_id}", headers=headers_b)).status_code == 404
    assert (await ask(client, headers_b, chat_id=chat_id)).status_code == 404
    assert len(fake_llm.calls) == calls_before


async def test_delete_chat_removes_its_messages(client):
    headers = await user_with_document(client)
    chat_id = (await ask(client, headers)).json()["chat_id"]

    response = await client.delete(f"{API}/chats/{chat_id}", headers=headers)
    assert response.status_code == 204
    assert (await client.get(f"{API}/chats", headers=headers)).json() == []
    assert await db_scalar("SELECT count(*) FROM messages") == 0


async def test_failed_ask_stores_nothing(client):
    headers = await user_with_document(client)
    response = await ask(client, headers, document_ids=[9999])
    assert response.status_code == 404
    assert (await client.get(f"{API}/chats", headers=headers)).json() == []


async def test_long_question_gets_a_shortened_title(client):
    headers = await user_with_document(client)
    await ask(client, headers, "Where was the reactor commissioned? " * 5)
    title = (await client.get(f"{API}/chats", headers=headers)).json()[0]["title"]
    assert len(title) <= 60
    assert title.endswith("…")


async def test_unknown_chat_id_is_rejected(client):
    headers = await user_with_document(client)
    response = await ask(client, headers, chat_id=9999)
    assert response.status_code == 404
    assert response.json() == {"detail": "Chat not found"}


async def test_chat_endpoints_require_login(client):
    assert (await client.get(f"{API}/chats")).status_code == 401
    assert (await client.get(f"{API}/chats/1/messages")).status_code == 401
    assert (await client.delete(f"{API}/chats/1")).status_code == 401