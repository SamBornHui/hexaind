import os
from pathlib import Path

import pandas as pd
import pytest
import pytest_mock
import pytest_asyncio

from app.services.data.datasets_conversion.schemas import DatasetsConversionType
from app.services.data.datasets_conversion.helper import TabularParquetToTabularCSV, DatasetsConversionFactory
from app.utils.dataset_utils import generate_dataset_object


class MockEnvironment:
    def __init__(self, datasets_folder):
        self.datasets_folder = datasets_folder


def test_tabular_parquet_to_csv_conversion(mocker):
    converter = TabularParquetToTabularCSV()
    penguin_csv_file_path = Path(__file__).parent.parent.parent.parent / "resources" / "penguins.parquet"

    mocker.patch("app.services.data.datasets_conversion.helper.environment",
                 MockEnvironment(penguin_csv_file_path.parent))

    dataset = generate_dataset_object(str(penguin_csv_file_path))
    result = converter.convert(dataset, kwargs={'last_modified_by': 'test_user'})


    assert result.dataset_location[0].extension == ".csv"

    assert all(pd.read_parquet(penguin_csv_file_path) == pd.read_csv(result.dataset_location[0].path))
    os.remove(result.dataset_location[0].path)


def test_datasets_conversion_factory():
    factory = DatasetsConversionFactory()
    converter = factory.get_factory(DatasetsConversionType.TABULAR_PARQUET_TO_CSV)
    assert isinstance(converter, TabularParquetToTabularCSV)


def test_datasets_conversion_factory_fail_case():
    factory = DatasetsConversionFactory()
    try:
        factory.get_factory(None)
        assert False
    except ValueError:
        assert True
