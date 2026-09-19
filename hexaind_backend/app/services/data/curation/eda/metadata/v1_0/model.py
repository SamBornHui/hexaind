from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

from .....assets.datasets.schemas import Dataset, DatasetMetadata
from .....assets.datasets.service import DatasetsService


class DataMetadata(BaseModel):
    version: Literal["1.0"]
    name: str
    data_source: Optional[str]
    data_column_types: Dict[str, Any] = Field(default_factory=dict)
    description: str
    dataset_id: Optional[str]

    @classmethod
    def from_dataset(cls, dataset: Dataset) -> DataMetadata:
        return cls(
            version="1.0",
            name=dataset.name,
            data_source=dataset.metadata.data_source if dataset.metadata else None,
            data_column_types=cls._get_column_metadata(dataset.metadata),
            description=dataset.description,
            dataset_id=dataset.id,
        )

    @staticmethod
    def _get_column_metadata(metadata: Optional[DatasetMetadata]) -> Dict[str, Any]:
        if metadata is None:
            return {}
        metadata_file = metadata.columns_metadata_file
        if metadata_file and (metadata_file_path := Path(metadata_file)).exists():
            return DatasetsService.read_column_metadata_from_file(metadata_file_path)
        # if file is not present, then return the old metadata from db in new format
        return DataMetadata._convert_metadata_to_new_format(metadata.columns_metadata)

    @staticmethod
    def _convert_metadata_to_new_format(
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if metadata is None:
            return {}
        return {
            column: {
                "datatype": str(dtype),
                "data_category": DatasetsService.get_data_category(dtype),
            }
            for column, dtype in metadata.items()
        }
