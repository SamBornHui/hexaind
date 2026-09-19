import os
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import ACTION_WORKER_DEFAULT_QUEUE, ML_ACTIONS_DEFAULT_QUEUE
from dotenv import load_dotenv
# from asgi_correlation_id.extensions.celery import load_correlation_ids
# from app.custom_logging import load_logging

# os.environ["OMP_NUM_THREADS"] = "1" # liniting the operations to a single thread, avoiding concurrency issues in certain scenarios.

load_dotenv()
# load_correlation_ids()
# load_logging()

tasks = [
    "app.workers.AI.automl.worker",
    "app.workers.AI.randomforest.worker",
    "app.workers.AI.linear_regression.worker",
    "app.workers.AI.lgbm.worker",
    "app.workers.AI.xgboost.worker",
    "app.workers.AI.catboost.worker",
    "app.workers.AI.extratrees.worker",
    "app.workers.AI.nn_torch.worker",
    "app.workers.AI.nnfastai.worker",
    "app.workers.AI.k_nearest_neighbors.worker",
]

# Initialize the Celery app
app = create_celery_app('ml_actions_performer', default_queue=ML_ACTIONS_DEFAULT_QUEUE, tasks=tasks)
