from app.services.data.curation.data.source.model import DataSourceModel


def test_csv_datasource_v1_0(sample_csv_file, sample_dataframe):
    data_source: DataSourceModel = DataSourceModel.model_validate(
        {"version": "1.0", "data_type": "CSV", "path": sample_csv_file}
    )
    assert all(data_source.dataframe.compute() == sample_dataframe.compute())


def test_parquet_datasource_v1_0(sample_parquet_file, sample_dataframe):
    data_source: DataSourceModel = DataSourceModel.model_validate(
        {"version": "1.0", "data_type": "PARQUET", "path": sample_parquet_file}
    )
    assert all(data_source.dataframe.compute() == sample_dataframe.compute())


def test_dataset_datasource_v1_0(sample_csv_dataset, sample_dataframe):
    data_source = DataSourceModel.from_dataset(sample_csv_dataset)
    assert all(data_source.dataframe.compute() == sample_dataframe.compute())
