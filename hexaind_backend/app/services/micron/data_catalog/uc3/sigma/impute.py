import pandas as pd

from .pivot import uc3_point_data_pivot_on_full_step


def get_imputed_wafer(wafer_data_pivot, wafer_traveler_step_df, dr):

    selected_cols = ["parentlot", "WAFER_ID", "WORK_WEEK", "RUN_COMPLETE_DATE"]
    final_imputed_wafer = wafer_data_pivot[selected_cols]

    for key, values in dr.items():
        value_pattern = "|".join(values)

        wafer_slice = wafer_data_pivot.filter(regex=value_pattern, axis=1)
        if wafer_slice.empty:
            continue

        wafer_slice_data = pd.concat(
            [wafer_slice, wafer_data_pivot[selected_cols]], axis=1
        )
        trav_slice = wafer_traveler_step_df.filter(regex=key, axis=1)
        if trav_slice.empty:
            continue

        wafer_traveler_slice = pd.concat(
            [trav_slice, wafer_traveler_step_df[["parentlot", "WAFER_ID"]]], axis=1
        )
        wafer_traveler_slice[trav_slice.columns[0]] = pd.to_datetime(
            wafer_traveler_slice[trav_slice.columns[0]], errors="ignore"
        )
        wafer_traveler_slice["WW"] = wafer_traveler_slice[trav_slice.columns[0]].apply(
            lambda x: f"{x.isocalendar()[0]}-{str(x.isocalendar()[1]).zfill(2)}"
        )

        wafer_traveler_slice = wafer_traveler_slice.drop_duplicates(
            ["parentlot", "WAFER_ID"], keep="last"
        )

        merge_df = pd.merge(
            wafer_slice_data,
            wafer_traveler_slice,
            on=["parentlot", "WAFER_ID"],
            how="inner",
        ).reset_index(drop=True)

        # modification made from trav_slice[0] to trav_slice.columns[0]
        merge_df = merge_df.sort_values(
            by=[trav_slice.columns[0]], ascending=True
        ).reset_index(drop=True)

        # Custom imputation function for wafer level data:

        numerical_columns = merge_df.select_dtypes(include=["number"])

        temp_df = merge_df.fillna(
            merge_df.groupby(["parentlot"])[numerical_columns.columns].transform("mean")
        )
        temp_df2 = merge_df.fillna(
            merge_df.groupby(["WW"])[numerical_columns.columns].transform("mean")
        )
        temp_df3 = merge_df.fillna(method="ffill").fillna(method="bfill")

        temp_df.sort_index(inplace=True)
        temp_df2.sort_index(inplace=True)
        temp_df3.sort_index(inplace=True)

        imputed_wafer_data = temp_df.combine_first(temp_df2).combine_first(temp_df3)
        # modification made from trav_slice[0] to trav_slice.columns[0]
        imputed_wafer_data.drop([trav_slice.columns[0], "WW"], axis=1, inplace=True)

        final_imputed_wafer = pd.merge(
            final_imputed_wafer,
            imputed_wafer_data,
            on=["parentlot", "WAFER_ID", "WORK_WEEK", "RUN_COMPLETE_DATE"],
            how="inner",
        ).reset_index(drop=True)
        del temp_df, temp_df2, temp_df3, imputed_wafer_data

    other_columns = [
        col
        for col in final_imputed_wafer.columns
        if col
        not in ["parentlot", "WAFER_ID", "REGION", "WORK_WEEK", "RUN_COMPLETE_DATE"]
    ]
    agg_dict = {col: "mean" for col in other_columns}
    agg_dict["RUN_COMPLETE_DATE"] = "first"
    agg_dict["WORK_WEEK"] = "first"

    final_imputed_wafer = (
        final_imputed_wafer.groupby(["parentlot", "WAFER_ID"])
        .agg(agg_dict)
        .reset_index()
    )

    return final_imputed_wafer


def get_imputed_point(
    point_data_files, point_traveler_step_df, dr, region, point_dropna_threshold
):

    region_filter = [("REGION", "==", region)]
    point_data = pd.read_parquet(point_data_files, filters=region_filter)
    point_data_pivot = uc3_point_data_pivot_on_full_step(point_data)
    point_data_pivot.dropna(
        axis=1,
        thresh=int(len(point_data_pivot) * (1 - point_dropna_threshold)),
        inplace=True,
    )
    point_data_E = point_data_pivot.query(f'REGION == "{region}"')

    point_traveler_step_df["parentlot"] = (
        point_traveler_step_df["LOT_ID"].astype(str).str[:-4]
    )

    final_imputed_point = point_data_E[
        ["parentlot", "WAFER_ID", "WORK_WEEK", "RUN_COMPLETE_DATE", "REGION"]
    ]
    # CHECKPOINT 0 - is it identical? final_imputed_point

    for key, values in dr.items():
        value_pattern = "|".join(values)

        # difference
        # col=list(point_data_E.columns.str.contains(value_pattern))
        col_mask = point_data_E.columns.str.contains(value_pattern)

        # difference
        point_slice = point_data_E.columns[col_mask]

        if point_slice.empty:
            continue
        point_slice_data = point_data_E[
            point_slice.tolist()
            + ["parentlot", "WAFER_ID", "WORK_WEEK", "RUN_COMPLETE_DATE", "REGION"]
        ]

        # CHECKPOINT 1 - is it identical point_slice_data

        trav_col_mask = point_traveler_step_df.columns.str.contains(key)
        trav_slice = point_traveler_step_df.columns[trav_col_mask]
        point_traveler_slice = point_traveler_step_df[
            trav_slice.tolist() + ["parentlot", "WAFER_ID"]
        ]
        point_traveler_slice[trav_slice[0]] = pd.to_datetime(
            point_traveler_step_df[trav_slice[0]], errors="ignore"
        )

        # Conversion of for loop into a more efficient form!!
        point_traveler_slice["WW"] = point_traveler_slice[trav_slice[0]].apply(
            lambda x: f"{x.isocalendar()[0]}-{str(x.isocalendar()[1]).zfill(2)}"
        )
        point_traveler_slice.drop_duplicates(
            ["parentlot", "WAFER_ID"], keep="last", inplace=True
        )
        # CHECKPOINT 2 - is it identical point_traveler_slice

        merge_df = (
            pd.merge(
                point_slice_data,
                point_traveler_slice,
                on=["parentlot", "WAFER_ID"],
                how="inner",
            )
            .sort_values(by=[trav_slice[0]])
            .reset_index(drop=True)
        )
        # CHECKPOINT 3 - is it identical merge_df

        numerical_columns = merge_df.select_dtypes(include=["number"])

        # Conversion of for loop into a more efficient form!!
        # temp_df = merge_df.groupby(['parentlot', 'WAFER_ID'])[numerical_columns.columns].transform(lambda x: x.fillna(x.mean()))
        # temp_df1 = merge_df.groupby(['parentlot'])[numerical_columns.columns].transform(lambda x: x.fillna(x.mean()))
        # temp_df2 = merge_df.groupby(['WW'])[numerical_columns.columns].transform(lambda x: x.fillna(x.mean()))
        # temp_df3 = merge_df.fillna(method='ffill').fillna(method='bfill')

        temp_df = merge_df.fillna(
            merge_df.groupby(["parentlot", "WAFER_ID"])[
                numerical_columns.columns
            ].transform("mean")
        )
        temp_df1 = merge_df.fillna(
            merge_df.groupby(["parentlot"])[numerical_columns.columns].transform("mean")
        )
        temp_df2 = merge_df.fillna(
            merge_df.groupby(["WW"])[numerical_columns.columns].transform("mean")
        )
        temp_df3 = merge_df.fillna(method="ffill").fillna(method="bfill")

        temp_df.sort_index(inplace=True)
        temp_df1.sort_index(inplace=True)
        temp_df2.sort_index(inplace=True)
        temp_df3.sort_index(inplace=True)

        ######
        ######
        # Hmm Missing sort_index
        # temp_df.sort_index(inplace=True)
        # temp_df1.sort_index(inplace=True)
        # temp_df2.sort_index(inplace=True)
        # temp_df3.sort_index(inplace=True)
        ######
        ######

        # CHECKPOINT 4 - are temp_df, temp_df1, temp_df2, temp_df3 all identical?

        imputed_point_data = (
            temp_df.combine_first(temp_df1)
            .combine_first(temp_df2)
            .combine_first(temp_df3)
        )
        imputed_point_data.drop([trav_slice[0], "WW"], axis=1, inplace=True)

        final_imputed_point = pd.merge(
            final_imputed_point,
            imputed_point_data,
            on=["parentlot", "WAFER_ID", "WORK_WEEK", "RUN_COMPLETE_DATE", "REGION"],
            how="inner",
        )
        # missing
        del temp_df, temp_df2, temp_df3, imputed_point_data

    other_columns = [
        col
        for col in final_imputed_point.columns
        if col
        not in ["parentlot", "WAFER_ID", "REGION", "WORK_WEEK", "RUN_COMPLETE_DATE"]
    ]
    agg_dict = {col: "mean" for col in other_columns}
    agg_dict["RUN_COMPLETE_DATE"] = "first"
    agg_dict["WORK_WEEK"] = "first"
    final_imputed_point = (
        final_imputed_point.groupby(["parentlot", "WAFER_ID", "REGION"])
        .agg(agg_dict)
        .reset_index()
    )

    return final_imputed_point
