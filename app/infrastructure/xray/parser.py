import urllib.parse
from urllib.parse import parse_qs, urlparse

from app.domain.models.models import VlessKey
from app.domain.exceptions.exceptions import InvalidVlessUriError


def parse_vless_uri(uri: str) -> VlessKey:
    try:
        parsed = urlparse(uri.strip())
    except Exception as e:
        raise InvalidVlessUriError(uri, str(e))

    if parsed.scheme != "vless":
        raise InvalidVlessUriError(uri, f"scheme={parsed.scheme}, ожидался vless")

    if not parsed.hostname or not parsed.port:
        raise InvalidVlessUriError(uri, "отсутствует host или port")

    params = parse_qs(parsed.query)

    def p(key: str, default: str = "") -> str:
        return params.get(key, [default])[0]

    name = urllib.parse.unquote(parsed.fragment or "").strip()
    if not name:
        name = f"{parsed.hostname}:{parsed.port}"

    return VlessKey(
        uri=uri,
        name=name,
        host=parsed.hostname,
        port=parsed.port,
        uuid=parsed.username or "",
        security=p("security", "none"),
        sni=p("sni", parsed.hostname or ""),
        fingerprint=p("fp", "chrome"),
        public_key=p("pbk", ""),
        short_id=p("sid", ""),
        spider_x=p("spx", "/"),
        network_type=p("type", "tcp"),
        flow=p("flow", ""),
        encryption=p("encryption", "none"),
    )
