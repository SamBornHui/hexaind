from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from enum import Enum, auto
from typing import Any


class API(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return name.lower()

    WORKFLOW = auto()
    MLFLOW = auto()
    THERMOCALC = auto()
    AUX = auto()
    MICRON = auto()
    GATEWAY = auto()


class Worker(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return name.lower()

    ACTION_MANAGER = auto()
    ACTION_WORKER = auto()
    AUX = auto()
    MOBO = auto()
    THERMOCALC = auto()
    ACTIVE_LEARNING = auto()
    ML = auto()
    ML2 = auto()
    RESCALE = auto()
    EVENTS_MANAGER = auto()
    CUSTOM_CODE = auto()
    THERMOCALC_EXTERNAL = auto()
    MICRON = auto()
    EXTERNAL_DATA = auto()


class Init(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return name.lower()

    DB = auto()
    MICRON = auto()


def main():
    parser = ArgumentParser(prog="hexaind", formatter_class=ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(required=True)

    api_parser = subparsers.add_parser(name="api")
    api_parser.add_argument("api", type=API, choices=[e.value for e in API])
    api_parser.add_argument("--host", "-H", type=str, default="0.0.0.0")
    api_parser.add_argument("--port", "-p", type=int, default=8000)
    api_parser.add_argument("--workers", "-w", type=int, default=1)
    api_parser.add_argument("--reload", "-r", action="store_true", default=False)

    worker_parser = subparsers.add_parser(name="worker")
    worker_parser.add_argument("worker", choices=[e.value for e in Worker])

    init_parser = subparsers.add_parser(name="init")
    init_parser.add_argument("init", choices=[e.value for e in Init])

    args = parser.parse_args()

    if "api" in args:  # api
        import uvicorn

        api: API = args.api
        match api:
            case API.WORKFLOW | API.AUX | API.MICRON:
                app = "app.main:app"
            case API.MLFLOW:
                app = "app.model_builder_apis:app"
            case API.THERMOCALC:
                app = "app.thermocalc_apis:app"
            case API.GATEWAY:
                app = "app.api.gateway:app"
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
        )
    elif "worker" in args:  # worker
        worker: Worker = args.worker
        match worker:
            case Worker.ACTION_MANAGER:
                from app.core.services.action_manager.worker import app as celery_app

                celery_queue = "start_end"
                celery_pool = "prefork"
            case Worker.ACTION_WORKER:
                from app.workers.celery_worker import app as celery_app

                celery_queue = "actions"
                celery_pool = "prefork"
            case Worker.AUX:
                from app.workers.data_curation.data_eda.worker import app as celery_app

                celery_queue = "api_jobs_queue"
                celery_pool = "prefork"
            case Worker.MOBO:
                from app.workers.AI.mobo.worker import app as celery_app

                celery_queue = "mobo_actions"
                celery_pool = "prefork"
            case Worker.THERMOCALC:
                from app.workers.AI.thermocalc.worker import app as celery_app

                celery_queue = "thermocalc_actions"
                celery_pool = "prefork"
            case Worker.ACTIVE_LEARNING:
                from app.workers.AI.active_learning.worker import app as celery_app

                celery_queue = "active_learning_actions"
                celery_pool = "solo"
            case Worker.ML:
                from app.workers.AI.celery_worker import app as celery_app

                celery_queue = "ml_actions"
                celery_pool = "prefork"
            case Worker.ML2:
                from app.workers.AI.celery_worker_2 import app as celery_app

                celery_queue = "ml_actions_2"
                celery_pool = "prefork"
            case Worker.RESCALE:
                from app.workers.AI.rescale.worker import app as celery_app

                celery_queue = "rescale_actions"
                celery_pool = "prefork"
            case Worker.EVENTS_MANAGER:
                from app.workers.scheduling.worker import app as celery_app

                celery_queue = "events_queue"
                celery_pool = "solo"
            case Worker.CUSTOM_CODE:
                from app.workers.custom_code.worker import app as celery_app

                celery_queue = "custom_code_actions"
                celery_pool = "prefork"
            case Worker.THERMOCALC_EXTERNAL:
                import os
                import subprocess

                thermocalc_wheel = os.getenv("THERMOCALC_WHL_FILE")
                if thermocalc_wheel is not None and thermocalc_wheel != "NONE":
                    subprocess.run(["pip", "install", thermocalc_wheel])

                from app.workers.AI.thermocalc.task_worker import app as celery_app

                celery_queue = "thermocalc_sub_actions"
                celery_pool = "prefork"
            case Worker.MICRON:
                from app.workers.micron.worker import app as celery_app

                celery_queue = "data_catalog"
                celery_pool = "prefork"
        celery_args = [
            "worker",
            f"--queues={celery_queue}",
            f"--pool={celery_pool}",
            "--loglevel=INFO",
        ]
        celery_app.worker_main(celery_args)
    elif "init" in args:  # init
        init: Init = args.init
        match init:
            case Init.DB:
                import asyncio

                from app.init_db import main as init_db_main

                asyncio.run(init_db_main())
            case Init.MICRON:
                from app.init_micron import main as init_micron_main

                init_micron_main()


if __name__ == "__main__":
    main()
