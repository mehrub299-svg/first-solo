import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.refresh_token import RefreshToken
from app.services.exceptions import InvalidRefreshToken


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class TokenService:
    def __init__(
        self,
        session: AsyncSession,
        refresh_ttl: timedelta,
        reuse_grace: timedelta,
    ) -> None:
        self._session = session
        self._refresh_ttl = refresh_ttl
        self._reuse_grace = reuse_grace

    async def issue_pair(self, user_id: int) -> TokenPair:
        """Start a new session (a new token family), e.g. on login."""
        now = datetime.now(timezone.utc)
        await self._session.execute(
            delete(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.expires_at < now
            )
        )
        pair = self._stage_pair(user_id, secrets.token_hex(16), now)
        await self._session.commit()
        return pair

    async def rotate(self, raw_token: str) -> TokenPair:
        record = await self._find(raw_token)
        now = datetime.now(timezone.utc)
        if record is None or record.revoked_at is not None or record.expires_at <= now:
            raise InvalidRefreshToken()

        if record.rotated_at is None:
            record.rotated_at = now
        elif now - record.rotated_at > self._reuse_grace:
            # An old token that was already swapped has come back: assume it
            # leaked and end the whole session family.
            await self._revoke_family(record.family_id, now)
            raise InvalidRefreshToken()
        # Otherwise it was rotated moments ago (two tabs refreshing at once), so
        # hand out another fresh pair in the same family instead of logging out.

        pair = self._stage_pair(record.user_id, record.family_id, now)
        await self._session.commit()
        return pair

    async def revoke(self, raw_token: str) -> None:
        record = await self._find(raw_token)
        if record is not None:
            await self._revoke_family(record.family_id, datetime.now(timezone.utc))

    def _stage_pair(self, user_id: int, family_id: str, now: datetime) -> TokenPair:
        raw = generate_refresh_token()
        self._session.add(
            RefreshToken(
                user_id=user_id,
                token_hash=hash_refresh_token(raw),
                family_id=family_id,
                expires_at=now + self._refresh_ttl,
            )
        )
        return TokenPair(access_token=create_access_token(str(user_id)), refresh_token=raw)

    async def _find(self, raw_token: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(raw_token)
            )
        )
        return result.scalar_one_or_none()

    async def _revoke_family(self, family_id: str, now: datetime) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self._session.commit()