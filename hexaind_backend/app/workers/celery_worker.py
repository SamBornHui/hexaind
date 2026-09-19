import os
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import ACTION_WORKER_DEFAULT_QUEUE
from dotenv import load_dotenv
# from asgi_correlation_id.extensions.celery import load_correlation_ids
# from app.custom_logging import load_logging

os.environ["OMP_NUM_THREADS"] = "1" # liniting the operations to a single thread, avoiding concurrency issues in certain scenarios.

load_dotenv()
# load_correlation_ids()
# load_logging()

tasks = [
    "app.workers.data_copy.bigquery.worker", 
    "app.workers.data_curation.data_filter.worker", 
    "app.workers.save.save_results.worker", 
    "app.workers.AI.machine_learning.worker", 
    "app.workers.loops.loop_start.worker", 
    "app.workers.loops.loop_end.worker", 
    #"app.workers.AI.mobo.worker", 
    #"app.workers.AI.rescale.worker",
    #"app.workers.AI.thermocalc.worker",
    "app.workers.data_curation.data_append.worker",
    "app.workers.data_curation.data_join.worker",
    "app.workers.data_curation.data_drop_missing.worker",
    "app.workers.data_curation.data_drop_columns.worker",
    "app.workers.data_curation.data_rename_columns.worker",
    "app.workers.data_curation.datatype_conversion.worker",
    "app.workers.data_curation.data_eda.worker",
    "app.workers.image_analysis.dataset_selection.worker",
    "app.workers.image_analysis.region_properties.worker",
    "app.workers.image_analysis.spatial_statistics.worker",
    "app.workers.data_copy.data_pull_sql.worker",
    "app.workers.jupyterhub.widget",
]

# Initialize the Celery app
app = create_celery_app('action_performer', default_queue=ACTION_WORKER_DEFAULT_QUEUE, tasks=tasks)
