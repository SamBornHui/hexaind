from pathlib import Path

import pandas as pd


def hexaind_custom_widget_function(
    summary_df: pd.DataFrame, old_parquet_path: str, file_to_concatenate: str
) -> str:
    """
    Reads two Parquet files (old and new), concatenates the new data to the old data,
    and writes the updated data back to the original Parquet file.

    Args:
        old_parquet_path (str): Path to the old Parquet file.
        new_parquet_path (str): Path to the new Parquet file.

    Returns:
        str: Path to the updated Parquet file.
    """
    try:
        # read from summary df
        new_parquet_path = str(summary_df[file_to_concatenate][0])

        if old_parquet_path == "" or old_parquet_path is None:
            print("No old file provided")
            return new_parquet_path

        if not Path(old_parquet_path).exists():
            print("No valid old file")
            return new_parquet_path

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

        # Step 3: Concatenate the new data to the old data
        updated_data = pd.concat([old_data, new_data], ignore_index=True)
        print(f"Updated data shape after concatenation: {updated_data.shape}")

        # Step 4: Write the updated data back to the old Parquet file
        updated_data.to_parquet(old_parquet_path, index=False)
        print(f"Successfully updated Parquet file at {old_parquet_path}")

    except Exception as e:
        print(f"Error occurred during processing: {e}")
        raise e

    return old_parquet_path
