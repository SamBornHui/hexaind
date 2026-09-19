from celery import Celery

app = Celery('my_celery_app')
app.config_from_object('my_celery_app.celery_config')
