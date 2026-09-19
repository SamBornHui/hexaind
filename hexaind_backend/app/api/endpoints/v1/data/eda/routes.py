import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, PositiveInt
from pymongo import MongoClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.config.env_vars import environment
from app.config.redis_config import AsyncRedis, get_async_redis_client
from app.core.services.action.service import ActionService
from app.services.data.correlation.schemas import (
    CorrelationFailureResponse,
    CorrelationInputSchema,
    CorrelationSuccessResponse,
)
from app.services.data.correlation.service import CorrelationService

from ......core.db.db_utils import close_db_sync, get_db_async, get_db_sync
from ......services.data.assets.datasets.schemas import Dataset
from ......services.data.assets.datasets.service import DatasetsService
from ......services.data.curation.eda.metadata.model import DataMetadata
from ......services.data.curation.eda.preview.model import DataPreview
from ......services.data.curation.eda.statistics.model import DataStatistics
from ......services.data.curation.eda.visualizations.model import (
    DataVisualization,
    DataVizResponse,
)
from app.actions import Actions
logger = logging.getLogger(__package__)

router = APIRouter(
    prefix="/v1/sites/{site_id}/projects/{project_id}/eda",
    tags=["EDA"],
    route_class=CheckNameRoute,
)


class Message(BaseModel):
    message: str


@router.get(
    "/preview",
    responses={
        status.HTTP_200_OK: {"model": DataPreview},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
    openapi_extra={"actions":Actions.Preview_Dataset_Result.value},

)
def get_preview(
    site_id: str,
    project_id: str,
    dataset_id: str,
    page: PositiveInt = 1,
    page_size: PositiveInt = 100,
    client: MongoClient = Depends(get_db_sync),
):
    """
    This API method is used for getting the preview data of the given dataset

    Args:
        site_id (str): site id of the user
        project_id (str): project id of the project user is using
        dataset_id (str): dataset id of the tabular dataset
        client (MongoClient, optional): _description_. Defaults to Depends(get_db_sync).

    Raises:
        HTTPException: KeyError
        HTTPException: Exception

    Returns:
        _type_: _description_
    """
    try:
        dataset_service_sync = DatasetsService(db_sync_client=client)
        action_service = ActionService(db_sync_client=client)

        dataset: Dataset = dataset_service_sync.get_dataset_by_id_sync(dataset_id)

        return DataPreview.from_db(
            dataset=dataset,
            page=page,
            page_size=page_size,
            dataset_service=dataset_service_sync,
            action_service=action_service,
        )

        # return DataPreview.from_dataset(dataset, page=page, page_size=page_size)

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Message(message=str(e)).model_dump(),
        )
    except Exception as e:
        logger.exception(f"Unabel to preview - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Message(message=str(e)).model_dump(),
        )
    finally:
        close_db_sync(client=client)


@router.get(
    "/statistics",
    responses={
        status.HTTP_200_OK: {"model": DataStatistics},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
)
def get_statistics(
    site_id: str,
    project_id: str,
    dataset_id: str,
    client: MongoClient = Depends(get_db_sync),
):
    """
    This methos is used for getting the statistics of the given dataset.

    Args:
        site_id (str): site id of the user
        project_id (str): project id of the project user is using
        dataset_id (str): dataset id of the tabular dataset
        client (MongoClient, optional): _description_. Defaults to Depends(get_db_sync).

    Raises:
        HTTPException: KeyError
        HTTPException: Exception

    Returns:
        _type_: _description_
    """
    try:
        dataset_service_sync = DatasetsService(db_sync_client=client)
        action_service = ActionService(db_sync_client=client)

        dataset: Dataset = dataset_service_sync.get_dataset_by_id_sync(dataset_id)

        return DataStatistics.from_db(
            dataset=dataset,
            num_stat=True,
            cat_stat=True,
            dataset_service=dataset_service_sync,
            action_service=action_service,
        )

        # return DataStatistics.from_dataset(dataset)

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Message(message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Message(message=str(e)).model_dump(),
        )
    finally:
        close_db_sync(client=client)


@router.get(
    "/statistics_numerical",
    responses={
        status.HTTP_200_OK: {"model": DataStatistics},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
)
def get_statistics_numerical(
    site_id: str,
    project_id: str,
    dataset_id: str,
    page: Optional[PositiveInt] = None,
    page_size: Optional[PositiveInt] = None,
    client: MongoClient = Depends(get_db_sync),
):
    """
    This methos is used for getting the statistics of the given dataset.

    Args:
        site_id (str): site id of the user
        project_id (str): project id of the project user is using
        dataset_id (str): dataset id of the tabular dataset
        client (MongoClient, optional): _description_. Defaults to Depends(get_db_async).

    Raises:
        HTTPException: KeyError
        HTTPException: Exception

    Returns:
        _type_: _description_
    """
    try:
        dataset_service_sync = DatasetsService(db_sync_client=client)
        action_service = ActionService(db_sync_client=client)

        dataset: Dataset = dataset_service_sync.get_dataset_by_id_sync(dataset_id)

        return DataStatistics.from_db(
            dataset,
            cat_stat=False,
            num_stat=True,
            page=page,
            page_size=page_size,
            dataset_service=dataset_service_sync,
            action_service=action_service,
        )

        # return DataStatistics.from_dataset(dataset)

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Message(message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Message(message=str(e)).model_dump(),
        )
    finally:
        close_db_sync(client=client)


@router.get(
    "/statistics_categorical",
    responses={
        status.HTTP_200_OK: {"model": DataStatistics},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
)
def get_statistics_categorical(
    site_id: str,
    project_id: str,
    dataset_id: str,
    page: Optional[PositiveInt] = None,
    page_size: Optional[PositiveInt] = None,
    client: MongoClient = Depends(get_db_sync),
):
    """
    This methos is used for getting the statistics of the given dataset.

    Args:
        site_id (str): site id of the user
        project_id (str): project id of the project user is using
        dataset_id (str): dataset id of the tabular dataset
        client (MongoClient, optional): _description_. Defaults to Depends(get_db_async).

    Raises:
        HTTPException: KeyError
        HTTPException: Exception

    Returns:
        _type_: _description_
    """
    try:
        dataset_service_sync = DatasetsService(db_sync_client=client)
        action_service = ActionService(db_sync_client=client)

        dataset: Dataset = dataset_service_sync.get_dataset_by_id_sync(dataset_id)

        return DataStatistics.from_db(
            dataset,
            cat_stat=True,
            num_stat=False,
            page=page,
            page_size=page_size,
            dataset_service=dataset_service_sync,
            action_service=action_service,
        )

        # return DataStatistics.from_dataset(dataset)

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Message(message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Message(message=str(e)).model_dump(),
        )
    finally:
        close_db_sync(client=client)


@router.get(
    "/metadata",
    responses={
        status.HTTP_200_OK: {"model": DataMetadata},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
)
def get_metadata(
    site_id: str,
    project_id: str,
    dataset_id: str,
    client: MongoClient = Depends(get_db_sync),
):
    """
    This API method is used for getting the metadata of the dataset

    Args:
        site_id (str): site id of the user
        project_id (str): project id of the project user is using
        dataset_id (str): dataset id of the tabular dataset
        client (MongoClient, optional): _description_. Defaults to Depends(get_db_async).

    Raises:
        HTTPException: KeyError
        HTTPException: Exception

    Returns:
        _type_: _description_
    """
    try:
        dataset: Dataset = DatasetsService(
            db_sync_client=client
        ).get_dataset_by_id_sync(dataset_id)
        return DataMetadata.from_dataset(dataset)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Message(message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Message(message=str(e)).model_dump(),
        )
    finally:
        close_db_sync(client=client)


@router.post(
    "/visualization",
    responses={
        status.HTTP_200_OK: {"model": DataVizResponse},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
    openapi_extra={"actions":Actions.EDA_visualization.value},

)
def get_visualization(
    site_id: str,
    project_id: str,
    dataset_id: str,
    visualization: DataVisualization,
    interactive: bool,
    client: MongoClient = Depends(get_db_sync),  # type: ignore
):
    """
    This API method is used to get the visualization plot.

    Args:
        site_id (str): site id of the user
        project_id (str): project id of the project user is using
        dataset_id (str): dataset id of the tabular dataset
        visualization (DataVisualization): visualization config
        interactive (bool): interactive or non-interactive plot
        client (MongoClient, optional): _description_. Defaults to Depends(get_db_sync).

    Raises:
        HTTPException: KeyError
        HTTPException: Exception

    Returns:
        _type_: path of the plot.
    """
    try:
        logger.info(
            f"[{visualization.root.root.plot_type}] Received request for plot with config as {visualization}"
        )
        dataset_service_sync = DatasetsService(db_sync_client=client)
        action_service_sync = ActionService(db_sync_client=client)

        dataset: Dataset = dataset_service_sync.get_dataset_by_id_sync(dataset_id)

        return DataVisualization.export_file(
            dataset=dataset,
            visualization=visualization,
            interactive=interactive,
            dataset_service=dataset_service_sync,
            action_service=action_service_sync,
        )

    except KeyError as e:
        logger.exception(f"Failed with Exception. {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Message(message=str(e)).model_dump(),
        )
    except Exception as e:
        logger.exception(f"Failed with Exception. {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Message(message=str(e)).model_dump(),
        )
    finally:
        close_db_sync(client=client)


@router.get(
    "/file",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
)
async def file_response(site_id: str, project_id: str, path: Path):
    """
    This method is used for parsing the filepath as a file response

    Args:
        path (Path): a file path

    Returns:
        _type_: FileResponse of the path
    """
    try:
        expected_parent = Path(environment.base_path)
        resolved_path = path.resolve()
        if not resolved_path.is_relative_to(expected_parent):
            raise ValueError(
                f"Access to {resolved_path} is restricted. Expected parent directory: {expected_parent}"
            )
        if not resolved_path.exists():
            raise FileNotFoundError(f"requested path doesnt exist {resolved_path}")
        if resolved_path.is_dir():
            raise ValueError(f"{resolved_path} is directory , expecting a file")
        logger.info(f"returning the given path as the file response. {resolved_path}")
        return FileResponse(resolved_path)
    except FileNotFoundError as e:
        logger.exception(f"file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"file not found: {e}"
        )
    except Exception as e:
        logger.exception(f"error from file_response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"error from file_response: {e}",
        )


@router.post(
    "/correlation_heatmap",
    responses={
        status.HTTP_200_OK: {"model": CorrelationSuccessResponse},
        status.HTTP_404_NOT_FOUND: {"model": CorrelationFailureResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": CorrelationFailureResponse},
    },
    openapi_extra={"actions":Actions.EDA_visualization.value},

)
def get_correlation_heatmap(
    site_id: str,
    project_id: str,
    corr_schema: CorrelationInputSchema,
    client: MongoClient = Depends(get_db_sync),
):
    """
    Correlation Heatmap:
    Args: dataset_id & columns
    Returns: Any: generated correlations data
    """

    try:
        dataset_service_sync = DatasetsService(db_sync_client=client)
        action_service_sync = ActionService(db_sync_client=client)

        correlation_response = CorrelationService.get_correlation(
            corr_schema=corr_schema,
            dataset_service=dataset_service_sync,
            action_service=action_service_sync,
        )

        return CorrelationSuccessResponse(status=True, data=correlation_response)

    except KeyError as e:
        logger.exception(f"Failed with Exception. {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CorrelationFailureResponse(
                status=False, msg=f"Dataset not found. Error Occurred - {str(e)}"
            ).model_dump(),
        )
    except Exception as e:
        logger.exception(f"Failed with Exception. {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CorrelationFailureResponse(
                status=False, msg=f"Error Occurred - {str(e)}"
            ).model_dump(),
        )
    finally:
        close_db_sync(client=client)


@router.get("/get_unique_values")
async def get_unique_values(
    site_id: str,
    project_id: str,
    dataset_id: str,
    column_name: str,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    db_async_client: AsyncIOMotorClient = Depends(get_db_async), # type: ignore
    redis_async_client: AsyncRedis = Depends(get_async_redis_client)
):
    try:
        dataset_service = DatasetsService(db_async_client=db_async_client)
        action_service = ActionService(db_async_client=db_async_client)
        
        logger.debug(f"Fetching dataset with ID '{dataset_id}'")
        dataset = await dataset_service.get_dataset_by_id(dataset_id)

        result = await DataStatistics.get_unique_column_values(
            dataset=dataset,
            column_name=column_name,
            page=page,
            page_size=page_size,
            dataset_service=dataset_service,
            action_service=action_service,
            redis_async_client=redis_async_client
        )
        
        logger.info(f"Successfully retrieved unique values for column '{column_name}' in dataset '{dataset_id}'")
        return result
    except Exception as e:
        logger.exception(f"Failed with Exception. {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(e)},
        ) 