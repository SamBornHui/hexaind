from app.core.celery import global_config
import celery

# Injecting logging into worker init
from asgi_correlation_id.extensions.celery import load_correlation_ids
from app.custom_logging import load_logging

load_correlation_ids()
load_logging()


_app = None

def create_celery_app(name, default_queue=None, tasks=None):

    global _app

    if _app is None:
        # Initialize the Celery app with the configuration file
        if tasks:
            _app = celery.Celery(name, include=tasks)

        else:
            _app = celery.Celery(name)

        _app.config_from_object(global_config)

        _app.conf.task_queues = global_config.task_queues

        _app.conf.result_backend = global_config.celery_result_backend_url

        _app.conf.task_ignore_result = True
        
        _app.conf.result_expires = 3600  # results will expire after 1 hour
 
        if default_queue:
            _app.conf.task_default_queue = default_queue

    return _app
    
