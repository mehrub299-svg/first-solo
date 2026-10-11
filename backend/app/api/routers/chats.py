from fastapi import APIRouter, Response, status

from app.api.deps import ConversationServiceDep, CurrentUser
from app.schemas.chat import ChatRead, MessageRead

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatRead])
async def list_chats(current_user: CurrentUser, conversations: ConversationServiceDep):
    return await conversations.list_chats(current_user.id)


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
async def list_messages(
    chat_id: int, current_user: CurrentUser, conversations: ConversationServiceDep
):
    return await conversations.get_messages(current_user.id, chat_id)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int, current_user: CurrentUser, conversations: ConversationServiceDep
):
    await conversations.delete_chat(current_user.id, chat_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)