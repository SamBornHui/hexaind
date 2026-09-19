import math
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
from google.cloud import bigquery

from app.config.env_vars import environment
from app.services.micron.data_catalog.fd_trace.schemas import (
    BigQueryDataPullJobStage,
    BigQueryDataPullJobStatus,
    BigQueryJobStatus,
    DataCatalogStatus,
    DataPullResult,
    DataPullStatus,
    ProbeDataPullConfig,
    ProbeDataPullInputs,
    ProbeDataPullOutputs,
)
from app.workers.micron.commons import StageConfigJobHandler
from app.workers.micron.utils import generate_preview_and_stats_for_all_result_files


def generate_pivoted_data(unpivoted_data_file_path, pivoted_data_file_path, yl_prefix):
    print(f"pivoting data:{unpivoted_data_file_path}")
    raw_probe_data = pd.read_parquet(unpivoted_data_file_path)
    raw_probe_data = (
        raw_probe_data.sort_values("RUN_COMPLETE_DATE", ascending=True)
        .reset_index(drop=True)
        .drop_duplicates(subset=["LOT_ID", "WAFER_ID", "piid", "REGION"], keep="first")
        .reset_index(drop=True)
    )
    raw_probe_data.groupby(["LOT_ID", "WAFER_ID", "REGION"]).nunique().sort_values(
        "RUN_COMPLETE_DATE"
    )[-50:]
    probe = raw_probe_data.drop("piid", axis=1)
    probe["lot_key"] = [i[:-4] for i in probe["LOT_ID"]]
    probe = (
        probe.sort_values("LOT_ID")
        .drop_duplicates(["lot_key", "WAFER_ID", "REGION"], keep="first")
        .reset_index(drop=True)
    )
    probe = probe.drop("LOT_ID", axis=1).rename(columns={"WAFER_ID": "WaferId"})
    probe = (
        probe.pivot(index=["lot_key", "WaferId"], columns=["REGION"], values="DIE_X")
        .rename_axis(None, axis=1)
        .reset_index(drop=False)
    )

    # selfnote: these below numericals might need to taken from user
    regions_map = {"A": 454, "B": 478, "C": 488, "D": 492, "E": 379}
    for region in regions_map:
        if region in probe.columns:
            probe[f"YL_{region}"] = probe[f"{region}"] / regions_map[region] * 100
            probe[f"{yl_prefix}_YL_{region}"] = (
                probe[f"{region}"] / regions_map[region] * 100
            )

    probe.to_parquet(pivoted_data_file_path)


def generate_wafer_related_data(
    raw_probe_data_path, wafer_related_probe_data_path, prefix_str
):
    b1_wafer = pd.read_parquet(raw_probe_data_path)
    b1_wafer["Workweek"] = [
        "WW" + "_" + str(math.ceil(((int(i) + 3) / 7)))
        for i in b1_wafer["RUN_COMPLETE_DATE"].dt.dayofyear
    ]
    b1_wafer = (
        b1_wafer.drop_duplicates()
        .sort_values("RUN_COMPLETE_DATE", ascending=True)
        .reset_index(drop=True)
    )
    b1_wafer = (
        b1_wafer[
            [
                "LOT_ID",
                "WAFER_ID",
                "DIE_X",
                "DIE_Y",
                "REGION",
                "piid",
                "Workweek",
                "RUN_COMPLETE_DATE",
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    b1_wafer = (
        b1_wafer.groupby(
            ["piid", "LOT_ID", "WAFER_ID", "RUN_COMPLETE_DATE", "Workweek"]
        )
        .agg({"DIE_X": "count"})
        .reset_index()
    )
    b1_wafer["YL%"] = b1_wafer["DIE_X"] / 2291 * 100
    b1_wafer["FAB_DESIGN_ID_PARETONAME"] = prefix_str
    b1_wafer = (
        b1_wafer.sort_values("RUN_COMPLETE_DATE", ascending=True)
        .reset_index(drop=True)
        .drop_duplicates(subset=["LOT_ID", "WAFER_ID", "piid"], keep="first")
        .reset_index(drop=True)
    )
    b1_wafer.to_parquet(wafer_related_probe_data_path)


def concatenate_vertically(parquet_files, concatenated_parquet_file):
    dfs = []
    for file_path in parquet_files:
        df = pd.read_parquet(file_path)
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_parquet(concatenated_parquet_file)


def join_pivoted_files(pivoted_file_paths_info, final_output_path):
    columns_to_ignore = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "YL_A",
        "YL_B",
        "YL_C",
        "YL_D",
        "YL_E",
    ]
    joined_df = None
    for info in pivoted_file_paths_info:
        df = pd.read_parquet(info["pivoted_file_path"])
        df = df.drop(
            columns=[col for col in columns_to_ignore if col in df.columns],
            errors="ignore",
        )
        if joined_df is None:
            joined_df = df
        else:
            joined_df = pd.merge(joined_df, df, on=["lot_key", "WaferId"], how="outer")

    joined_df.to_parquet(final_output_path)


def probe_datapull_method(
    stage_config_obj: StageConfigJobHandler,
    stage_job_id: str,
    data_pull_job_id: str,
    user_name: str,
    override_uc3_probe_final_results_folder: Optional[str] = None,
    override_gcp_creds_file: Optional[str] = None,
):
    stage_job_config_record = stage_config_obj.stage_job_record
    if not isinstance(
        (config := stage_job_config_record.stage_config), ProbeDataPullConfig
    ):
        raise TypeError(f"Invalid Stage {stage_job_config_record.stage}")
    unique_downloaded_id = uuid.uuid4()

    if override_uc3_probe_final_results_folder:
        probe_final_destination_folder = (
            Path(override_uc3_probe_final_results_folder) / f"{unique_downloaded_id}"
        )
    else:
        probe_final_destination_folder = (
            Path(
                environment.tdam_datacatalog_databrick_session_path_format.format(
                    data_pull_job_id
                )
            )
            / f"{user_name}/results/probe_final_data/{unique_downloaded_id}/"
        )
    probe_final_destination_folder.mkdir(parents=True, exist_ok=True)
    inputs: ProbeDataPullInputs = config.inputs

    if inputs.uploaded_probe_data and inputs.uploaded_probe_data.uploaded_file_path:
        print("Entering uploaded probe data flow")
        # probe data exists therefore just conversion to parquet
        current_status = BigQueryDataPullJobStatus(
            job_stage=BigQueryDataPullJobStage.QUERY_REGISTRATION,
            job_stage_status=BigQueryJobStatus(
                total_bytes_processed="122434242",
                total_bytes_billed="$100",
                progress_percentage=10,
                progress_message="Reading uploaded file",
            ),
        )
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        file_path = inputs.uploaded_probe_data.uploaded_file_path
        probe_final_destination_folder.mkdir(parents=True, exist_ok=True)
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
            df.to_parquet(probe_final_destination_folder / "probe_results.parquet")
        elif file_path.endswith(".xls") or file_path.endswith(".xlsx"):
            excel_data = pd.read_excel(file_path, sheet_name=None)
            dataframes = []
            for sheet_name, df in excel_data.items():
                df["sheet_name"] = sheet_name
                dataframes.append(df)
            combined_df = pd.concat(dataframes, ignore_index=True)
            combined_df.to_parquet(
                probe_final_destination_folder / "probe_results.parquet"
            )
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
        current_status.job_stage_status.progress_percentage = 75
        current_status.job_stage_status.progress_message = "Converting uploaded file"
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )
        result = ProbeDataPullOutputs(
            probe_data=DataPullResult.model_validate(
                dict(file_path=probe_final_destination_folder)
            )
        ).model_dump(by_alias=True, mode="json")
        print("### Task Done.(calculating preview..)")
        generate_preview_and_stats_for_all_result_files(
            str(probe_final_destination_folder)
        )
        print("### Task Done")
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
            job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
        )
        stage_config_obj.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
            job_id=data_pull_job_id,
            current_stage=stage_config_obj.stage_job_record.stage,
            current_stage_status=DataCatalogStatus.IDLE,
        )
        return

    if inputs is None:
        raise ValueError("Not inputs are given")

    if inputs.facilities is None or not inputs.facilities.selected_values:
        raise ValueError("no facility is selected")
    if len(inputs.facilities.selected_values) > 1:
        raise ValueError("only one facility is supported")

    if inputs.design_ids is None or not inputs.design_ids.selected_values:
        raise ValueError("no design_id is selected")
    if len(inputs.design_ids.selected_values) > 1:
        raise ValueError("only one design_id is supported")

    facility = inputs.facilities.selected_values[0]
    design_id = inputs.design_ids.selected_values[0]
    probe_context_file_path = inputs.paretoname.file_path
    paretonames = inputs.paretoname.selected_values
    paretotitles = inputs.paretotitle.selected_values
    start_date = inputs.start_date
    end_date = inputs.end_date

    max_die_counts_per_region_user_input = [
        inputs.die_counts_per_region.A,
        inputs.die_counts_per_region.B,
        inputs.die_counts_per_region.C,
        inputs.die_counts_per_region.D,
        inputs.die_counts_per_region.E,
    ]
    max_die_counts_per_region = {}
    region_names = ["A", "B", "C", "D", "E"]
    # There is always only 5 regions, no more and no less. These region names are also static and do not change.
    for index in range(len(region_names)):
        max_die_counts_per_region[region_names[index]] = (
            max_die_counts_per_region_user_input[index]
        )

    # read probe catalog
    probe_catalog = pd.read_parquet(probe_context_file_path)
    wafer_related_file_paths = []
    pivoted_file_paths_info = []
    original_raw_probe_paths = []

    temp_probe_folder_destination = (
        probe_final_destination_folder.parent / f"{unique_downloaded_id}_temp"
    )
    temp_probe_folder_destination.mkdir(parents=True, exist_ok=True)
    print(f"Entered with paretonames :: {paretonames}")
    for idx, paretoname in enumerate(paretonames):
        print(f"fetching data for paretoname: {paretoname}")
        resulting_pareto_ids = (
            probe_catalog[
                (probe_catalog["paretoname"] == paretoname)
                & (probe_catalog["paretotitle"].isin(paretotitles))
            ]["paretoid"]
            .drop_duplicates()
            .to_list()
        )
        resulting_piids = (
            probe_catalog[
                (probe_catalog["paretoname"] == paretoname)
                & (probe_catalog["paretotitle"].isin(paretotitles))
            ]["piid"]
            .drop_duplicates()
            .to_list()
        )

        if len(resulting_pareto_ids) == 0 or len(resulting_piids) == 0:
            print(
                f"probe_datapull_method: Skipping Probe data download for paretoname:{paretoname}, pareto_ids:{resulting_pareto_ids}, piids:{resulting_piids}"
            )
            continue

        print(
            f"probe_datapull_method: Downloading Probe data for paretoname:{paretoname}, pareto_ids:{resulting_pareto_ids}, piids:{resulting_piids}"
        )

        current_status = BigQueryDataPullJobStatus(
            job_stage=BigQueryDataPullJobStage.QUERY_VERIFICATION,
            job_stage_status=BigQueryJobStatus(
                total_bytes_processed="122434242",
                total_bytes_billed="$100",
                progress_percentage=0,
                progress_message=f"{idx + 1}/{len(paretonames)}: Query Verification",
            ),
        )
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        selected_pareto_id = resulting_pareto_ids[0]
        selected_piids = resulting_piids

        probe_sql = f"""
                            SELECT DISTINCT
                            PROBE.fab_no AS FACILITY,
                            PROBE.DESIGN_ID,
                            PROBE.LOT_ID, 
                            PROBE.WAFER_ID, 
                            tte_die.diex AS DIE_X, 
                            tte_die.diey AS DIE_Y, 
                            tte_die.zone AS REGION, 
                            piid, 
                            PROBE.PROBEDATE AS RUN_COMPLETE_DATE,
                            CAST(FORMAT_DATE('%Y-%U', PROBE.PROBEDATE) AS STRING) AS WORK_WEEK,
                            FROM `gdw-prod-data.ww_dierbl.dierbl_wafers` PROBE, 
                            UNNEST(tte_die) as tte_die 
                            WHERE 1=1
                            AND pareto_id = {selected_pareto_id}
                            AND piid IN UNNEST({selected_piids})
                            AND PROBE.DESIGN_ID = '{design_id}' 
                            AND PROBE.fab_no = '{facility}' 
                            AND PROBE.PROBEDATE BETWEEN '{start_date}' AND '{end_date}'
                        """

        current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
        current_status.job_stage_status.progress_percentage = 50
        current_status.job_stage_status.progress_message = (
            f"{idx + 1}/{len(paretonames)}: Query Execution"
        )
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        print(f"Probe SQL #{idx}: {probe_sql}")
        conn = bigquery.Client(project="gdw-team-tdam-vpm")
        probe_data = conn.query(probe_sql).to_arrow().to_pandas()
        print(f"successfully downloaded probe data for paretoname:{paretoname}")

        current_status.job_stage = BigQueryDataPullJobStage.SAVING_RESULTS
        current_status.job_stage_status.progress_percentage = 75
        current_status.job_stage_status.progress_message = (
            f"{idx + 1}/{len(paretonames)}: processing probe data"
        )
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )
        rough_probe_file_destination = (
            temp_probe_folder_destination / f"rough_probe_{paretoname}.parquet"
        )
        probe_data.to_parquet(rough_probe_file_destination)

        final_probe_data: pd.DataFrame = (
            probe_data.groupby(
                [
                    "piid",
                    "LOT_ID",
                    "WAFER_ID",
                    "RUN_COMPLETE_DATE",
                    "WORK_WEEK",
                    "REGION",
                ]
            )
            .agg({"DIE_X": "count"})
            .sort_values(by=["WORK_WEEK", "LOT_ID", "WAFER_ID", "REGION"])
            .rename(columns={"DIE_X": "DIE_COUNT"})
            .reset_index()
        )

        final_probe_data["TOTAL_DIE_COUNT"] = final_probe_data["REGION"].map(
            max_die_counts_per_region
        )
        final_probe_data["YL"] = (
            final_probe_data["DIE_COUNT"] / final_probe_data["TOTAL_DIE_COUNT"]
        )
        final_probe_data["PARETO_NAME"] = paretoname
        final_probe_data["DIE_X"] = final_probe_data[
            "DIE_COUNT"
        ]  # reintroducing dieX for further steps
        paretoname_str = paretoname.replace(" ", "_")
        temp_probe_file_destination = (
            temp_probe_folder_destination / f"result_{paretoname_str}.parquet"
        )
        temp_probe_file_destination.parent.mkdir(exist_ok=True, parents=True)
        final_probe_data.to_parquet(temp_probe_file_destination)

        # pivot data
        temp_pivoted_data_destination = (
            temp_probe_folder_destination / f"pivoted_probe_{paretoname_str}.parquet"
        )
        generate_pivoted_data(
            temp_probe_file_destination,
            temp_pivoted_data_destination,
            f"{inputs.facilities.selected_values[0]}_{inputs.design_ids.selected_values[0]}_{paretoname}",
        )
        # wafer_related
        temp_wafer_related_file_path = (
            temp_probe_folder_destination
            / f"wafer_related_probe_{paretoname_str}.parquet"
        )
        generate_wafer_related_data(
            rough_probe_file_destination,
            temp_wafer_related_file_path,
            f"{inputs.facilities.selected_values[0]}_{inputs.design_ids.selected_values[0]}_{paretoname}",
        )

        wafer_related_file_paths.append(temp_wafer_related_file_path)
        original_raw_probe_paths.append(temp_probe_file_destination)
        pivoted_file_paths_info.append(
            {
                "pareto_name": paretoname,
                "pivoted_file_path": temp_pivoted_data_destination,
                "rough_data_file_path": rough_probe_file_destination,
            }
        )

    print("downloaded all paretoname, concatenating them..and move to results path")
    concatenate_vertically(
        wafer_related_file_paths,
        probe_final_destination_folder / "wafer_id_probe.parquet",
    )
    concatenate_vertically(
        original_raw_probe_paths, probe_final_destination_folder / "probe.parquet"
    )

    join_pivoted_files(
        pivoted_file_paths_info,
        probe_final_destination_folder / f"pivoted_probe.parquet",
    )
    # for info in pivoted_file_paths_info:
    #     print(f"copying file {info}")
    #     copy_parquet_files(info['pivoted_file_path'],probe_final_destination_folder/f"pivoted_{info['pareto_name']}.parquet")
    # copy_parquet_files(info['rough_data_file_path'],probe_final_destination_folder/f"rough_probe_{info['pareto_name']}.parquet")

    print("### Task Done.(calculating preview..)")
    generate_preview_and_stats_for_all_result_files(str(probe_final_destination_folder))
    print("### Task Done")

    result = ProbeDataPullOutputs(
        probe_data=DataPullResult.model_validate(
            dict(file_path=probe_final_destination_folder)
        )
    ).model_dump(by_alias=True, mode="json")

    # updating the stage job and data pull job
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
        job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
    )

    stage_config_obj.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
        job_id=data_pull_job_id,
        current_stage=stage_config_obj.stage_job_record.stage,
        current_stage_status=DataCatalogStatus.IDLE,
    )
