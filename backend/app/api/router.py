from fastapi import APIRouter, Depends

from app.api.ratelimit import enforce_rate_limits
from app.api.routers import auth, chat, chats, documents, health

api_router = APIRouter(dependencies=[Depends(enforce_rate_limits)])
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(chats.router)