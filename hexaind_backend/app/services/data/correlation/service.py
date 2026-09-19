import logging
from pathlib import Path

import numpy as np
import plotly.graph_objs as go
from dask.dataframe import DataFrame

from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import API_JOBS_QUEUE, API_JOBS_RK
from app.core.services.action.schemas import Action, ActionRunStatus
from app.core.services.action.service import ActionService
from app.services.data.assets.datasets.schemas import ApiJobType, DatasetType
from app.services.data.assets.datasets.service import Dataset, DatasetsService
from app.services.data.correlation.schemas import (
    CorrelationInputSchema,
    CorrelationResponse,
    CorrHeatmap,
)
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.data.curation.eda.utils import hash_obj
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import (
    ApiCorrelationConfig,
    ApiJobsConfig,
    Widget,
)

logger = logging.getLogger(__package__)


class CorrelationService:

    @staticmethod
    def get_correlation(
        corr_schema: CorrelationInputSchema,
        dataset_service: DatasetsService,
        action_service: ActionService,
    ) -> CorrelationResponse:
        """
        Get or generate correlation data for a given dataset and correlation schema.

        This function checks if the correlation data already exists, if a job is already in progress,
        or if a new job needs to be created to compute the correlation. It handles the creation of action
        records and sends tasks to the Celery worker.

        Args:
            corr_schema (CorrelationInputSchema): The schema defining the correlation computation parameters.
            dataset_service (DatasetsService): Service for dataset operations.
            action_service (ActionService): Service for action operations.

        Returns:
            CorrelationResponse: A response object containing the correlation heatmap (if exists) and the correlation job ID.
        """

        logger.info(
            "Starting get_correlation for dataset ID: %s", corr_schema.dataset_id
        )

        dataset: Dataset = dataset_service.get_dataset_by_id_sync(
            corr_schema.dataset_id
        )

        if not dataset:
            raise Exception(f"Dataset with id {corr_schema.dataset_id} not found.")

        # Compute the hash of corr_schema
        correlation_hash = hash_obj(object=corr_schema)
        logger.debug("Computed correlation hash: %s", correlation_hash)

        # check if data already exists for the corr_schema
        corr_plot_path = dataset.correlation_paths.get(correlation_hash)
        if corr_plot_path and Path(corr_plot_path).exists():
            logger.info("Correlation data already exists at path: %s", corr_plot_path)
            return CorrelationResponse(
                file_path=corr_plot_path, correlation_job_id=None, corr_heatmap=None
            )

        # check if a job is already created for computing correlation
        corr_job_id = dataset.correlation_job_ids.get(correlation_hash)
        if corr_job_id:
            logger.info("Correlation job already exists with ID: %s", corr_job_id)
            action_record = dataset_service.get_api_job_action_record_sync(
                api_job_id=corr_job_id
            )
            action_status = action_record.status if action_record else None
            logger.debug("Action status for job ID %s: %s", corr_job_id, action_status)
            if action_status in [ActionRunStatus.RUNNING, ActionRunStatus.SCHEDULED]:
                logger.info("Correlation job is already in progress.")
                return CorrelationResponse(
                    correlation_job_id=corr_job_id, corr_heatmap=None, file_path=None
                )
            # elif action_status == ActionRunStatus.IDLE:
            #     logger.info(
            #         "Correlation job is in IDLE state. Resending task to worker."
            #     )
            #     CorrelationService._send_correlation_task_to_worker(action_record.id)
            #     return CorrelationResponse(
            #         corr_heatmap=None, correlation_job_id=corr_job_id
            #     )
            # elif action_status == ActionRunStatus.SUCCEEDED:
            #     logger.info(
            #         "Previous correlation job succeeded but data file is not present. Creating new task and sending it to worker."
            #     )
            elif action_status == ActionRunStatus.FAILED:
                raise Exception(
                    f"Correlation job with ID {corr_job_id} failed."
                )
            # else:
            #     error_msg = (
            #         f"Error in generating the correlation data for dataset {dataset.id} and correlation config {corr_schema}. "
            #         f"Action status: {action_status}"
            #     )
            #     logger.error(error_msg)
            #     raise ValueError(error_msg)

        # create a new action for computing correlation data.
        logger.info("Creating new action for correlation data.")
        action_config = Widget(
            urn="",
            name=f"Correlation_{dataset.id}_{correlation_hash}",
            description=f"Correlation data generation for dataset id {dataset.id}",
            type=WidgetType.API_JOBS,
            config=ApiJobsConfig(
                config=ApiCorrelationConfig(
                    job_type=ApiJobType.CORRELATION,
                    dataset_id=str(dataset.id),
                    correlation_schema=corr_schema,
                    correlation_hash=correlation_hash,
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
            job_type=ApiJobType.CORRELATION,
            correlation_hash=correlation_hash,
        )
        dataset.correlation_job_ids.update({correlation_hash: api_job_id})
        dataset_service.update_dataset_record_data_sync(
            dataset_id=str(dataset.id),
            key_to_update="correlation_job_ids",
            data=dataset.correlation_job_ids,
        )
        logger.info("Job ID %s saved in dataset record.", api_job_id)

        # send the job to the celery worker
        celeryApp = create_celery_app("eda_generator")
        celeryApp.send_task(
            "task_eda_generate_correlation",
            kwargs={"action_id": action_ids[0]},
            queue=API_JOBS_QUEUE,
            routing_key=API_JOBS_RK,
        )

        return CorrelationResponse(
            correlation_job_id=api_job_id, corr_heatmap=None, file_path=None
        )

    @staticmethod
    def correlation(
        corr_schema: CorrelationInputSchema, dataset: Dataset
    ) -> CorrelationResponse:
        columns = corr_schema.columns
        min_periods = corr_schema.min_period
        clip_percentiles = corr_schema.clip_percentiles
        symmetric_bounds = corr_schema.symmetric_bounds

        if dataset.dataset_type != DatasetType.TABULAR:
            raise Exception(
                f"The provided dataset is not {DatasetType.TABULAR}. Not possible to provide a correlation heatmap."
            )

        ds_model: DataSourceModel = DataSourceModel.from_dataset(dataset)
        ddf_analysis = ds_model.dataframe.replace([np.nan, np.inf, -np.inf], 0)

        if columns or len(columns) > 0:
            ddf_analysis = ddf_analysis[columns]

        return CorrelationService.get_heatmap(
            ddf_analysis, min_periods, clip_percentiles, symmetric_bounds
        )

    @staticmethod
    def get_heatmap(
        ddf: DataFrame,
        min_periods: int,
        clip_percentiles: float,
        symmetric_bounds: bool,
    ) -> CorrelationResponse:

        corr = ddf.corr(method="pearson", min_periods=min_periods).fillna(
            0
        )  # Since we are considering only numeric data
        corr = corr.replace([np.nan, np.inf, -np.inf], 0)
        corr = corr.compute()
        corr_values = np.abs(corr.values.flatten())

        if symmetric_bounds:
            vmax = np.nanpercentile(corr_values, clip_percentiles)
            vmin = -vmax
        else:
            vmin, vmax = np.nanpercentile(
                corr_values, [100 - clip_percentiles, clip_percentiles]
            )

        corr_heatmap = CorrHeatmap(
            columns=corr.columns.to_list(),
            heatmap_data_z=corr.round(2).to_numpy().tolist(),
            vmin=vmin,
            vmax=vmax,
        )

        return CorrelationResponse(
            corr_heatmap=corr_heatmap, correlation_job_id=None, file_path=None
        )

    @staticmethod
    def generate_heatmap_plot(corr_heatmap: CorrHeatmap, output_file_path: str) -> str:
        """
        Generates a heatmap plot from the given correlation heatmap data and saves it as an HTML file.
        Args:
            corr_heatmap (CorrHeatmap): An instance of CorrHeatmap containing the heatmap data.
            output_file_path (str): The file path where the heatmap plot will be saved.
        Returns:
            str: The file path where the heatmap plot was saved.
        """

        def create_annotations(data):
            annotations = []
            for i in range(len(data["z"])):
                for j in range(len(data["z"][i])):
                    if not np.isnan(data["z"][i][j]):  # Skip NaN values
                        annotations.append(
                            dict(
                                x=data["x"][j],
                                y=data["y"][i],
                                text=str(data["z"][i][j]),
                                xref="x",
                                yref="y",
                                showarrow=False,
                                font=dict(family="Arial", size=12, color="white"),
                            )
                        )
            return annotations

        # Mask the upper diagonal and diagonal elements
        mask = np.triu(np.ones_like(corr_heatmap.heatmap_data_z, dtype=bool))
        masked_z = np.where(mask, np.nan, corr_heatmap.heatmap_data_z)

        # Define the new colorscale
        colorscale = [
            [0.0, 'rgb(127, 59, 8)'],
            [0.1, 'rgb(179, 88, 6)'],
            [0.2, 'rgb(224, 130, 20)'],
            [0.3, 'rgb(253, 184, 99)'],
            [0.4, 'rgb(254, 224, 182)'],
            [0.5, 'rgb(247, 247, 247)'],
            [0.6, 'rgb(216, 218, 235)'],
            [0.7, 'rgb(178, 171, 210)'],
            [0.8, 'rgb(128, 115, 172)'],
            [0.9, 'rgb(84, 39, 136)'],
            [1.0, 'rgb(45, 0, 75)']
        ]

        # Create the heatmap trace
        heatmap = go.Heatmap(
            x=corr_heatmap.columns,
            y=corr_heatmap.columns,
            z=masked_z,
            colorscale=colorscale,
            zmin=corr_heatmap.vmin,
            zmax=corr_heatmap.vmax,
            colorbar=dict(title="Correlation"),
        )

        # Create annotations
        annotations = create_annotations(
            {"x": corr_heatmap.columns, "y": corr_heatmap.columns, "z": masked_z}
        )

        # Truncate column names for axes
        max_name_length = 23
        truncated_columns = [
            col[:max_name_length] + "..." if len(col) > max_name_length else col
            for col in corr_heatmap.columns
        ]

        # Define the layout
        layout = go.Layout(
            xaxis=dict(
                ticks="",
                side="bottom",
                title="Columns",
                tickvals=corr_heatmap.columns,
                ticktext=truncated_columns
            ),
            yaxis=dict(
                ticks="",
                ticksuffix=" ",
                showticklabels=True,
                title="Columns",
                autorange="reversed",
                tickvals=corr_heatmap.columns,
                ticktext=truncated_columns
            ),
            margin=dict(l=10, r=10, t=10, b=10),
            autosize=True,
            annotations=annotations,
        )

        # Create the figure
        fig = go.Figure(data=[heatmap], layout=layout)

        # Save the figure as an interactive HTML file
        fig.write_html(output_file_path, include_plotlyjs="cdn")
        logger.info(f"Heatmap plot saved to {output_file_path}")

        return output_file_path
