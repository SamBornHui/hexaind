import pandas as pd
from pathlib import Path


def hexaind_custom_merge_widget_function(
    old_parquet_path: str, new_parquet_path: str, on: list[str], how: str = "inner"
) -> str:
    """
    Reads two Parquet files (old and new), merges the new data with the old data based on the specified columns,
    and writes the updated data back to the original Parquet file.

    Args:
        old_parquet_path (str): Path to the old Parquet file.
        new_parquet_path (str): Path to the new Parquet file.
        on (list[str]): List of column names to merge on.
        how (str, optional): Merge method, one of 'left', 'right', 'outer', 'inner'. Defaults to 'inner'.

    Returns:
        str: Path to the updated Parquet file.
    """
    try:
        # Step 1: Read the existing Parquet file if it exists, otherwise start with an empty DataFrame
        old_data = (
            pd.read_parquet(old_parquet_path)
            if Path(old_parquet_path).exists()
            else pd.DataFrame()
        )
        print(
            f"Successfully read old parquet file from {old_parquet_path}. Shape: {old_data.shape}"
        )

        # Step 2: Read the new Parquet file
        new_data = pd.read_parquet(new_parquet_path)
        print(
            f"Successfully read new parquet file from {new_parquet_path}. Shape: {new_data.shape}"
        )

        # Step 3: Merge the new data with the old data
        updated_data = pd.merge(old_data, new_data, on=on, how=how)
        print(f"Updated data shape after merge: {updated_data.shape}")

        # Step 4: Write the updated data back to the old Parquet file
        updated_data.to_parquet(old_parquet_path, index=False)
        print(f"Successfully updated Parquet file at {old_parquet_path}")

    except Exception as e:
        print(f"Error occurred during processing: {e}")
        raise e

    return old_parquet_path
