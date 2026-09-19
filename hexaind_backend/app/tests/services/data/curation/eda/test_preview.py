from app.services.data.curation.eda.preview.model import DataPreview

import pytest
@pytest.mark.fixme
def test_preview_from_dataset_v1_0(sample_csv_dataset, sample_dataframe):
    computed_preview = DataPreview.from_dataset(
        sample_csv_dataset, page=1, page_size=100
    )
    expected_preview = DataPreview.model_validate(
        {
            "version": "1.0",
            "column_names": sample_dataframe.columns.to_list(),
            "data": sample_dataframe.compute().to_numpy().tolist(),
            "total_rows": sample_dataframe.shape[0].compute(),
            "page": 1,
            "page_size": 100,
        }
    )
    assert computed_preview == expected_preview
