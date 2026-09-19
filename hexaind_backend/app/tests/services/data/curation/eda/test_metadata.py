from app.services.data.curation.eda.metadata.model import DataMetadata

import pytest

@pytest.mark.fixme
def test_metadata_from_dataset_v1_0(sample_csv_dataset):
    computed_metadata = DataMetadata.from_dataset(sample_csv_dataset)
    expected_metadata = DataMetadata.model_validate(
        {
            "version": "1.0",
            "name": sample_csv_dataset.name,
            "data_source": '',
            "description": sample_csv_dataset.description,
            "dataset_id": sample_csv_dataset.id,
        }
    )
    assert computed_metadata == expected_metadata
