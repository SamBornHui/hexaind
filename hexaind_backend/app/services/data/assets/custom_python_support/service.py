from pathlib import Path
from typing import Any, Optional, List
import os

from pydantic import BaseModel
from pymongo import MongoClient

from app.config.env_vars import environment
from app.services.data.assets.datasets.dao import DatasetsDao
from app.core.db.db_utils import get_db_sync
from app.services.data.assets.datasets.schemas import DatasetType
from app.services.data.folder_management.dao import FolderManagementDao


class CPWDataset(BaseModel):
    dataset_id: Optional[str] = None
    dataset_file_paths: Optional[List[Path]] = None


class TabularCPWDataset(CPWDataset):
    dataset_type: DatasetType = DatasetType.TABULAR


class TextCPWDataset(CPWDataset):
    dataset_type: DatasetType = DatasetType.TEXT


class DataManager:

    def __init__(
        self, db_sync_client: MongoClient = None, project_id: str = None
    ) -> None:
        db_client = get_db_sync() if db_sync_client is None else db_sync_client
        self.project_id = project_id
        self.datasets_dao = DatasetsDao(db_sync_client=db_client)
        self.folder_management_dao = FolderManagementDao(db_sync_client=db_client)

    def fetch_dataset_path(self, cp_dataset: CPWDataset) -> Path:
        dataset = self.datasets_dao.get_dataset_by_id(dataset_id=cp_dataset.dataset_id)
        dataset_path = Path(dataset.dataset_location[0].path)

        if not dataset_path.exists():
            raise ValueError("The dataset path doesn't exist.")

        return dataset_path

    # TODO: add pydoc for this class
    def fetch_dataset_paths_with_name(self, dataset_name: str) -> Optional[List[Path]]:
        if self.project_id is None:
            raise NotImplementedError(
                "This method can be use used on when project_id is present."
            )
        dataset = self.datasets_dao.get_dataset_by_name_sync(
            dataset_name, self.project_id
        )  # raises KeyError if no record found
        return [
            Path(dataset_location.path) for dataset_location in dataset.dataset_location
        ]

    def fetch_CPW_Datasets(
        self,
        folder_prefix: str,
        dataset_type: DatasetType = DatasetType.TABULAR,
        page_number: int = 1,
        page_limit: int = 100,
    ):
        additional_filter = {
            "project_id": self.project_id,
            "dataset_type": dataset_type,
        }
        datasets, count = self.folder_management_dao.get_datasets_based_on_path_prefix(
            folder_prefix, page_number, page_limit, additional_filter
        )
        if len(datasets) < count:
            raise Exception(
                f"fetching of datasets crossed the default limit set, please use more refined path prefix {count}"
            )
        return [
            CPWDataset(
                dataset_id=dataset.id,
                dataset_file_paths=[
                    Path(location.path) for location in dataset.dataset_location
                ],
            )
            for dataset in datasets
        ]

    @staticmethod
    def from_paths(path: Any) -> CPWDataset:
        return CPWDataset(dataset_file_path=Path(path))

    @staticmethod
    def datasets_path():
        datasets_folder = environment.datasets_folder

        return Path(datasets_folder)

    @property
    def results_folder(self) -> Path:
        results_dir = os.environ.get("RESULTS_DIR")
        if results_dir is None:
            raise ValueError("no results direcotry")
        return Path(results_dir)
