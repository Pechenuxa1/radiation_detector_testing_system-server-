import os

from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from starlette import status

api_key_header = APIKeyHeader(name="api-key", auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key == os.getenv("API_KEY"):
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
