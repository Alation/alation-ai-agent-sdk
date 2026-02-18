from typing import NamedTuple, Union


class ServiceAccountAuthParams(NamedTuple):
    client_id: str
    client_secret: str

    def __repr__(self) -> str:
        """Override __repr__ to redact sensitive client_secret."""
        return f"ServiceAccountAuthParams(client_id={self.client_id!r}, client_secret='***REDACTED***')"


class BearerTokenAuthParams(NamedTuple):
    token: str

    def __repr__(self) -> str:
        """Override __repr__ to redact sensitive token."""
        return "BearerTokenAuthParams(token='***REDACTED***')"


class SessionAuthParams(NamedTuple):
    session_cookie: str

    def __repr__(self) -> str:
        """Override __repr__ to redact sensitive session_cookie."""
        return "SessionAuthParams(session_cookie='***REDACTED***')"


AuthParams = Union[
    ServiceAccountAuthParams,
    BearerTokenAuthParams,
    SessionAuthParams,
]
