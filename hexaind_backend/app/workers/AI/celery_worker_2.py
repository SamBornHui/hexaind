import os
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import ML_ACTIONS_DEFAULT_2_QUEUE
from dotenv import load_dotenv
# from asgi_correlation_id.extensions.celery import load_correlation_ids
# from app.custom_logging import load_logging

# os.environ["OMP_NUM_THREADS"] = "1" # liniting the operations to a single thread, avoiding concurrency issues in certain scenarios.

load_dotenv()
# load_correlation_ids()
# load_logging()

tasks = [
    "app.workers.AI.gpr.worker",
    "app.workers.AI.gaussian_process_cls.worker",
    "app.workers.AI.svm.worker",
    "app.workers.AI.prediction.worker",
    "app.workers.AI.multi_polynomial_regression.worker"
]

# Initialize the Celery app
app = create_celery_app('ml_actions_2_performer', default_queue=ML_ACTIONS_DEFAULT_2_QUEUE, tasks=tasks)
