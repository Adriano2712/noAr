import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from noar.core.config import Settings, get_settings
from noar.core.security import decode_access_token
from noar.db.models import User
from noar.db.session import async_session_factory, get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _user_from_token(token: str, session: AsyncSession, settings: Settings) -> User:
    subject = decode_access_token(token, settings.api_secret_key)
    if subject is None:
        raise _CREDENTIALS_ERROR

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise _CREDENTIALS_ERROR from None

    user = await session.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_ERROR
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    return await _user_from_token(token, session, settings)


async def get_current_user_from_query_token(
    token: str,
    settings: Settings = Depends(get_settings),
) -> User:
    """Same as `get_current_user`, but the token comes from `?token=`.

    Only for the SSE endpoint: the browser's EventSource can't set an
    Authorization header, so this is the pragmatic way to authenticate it
    (see ADR 0010). Never use this for anything else -- tokens in URLs end
    up in access logs and browser history in a way headers don't.

    Opens its own short-lived session instead of depending on `get_session`:
    that dependency stays open for the whole request, and for a streaming
    response "the request" means the entire SSE connection -- a `Depends`
    session here would hold a pooled DB connection idle for as long as the
    client stays subscribed, for no reason beyond this one lookup.
    """
    async with async_session_factory() as session:
        return await _user_from_token(token, session, settings)
