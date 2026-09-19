from fastapi import HTTPException, status


class JupyterServerException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "Jupyter Server Exception",
    ):
        super().__init__(
            status_code=status_code, detail={"status": status_code, "message": message}
        )


class UnAuthorizedException(JupyterServerException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="request is not authorized",
        )


class RoleAccessDeniedException(JupyterServerException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="operation is not allowed for this role",
        )


class ServerNotFoundException(JupyterServerException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, message="server doesn't exist"
        )


class ServerStillCreatingException(JupyterServerException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="server is not yet created",
        )


class ServerAlreadyExistsException(JupyterServerException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="server already exists",
        )

class JupyterNBDataNotFound(JupyterServerException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Notebooks data and their types not found!",
        )
