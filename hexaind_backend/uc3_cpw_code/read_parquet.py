from pathlib import Path

import pandas as pd


def hexaind_custom_widget_function(
    summary_df: pd.DataFrame, file_to_concatenate: str
) -> pd.DataFrame:
    try:
        # read from summary df
        new_parquet_path = str(summary_df[file_to_concatenate][0])
        return pd.read_parquet(new_parquet_path)
    except Exception as e:
        print(f"Error occurred during processing: {e}")
        raise e
