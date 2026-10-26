"""Kompatibilitas client ASGI untuk test backend dengan HTTPX.

Shim dipasang saat pytest mengimpor conftest agar test lama tidak perlu
diubah.
"""
import httpx
from httpx import ASGITransport

# Compatibility shim: httpx >=0.27 removed the `app=` kwarg from AsyncClient.
# Allow tests written with the older `AsyncClient(app=app, ...)` style to work.
_original_async_client = httpx.AsyncClient


class _CompatAsyncClient(_original_async_client):
    """Adaptasi app= lama tanpa menimpa transport eksplisit."""

    def __init__(self, *args, app=None, **kwargs):
        """Pasang transport ASGI bila app diberikan."""
        if app is not None and "transport" not in kwargs:
            kwargs["transport"] = ASGITransport(app=app)
        super().__init__(*args, **kwargs)


httpx.AsyncClient = _CompatAsyncClient