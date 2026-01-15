from typing import NamedTuple, Union


class ServiceAccountAuthParams(NamedTuple):
    client_id: str
    client_secret: str


class BearerTokenAuthParams(NamedTuple):
    token: str


class SessionAuthParams(NamedTuple):
    session_cookie: str


AuthParams = Union[
    ServiceAccountAuthParams,
    BearerTokenAuthParams,
    SessionAuthParams,
]
