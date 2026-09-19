import pytest
import pandas as pd
import dask.dataframe as dd
from pathlib import Path
import shutil
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from app.services.data.assets.datasets.schemas import Dataset


@pytest.fixture(scope="session")
def sample_dataframe() -> dd.DataFrame:
    return dd.from_pandas(
        pd.DataFrame(
            columns=["a", "b", "c", "d"],
            data=[[1, 2, 3, "hello"], [4, 5, 6, "bye"]],
        ),
        npartitions=1,
    )


@pytest.fixture(scope="session")
def temp_data_dir(tmp_path_factory) -> Path:
    temp_dir = tmp_path_factory.mktemp("data")
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def sample_csv_file(temp_data_dir, sample_dataframe) -> Path:
    csv_file = temp_data_dir / "test.csv"
    sample_dataframe.compute().to_csv(str(csv_file), index=False)
    return csv_file


@pytest.fixture(scope="session")
def sample_parquet_file(temp_data_dir, sample_dataframe) -> Path:
    parquet_file = temp_data_dir / "test.parquet"
    sample_dataframe.compute().to_parquet(str(parquet_file))
    return parquet_file


@pytest.fixture(scope="session")
def sample_csv_dataset(sample_csv_file) -> Dataset:
    gen_time = datetime.now(timezone.utc)
    return Dataset.model_validate(
        {
            "_id": str(ObjectId.from_datetime(gen_time)),
            "version": "1.0",
            "user_id": str(
                ObjectId.from_datetime(gen_time + timedelta(days=1))
            ),
            "project_id": str(
                ObjectId.from_datetime(gen_time + timedelta(days=2))
            ),
            "site_id": str(
                ObjectId.from_datetime(gen_time + timedelta(days=3))
            ),
            "action_id": str(
                ObjectId.from_datetime(gen_time + timedelta(days=4))
            ),
            "name": "Sample Dataset",
            "description": "Sample Dataset for testing",
            "dataset_type": "TABULAR",
            "upload_status": "COMPLETED",
            "upload_stats": {"percentage": "100%"},
            "metadata": {},
            "created_at": gen_time,
            "dataset_location": [
                {
                    "isfolder": False,
                    "size": str(sample_csv_file.stat().st_size),
                    "extension": sample_csv_file.suffix,
                    "path": str(sample_csv_file),
                    "last_modified_by": None,
                    "last_modified_at": None,
                }
            ],
            "access_mode": "INTERNAL",
            "tags": [],
        }
    )
