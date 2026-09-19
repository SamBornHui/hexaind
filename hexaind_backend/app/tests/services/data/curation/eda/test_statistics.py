from app.services.data.curation.eda.statistics.model import DataStatistics

from dask.dataframe import concat


def test_statistics_from_dataset_v1_0(sample_csv_dataset, sample_dataframe):
    computed_statistics = DataStatistics.from_dataset(sample_csv_dataset)
    # numerical
    numerical_df = sample_dataframe.select_dtypes(include="number")
    numerical_statistics = (
        concat(
            [
                numerical_df.describe(include="number"),
                numerical_df.isnull()
                .sum()
                .to_frame(name="missing")
                .compute()
                .T,
            ],
        )
        .compute()
        .T.to_dict(orient="split")
    )
    # categorical
    categorical_df = sample_dataframe.select_dtypes(exclude="number")
    categorical_statistics = (
        concat(
            [
                categorical_df.describe(exclude="number"),
                categorical_df.isnull()
                .sum()
                .to_frame(name="missing")
                .compute()
                .T,
            ],
        )
        .compute()
        .T.to_dict(orient="split")
    )

    expected_statistics = DataStatistics.model_validate(
        {
            "version": "1.0",
            "statistics": [
                {
                    "column_type": "NUMERICAL",
                    "column_names": numerical_statistics["index"],
                    "row_names": numerical_statistics["columns"],
                    "data": numerical_statistics["data"],
                },
                {
                    "column_type": "CATEGORICAL",
                    "column_names": categorical_statistics["index"],
                    "row_names": categorical_statistics["columns"],
                    "data": categorical_statistics["data"],
                },
            ],
        }
    )
    assert computed_statistics == expected_statistics
