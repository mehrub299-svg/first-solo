from fastapi import APIRouter

from app.api.deps import ConversationServiceDep, CurrentUser
from app.schemas.chat import ChatAnswer, ChatQuestion

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatAnswer)
async def ask(
    payload: ChatQuestion,
    current_user: CurrentUser,
    conversations: ConversationServiceDep,
):
    result = await conversations.ask(
        current_user.id,
        payload.question,
        payload.top_k,
        payload.document_ids,
        payload.chat_id,
    )
    return ChatAnswer.model_validate(result, from_attributes=True)