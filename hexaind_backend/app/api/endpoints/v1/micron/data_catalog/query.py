from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import PositiveInt

from app.api.endpoints.v1.data.eda.routes import Message
from app.services.data.assets.datasets.schemas import Dataset, TabularDatasetInformation
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.data.curation.eda.preview.model import DataPreview
from app.services.micron.data_catalog.query import (
    DataQueryRequest,
    DataQueryResponse,
    SelectionQueryRequest,
    SelectionQueryResponse,
    UniquesQueryRequest,
    UniquesQueryResponse,
)
from app.utils.dataset_utils import generate_dataset_object

router = APIRouter(prefix="/query")


@router.post("/data")
def data_query(query_request: DataQueryRequest) -> DataQueryResponse:
    return DataQueryResponse.from_data_query(query_request)


@router.post("/uniques")
def uniques_query(query_request: UniquesQueryRequest) -> UniquesQueryResponse:
    return UniquesQueryResponse.from_uniques_query(query_request)

# currently same as unique
@router.post("/advanced_uniques")
def uniques_query(query_request: UniquesQueryRequest) -> UniquesQueryResponse:
    return UniquesQueryResponse.from_uniques_query(query_request)


@router.post("/select")
def select_query(query_request: SelectionQueryRequest) -> SelectionQueryResponse:
    return SelectionQueryResponse.from_selection_query(query_request)


@router.post("/unselect")
def unselect_query(query_request: SelectionQueryRequest) -> SelectionQueryResponse:
    return SelectionQueryResponse.from_unselection_query(query_request)


@router.get(
    "/get_tabular_files",
)
async def get_tabular_files(
    file_path: str
) -> List[str]:
    try:
        data_files_path = Path(file_path)
        if not data_files_path.exists():
            raise KeyError('file not found')
        if data_files_path.is_file() and data_files_path.suffix in {'.csv', '.parquet'}:
            return [file_path]
        if data_files_path.is_dir():
            file_paths = [str(path) for path in data_files_path.rglob('*') if path.suffix in {'.csv', '.parquet'}]
            return file_paths
        return []
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


@router.get(
    "/data_preview",
    responses={
        status.HTTP_200_OK: {"model": DataPreview},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    },
)
async def get_preview(
    project_id: str,
    file_path: str,
    page: PositiveInt = 1,
    page_size: PositiveInt = 50
):
    try:

        fpath = Path(file_path)
        json_fpath = fpath.parent / f"{fpath.name.split('.')[0]}.json"
        if json_fpath.exists():
            with json_fpath.open("r") as file:
                td_info = TabularDatasetInformation.model_validate_json(file.read())
            dataset_information = [td_info]
        else:
            raise Exception(f"Preview is not pre calculated for {fpath.name}")

        dataset: Dataset = generate_dataset_object(
            file_path=file_path, project_id=project_id
        )
        dataset.dataset_information = dataset_information

        return DataPreview.from_db(dataset,
                                   page=page,
                                   page_size=page_size,
                                   dataset_service=None)

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