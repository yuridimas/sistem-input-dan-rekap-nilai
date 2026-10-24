import httpx
from httpx import ASGITransport

# Compatibility shim: httpx >=0.27 removed the `app=` kwarg from AsyncClient.
# Allow tests written with the older `AsyncClient(app=app, ...)` style to work.
_original_async_client = httpx.AsyncClient


class _CompatAsyncClient(_original_async_client):
    def __init__(self, *args, app=None, **kwargs):
        if app is not None and "transport" not in kwargs:
            kwargs["transport"] = ASGITransport(app=app)
        super().__init__(*args, **kwargs)


httpx.AsyncClient = _CompatAsyncClient