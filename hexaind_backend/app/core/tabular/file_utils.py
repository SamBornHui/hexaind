import pandas as pd
import dask.dataframe as dd
from dask.delayed import delayed
from pathlib import Path
from pandas.api.types import is_numeric_dtype

from app.services.data.assets.datasets.schemas import (
    TabularColumnType,
    TabularDatasetField,
)


def read_csv_file(filepath: str) -> dd.DataFrame:
    """
    Method for reading csv files

    Args:
        filepath (Path): takes filepath to read

    Returns:
        pd.DataFrame: returns a pandas dataframe
    """
    df = dd.read_csv(filepath)

    return df


def read_excel_file(filepath: str) -> dd.DataFrame:
    """
    Method for reading excel files

    Args:
        filepath (Path): takes filepath to read

    Returns:
        pd.DataFrame: returns a pandas dataframe
    """
    parts = delayed(pd.read_excel)(filepath)
    df = dd.from_delayed(parts)

    return df


def read_parquet_file(filepath: str) -> dd.DataFrame:
    """
    Method for reading parquet files

    Args:
        filepath (Path): takes filepath to read

    Returns:
        pd.DataFrame: returns a pandas dataframe
    """
    df = dd.read_parquet(filepath, engine="pyarrow", npartitions=-1)

    return df


def read_file(filepath: str) -> dd.DataFrame:
    """Responsible for the reading the given file based on file type

    Args:
        filepath (Path): path of the data file.

    Returns:
        pd.DataFrame: returns a pandas dataframe
    """

    if filepath.endswith(".csv"):
        df = read_csv_file(filepath=filepath)

    elif filepath.endswith((".xlsx", ".xls")):
        df = read_excel_file(filepath=filepath)

    elif filepath.endswith(".parquet") or filepath.endswith(".parq"):
        df = read_parquet_file(filepath=filepath)

    return df


def get_dataframe_columns(df: dd.DataFrame):
    """_summary_

    Args:
        df (pd.DataFrame): _description_

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """

    if not isinstance(df, dd.DataFrame):
        raise Exception("Expecting the input_data as dask dataframe")

    columns = df.columns
    col_data = [
        TabularDatasetField(column_name=column, column_type=dtype)
        for column, dtype in zip(
            columns,
            map(
                lambda x: (
                    TabularColumnType.NUMERICAL
                    if is_numeric_dtype(x)
                    else TabularColumnType.CATEGORICAL
                ),
                df.dtypes,
            ),
        )
    ]
    return col_data
