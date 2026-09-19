import pandas as pd


def uc3_wafer_data_pivot_on_full_step(dataframe_file_path, pivot_destination_file_path, wafer_drop_na_threshold):

    dataframe = pd.read_parquet(dataframe_file_path)

    dataframe.drop_duplicates(inplace=True)

    # dataframe['parentlot'] = [ i[:-4] for i in dataframe['LOT_ID']]
    dataframe["parentlot"] = dataframe["LOT_ID"].astype(str).str[:-4]

    dataframe["STEP_FULL"] = (
        dataframe["MFG_PROCESS_STEP"] + "-" + dataframe["COMMON_TEST_ID"]
    )
    dataframe.drop_duplicates(inplace=True)

    # Remove ' - RAW_WAFER (Mean)' from the STEP_FULL column, because we need to combine them according the the step name only
    dataframe["STEP_FULL"] = dataframe["STEP_FULL"].str.replace(
        " - RAW_WAFER (Mean)", "", regex=False
    )
    dataframe["STEP_FULL"] = dataframe["STEP_FULL"].str.replace(
        " - DG_CV (Mean)", "", regex=False
    )

    grouping_cols_1 = [
        "parentlot",
        "WAFER_ID",
        "MFG_PROCESS_STEP",
        "COMMON_TEST_ID",
        "STEP_FULL",
        "WORK_WEEK",
    ]
    dataframe = dataframe.groupby(grouping_cols_1).first().reset_index()

    grouping_cols_2 = [
        "parentlot",
        "WAFER_ID",
        "MFG_PROCESS_STEP",
        "COMMON_TEST_ID",
        "STEP_FULL",
    ]
    dataframe = dataframe.groupby(grouping_cols_2).first().reset_index()

    dataframe.drop_duplicates(inplace=True)
    # dataframe=dataframe.groupby(['parentlot','WAFER_ID','REGION','MFG_PROCESS_STEP','COMMON_TEST_ID','STEP_FULL','WORK_WEEK','RUN_COMPLETE_DATE']).mean().reset_index()

    dataframe_pivot = (
        pd.pivot_table(
            dataframe,
            values="TEST_VALUE",
            index=["parentlot", "WAFER_ID", "WORK_WEEK", "RUN_COMPLETE_DATE"],
            columns=["STEP_FULL"],
        )
        .rename_axis(None, axis=1)
        .reset_index(drop=False)
    )

    dataframe_pivot.dropna(
        axis=1,
        thresh=int(len(dataframe_pivot)*(1-wafer_drop_na_threshold)),
        inplace=True,
    )
    
    dataframe_pivot.to_parquet(pivot_destination_file_path)


def uc3_point_data_pivot_on_full_step(dataframe_file_path, pivot_destination_file_path, point_drop_na_threshold):

    dataframe = pd.read_parquet(dataframe_file_path)

    dataframe.drop_duplicates(inplace=True)

    dataframe["parentlot"] = dataframe["LOT_ID"].astype(str).str[:-4]
    dataframe["STEP_FULL"] = (
        dataframe["MFG_PROCESS_STEP"] + "-" + dataframe["COMMON_TEST_ID"]
    )

    dataframe.drop_duplicates(inplace=True)

    numeric_str_to_remove = r"\d{1,5}"
    dataframe["STEP_FULL"] = dataframe["STEP_FULL"].str.replace(
        f" - RAW_POINT - P{numeric_str_to_remove}", "", regex=True
    )

    grouping_cols_1 = [
        "parentlot",
        "WAFER_ID",
        "DIE_X",
        "DIE_Y",
        "REGION",
        "MFG_PROCESS_STEP",
        "COMMON_TEST_ID",
        "STEP_FULL",
    ]
    dataframe = dataframe.groupby(grouping_cols_1).first().reset_index()

    grouping_cols_2 = [
        "parentlot",
        "WAFER_ID",
        "DIE_X",
        "DIE_Y",
        "MFG_PROCESS_STEP",
        "COMMON_TEST_ID",
        "STEP_FULL",
        "WORK_WEEK",
    ]
    dataframe = dataframe.groupby(grouping_cols_2).first().reset_index()

    grouping_cols_3 = [
        "parentlot",
        "WAFER_ID",
        "REGION",
        "TEST_VALUE",
        "MFG_PROCESS_STEP",
        "COMMON_TEST_ID",
        "STEP_FULL",
        "WORK_WEEK",
        "RUN_COMPLETE_DATE",
    ]
    dataframe = dataframe = dataframe[grouping_cols_3]

    dataframe.drop_duplicates(inplace=True)
    final_grouping_cols = [
        "parentlot",
        "WAFER_ID",
        "REGION",
        "MFG_PROCESS_STEP",
        "COMMON_TEST_ID",
        "STEP_FULL",
        "WORK_WEEK",
        "RUN_COMPLETE_DATE",
    ]
    dataframe = dataframe.groupby(final_grouping_cols).mean().reset_index()

    dataframe_pivot = pd.pivot_table(
        dataframe,
        values="TEST_VALUE",
        index=["parentlot", "WAFER_ID", "WORK_WEEK", "REGION", "RUN_COMPLETE_DATE"],
        columns=["STEP_FULL"],
    )
    dataframe_pivot = dataframe_pivot.rename_axis(None, axis=1).reset_index()

    dataframe_pivot.dropna(
        axis=1,
        thresh=int(len(dataframe_pivot)*(1-point_drop_na_threshold)),
        inplace=True,
    )

    dataframe_pivot.to_parquet(pivot_destination_file_path)
