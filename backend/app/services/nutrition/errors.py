"""Errors raised by nutrition lookup clients."""


class NutritionUpstreamError(Exception):
    """Raised when an upstream nutrition API is unreachable or returns a non-2xx."""

    def __init__(self, source: str, message: str) -> None:
        super().__init__(f"[{source}] {message}")
        self.source = source
        self.message = message
