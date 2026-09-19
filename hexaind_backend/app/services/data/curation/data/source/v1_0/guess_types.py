from pandas import DataFrame, to_datetime


def guess_datatypes(dataframe: DataFrame) -> DataFrame:
    # guessing datetype columns
    guess_datetype_columns = ["dt", "date", "datetime", "timestamp"]
    guessed_datetype_columns = dataframe.columns[
        dataframe.columns.str.contains(
            "|".join(guess_datetype_columns), case=False, regex=True
        )
    ]
    for column in guessed_datetype_columns:
        dataframe[column] = to_datetime(
            dataframe[column],
            infer_datetime_format=True,
            errors="ignore",  # type: ignore
        )

    return dataframe
