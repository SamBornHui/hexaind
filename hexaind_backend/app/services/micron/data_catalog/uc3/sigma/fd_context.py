import os

import pandas as pd


def generated_fd_context_query(fab, design_id, start_date, end_date, traveler_step, filtered_lot_ids=None, filtered_wafer_ids=None):
    lot_ids_where_clause = f"AND lot.LOT_ID IN {filtered_lot_ids}" if filtered_lot_ids else ""
    wafer_ids_where_clause = f"AND wafer.WAFER_ID IN {filtered_wafer_ids}" if filtered_wafer_ids else ""
    if fab == "10":
        # Apply the padding
        fd_context_sql = f"""
        SELECT DISTINCT
        CAST(START_DATE AS STRING) AS START_DATE,
        DESIGN_ID AS DESIGN_ID,
        LOT_ID AS LOT_ID,
        WAFER_ID AS WAFER_ID,
        TRAVELER_STEP AS TRAVELER_STEP
        FROM `gdw-prod-data.fab_{fab}_fd.fd_common_context_step` 
        WHERE 1=1
        AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
        AND TRAVELER_STEP = '{traveler_step}'
        AND DESIGN_ID = '{design_id}'
        {lot_ids_where_clause}
        {wafer_ids_where_clause}

        UNION ALL

        SELECT DISTINCT
        CAST(START_DATE AS STRING) AS START_DATE,
        DESIGN_ID AS DESIGN_ID,
        LOT_ID AS LOT_ID,
        WAFER_ID AS WAFER_ID,
        TRAVELER_STEP AS TRAVELER_STEP
        FROM `gdw-prod-data.fab_{fab}a_fd.fd_common_context_step` 
        WHERE 1=1
        AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
        AND TRAVELER_STEP = '{traveler_step}'
        AND DESIGN_ID = '{design_id}'
        {lot_ids_where_clause}
        {wafer_ids_where_clause}
        """
    else:
        # Apply the padding
        fd_context_sql = f"""
        SELECT DISTINCT
        CAST(START_DATE AS STRING) AS START_DATE,
        DESIGN_ID AS DESIGN_ID,
        LOT_ID AS LOT_ID,
        WAFER_ID AS WAFER_ID,
        TRAVELER_STEP AS TRAVELER_STEP
        FROM `gdw-prod-data.fab_{fab}_fd.fd_common_context_step` 
        WHERE 1=1
        AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
        AND TRAVELER_STEP = '{traveler_step}'
        AND DESIGN_ID = '{design_id}'
        {lot_ids_where_clause}
        {wafer_ids_where_clause}
        """

    return fd_context_sql


def get_fd_context_data(wafer_traveler_step_files):
    dfs = []

    for wafer_traveler_step_file in wafer_traveler_step_files:
        traveler_step_name = wafer_traveler_step_file.split(".parquet")[0].split("/")[
            -1
        ]
        temp_wafer = pd.read_parquet(wafer_traveler_step_file)

        temp_wafer.rename(
            columns={"START_DATE": f"{traveler_step_name}_StartDate"}, inplace=True
        )
        temp_wafer.drop("TRAVELER_STEP", axis=1, inplace=True)
        temp_wafer.sort_values(by=f"{traveler_step_name}_StartDate", inplace=True)
        dfs.append(temp_wafer)

    # Perform outer join on all dataframes
    wafer_traveler_step_df = dfs[0]
    for df in dfs[1:]:
        wafer_traveler_step_df = wafer_traveler_step_df.merge(
            df, how="outer", on=["DESIGN_ID", "LOT_ID", "WAFER_ID"]
        )

    # Re-order the column names for convenience
    wafer_traveler_step_df = wafer_traveler_step_df[
        ["DESIGN_ID", "LOT_ID", "WAFER_ID"]
        + [
            col
            for col in wafer_traveler_step_df.columns
            if col not in ["DESIGN_ID", "LOT_ID", "WAFER_ID"]
        ]
    ]

    wafer_traveler_step_df.dropna(inplace=True)
    wafer_traveler_step_df.drop_duplicates(
        subset=["DESIGN_ID", "LOT_ID", "WAFER_ID"], keep="last", inplace=True
    )
    wafer_traveler_step_df.reset_index(drop=True, inplace=True)

    return wafer_traveler_step_df


def get_fd_context_data_sliced(wafer_traveler_step_files, steps):
    wafer_traveler_step_df = pd.DataFrame(columns=["DESIGN_ID", "LOT_ID", "WAFER_ID"])
    for wafer_traveler_step_file in wafer_traveler_step_files:

        traveler_step_name = wafer_traveler_step_file.split(".parquet")[0].split("/")[
            -1
        ]

        temp_wafer = pd.read_parquet(wafer_traveler_step_file)
        temp_wafer.rename(
            columns={"START_DATE": f"{traveler_step_name}_StartDate"}, inplace=True
        )
        temp_wafer.drop("TRAVELER_STEP", axis=1, inplace=True)

        temp_wafer.sort_values(by=f"{traveler_step_name}_StartDate", inplace=True)

        if len(wafer_traveler_step_df) < 1:
            # If this is the first iteration, just save a copy
            wafer_traveler_step_df = temp_wafer.copy()
        else:
            # This outer join will help us not miss any RUN_COMPLETE_DATEs across the different metro steps
            wafer_traveler_step_df = wafer_traveler_step_df.merge(
                temp_wafer, how="outer", on=["DESIGN_ID", "LOT_ID", "WAFER_ID"]
            )

    # Re-order the column names for convenience
    wafer_traveler_step_df.insert(0, "WAFER_ID", wafer_traveler_step_df.pop("WAFER_ID"))
    wafer_traveler_step_df.insert(0, "LOT_ID", wafer_traveler_step_df.pop("LOT_ID"))
    wafer_traveler_step_df.insert(
        0, "DESIGN_ID", wafer_traveler_step_df.pop("DESIGN_ID")
    )

    wafer_traveler_step_df.dropna(inplace=True)

    wafer_traveler_step_df.drop_duplicates(
        ["DESIGN_ID", "LOT_ID", "WAFER_ID"], keep="last"
    )

    wafer_traveler_step_df = wafer_traveler_step_df.reset_index(drop=True)

    return wafer_traveler_step_df
