from pathlib import Path

import pandas as pd

from app.services.micron.data_catalog.fd_trace.schemas import (
    UC2SigmaDataPullInput,
    FdDataPullJobConfig,
    BigQueryDataPullJobStatus,
    BigQueryDataPullJobStage,
    BigQueryJobStatus,
)
from app.workers.micron.gcp_hooks import BigQueryJobsManager
from app.workers.micron.utils import (
    bigquery_manager_query_registration,
    bigquery_manager_query_monitoring,
    bigquery_manager_results_download,
)


def generate_query_idl_sigma_catalog_query_and_path(
    facility,
    startdate,
    enddate,
    days_to_pad,
    steps,
    designid,
    output_dir,
) -> (str, str, str):
    """

    Takes initial set of user inputs to extract the initial catalog data that contains LOT/WAFER/RUN_DATE information

    INPUTS:

    - facility: str, facility number (4: Boise, 10: Singapore, etc.)

    - startdate: str, YYYY-MM-DD

    - enddate: str, YYYY-MM-DD

    - days_to_pad: int, number of days to extend the search (both startdate and enddate)

    >> this is necessary just in case startdate and enddate abruptly cut off data acquisition currently in progress

    - steps: tuple, a tuple of process step names to be used for data pull

    - designid: str, 4 characters long, alphanumeric

    - output_dir: str, path to directory where the temporary data will be saved

    >> temporary data is necessary for offloading memory during data download process

    OUTPUTS:

    - FULL_CATALOG: pd.DataFrame(), dataframe that contains the catalog data

    - fpath: str, path to where the catalog is downloaded

    """
    if len(steps) <= 1:
        steps = str(steps).replace(',)',')')

    declarations_sql = f"""
                                        DECLARE START_DATE DATE;

                                        DECLARE END_DATE DATE;

                                        DECLARE START_DATE_PADDED DATE;

                                        DECLARE END_DATE_PADDED DATE;

                                        SET START_DATE = '{startdate}';

                                        SET END_DATE = '{enddate}';

                                        SET START_DATE_PADDED = DATE_SUB(START_DATE, INTERVAL {days_to_pad} DAY);

                                        SET END_DATE_PADDED = DATE_ADD(END_DATE, INTERVAL {days_to_pad} DAY);
                        """

    initial_sigma_lot_wafer_sql = f"""

                                        WITH INITIAL_CATALOG AS (SELECT DISTINCT

                                        DESIGN_ID

                                        ,RUN_COMPLETE_DATE

                                        ,LOT_ID

                                        ,WAFER_ID

                                        ,MFG_PROCESS_STEP

                                        ,WAFER_SCRIBE

                                        FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer`

                                        WHERE 1=1

                                        AND RUN_COMPLETE_DATE BETWEEN START_DATE AND END_DATE

                                        AND MFG_PROCESS_STEP IN {steps}

                                        AND DESIGN_ID = '{designid}'

                                        )

                                        SELECT DISTINCT

                                        DWH_SRCID

                                        ,MFG_FACILITY_ID

                                        ,DESIGN_ID

                                        ,CAST(RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE

                                        ,CAST(TIME(RUN_COMPLETE_DATETIME) AS STRING) AS RUN_COMPLETE_TIME

                                        ,CAST(RUN_COMPLETE_DATETIME AS STRING) AS RUN_COMPLETE_DATETIME

                                        ,CAST(FORMAT_DATE('%Y-%U', RUN_COMPLETE_DATETIME) AS STRING) AS WORK_WEEK

                                        ,LOT_ID

                                        ,WAFER_ID

                                        ,MFG_PROCESS_STEP                                        

                                        ,WAFER_SCRIBE

                                        ,SLOT_NO

                                        ,CAST(RUN_OID AS STRING) AS RUN_OID

                                        FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer`

                                        WHERE 1=1

                                        AND RUN_COMPLETE_DATE BETWEEN START_DATE_PADDED AND END_DATE_PADDED

                                        AND MFG_PROCESS_STEP IN (SELECT DISTINCT MFG_PROCESS_STEP FROM INITIAL_CATALOG)

                                        AND DESIGN_ID IN (SELECT DISTINCT DESIGN_ID FROM INITIAL_CATALOG)

                                        AND WAFER_SCRIBE IN (SELECT DISTINCT WAFER_SCRIBE FROM INITIAL_CATALOG)

                                        AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM INITIAL_CATALOG)

                                        AND WAFER_ID IN (SELECT DISTINCT WAFER_ID FROM INITIAL_CATALOG)

                                    """

    fpath = f"{output_dir}/f{facility}_idl_sigma_wafer_lot_catalog"

    return declarations_sql, initial_sigma_lot_wafer_sql, str(fpath)


def extract_sigma_catalogs(catalog_path, sigma_measurement_steps, sigma_point_steps):
    """

    Splits the catalog based on measurement and point steps

    INPUTS:

    - catalog: pd.DataFrame(), original catalog data

    - sigma_measurement_steps: List, list of wafer level steps

    - sigma_point_steps: List, list of die level steps

    OUTPUTS:

    - measurement_catalog: pd.DataFrame(), subset of catalog containing only wafer level steps

    - point_catalog: pd.DataFrame(), subset of catalog containing only die level steps

    """

    # Grab the step names for the ADD steps only
    catalog = pd.read_parquet(catalog_path)
    parent_path = Path(catalog_path).parent
    measurement_catalog_path = parent_path / "measurement_catalog/results.parquet"
    measurement_catalog_path.parent.mkdir(exist_ok=True, parents=True)
    point_catalog_path = parent_path / "point_catalog/results.parquet"
    point_catalog_path.parent.mkdir(exist_ok=True, parents=True)
    measurement_catalog = pd.DataFrame()

    for sigma_measurement_step in sigma_measurement_steps:
        measurement_catalog = pd.concat(
            [
                measurement_catalog,
                catalog[catalog["MFG_PROCESS_STEP"] == sigma_measurement_step],
            ]
        )
    measurement_catalog = measurement_catalog.reset_index(drop=True)
    measurement_catalog.to_parquet(measurement_catalog_path)

    point_catalog = pd.DataFrame()
    for sigma_point_step in sigma_point_steps:
        point_catalog = pd.concat(
            [point_catalog, catalog[catalog["MFG_PROCESS_STEP"] == sigma_point_step]]
        )

    point_catalog = point_catalog.reset_index(drop=True)
    point_catalog.to_parquet(point_catalog_path)

    # convert all files in catalog path to single results file
    dir_path = Path(catalog_path)
    for parquet_file in dir_path.glob("*.parquet"):
        parquet_file.unlink()
        print(f"Deleted: {parquet_file} to re-update")
    catalog_path_results = dir_path / "results.parquet"
    catalog.to_parquet(catalog_path_results)

    return str(measurement_catalog_path), str(point_catalog_path)


def generate_query_idl_sigma_measurement_summary_sql_and_path(
    facility, catalog_path, output_dir, common_test_ids
) -> (str, str):
    """

        Downloads data from the idl_sigma_measurement_summary table

        - Contains wafer level metrology data

        INPUTS:

        - facility: str, facility number (4: Boise, 10: Singapore, etc.)

        - catalog: pd.DataFrame(), catalog data to use for pulling this metrology data

        - output_dir: str, path to directory where the temporary data will be saved
    >> temporary data is necessary for offloading memory during data download process

        - common_test_ids: List, list of test ids to match when pulling data
    >> test ids describe what type of measurement was taken
    >> example values: ['CD1 Bot CH DF - RAW_WAFER (Mean)']

        OUTPUTS:

        - fpath: str, path to where the catalog is downloaded

    """
    catalog = pd.read_parquet(catalog_path)
    catalog.dropna(
        subset=[
            "RUN_COMPLETE_DATE",
            "DESIGN_ID",
            "LOT_ID",
            "WAFER_ID",
            "MFG_PROCESS_STEP",
        ],
        inplace=True,
    )

    # Extract filter values from catalog

    # run_dates = tuple(catalog['RUN_COMPLETE_DATE'].drop_duplicates())

    start_date = min(catalog["RUN_COMPLETE_DATE"])

    end_date = max(catalog["RUN_COMPLETE_DATE"])

    design_ids = list(catalog["DESIGN_ID"].drop_duplicates())

    lot_ids = tuple(catalog["LOT_ID"].drop_duplicates())

    wafer_ids = tuple(catalog["WAFER_ID"].drop_duplicates())

    process_steps = tuple(catalog["MFG_PROCESS_STEP"].drop_duplicates())

    if len(process_steps) <= 1:
        process_steps = str(process_steps).replace(",)", ")")

    common_test_ids = tuple(common_test_ids)

    if len(common_test_ids) <= 1:
        common_test_ids = str(common_test_ids).replace(",)", ")")

    sigma_measurement_summary_sql = f"""

                                        SELECT DISTINCT

                                        LOT_ID,

                                        DESIGN_ID,

                                        WAFER_ID,

                                        WAFER_SCRIBE,

                                        MFG_PROCESS_STEP,

                                        TEST_VALUE,

                                        TEST_ID,

                                        BRIEF_COMMON_TEST_ID,

                                        COMMON_TEST_ID,

                                        CAST(RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,

                                        CAST(RUN_COMPLETE_DATETIME AS STRING) AS RUN_COMPLETE_DATETIME,

                                        CAST(RUN_OID AS STRING) AS RUN_OID,
                                        
                                        CAST(MEASUREMENT_OID AS STRING) AS MEASUREMENT_OID,
                                        
                                        WAFER_SPEC_ID

                                        FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_measurement_summary` SIGMA_MEASUREMENT

                                        WHERE 1=1

                                        AND SIGMA_MEASUREMENT.RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'

                                        AND SIGMA_MEASUREMENT.MFG_PROCESS_STEP IN {process_steps}

                                        AND SIGMA_MEASUREMENT.LOT_ID IN {lot_ids}

                                        AND SIGMA_MEASUREMENT.WAFER_ID IN {wafer_ids}

                                        AND SIGMA_MEASUREMENT.DESIGN_ID IN UNNEST({design_ids})

                                        AND COMMON_TEST_ID IN {common_test_ids}

                                    """

    fpath = f"{output_dir}/f{facility}_idl_sigma_measurement_summary_data"

    return sigma_measurement_summary_sql, fpath


def update_simga_measurement_summary_data(file_path):
    idl_sigma_measurement_summary_data = pd.read_parquet(file_path)
    if len(idl_sigma_measurement_summary_data) > 0:
        idl_sigma_measurement_summary_data["LOT_KEY"] = (
            idl_sigma_measurement_summary_data["LOT_ID"].apply(lambda x: x[:7])
        )
        dir_path = Path(file_path)
        for parquet_file in dir_path.glob("*.parquet"):
            parquet_file.unlink()
            print(f"Deleted: {parquet_file} to re-update")
        results_path = dir_path / "results.parquet"
        idl_sigma_measurement_summary_data.to_parquet(results_path, index=False)
        print(f"SIGMA MEASUREMENT SUMMARY DATA updated at downloaded to: {file_path}")
    del idl_sigma_measurement_summary_data


def generate_query_idl_sigma_point_and_path(
    facility, catalog_path, output_dir, common_test_ids
):
    """

        Downloads data from the idl_sigma_point table

        - Contains die level metrology data

        INPUTS:

        - facility: str, facility number (4: Boise, 10: Singapore, etc.)

        - catalog: pd.DataFrame(), catalog data to use for pulling this metrology data

        - output_dir: str, path to directory where the temporary data will be saved
    >> temporary data is necessary for offloading memory during data download process

        - common_test_ids: List, list of test ids to match when pulling data
    >> test ids describe what type of measurement was taken
    >> example values: ["StepNo:04 - StepData - RAW_POINT - P197 - RFOnTime",

                 "StepNo:14 - StepData - RAW_POINT - P195 - RFOnTime",

                 "OVERETCH PERCENT - RAW_POINT - P1"]

        OUTPUTS:

        - fpath: str, path to where the catalog is downloaded

    """
    catalog = pd.read_parquet(catalog_path)
    catalog.dropna(
        subset=[
            "RUN_COMPLETE_DATE",
            "DESIGN_ID",
            "LOT_ID",
            "WAFER_ID",
            "MFG_PROCESS_STEP",
        ],
        inplace=True,
    )

    process_steps = tuple(catalog["MFG_PROCESS_STEP"].drop_duplicates())

    if len(process_steps) <= 1:
        process_steps = str(process_steps).replace(",)", ")")

    common_test_ids = tuple(common_test_ids)

    if len(common_test_ids) <= 1:
        common_test_ids = str(common_test_ids).replace(",)", ")")

    start_date = min(catalog["RUN_COMPLETE_DATE"])

    end_date = max(catalog["RUN_COMPLETE_DATE"])

    lot_ids = tuple(catalog["LOT_ID"].drop_duplicates())

    wafer_ids = tuple(catalog["WAFER_ID"].drop_duplicates())

    design_ids = list(catalog["DESIGN_ID"].drop_duplicates())

    sigma_point_sql = f"""

                            SELECT DISTINCT

                            LOT_ID,

                            DESIGN_ID,

                            WAFER_ID,

                            WAFER_SCRIBE,

                            MFG_PROCESS_STEP,

                            TEST_VALUE,

                            TEST_ID,

                            BRIEF_COMMON_TEST_ID,

                            COMMON_TEST_ID,

                            CAST(RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,

                            CAST(RUN_COMPLETE_DATETIME AS STRING) AS RUN_COMPLETE_DATETIME,

                            CAST(RUN_OID AS STRING) AS RUN_OID,
                            
                            CAST(MEASUREMENT_OID AS STRING) AS MEASUREMENT_OID,
                            
                            WAFER_SPEC_ID

                            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_point` SIGMA_POINT

                            WHERE 1=1

                            AND SIGMA_POINT.RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'

                            AND LOT_ID IN {lot_ids}

                            AND WAFER_ID IN {wafer_ids}

                            AND MFG_PROCESS_STEP IN {process_steps}

                            AND COMMON_TEST_ID IN {common_test_ids}

                            AND DESIGN_ID IN UNNEST({design_ids})

                        """

    fpath = f"{output_dir}/f{facility}_idl_sigma_point_data"

    return sigma_point_sql, fpath


def update_sigma_point_data(file_path):
    idl_sigma_point_data = pd.read_parquet(file_path)
    if len(idl_sigma_point_data) > 0:
        idl_sigma_point_data["LOT_KEY"] = idl_sigma_point_data["LOT_ID"].apply(
            lambda x: x[:7]
        )
        dir_path = Path(file_path)
        for parquet_file in dir_path.glob("*.parquet"):
            parquet_file.unlink()
            print(f"Deleted: {parquet_file} to re-update")
        results_path = dir_path / "results.parquet"
        idl_sigma_point_data.to_parquet(results_path, index=False)

        print(f"SIGMA POINT DATA successfully downloaded to: {file_path}")
    del idl_sigma_point_data


def generate_query_idl_sigma_run_sql_and_path(
    facility, catalog_path, output_dir, common_test_ids
):
    """

        Downloads data from the query_idl_sigma_run table

        - Contains metadata related to the wafer process run

        INPUTS:

        - facility: str, facility number (4: Boise, 10: Singapore, etc.)

        - catalog: pd.DataFrame(), catalog data to use for pulling this metrology data

        - output_dir: str, path to directory where the temporary data will be saved
    >> temporary data is necessary for offloading memory during data download process

        - common_test_ids: List, list of test ids to match when pulling data
    >> test ids describe what type of measurement was taken
    >> example values: ["R2RControlEnabled - RUN_PROC_DATA"]

        OUTPUTS:

        - fpath: str, path to where the catalog is downloaded

    """
    catalog = pd.read_parquet(catalog_path)
    catalog.dropna(
        subset=[
            "RUN_COMPLETE_DATE",
            "DESIGN_ID",
            "LOT_ID",
            "WAFER_ID",
            "MFG_PROCESS_STEP",
        ],
        inplace=True,
    )

    process_steps = tuple(catalog["MFG_PROCESS_STEP"].drop_duplicates())

    if len(process_steps) <= 1:
        process_steps = str(process_steps).replace(",)", ")")

    common_test_ids = tuple(common_test_ids)

    if len(common_test_ids) <= 1:
        common_test_ids = str(common_test_ids).replace(",)", ")")

    start_date = min(catalog["RUN_COMPLETE_DATE"])

    end_date = max(catalog["RUN_COMPLETE_DATE"])

    run_dates = tuple(catalog["RUN_COMPLETE_DATE"].drop_duplicates())

    if len(run_dates) <= 1:
        run_dates = str(run_dates).replace(",)", ")")

    lot_ids = tuple(catalog["LOT_ID"].drop_duplicates())

    wafer_ids = tuple(catalog["WAFER_ID"].drop_duplicates())

    design_ids = list(catalog["DESIGN_ID"].drop_duplicates())

    sigma_run_sql = f"""

                        WITH WAFER_LOT_DATA AS (

                          SELECT DISTINCT

                        DWH_SRCID

                        ,MFG_FACILITY_ID

                        ,DESIGN_ID

                        ,RUN_COMPLETE_DATE

                        ,RUN_COMPLETE_DATETIME

                        ,WAFER_RUN_OID

                        ,LOT_ID

                        ,WAFER_ID

                        ,MFG_PROCESS_STEP

                        ,RUN_OID

                        ,METRIC_POSITION

                        ,WAFER_TYPE

                        ,WAFER_SPEC_ID

                        ,WAFER_SCRIBE

                        ,SLOT_NO

                        ,SOURCE_FILE

                        FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer`

                        WHERE 1=1

                        AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'

                        AND MFG_PROCESS_STEP IN {process_steps}

                        AND LOT_ID IN {lot_ids}

                        AND WAFER_ID IN {wafer_ids}

                        AND DESIGN_ID IN UNNEST({design_ids})

                        ),

                        SIGMA_RUN AS (

                          SELECT DISTINCT

                          MFG_AREA_ID,

                          RUN_OID,

                          EQUIPMENT_ID,

                          PROCESS_ID,

                          PROCESS_SPEC_ID,

                          RUN_COMPLETE_DATE,

                          FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_run`

                          WHERE 1=1

                          AND RUN_OID IN (

                            SELECT DISTINCT

                            RUN_OID

                            FROM WAFER_LOT_DATA

                          )

                        )

                        SELECT DISTINCT

                        SIGMA_RUN_SUMMARY.DWH_SRCID,

                        SIGMA_RUN_SUMMARY.MFG_FACILITY_ID,

                        WAFER_LOT_DATA.DESIGN_ID,

                        WAFER_LOT_DATA.LOT_ID,

                        WAFER_LOT_DATA.WAFER_ID,

                        WAFER_LOT_DATA.WAFER_SCRIBE,

                        WAFER_LOT_DATA.MFG_PROCESS_STEP,

                        CAST(SIGMA_RUN.RUN_OID AS STRING) AS RUN_OID,

                        SIGMA_RUN.EQUIPMENT_ID,

                        SIGMA_RUN.PROCESS_ID,

                        METRIC_FLAG,

                        CAST(SIGMA_RUN_SUMMARY.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,

                        CAST(TIME(SIGMA_RUN_SUMMARY.RUN_COMPLETE_DATETIME) AS STRING) AS RUN_COMPLETE_TIME,

                        CAST(SIGMA_RUN_SUMMARY.RUN_COMPLETE_DATETIME AS STRING) AS RUN_COMPLETE_DATETIME,

                        CAST(FORMAT_DATE('%Y-%U', SIGMA_RUN_SUMMARY.RUN_COMPLETE_DATETIME) AS STRING) AS WORK_WEEK,

                        ITEM_SEQ_NO,

                        TEST_VALUE,

                        TEST_ID,

                        BRIEF_COMMON_TEST_ID,

                        COMMON_TEST_ID,

                        SIGMA_RUN_SUMMARY.SOURCE_FILE,

                        FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_run_summary` SIGMA_RUN_SUMMARY

                        INNER JOIN SIGMA_RUN

                        ON (

                          SIGMA_RUN_SUMMARY.RUN_OID = SIGMA_RUN.RUN_OID

                          AND SIGMA_RUN_SUMMARY.RUN_COMPLETE_DATE = SIGMA_RUN.RUN_COMPLETE_DATE

                        )

                        INNER JOIN WAFER_LOT_DATA

                        ON (

                          SIGMA_RUN_SUMMARY.RUN_COMPLETE_DATETIME= WAFER_LOT_DATA.RUN_COMPLETE_DATETIME

                          AND SIGMA_RUN_SUMMARY.RUN_OID = WAFER_LOT_DATA.RUN_OID

                          AND SIGMA_RUN_SUMMARY.SOURCE_FILE= WAFER_LOT_DATA.SOURCE_FILE

                        )

                        WHERE 1=1

                        AND SIGMA_RUN_SUMMARY.RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'

                        AND COMMON_TEST_ID IN {common_test_ids}

                        AND DESIGN_ID IN UNNEST({design_ids})

                    """

    fpath = f"{output_dir}/f{facility}_idl_sigma_run_data"

    return sigma_run_sql, fpath


def update_sigma_run_data(file_path):
    idl_sigma_point_data = pd.read_parquet(file_path)
    if len(idl_sigma_point_data) > 0:
        idl_sigma_point_data["LOT_KEY"] = idl_sigma_point_data["LOT_ID"].apply(
            lambda x: x[:7]
        )
        dir_path = Path(file_path)
        for parquet_file in dir_path.glob("*.parquet"):
            parquet_file.unlink()
            print(f"Deleted: {parquet_file} to re-update")
        results_path = dir_path / "results.parquet"
        idl_sigma_point_data.to_parquet(results_path, index=False)

        print(f"SIGMA RUN DATA successfully downloaded to: {file_path}")
    del idl_sigma_point_data


def generate_query_idl_sigma_wafer_sql_and_path(
    facility, catalog_path, output_dir, common_test_ids
):
    """

        Downloads data from the query_idl_sigma_wafer table

        - Contains metadata related to the wafer properties

        INPUTS:

        - facility: str, facility number (4: Boise, 10: Singapore, etc.)

        - catalog: pd.DataFrame(), catalog data to use for pulling this metrology data

        - output_dir: str, path to directory where the temporary data will be saved
    >> temporary data is necessary for offloading memory during data download process

        - common_test_ids: List, list of test ids to match when pulling data
    >> test ids describe what type of measurement was taken
    >> example values: ['PROCESS_CHAMBER - DG_AD']

        OUTPUTS:

        - fpath: str, path to where the catalog is downloaded

    """
    catalog = pd.read_parquet(catalog_path)
    catalog.dropna(
        subset=[
            "RUN_COMPLETE_DATE",
            "DESIGN_ID",
            "LOT_ID",
            "WAFER_ID",
            "MFG_PROCESS_STEP",
        ],
        inplace=True,
    )

    process_steps = tuple(catalog["MFG_PROCESS_STEP"].drop_duplicates())

    if len(process_steps) <= 1:
        process_steps = str(process_steps).replace(",)", ")")

    common_test_ids = tuple(common_test_ids)

    if len(common_test_ids) <= 1:
        common_test_ids = str(common_test_ids).replace(",)", ")")

    start_date = min(catalog["RUN_COMPLETE_DATE"])

    end_date = max(catalog["RUN_COMPLETE_DATE"])

    lot_ids = tuple(catalog["LOT_ID"].drop_duplicates())

    wafer_ids = tuple(catalog["WAFER_ID"].drop_duplicates())

    design_ids = list(catalog["DESIGN_ID"].drop_duplicates())

    sigma_wafer_sql = f"""

                            SELECT DISTINCT

                            DESIGN_ID,

                            LOT_ID,

                            WAFER_ID,

                            WAFER_SCRIBE,

                            CAST(RUN_OID AS STRING) AS RUN_OID,

                            TEST_VALUE,

                            CAST(SIGMA_WAFER_SUMMARY.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,

                            CAST(TIME(SIGMA_WAFER_SUMMARY.RUN_COMPLETE_DATETIME) AS STRING) AS RUN_COMPLETE_TIME,

                            CAST(SIGMA_WAFER_SUMMARY.RUN_COMPLETE_DATETIME AS STRING) AS RUN_COMPLETE_DATETIME,

                            CAST(FORMAT_DATE('%Y-%U', SIGMA_WAFER_SUMMARY.RUN_COMPLETE_DATETIME) AS STRING) AS WORK_WEEK,

                            MFG_PROCESS_STEP,

                            COMMON_TEST_ID,
                            
                            WAFER_SPEC_ID,
                            
                            ITEM_SEQ_NO

                            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer_summary` SIGMA_WAFER_SUMMARY

                            WHERE 1=1

                            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'

                            AND MFG_PROCESS_STEP IN {process_steps}

                            AND LOT_ID IN {lot_ids}

                            AND WAFER_ID IN {wafer_ids}

                            AND COMMON_TEST_ID IN {common_test_ids}

                            AND DESIGN_ID IN UNNEST({design_ids})

                        """

    fpath = f"{output_dir}/f{facility}_idl_sigma_wafer_data"

    return sigma_wafer_sql, fpath


def update_sigma_wafer_data(file_path):
    idl_sigma_wafer_data = pd.read_parquet(file_path)
    if len(idl_sigma_wafer_data) > 0:
        idl_sigma_wafer_data["LOT_KEY"] = idl_sigma_wafer_data["LOT_ID"].apply(
            lambda x: x[:7]
        )
        dir_path = Path(file_path)
        for parquet_file in dir_path.glob("*.parquet"):
            parquet_file.unlink()
            print(f"Deleted: {parquet_file} to re-update")
        results_path = dir_path / "results.parquet"
        idl_sigma_wafer_data.to_parquet(results_path, index=False)

        print(f"SIGMA WAFER DATA successfully downloaded to: {file_path}")
    del idl_sigma_wafer_data


def columnize_sigma_data(
    data_path,
    columns_to_join_on=["DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
    step_name_column="MFG_PROCESS_STEP",
    test_id_column="COMMON_TEST_ID",
    test_value_column="TEST_VALUE",
    other_columns_to_keep=[],
    join_method="outer",
):
    """

    Generalized function for transforming the SIGMA data

    - Works based on the assumption that the lot/wafers are consistent across all different SIGMA tables

    - Collects the initial set of unique lot/wafers to build the transformed dataframe

    - Divides the flat data according to the different unique values in the step_name and test_id columns

    - Loops over all different combinations of step_name/test_id and structures the data based on wafer/lots

    - This function should work for all SIGMA tables that have COMMON_TEST_ID and TEST_VALUE as column name

    INPUTS:

    - data: pd.DataFrame(), the SIGMA table as a dataframe that has the COMMON_TEST_ID, and TEST_VALUE as columns

    - columns_to_join_on: List[str], list of columns to perform joins on (usually it is going to be lot/wafer id)

    - test_id_column: str, the column name that has the test_id name information

    - test_value_column: str, the column name that has the test_value information

    - other_columns_to_keep: List[str], list of any additional columns that needs to be preserved, this is optional

    - join_method: str, the pandas join method, can be 'inner', 'left', 'right' or 'outer. By default, it is outer

    OUTPUTS:

    - lot_wafers: pd.DataFrame(), pivoted data that maps all of the measurement and point rows to unique LOT/WAFERs

    TO DO:

    - Assertion statements and error catching can be implemented for robustness

    """
    data = pd.read_parquet(data_path)

    total_column_list = (
        columns_to_join_on + [step_name_column] + [test_id_column] + [test_value_column]
    )

    if len(other_columns_to_keep) > 0:
        total_column_list += other_columns_to_keep

    unique_step_test_ids = (
        data[[step_name_column, test_id_column]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    lot_wafers = data[columns_to_join_on].drop_duplicates().reset_index(drop=True)

    for index in range(len(unique_step_test_ids)):

        step_name = unique_step_test_ids[step_name_column].iloc[index]

        test_id = unique_step_test_ids[test_id_column].iloc[index]

        sub_data = data[
            (data[step_name_column] == step_name) & (data[test_id_column] == test_id)
        ].reset_index(drop=True)

        sub_data = sub_data[total_column_list]

        sub_data.rename(
            columns={test_value_column: f"{step_name}::{test_id}"}, inplace=True
        )

        if len(other_columns_to_keep) > 0:

            for column in other_columns_to_keep:
                sub_data.rename(
                    columns={column: f"{step_name}::{test_id}::{column}"}, inplace=True
                )

        sub_data.drop(columns=[step_name_column, test_id_column], axis=1, inplace=True)

        # Need to drop duplicates, or else there is risk of exploding dataframes

        sub_data = sub_data.drop_duplicates().reset_index(drop=True)

        lot_wafers = lot_wafers.merge(sub_data, on=columns_to_join_on, how=join_method)

    dir_path = Path(data_path)
    for parquet_file in dir_path.glob("*.parquet"):
        parquet_file.unlink()
        print(f"Deleted: {parquet_file} to re-update")
    results_path = dir_path / "results.parquet"
    lot_wafers.to_parquet(results_path)


def columnize_data(
    data,
    client,
    columns_to_join_on=["LOT_ID", "WAFER_ID"],
    step_name_column="TRAVELER_STEP",
    categorical_id_column="COMMON_TEST_ID",
    numeric_value_column="TEST_VALUE",
    other_columns_to_keep=[],
    join_method="outer",
):
    """

    Generalized function for transforming data (originally written for SIGMA, but generalized for FD)

    - Works based on the assumption that the lot/wafers are consistent across all different SIGMA tables

    - Collects the initial set of unique lot/wafers to build the transformed dataframe

    - Divides the flat data according to the different unique values in the step_name and test_id columns

    - Loops over all different combinations of step_name/test_id and structures the data based on wafer/lots

    - This function should work for all SIGMA tables that have COMMON_TEST_ID and TEST_VALUE as column name

    INPUTS:

    - data: pd.DataFrame(), the SIGMA table as a dataframe that has the COMMON_TEST_ID, and TEST_VALUE as columns

    - columns_to_join_on: List[str], list of columns to perform joins on (usually it is going to be lot/wafer id)

    - step_name_column: str, the column name that has the step name (either metro or process step) information

    - categorical_id_column: str, the column name that is the pivoting column, usually categorical (for FD, it is the SENSOR)

    - numeric_value_column: str, the column name that has the numeric data corresponding to the pivoting column

    - other_columns_to_keep: List[str], list of any additional columns that needs to be preserved, this is optional

    - join_method: str, the pandas join method, can be 'inner', 'left', 'right' or 'outer. By default, it is outer

    OUTPUTS:

    - lot_wafers: pd.DataFrame(), pivoted data that maps all of the measurement and point rows to unique LOT/WAFERs

    TO DO:

    - Assertion statements and error catching can be implemented for robustness

    """

    total_column_list = (
        columns_to_join_on
        + [step_name_column]
        + [categorical_id_column]
        + [numeric_value_column]
    )

    if len(other_columns_to_keep) > 0:
        total_column_list += other_columns_to_keep

    unique_step_test_ids = (
        data[[step_name_column, categorical_id_column]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    lot_wafers = data[columns_to_join_on].drop_duplicates().reset_index(drop=True)

    for index in range(len(unique_step_test_ids)):

        step_name = unique_step_test_ids[step_name_column].iloc[index]

        test_id = unique_step_test_ids[categorical_id_column].iloc[index]

        sub_data = data[
            (data[step_name_column] == step_name)
            & (data[categorical_id_column] == test_id)
        ].reset_index(drop=True)

        sub_data = sub_data[total_column_list]

        sub_data.rename(
            columns={numeric_value_column: f"{step_name}::{test_id}"}, inplace=True
        )

        if len(other_columns_to_keep) > 0:

            for column in other_columns_to_keep:
                sub_data.rename(
                    columns={column: f"{step_name}::{test_id}::{column}"}, inplace=True
                )

        sub_data.drop(
            columns=[step_name_column, categorical_id_column], axis=1, inplace=True
        )

        # Need to drop duplicates, or else there is risk of exploding dataframes

        sub_data = sub_data.drop_duplicates().reset_index(drop=True)

        lot_wafers = lot_wafers.merge(sub_data, on=columns_to_join_on, how=join_method)

    return lot_wafers


# Download the initial sigma catalog to set up all subsequent data pulls


def uc2_sigma_full_catalog_query(
    bigquery_manager: BigQueryJobsManager,
    stage_config_obj,
    stage_job_id,
    full_catalog_query,
    destination_folder_path,
    declarations_query,
):

    job_creation_time = stage_config_obj.datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    job_name = (
        stage_config_obj.datacatalog_session_record.name.lower().replace(" ", "_")
        + "_FULL_CATALOG"
    )

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_REGISTRATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=25,
            progress_message="[1] 1/4 Started full catalog query registration",
        ),
    )

    bq_job_ids, bq_job_objects, result_folder_blobs, bq_job_indexes = (
        bigquery_manager_query_registration(
            bigquery_manager, full_catalog_query, declarations_query
        )
    )
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 50
    current_status.job_stage_status.progress_message = (
        "[1] 2/4 Started execution full catalog"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_query_monitoring(bigquery_manager, bq_job_objects, stage_job_id)
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.progress_message = (
        "[1] 3/4 Started query result full catalog"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )
    Path(destination_folder_path).mkdir(parents=True, exist_ok=True)
    bigquery_manager_results_download(
        bigquery_manager,
        result_folder_blobs,
        job_creation_time,
        job_name,
        destination_folder_path,
    )

    current_status.job_stage_status.progress_percentage = 100
    current_status.job_stage_status.progress_message = "[1] 4/4 completed full catalog"
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )


def uc2_sigma_measurement_summary_method(
    bigquery_manager: BigQueryJobsManager,
    stage_config_obj,
    stage_job_id,
    idl_sigma_measurement_summary_query,
    idl_sigma_measurement_summary_path,
):
    job_creation_time = stage_config_obj.datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    job_name = (
        stage_config_obj.datacatalog_session_record.name.lower().replace(" ", "_")
        + "_SIGMA_MEASUREMENT_SUMMARY"
    )

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_REGISTRATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=25,
            progress_message="[2] 1/4 Started measurement summary query registration",
        ),
    )

    bq_job_ids, bq_job_objects, result_folder_blobs, bq_job_indexes = (
        bigquery_manager_query_registration(
            bigquery_manager, idl_sigma_measurement_summary_query
        )
    )
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 50
    current_status.job_stage_status.progress_message = (
        "[2] 2/4 Started execution measurement_summary"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_query_monitoring(bigquery_manager, bq_job_objects, stage_job_id)
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.progress_message = (
        "[2] 3/4 Started query result measurement summary"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_results_download(
        bigquery_manager,
        result_folder_blobs,
        job_creation_time,
        job_name,
        idl_sigma_measurement_summary_path,
    )

    current_status.job_stage_status.progress_percentage = 100
    current_status.job_stage_status.progress_message = (
        "[2] 4/4 completed measurement summary"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )


def uc2_sigma_point_data_method(
    bigquery_manager: BigQueryJobsManager,
    stage_config_obj,
    stage_job_id,
    idl_sigma_measurement_summary_query,
    idl_sigma_measurement_summary_path,
):
    job_creation_time = stage_config_obj.datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    job_name = (
        stage_config_obj.datacatalog_session_record.name.lower().replace(" ", "_")
        + "_SIGMA_POINT_DATA"
    )

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_REGISTRATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=25,
            progress_message="[3] 1/4 Started point data query registration",
        ),
    )

    bq_job_ids, bq_job_objects, result_folder_blobs, bq_job_indexes = (
        bigquery_manager_query_registration(
            bigquery_manager, idl_sigma_measurement_summary_query
        )
    )
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 50
    current_status.job_stage_status.progress_message = (
        "[3] 2/4 Started execution point data"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_query_monitoring(bigquery_manager, bq_job_objects, stage_job_id)
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.progress_message = (
        "[3] 3/4 Started query result point data"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_results_download(
        bigquery_manager,
        result_folder_blobs,
        job_creation_time,
        job_name,
        idl_sigma_measurement_summary_path,
    )

    current_status.job_stage_status.progress_percentage = 100
    current_status.job_stage_status.progress_message = "[3] 4/4 completed point data"
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )


def uc2_sigma_run_data_method(
    bigquery_manager: BigQueryJobsManager,
    stage_config_obj,
    stage_job_id,
    idl_sigma_measurement_summary_query,
    idl_sigma_measurement_summary_path,
):
    job_creation_time = stage_config_obj.datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    job_name = (
        stage_config_obj.datacatalog_session_record.name.lower().replace(" ", "_")
        + "_SIGMA_RUN_DATA"
    )

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_REGISTRATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=25,
            progress_message="[4] 1/4 Started run data query registration",
        ),
    )

    bq_job_ids, bq_job_objects, result_folder_blobs, bq_job_indexes = (
        bigquery_manager_query_registration(
            bigquery_manager, idl_sigma_measurement_summary_query
        )
    )
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 50
    current_status.job_stage_status.progress_message = (
        "[4] 2/4 Started execution run data"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_query_monitoring(bigquery_manager, bq_job_objects, stage_job_id)
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.progress_message = (
        "[4] 3/4 Started query result run data"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_results_download(
        bigquery_manager,
        result_folder_blobs,
        job_creation_time,
        job_name,
        idl_sigma_measurement_summary_path,
    )

    current_status.job_stage_status.progress_percentage = 100
    current_status.job_stage_status.progress_message = "[4] 4/4 completed run data"
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )


def uc2_sigma_wafer_data_method(
    bigquery_manager: BigQueryJobsManager,
    stage_config_obj,
    stage_job_id,
    idl_sigma_measurement_summary_query,
    idl_sigma_measurement_summary_path,
):
    job_creation_time = stage_config_obj.datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    job_name = (
        stage_config_obj.datacatalog_session_record.name.lower().replace(" ", "_")
        + "_SIGMA_RUN_DATA"
    )

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_REGISTRATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=25,
            progress_message="[5] 1/4 Started wafer data query registration",
        ),
    )

    bq_job_ids, bq_job_objects, result_folder_blobs, bq_job_indexes = (
        bigquery_manager_query_registration(
            bigquery_manager, idl_sigma_measurement_summary_query
        )
    )
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 50
    current_status.job_stage_status.progress_message = (
        "[5] 2/4 Started execution wafer data"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_query_monitoring(bigquery_manager, bq_job_objects, stage_job_id)
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.progress_message = (
        "[5] 3/4 Started query result wafer data"
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_results_download(
        bigquery_manager,
        result_folder_blobs,
        job_creation_time,
        job_name,
        idl_sigma_measurement_summary_path,
    )

    current_status.job_stage_status.progress_percentage = 100
    current_status.job_stage_status.progress_message = "[5] 4/4 completed wafer data"
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )


def join_uc2_sigma_results(
    measurement_path, point_path, run_path, wafer_path, results_path
):
    transformed_measurement_data = pd.read_parquet(measurement_path)
    transformed_point_data = pd.read_parquet(point_path)
    transformed_run_data = pd.read_parquet(run_path)
    transformed_wafer_data = pd.read_parquet(wafer_path)

    final_sigma_data = transformed_measurement_data.merge(
        transformed_point_data,
        on=["DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
        how="outer",
    )

    # Outer join 2
    final_sigma_data = final_sigma_data.merge(
        transformed_run_data,
        on=["DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
        how="outer",
    )

    # Outer join 3
    final_sigma_data = final_sigma_data.merge(
        transformed_wafer_data,
        on=["DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
        how="outer",
    )

    final_sigma_data.to_parquet(results_path)

    # # ONLY IF FD AGGREGATE IS DOWNLOADED
    # # For FD aggregate, we omit WAFER_SCRIBE from the joining index
    # # Outer join 4
    # final_sigma_data = final_sigma_data.merge(
    #     FD_AGGREGATE_DATA,
    #     on = ['DESIGN_ID', 'LOT_ID', 'WAFER_ID'],
    #     how = 'outer'
    # )


def limit_columns(
    structured_inputs_file_path: str,
    file_path: str,
    table: str,
    override_filepath: bool = True,
):

    # Use the data structure from new gql function to get exact column name pairs
    if table not in [
        "idl_sigma_wafer_summary",
        "idl_sigma_run_summary",
        "idl_sigma_point",
        "idl_sigma_measurement_summary",
    ]:
        raise ValueError(f"Not known value for table {table}")
    # Read data once
    data_structure = pd.read_parquet(structured_inputs_file_path)
    transformed_data = pd.read_parquet(file_path)

    # Filter the data_structure for the relevant table
    filtered_data_structure = data_structure[data_structure["table"] == table]

    step_names = filtered_data_structure["step_names"].values
    parameter_names = filtered_data_structure["parameter_names"].values

    columns_to_keep = [
        column
        for column in transformed_data.columns
        if any(
            step_name in column and parameter_name in column
            for step_name, parameter_name in zip(step_names, parameter_names)
        )
    ]

    # Select and deduplicate relevant columns from transformed_data
    required_columns = ["DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"] + list(
        set(columns_to_keep)
    )

    transformed_data = (
        transformed_data[required_columns].drop_duplicates().reset_index(drop=True)
    )

    if override_filepath:
        fpath = Path(file_path)
        if fpath.is_dir():
            transformed_data.to_parquet(fpath/"results.parquet")
        else:
            transformed_data.to_parquet(fpath)
    else:
        raise NotImplementedError("currently handling only for overriding")

def check_subset_to_gql(file_path, run_parameters,wafer_parameters,measurement_steps,measurement_parameters,point_steps,point_parameters):
    # this method confirms that the selected values we got are infact from gql and not added by user ..etc
    df = pd.read_parquet(file_path)

    if not set(run_parameters).issubset(df['run_parameters'].unique()):
        return False
    if not set(wafer_parameters).issubset(df['wafer_parameters'].unique()):
        return False
    if not set(measurement_steps).issubset(df['measurement_steps'].unique()):
        return False
    if not set(measurement_parameters).issubset(df['measurement_parameters'].unique()):
        return False
    if not set(point_steps).issubset(df['point_steps'].unique()):
        return False
    if not set(point_parameters).issubset(df['point_parameters'].unique()):
        return False

    return True



# TODO: many methods here can be optimized there are 4 fnctions for same fnctionality
def uc2_sigma_data_pull(
    bigquery_manager: BigQueryJobsManager, stage_config_obj, stage_job_id, output_dir
):

    fd_data_pull_job_config: FdDataPullJobConfig = stage_config_obj.stage_job_record
    inputs: UC2SigmaDataPullInput = fd_data_pull_job_config.stage_config.inputs

    if inputs is None:
        raise ValueError(
            "The inputs for UC2 sigma data pull is None , UC2SigmaDataPullInput"
        )

    facility = int(inputs.facilities.selected_values[0])
    startdate = inputs.start_date
    enddate = inputs.end_date
    days_to_pad = 10  # TODO: make this input from user
    steps = inputs.traveler_steps.selected_values
    designid = inputs.design_ids.selected_values[0]

    # to get structured df
    only_gql_flow = (inputs.gql_file_details is not None and inputs.gql_file_details.gql_file_path)
    if only_gql_flow and str(inputs.measurement_steps.file_path) != '.': #having file in measurement steps => not just gql flow , TODO : add explicit variable to find this as there can be add_item
        only_gql_flow = False

    sigma_measurement_steps = inputs.measurement_steps.selected_values
    sigma_point_steps = inputs.point_steps.selected_values
    sigma_measurement_parameters = inputs.measurement_parameters.selected_values
    sigma_point_parameters = inputs.point_parameters.selected_values
    sigma_run_parameters = inputs.run_parameters.selected_values
    sigma_wafer_parameters = inputs.wafer_parameters.selected_values
    structured_inputs_file_path = None
    if only_gql_flow : #verify if user added values via manually (additem)
        only_gql_flow = check_subset_to_gql(inputs.gql_file_details.parquet_file_path, sigma_run_parameters, sigma_wafer_parameters,
                           sigma_measurement_steps, sigma_measurement_parameters, sigma_point_steps,
                           sigma_point_parameters)
        structured_inputs_file_path = (
            str(inputs.gql_file_details.parquet_file_path).split(".")[0] + "_structured.parquet" if only_gql_flow else ''
        )


    # overriding..steps..as given in notebook
    steps = tuple(set(sigma_measurement_steps + sigma_point_steps))

    # FULL CATALOG [SUB STAGE-1]
    declarations_query, full_catalog_query, catalog_path = (
        generate_query_idl_sigma_catalog_query_and_path(
            facility=facility,
            startdate=startdate,
            enddate=enddate,
            days_to_pad=days_to_pad,
            steps=steps,
            designid=designid,
            output_dir=output_dir,
        )
    )
    uc2_sigma_full_catalog_query(
        bigquery_manager,
        stage_config_obj,
        stage_job_id,
        full_catalog_query,
        catalog_path,
        declarations_query,
    )
    # We're going to split the catalog based on the step names
    measurement_catalog_path, point_catalog_path = extract_sigma_catalogs(
        catalog_path=catalog_path,
        sigma_measurement_steps=sigma_measurement_steps,
        sigma_point_steps=sigma_point_steps,
    )

    # SIGMA MEASUREMENT SUMMARY [SUB STAGE-2]
    idl_sigma_measurement_summary_query, idl_sigma_measurement_summary_path = (
        generate_query_idl_sigma_measurement_summary_sql_and_path(
            facility=facility,
            catalog_path=measurement_catalog_path,
            output_dir=output_dir,
            common_test_ids=sigma_measurement_parameters,
        )
    )
    uc2_sigma_measurement_summary_method(
        bigquery_manager,
        stage_config_obj,
        stage_job_id,
        idl_sigma_measurement_summary_query,
        idl_sigma_measurement_summary_path,
    )
    update_simga_measurement_summary_data(idl_sigma_measurement_summary_path)

    # SIGMA POINT SUMMARY [SUB STAGE-3]
    idl_sigma_point_data_query, idl_sigma_point_data_path = (
        generate_query_idl_sigma_point_and_path(
            facility=facility,
            catalog_path=point_catalog_path,
            output_dir=output_dir,
            common_test_ids=sigma_point_parameters,
        )
    )
    uc2_sigma_point_data_method(
        bigquery_manager,
        stage_config_obj,
        stage_job_id,
        idl_sigma_point_data_query,
        idl_sigma_point_data_path,
    )
    update_sigma_point_data(idl_sigma_point_data_path)

    # SIGMA RUN DATA [SUB STAGE-4]

    # Download sigma run data
    idl_sigma_run_data_path = None
    if sigma_run_parameters:
        idl_sigma_run_data_query, idl_sigma_run_data_path = (
            generate_query_idl_sigma_run_sql_and_path(
                facility=facility,
                catalog_path=point_catalog_path,
                output_dir=output_dir,
                common_test_ids=sigma_run_parameters,
            )
        )
        uc2_sigma_run_data_method(
            bigquery_manager,
            stage_config_obj,
            stage_job_id,
            idl_sigma_run_data_query,
            idl_sigma_run_data_path,
        )
        update_sigma_run_data(idl_sigma_run_data_path)

    # SIGMA wafer DATA [SUB STAGE-5]
    idl_sigma_wafer_data_query, idl_sigma_wafer_data_path = (
        generate_query_idl_sigma_wafer_sql_and_path(
            facility=facility,
            catalog_path=point_catalog_path,
            output_dir=output_dir,
            common_test_ids=sigma_wafer_parameters,
        )
    )
    uc2_sigma_wafer_data_method(
        bigquery_manager,
        stage_config_obj,
        stage_job_id,
        idl_sigma_wafer_data_query,
        idl_sigma_wafer_data_path,
    )
    update_sigma_wafer_data(idl_sigma_wafer_data_path)

    print(idl_sigma_measurement_summary_path)

    print(idl_sigma_point_data_path)

    print(idl_sigma_run_data_path)

    print(idl_sigma_wafer_data_path)

    # add new cols to
    def add_wafer_spec_common_test_id_column(file_path):
        df = pd.read_parquet(file_path)
        df['WAFER_SPEC_ID::COMMON_TEST_ID'] = df['WAFER_SPEC_ID'] + '::' + df['COMMON_TEST_ID']
        df.to_parquet(Path(file_path)/"results.parquet")

    add_wafer_spec_common_test_id_column(idl_sigma_measurement_summary_path)
    columnize_sigma_data(
        idl_sigma_measurement_summary_path,
        step_name_column='MFG_PROCESS_STEP',
        test_id_column='WAFER_SPEC_ID::COMMON_TEST_ID',
        test_value_column='TEST_VALUE',
        columns_to_join_on=['DESIGN_ID', 'LOT_ID', 'WAFER_ID', 'WAFER_SCRIBE'],
        other_columns_to_keep=['RUN_COMPLETE_DATETIME']
    )

    add_wafer_spec_common_test_id_column(idl_sigma_point_data_path)
    columnize_sigma_data(
        idl_sigma_point_data_path,
        columns_to_join_on=["DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
        other_columns_to_keep=["RUN_COMPLETE_DATETIME"],
        test_id_column='WAFER_SPEC_ID::COMMON_TEST_ID',
        test_value_column='TEST_VALUE',
    )

    if idl_sigma_run_data_path:
        columnize_sigma_data(
            idl_sigma_run_data_path,
            columns_to_join_on=["DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
            other_columns_to_keep=["PROCESS_ID", "RUN_COMPLETE_DATETIME", "EQUIPMENT_ID"],
        )

    def add_wafer_spec_item_seq_common_test_id_column(file_path):
        df = pd.read_parquet(file_path)
        df['WAFER_SPEC_ID::ITEM_SEQ_NO::COMMON_TEST_ID'] = df['WAFER_SPEC_ID'] + '::' + df['ITEM_SEQ_NO'].astype(
            str) + '::' + df['COMMON_TEST_ID']
        df.to_parquet(Path(file_path)/"results.parquet")

    add_wafer_spec_item_seq_common_test_id_column(idl_sigma_wafer_data_path)
    columnize_sigma_data(
        idl_sigma_wafer_data_path,
        columns_to_join_on=['DESIGN_ID', 'LOT_ID', 'WAFER_ID', 'WAFER_SCRIBE', 'WORK_WEEK'],
        other_columns_to_keep=['RUN_COMPLETE_DATETIME'],
        test_id_column='WAFER_SPEC_ID::ITEM_SEQ_NO::COMMON_TEST_ID',
        test_value_column='TEST_VALUE',
        join_method='outer'
    )

    # limit columns
    if only_gql_flow:
        print("only gql flow...limiting columns")
        limit_columns(
            structured_inputs_file_path,
            idl_sigma_measurement_summary_path,
            "idl_sigma_measurement_summary",
        )
        limit_columns(
            structured_inputs_file_path, idl_sigma_point_data_path, "idl_sigma_point"
        )
        limit_columns(
            structured_inputs_file_path, idl_sigma_run_data_path, "idl_sigma_run_summary"
        )
        limit_columns(
            structured_inputs_file_path,
            idl_sigma_wafer_data_path,
            "idl_sigma_wafer_summary",
        )

    # currently commenting joining as edge cases need to be taken care
    # final_joined_results_file = (
    #     Path(idl_sigma_measurement_summary_path).parent
    #     / "joined_data/results.parquet"
    # )
    #
    # final_joined_results_file.parent.mkdir(parents=True, exist_ok=True)
    #
    # join_uc2_sigma_results(
    #     idl_sigma_measurement_summary_path,
    #     idl_sigma_point_data_path,
    #     idl_sigma_run_data_path,
    #     idl_sigma_wafer_data_path,
    #     final_joined_results_file,
    # )

    return (
        idl_sigma_measurement_summary_path,
        idl_sigma_point_data_path,
        idl_sigma_run_data_path,
        idl_sigma_wafer_data_path,
    )
    # # The data is usually pretty small. It is safe to read all of them at once.
    #
    # idl_sigma_measurement_summary_data = pd.read_parquet(idl_sigma_measurement_summary_data_path)
    #
    # idl_sigma_point_data = pd.read_parquet(idl_sigma_point_data_path)
    #
    # idl_sigma_run_data = pd.read_parquet(idl_sigma_run_data_path)
    #
    # idl_sigma_wafer_data = pd.read_parquet(idl_sigma_wafer_data_path)
