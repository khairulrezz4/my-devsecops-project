"""Small Python POC used to exercise the reusable CI pipeline."""


def health_check() -> dict[str, str]:
    """Return a deterministic build/test health response."""
    return {"service": "python-poc", "status": "ok"}
