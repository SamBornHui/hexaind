from fastapi import HTTPException, status
from typing import Any


class DataCatalogException(HTTPException):
    def __init__(self, detail: Any):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
