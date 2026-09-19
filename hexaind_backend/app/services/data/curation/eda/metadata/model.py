from __future__ import annotations

from typing import Annotated

from pydantic import Field, RootModel

from ....assets.datasets.schemas import Dataset
from .v1_0.model import DataMetadata as DataMetadataV1_0


class DataMetadata(RootModel):
    root: Annotated[DataMetadataV1_0, Field(discriminator="version")]

    @classmethod
    def from_dataset(cls, dataset: Dataset) -> DataMetadata:
        return DataMetadata(root=DataMetadataV1_0.from_dataset(dataset))
