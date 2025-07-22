from typing import NamedTuple, Union, Any
from typing_extensions import TypedDict


class UserAccountAuthParams(NamedTuple):
    user_id: int
    refresh_token: str


class ServiceAccountAuthParams(NamedTuple):
    client_id: str
    client_secret: str


AuthParams = Union[UserAccountAuthParams, ServiceAccountAuthParams]


class CatalogAssetMetadataPayloadItem(TypedDict):
    oid: str
    otype: str  # Only 'glossary_v3' or 'glossary_term'
    field_id: int  # Only 3 (TEXT) or 4 (RICH_TEXT)
    value: Any  # Accept any type, validated by field_id -> type mapping
