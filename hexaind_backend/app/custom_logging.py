from contextvars import ContextVar
from logging import Filter, Handler, LogRecord
from logging.config import dictConfig
from fastapi import Request
from hashlib import md5

from app.config.env_vars import environment
from app.services.workflows.designer.schemas import Widget
from app.core.services.action.schemas import Action

ctx_request = ContextVar("request", default=None)
ctx_widget = ContextVar("worker", default=None)
ctx_action = ContextVar("action_id", default=None)
ctx_action_record = ContextVar("action_record", default=None)
ctx_user = ContextVar("user_data", default=None)


class ActivityCustomHandler(Handler):

    def __init__(self, identifier: str) -> None:
        super().__init__()
        self.identifier = identifier

    def emit(self, record: LogRecord) -> None:
        message = self.format(record)
        if (unique_id := record.correlation_id) is not None:
            file = environment.validation_logs_folder / f"{unique_id}.log"
            with file.open("a") as file_io:
                file_io.write(message + "\n")


class ValidationLogsFilter(Filter):
    def __init__(self):
        super().__init__()

    def filter(self, record):
        request: Request = ctx_request.get()
        if request is None:
            return False
        projectId = request.path_params.get("projectId")
        siteId = request.path_params.get("siteId")
        return (
            request.url.path
            == f"/v1/sites/{siteId}/projects/{projectId}/assets/custom_python_code_builder/validate_custom_code"
        )


class APIInjectingFilter(Filter):

    def __init__(self):
        super().__init__()

    def filter(self, record):
        request: Request = ctx_request.get()
        if request is not None:
            record.project_id = request.path_params.get("projectId")
            record.site_id = request.path_params.get("siteId")
            record.client_ip = request.client.host
            auth_token = request.headers.get("Authorization", "Bearer None").split(" ")[
                1
            ]
            record.session_token = md5(string=auth_token.encode()).hexdigest()

        return True


class UserInjectingFilter(Filter):
    def __init__(self):
        super().__init__()

    def filter(self, record):
        user = ctx_user.get()
        if user is not None:
            record.user_email = user.get("email")
            record.user_id = user.get("user_id")
        return True


class WorkerInjectingFilter(Filter):

    def __init__(self):
        super().__init__()

    def filter(self, record):
        widget: Widget = ctx_widget.get()
        if widget is not None:
            record.widget_type = widget.type
            record.widget_state = widget.state
            record.widget_urn = widget.urn
        action = ctx_action.get()
        if action is not None:
            """Please don't confuse with name here, this is not action, this is run not action record"""
            record.workflow_id = action.workflow_id
            record.project_id = action.project_id
            record.run_status = action.run_status
            record.run_id = action.id
            record.recent_run = action.recent_run_created_at

        action_record: Action = ctx_action_record.get()
        if action_record is not None:
            record.action_id = action_record.id
            record.action_status = action_record.status

        return True


logging_config_data = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "brief": {
            "format": "%(levelname)s: %(asctime)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "timestamp: %(asctime)s level:[%(levelname)s] - package: %(name)s - filename: %(filename)s - func: %(funcName)s - line: %(lineno)s - message: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": """
                time: %(asctime)s
                level: %(levelname)s
                message: %(message)s
                exc_info: %(exc_info)s
                pathname: %(pathname)s
                filename: %(filename)s
                lineno: %(lineno)d
                package: %(name)s
                funcName: %(funcName)s
            """,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "api_injection_filter": {"()": "app.custom_logging.APIInjectingFilter"},
        "worker_injection_filter": {"()": "app.custom_logging.WorkerInjectingFilter"},
        "correlation_id_filter": {
            "()": "asgi_correlation_id.CorrelationIdFilter",
            "default_value": "-",
        },
        "user_data_filter": {"()": "app.custom_logging.UserInjectingFilter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
        "api_file": {
            "class": "logging.FileHandler",
            "formatter": "json",
            "level": "DEBUG",
            "filename": f"{environment.logs_folder}/api.log",
            "filters": [
                "api_injection_filter",
                "user_data_filter",
                "correlation_id_filter",
            ],
        },
        "service_file": {
            "class": "logging.FileHandler",
            "formatter": "json",
            "level": "DEBUG",
            "filename": f"{environment.logs_folder}/services.log",
            "filters": [
                "api_injection_filter",
                "worker_injection_filter",
                "user_data_filter",
                "correlation_id_filter",
            ],
        },
        "worker_file": {
            "class": "logging.FileHandler",
            "formatter": "json",
            "level": "DEBUG",
            "filename": f"{environment.logs_folder}/workers.log",
            "filters": [
                "worker_injection_filter",
                "user_data_filter",
                "correlation_id_filter",
            ],
        },
        "custom_handler": {
            "class": "app.custom_logging.ActivityCustomHandler",
            "formatter": "brief",
            "level": "INFO",
            "identifier": "hello",
            "filters": ["correlation_id_filter"],
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO"},
        "app": {
            "handlers": ["api_file", "console"],
            "propagate": False,
            "level": "DEBUG",
        },
        "app.api": {
            "handlers": ["console", "api_file"],
            "propagate": False,
            "level": "DEBUG",
        },
        "app.services": {
            "handlers": ["console", "service_file"],
            "propagate": False,
            "level": "DEBUG",
        },
        "app.workers": {
            "handlers": ["console", "worker_file"],
            "propagate": False,
            "level": "DEBUG",
        },
    },
}


def load_logging():
    try:
        dictConfig(logging_config_data)
    except Exception as e:
        raise ValueError("Unable to load logging config") from e
