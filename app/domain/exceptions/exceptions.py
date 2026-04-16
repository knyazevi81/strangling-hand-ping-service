class PingServiceError(Exception):
    pass


class InvalidVlessUriError(PingServiceError):
    def __init__(self, uri: str, reason: str) -> None:
        super().__init__(f"Невалидный VLESS URI [{uri[:40]}]: {reason}")


class XrayNotFoundError(PingServiceError):
    def __init__(self) -> None:
        super().__init__("xray бинарник не найден")


class XrayStartError(PingServiceError):
    def __init__(self, timeout: float) -> None:
        super().__init__(f"xray не запустился за {timeout} сек")
