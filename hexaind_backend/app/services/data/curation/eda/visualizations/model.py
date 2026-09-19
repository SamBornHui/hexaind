from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Optional

import dask.dataframe as dd
from plotly.graph_objects import Figure
from pydantic import BaseModel, Field, RootModel

from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import API_JOBS_QUEUE, API_JOBS_RK
from app.core.services.action.schemas import Action, ActionRunStatus
from app.core.services.action.service import ActionService
from app.services.data.assets.datasets.schemas import ApiJobType
from app.services.data.assets.datasets.service import Dataset, DatasetsService
from app.services.data.curation.eda.utils import hash_obj
from app.services.data.curation.eda.visualizations.v1_0.model import (
    DataVisualization as DataVisualizationV1_0,
)
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import (
    ApiJobsConfig,
    ApiVisualizationConfig,
    Widget,
)

from ......config.env_vars import environment
from ....assets.datasets.schemas import Dataset
from ...data.source.model import DataSourceModel

logger = logging.getLogger(__package__)


class DataVisualization(RootModel):
    root: Annotated[DataVisualizationV1_0, Field(discriminator="version")]
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "version": "1.0",
                    "x": "x column",
                    "y": "y column",
                    "color_by": "color by column",
                    "plot_type": "DISTRIBUTION",
                }
            ]
        }
    }

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        logger.info("Returning figure from dataframe")
        figure_ = self.root.figure(dataframe=dataframe)
        # HEXAIND-8598 changing colorbar title position
        figure_.update_coloraxes(colorbar_title_side="right")
        return figure_

    def fig_from_dataset(self, dataset: Dataset) -> Figure:
        logger.info("Returing figure from the dataset.")
        return self.figure(dataframe=DataSourceModel.from_dataset(dataset).dataframe)

    @staticmethod
    def write(figure: Figure, interactive: bool, plot_path: Path):
        logger.info("Exporting the figure to a path based on the interactive type")
        figure.update_layout(margin=dict(l=0, r=0, t=25, b=0))
        if interactive:
            figure.write_html(plot_path, include_plotlyjs="cdn")
        else:
            figure.write_image(plot_path)

    @staticmethod
    def export_file(
        visualization: DataVisualization,
        dataset: Dataset,
        interactive: bool,
        dataset_service: DatasetsService,
        action_service: ActionService,
    ) -> Path:
        """
        Export a visualization for a given dataset and visualization configuration.

        This function checks if the visualization already exists, if a job is already in progress,
        or if a new job needs to be created to generate the visualization. It handles the creation
        of action records and sends tasks to the Celery worker.

        Args:
            visualization (DataVisualization): The visualization configuration.
            dataset (Dataset): The dataset associated with the visualization.
            interactive (bool): Flag indicating if the visualization is interactive.
            dataset_service (DatasetsService): Service for dataset operations.
            action_service (ActionService): Service for action operations.

        Returns:
            DataVizResponse: A response object containing the filepath of the visualization (if exists)
            and the visualization job ID.
        """

        logger.info(
            "Starting export_file for dataset ID: %s", getattr(dataset, "id", "Unknown")
        )

        if not dataset:
            raise ValueError("Dataset is required to export the visualization.")

        # Add interactive flag to the visualization to compute the hash
        visualization.root.root.interactive = interactive
        visualization_hash = hash_obj(visualization)
        logger.debug("Computed visualization hash: %s", visualization_hash)

        # Check if the visualization path is already present in the dataset
        visualization_path = dataset.visualization_paths.get(visualization_hash)
        if visualization_path and Path(visualization_path).exists():
            logger.info("Visualization already exists at path: %s", visualization_path)
            return DataVizResponse(
                filepath=Path(visualization_path), visualization_job_id=None
            )

        # Check if a job is already created for the visualization
        visualization_job_id = dataset.visualization_job_ids.get(visualization_hash)
        if visualization_job_id:
            logger.info(
                "Visualization job already exists with ID: %s", visualization_job_id
            )
            action_record = dataset_service.get_api_job_action_record_sync(
                api_job_id=visualization_job_id
            )
            action_status = action_record.status if action_record else None
            logger.debug(
                "Action status for job ID %s: %s", visualization_job_id, action_status
            )
            if action_status in [ActionRunStatus.RUNNING, ActionRunStatus.SCHEDULED]:
                logger.info("Visualization job is already in progress.")
                return DataVizResponse(
                    filepath=None, visualization_job_id=visualization_job_id
                )
            # elif action_status == ActionRunStatus.IDLE:
            #     logger.info(
            #         "Visualization job is in IDLE state. Resending task to worker."
            #     )
            #     DataVisualization._send_visualization_task_to_worker(
            #         action_id=action_record.id
            #     )
            #     return DataVizResponse(
            #         filepath=None, visualization_job_id=visualization_job_id
            #     )
            # elif action_status == ActionRunStatus.SUCCEEDED:
            #     logger.info(
            #         "Previous visualization job succeeded but file is not present. Creating new task and sending it to worker."
            #     )
            elif action_status == ActionRunStatus.FAILED:
                raise Exception(f"Previous visualization job with ID {visualization_job_id} failed.")
            # else:
            #     error_msg = (
            #         f"Error in generating the visualization for dataset {dataset.id} and visualization {visualization}. "
            #         f"Action status: {action_status}"
            #     )
            #     logger.error(error_msg)
            #     raise ValueError(error_msg)

        # Create a new action for the visualization
        logger.info("Creating new action for visualization.")
        action_config = Widget(
            urn="",
            name=f"Visualization_{dataset.id}_{visualization_hash}",
            description=f"Visualization generation for dataset id {dataset.id}",
            type=WidgetType.API_JOBS,
            config=ApiJobsConfig(
                config=ApiVisualizationConfig(
                    job_type=ApiJobType.VISUALIZATION,
                    dataset_id=str(dataset.id),
                    visualization=visualization.root.root,
                    visualization_hash=visualization_hash,
                ),
                widget_type=WidgetType.API_JOBS,
            ),
        )
        action = Action(
            run_id="",
            action_config=action_config,
            status=ActionRunStatus.IDLE,
        )
        action_ids = action_service.create_actions_sync(actions=[action])
        logger.info("Action created with ID: %s", action_ids[0])

        # save the job id in the dataset record
        api_job_id = dataset_service.save_api_jobs_record_sync(
            dataset_id=dataset.id,
            user_id=dataset.user_id,
            action_id=action_ids[0],
            job_type=ApiJobType.VISUALIZATION,
            visualization_hash=visualization_hash,
        )
        dataset.visualization_job_ids.update({visualization_hash: api_job_id})
        dataset_service.update_dataset_record_data_sync(
            dataset_id=str(dataset.id),
            key_to_update="visualization_job_ids",
            data=dataset.visualization_job_ids,
        )
        logger.info("Job ID %s saved in dataset record.", api_job_id)

        # send the job to the celery worker
        celeryApp = create_celery_app("eda_generator")
        celeryApp.send_task(
            "task_eda_generate_visualization",
            kwargs={"action_id": action_ids[0]},
            queue=API_JOBS_QUEUE,
            routing_key=API_JOBS_RK,
        )


        return DataVizResponse(filepath=None, visualization_job_id=api_job_id)


class DataVizResponse(BaseModel):
    filepath: Optional[Path]
    visualization_job_id: Optional[str]
