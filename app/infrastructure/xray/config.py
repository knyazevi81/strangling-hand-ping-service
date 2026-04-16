import json
from app.domain.models.models import VlessKey


def build_xray_config(key: VlessKey, socks_port: int) -> dict:
    stream: dict = {"network": key.network_type, "security": key.security}

    if key.security == "reality":
        stream["realitySettings"] = {
            "serverName": key.sni,
            "fingerprint": key.fingerprint,
            "publicKey": key.public_key,
            "shortId": key.short_id,
            "spiderX": key.spider_x,
        }
    elif key.security == "tls":
        stream["tlsSettings"] = {
            "serverName": key.sni,
            "fingerprint": key.fingerprint,
        }

    if key.network_type == "grpc":
        stream["grpcSettings"] = {"serviceName": "xyz"}

    return {
        "log": {"loglevel": "none"},
        "inbounds": [
            {
                "port": socks_port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"auth": "noauth", "udp": False},
            }
        ],
        "outbounds": [
            {
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": key.host,
                            "port": key.port,
                            "users": [
                                {
                                    "id": key.uuid,
                                    "encryption": key.encryption,
                                    "flow": key.flow,
                                }
                            ],
                        }
                    ]
                },
                "streamSettings": stream,
            }
        ],
    }


def config_to_json(cfg: dict) -> str:
    return json.dumps(cfg, ensure_ascii=False)
