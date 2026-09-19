from pathlib import Path

import pandas as pd


def hexaind_custom_widget_function(file_path: str) -> pd.DataFrame:
    try:
        # read from summary df
        new_parquet_path = str(file_path)
        return pd.read_parquet(new_parquet_path)
    except Exception as e:
        print(f"Error occurred during processing: {e}")
        raise e
