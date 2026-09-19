import json
import logging
import uuid
from pathlib import Path

from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.workers.utils import common_widget_manager
from app.core.schemas.action_result import (
    ActionResult,
    ActionResultType,
    DictionaryActionResult,
)

from app.core.services.action_handler.handler import AccessMode, ActionHandler
from app.services.data.assets.image_datasets.schemas import ImageDatasetConfig, RegionPropertiesConfig
from app.services.workflows.designer.schemas import (
    WidgetType,
)
logger = logging.getLogger(__package__)

app = create_celery_app("image_dataset_action_worker")


@app.task(name="task_image_dataset")
def task_image_dataset(action_id: str):

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.IMAGE_DATASET:
            logger.exception("Invalid action submited to IMAGE_DATASET worker")
            raise KeyError("Invalid action submited to IMAGE_DATASET worker")

        image_dataset_config: ImageDatasetConfig = widget.config
        image_dataset_config = image_dataset_config.dict()
        action_results = [
            ActionResult(
                type=ActionResultType.DICTIONARY,
                result=DictionaryActionResult(dict_value = json.dumps(image_dataset_config)),
            )
        ]

        action_result_ids = action_handler.create_action_result_records(
            action_results = action_results, outputs = widget.outputs
        )
        logger.info("widget results stored successfully")

        # save the results
        for action_result_id in action_result_ids:
            action_handler.action_success_handler(action_result_id=action_result_id)
