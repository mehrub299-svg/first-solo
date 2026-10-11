import asyncio

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DUMMY_HASH, hash_password, verify_password
from app.models.user import User
from app.services.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    UserNotFound,
)
from app.services.tokens import TokenPair, TokenService


class AuthService:
    def __init__(self, session: AsyncSession, tokens: TokenService) -> None:
        self._session = session
        self._tokens = tokens

    async def register(self, email: str, password: str) -> User:
        hashed = await asyncio.to_thread(hash_password, password)
        user = User(email=self._normalize(email), hashed_password=hashed)
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise EmailAlreadyRegistered()
        await self._session.refresh(user)
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._get_by_email(email)
        if user is None:
            await asyncio.to_thread(verify_password, password, DUMMY_HASH)
            raise InvalidCredentials()
        valid = await asyncio.to_thread(verify_password, password, user.hashed_password)
        if not valid:
            raise InvalidCredentials()
        return await self._tokens.issue_pair(user.id)

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        return await self._tokens.rotate(raw_refresh_token)

    async def logout(self, raw_refresh_token: str) -> None:
        await self._tokens.revoke(raw_refresh_token)

    async def get_user(self, user_id: int) -> User:
        user = await self._session.get(User, user_id)
        if user is None:
            raise UserNotFound()
        return user

    async def _get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == self._normalize(email))
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _normalize(email: str) -> str:
        return email.strip().lower()