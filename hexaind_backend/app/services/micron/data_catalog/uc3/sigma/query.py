import glob
import os
from copy import deepcopy

import pandas as pd

from typing import List

# def generate_mfg_steps_query(
#     steps: List[str],
#     keys: List[str],
#     fab: str,
#     start_date: str,
#     end_date: str,
#     design_id: str
# ) -> str:
#     # Generate tuples for steps and keys using repr for quoting
#     t_steps = "([" + ", ".join(repr(step) for step in steps) + ")"
#     t_keys = "(" + ", ".join(repr(key) for key in keys) + ")"
    
#     print(f"Steps Tuple: {t_steps}")
#     print(f"Keys Tuple: {t_keys}")
    
#     return (
#         f"WITH step_array AS (\n"
#         f"    SELECT \n"
#         f"        step\n"
#         f"    FROM\n"
#         f"        UNNEST{t_steps} AS step\n"
#         f"),\n"
#         f"key_array AS (\n"
#         f"    SELECT \n"
#         f"        key\n"
#         f"    FROM\n"
#         f"        UNNEST{t_keys} AS key\n"
#         f"),\n"
#         f"selected_steps AS (\n"
#         f"    SELECT DISTINCT\n"
#         f"        CONCAT(step_array.step, '-', key_array.key) AS steps\n"
#         f"    FROM \n"
#         f"        step_array\n"
#         f"        CROSS JOIN key_array\n"
#         f")\n"
#         f"SELECT DISTINCT\n"
#         f"    MFG_PROCESS_STEP,\n"
#         f"    CAST(RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE\n"
#         f"FROM `gdw-prod-data.fab_{fab}_sigma.idl_sigma_lot`,\n"
#         f"UNNEST(ARRAY(SELECT steps FROM selected_steps)) AS STEP_NAMES_LIST\n"
#         f"WHERE \n"
#         f"    RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'\n"
#         f"    AND MFG_PROCESS_STEP LIKE CONCAT(STEP_NAMES_LIST, '%')\n"
#         f"    AND DESIGN_ID = '{design_id}'"
#     )


def generate_mfg_steps_query(steps, keys, fab, start_date, end_date, design_id):
    # t_steps = str(tuple(steps)).replace(',)',')')
    # t_keys = str(tuple(keys)).replace(',)',')')
    # print(t_keys)
    # print(t_steps)
    return f"""WITH step_array AS (
    SELECT 
        step
    FROM
        UNNEST({steps}) AS step)
    
    , key_array AS (
    SELECT 
        key
    FROM
        UNNEST({keys}) AS key)
    
    , selected_steps as (
    SELECT DISTINCT
        concat(step_array.step, '-', key_array.key) AS steps,
    FROM 
        step_array
        CROSS JOIN key_array
    )
    
    SELECT DISTINCT
    MFG_PROCESS_STEP,
    CAST(RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
    FROM `gdw-prod-data.fab_{fab}_sigma.idl_sigma_lot`
    JOIN UNNEST(ARRAY(SELECT steps FROM selected_steps)) AS STEP_NAMES_LIST
    WHERE 1=1
    AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
    AND MFG_PROCESS_STEP LIKE '' || STEP_NAMES_LIST || '%'
    AND DESIGN_ID = '{design_id}'
    """


def generate_optional_query(wafer_test_id_pairs, include_back):
    optional_query = ""
    # Then grab the all of the test ids from the data
    if len(wafer_test_id_pairs) > 0:
        optional_query += f"    AND ((\n    "
        for unique_test_id_pair in wafer_test_id_pairs:
            for unique_test_id in unique_test_id_pair:
                optional_query += f"COMMON_TEST_ID LIKE '%{unique_test_id}%' AND\n    "
            optional_query = optional_query[:-9]
            optional_query += f"\n    )\n    OR\n    (\n     "
        optional_query = optional_query[:-16]
        optional_query += "  )\n),"

    optional_query = optional_query[:-2]

    # If INCLUDE_BACK is True, then keep everything
    # If INCLUDE_BACK is False, then exclude it
    if include_back:
        pass
    else:
        optional_query += (
            f"\n    AND NOT CONTAINS_SUBSTR(summary.COMMON_TEST_ID, 'back')"
        )
    return optional_query


def generate_wafer_query(
    fab,
    design_id,
    start_date,
    end_date,
    start_date_padding,
    end_date_padding,
    wafer_test_id_pairs,
    unique_mfg_process_steps,
    include_back,
    optional_query,
    filtered_lot_ids = None,
    filtered_wafer_ids = None,
):
    lot_ids_where_clause = f"AND lot.LOT_ID IN {filtered_lot_ids}" if filtered_lot_ids else ""
    wafer_ids_where_clause = f"AND wafer.WAFER_ID IN {filtered_wafer_ids}" if filtered_wafer_ids else ""
    declerations = f"""
    DECLARE DESIGNID STRING DEFAULT '{design_id}';
    DECLARE START_DATE DATE DEFAULT '{start_date}';
    DECLARE END_DATE DATE DEFAULT '{end_date}';
    DECLARE START_DATE_PADDING INT64 DEFAULT {start_date_padding};
    DECLARE END_DATE_PADDING INT64 DEFAULT {end_date_padding};
    """
    # note: need to check . these queries can be further optimized as lotid and waferids filtering might not required if they are already filtered..
    wafer_query = f"""
    WITH filtered_lots AS (
      SELECT 
          lot.DESIGN_ID,
          lot.LOT_ID,
          lot.TRAVELER_ID,
          lot.MFG_PROCESS_STEP,
          CAST(lot.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
          CAST(FORMAT_DATE('%Y-%m', lot.RUN_COMPLETE_DATETIME) AS STRING) AS MONTH 
      FROM 
          `gdw-prod-data.fab_{fab}_sigma.idl_sigma_lot` lot
      WHERE 
          lot.RUN_COMPLETE_DATE BETWEEN START_DATE AND END_DATE
          AND lot.MFG_PROCESS_STEP IN {unique_mfg_process_steps}
          AND lot.DESIGN_ID = DESIGNID
          {lot_ids_where_clause}
    ),

    filtered_wafer AS (
      SELECT 
          wafer.DESIGN_ID,
          wafer.LOT_ID,
          wafer.WAFER_ID,
          wafer.MFG_PROCESS_STEP,
          CAST(wafer.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
          CAST(FORMAT_DATE('%Y-%m', wafer.RUN_COMPLETE_DATETIME) AS STRING) AS MONTH
      FROM 
          filtered_lots lot
      JOIN 
          `gdw-prod-data.fab_{fab}_sigma.idl_sigma_wafer` wafer
          ON lot.LOT_ID = wafer.LOT_ID 
          AND lot.DESIGN_ID = wafer.DESIGN_ID
          AND lot.MFG_PROCESS_STEP = wafer.MFG_PROCESS_STEP
      WHERE 
          wafer.RUN_COMPLETE_DATE BETWEEN START_DATE AND END_DATE
          {wafer_ids_where_clause}
    )
    SELECT DISTINCT
        summary.DESIGN_ID,
        summary.LOT_ID,
        summary.WAFER_ID,
        SAFE_CAST(summary.TEST_VALUE AS FLOAT64) AS TEST_VALUE,
        summary.MFG_PROCESS_STEP,
        summary.COMMON_TEST_ID,
        CAST(summary.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
        CAST(FORMAT_DATE('%Y-%U', summary.RUN_COMPLETE_DATE) AS STRING) AS WORK_WEEK
    FROM  
        `gdw-prod-data.fab_{fab}_sigma.idl_sigma_measurement_summary` summary
    JOIN 
        filtered_wafer wafer
        ON summary.LOT_ID = wafer.LOT_ID
        AND summary.WAFER_ID = wafer.WAFER_ID
        AND summary.DESIGN_ID = wafer.DESIGN_ID
        AND summary.MFG_PROCESS_STEP = wafer.MFG_PROCESS_STEP
    WHERE 
        summary.RUN_COMPLETE_DATE BETWEEN DATE_SUB(START_DATE, INTERVAL START_DATE_PADDING DAY) 
        AND DATE_ADD(END_DATE, INTERVAL END_DATE_PADDING DAY) 
    """
    # print(wafer_query + optional_query)
    return declerations, wafer_query + optional_query


def genereted_point_query(
    fab,
    design_id,
    start_date,
    end_date,
    start_date_padding,
    end_date_padding,
    point_steps_list,
    optional_query,
    filtered_lot_ids = None,
    filtered_wafer_ids = None,
):
    declarations = f"""
    DECLARE DESIGNID STRING DEFAULT '{design_id}';
    DECLARE START_DATE DATE DEFAULT '{start_date}';
    DECLARE END_DATE DATE DEFAULT '{end_date}';
    DECLARE START_DATE_PADDING INT64 DEFAULT {start_date_padding};
    DECLARE END_DATE_PADDING INT64 DEFAULT {end_date_padding};
    """
    lot_ids_where_clause = f"AND lot.LOT_ID IN {filtered_lot_ids}" if filtered_lot_ids else ""
    wafer_ids_where_clause = f"AND wafer.WAFER_ID IN {filtered_wafer_ids}" if filtered_wafer_ids else ""
    
    point_query = f"""(

        WITH filtered_lots AS (
          SELECT DISTINCT
              lot.DESIGN_ID,
              lot.LOT_ID,
              lot.TRAVELER_ID,
              lot.MFG_PROCESS_STEP,
              CAST(lot.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
              CAST(FORMAT_DATE('%Y-%m', lot.RUN_COMPLETE_DATETIME) AS STRING) AS MONTH 
          FROM 
              `gdw-prod-data.fab_{fab}_sigma.idl_sigma_lot` lot
          WHERE 
              lot.RUN_COMPLETE_DATE BETWEEN START_DATE AND END_DATE
              AND lot.DESIGN_ID = DESIGNID
              AND lot.MFG_PROCESS_STEP IN {point_steps_list}
              {lot_ids_where_clause}
        ),

        filtered_wafer AS (
          SELECT DISTINCT
              wafer.DESIGN_ID,
              wafer.LOT_ID,
              wafer.WAFER_ID,
              wafer.MFG_PROCESS_STEP,
              CAST(wafer.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
              CAST(FORMAT_DATE('%Y-%m', wafer.RUN_COMPLETE_DATETIME) AS STRING) AS MONTH
          FROM 
              filtered_lots lot
          JOIN 
              `gdw-prod-data.fab_{fab}_sigma.idl_sigma_wafer` wafer
              ON lot.LOT_ID = wafer.LOT_ID 
              AND lot.DESIGN_ID = wafer.DESIGN_ID
              AND lot.MFG_PROCESS_STEP = wafer.MFG_PROCESS_STEP
          WHERE 
              wafer.RUN_COMPLETE_DATE BETWEEN START_DATE AND END_DATE
              {wafer_ids_where_clause}
        ),

        wafer_summary as (
            SELECT DISTINCT
                summary.DESIGN_ID,
                summary.LOT_ID,
                summary.WAFER_ID,
                SAFE_CAST(summary.TEST_VALUE AS FLOAT64) AS TEST_VALUE,
                summary.MFG_PROCESS_STEP,
                summary.COMMON_TEST_ID,
                CAST(summary.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
                CAST(FORMAT_DATE('%Y-%U', summary.RUN_COMPLETE_DATE) AS STRING) AS WORK_WEEK
            FROM 
                `gdw-prod-data.fab_{fab}_sigma.idl_sigma_measurement_summary` summary
            JOIN 
                filtered_wafer wafer
                ON summary.LOT_ID = wafer.LOT_ID
                AND summary.WAFER_ID = wafer.WAFER_ID
                AND summary.DESIGN_ID = wafer.DESIGN_ID
                AND summary.MFG_PROCESS_STEP = wafer.MFG_PROCESS_STEP
            WHERE 
                summary.RUN_COMPLETE_DATE BETWEEN DATE_SUB(START_DATE, INTERVAL START_DATE_PADDING DAY) 
                AND DATE_ADD(END_DATE, INTERVAL END_DATE_PADDING DAY) 
        """

    point_query += optional_query

    point_query += f"""
        ),

        filtered_point AS (
            SELECT DISTINCT
                point.POINT_INDEX,
                point.MEASUREMENT_OID,
                point.LOT_ID,
                point.WAFER_ID,
                SAFE_CAST(point.TEST_VALUE AS FLOAT64) AS TEST_VALUE,
                point.DESIGN_ID,
                point.MFG_PROCESS_STEP,
                point.COMMON_TEST_ID,
                CONCAT(point.MFG_PROCESS_STEP, '-', point.COMMON_TEST_ID) AS STEP_FULL, 
                point.RUN_COMPLETE_DATE,
                CAST(FORMAT_DATE('%Y-%U', point.RUN_COMPLETE_DATE) AS STRING) AS WORK_WEEK,
            FROM 
                `gdw-prod-data.fab_{fab}_sigma.idl_sigma_point` point
            JOIN 
                wafer_summary summary
                ON point.LOT_ID = summary.LOT_ID
                AND point.WAFER_ID = summary.WAFER_ID
                AND point.MFG_PROCESS_STEP = summary.MFG_PROCESS_STEP
                AND point.DESIGN_ID = summary.DESIGN_ID
                AND point.COMMON_TEST_ID like CONCAT("%", REPLACE(summary.COMMON_TEST_ID, 'RAW_WAFER (Mean)','RAW_POINT'), "%")
            WHERE
                summary.COMMON_TEST_ID not like '%- DG_CV (Mean)%' 
                AND point.RUN_COMPLETE_DATE BETWEEN START_DATE AND END_DATE
        )

        SELECT DISTINCT
            point.LOT_ID, 
            point.WAFER_ID,
            SAFE_CAST(point.TEST_VALUE AS FLOAT64) AS TEST_VALUE,
            point.DESIGN_ID,
            point.MFG_PROCESS_STEP,
            point.COMMON_TEST_ID,
            loc.NORMALIZED_X,
            loc.NORMALIZED_Y,
            loc.DIE_X,
            loc.DIE_Y,
            loc.POINT_INDEX,
            -- loc.MEASUREMENT_OID,
            CASE 
                WHEN SQRT(POW(loc.NORMALIZED_X,2) + POW(loc.NORMALIZED_Y,2)) < 67.08 THEN 'A' 
                WHEN SQRT(POW(loc.NORMALIZED_X,2) + POW(loc.NORMALIZED_Y,2)) > 67.08 
                    AND SQRT(POW(loc.NORMALIZED_X,2) + POW(loc.NORMALIZED_Y,2)) < 94.87 THEN 'B' 
                WHEN SQRT(POW(loc.NORMALIZED_X,2) + POW(loc.NORMALIZED_Y,2)) > 94.87 
                    AND SQRT(POW(loc.NORMALIZED_X,2) + POW(loc.NORMALIZED_Y,2)) < 116.19 THEN 'C' 
                WHEN SQRT(POW(loc.NORMALIZED_X,2) + POW(loc.NORMALIZED_Y,2)) > 116.19 
                    AND SQRT(POW(loc.NORMALIZED_X,2) + POW(loc.NORMALIZED_Y,2)) < 134.16 THEN 'D' 
                ELSE 'E' 
            END AS REGION,
            CAST(point.RUN_COMPLETE_DATE AS STRING) AS RUN_COMPLETE_DATE,
            CAST(FORMAT_DATE('%Y-%U', point.RUN_COMPLETE_DATE) AS STRING) AS WORK_WEEK,
        FROM 
            `gdw-prod-data.fab_{fab}_sigma.idl_sigma_point_location` loc
        INNER JOIN 
            filtered_point point
            ON loc.POINT_INDEX = point.POINT_INDEX
            AND loc.MEASUREMENT_OID = point.MEASUREMENT_OID
            AND loc.LOT_ID = point.LOT_ID
            AND loc.WAFER_ID = point.WAFER_ID
            AND loc.DESIGN_ID = point.DESIGN_ID
            AND loc.MFG_PROCESS_STEP = point.MFG_PROCESS_STEP
        WHERE 
            loc.RUN_COMPLETE_DATE BETWEEN START_DATE AND END_DATE
    );
    """
    return declarations, point_query


def genereted_traveler_query(fab, traveler_id):
    traveler_sql = f"""
    select distinct
        rtrim(f.mfg_facility_id) as Facility
        , substr(t.trav_id, 1, 4) as DesignId
        , rtrim(t.trav_id) as TravelerId
        , ts.trav_step_seq_no as StepSeqNo
        , rtrim(s.masking_level_code) as MaskingLevel
        , rtrim(s.step_name) as Step
        , rtrim(a.mfg_area_id) as MfgArea
    from gdw-prod-data.fab_{fab}_trv.traveler t
        inner join gdw-prod-data.fab_{fab}_trv.trav_step ts
            on t.trav_OID = ts.trav_OID
        inner join gdw-prod-data.fab_{fab}_ref.step s
            on ts.step_OID = s.step_OID
        inner join gdw-prod-data.fab_{fab}_ref.mfg_facility f
            on f.mfg_facility_OID = t.mfg_facility_OID
        left outer join gdw-prod-data.fab_{fab}_ref.step_data_for_fab sd
            on sd.mfg_facility_OID = t.mfg_facility_OID
            and sd.step_OID = s.step_OID
        left outer join gdw-prod-data.fab_{fab}_ref.mfg_area a
            on a.mfg_area_OID = sd.mfg_area_OID
    where 1=1
        -- and f.mfg_facility_id = 'FAB {fab}'
        and rtrim(t.trav_id) = '{traveler_id}'
    order by TravelerId, ts.trav_step_seq_no
    """
    return traveler_sql


def get_top_steps(wafer_traveler_dir, quantile):

    # Collect file paths and counts in a single list comprehension
    data = [
        (os.path.basename(path).replace(".parquet", ""), len(pd.read_parquet(path)))
        for path in glob.glob(os.path.join(wafer_traveler_dir, "*.parquet"))
    ]

    # Create DataFrame directly from the list of tuples
    df = pd.DataFrame(data, columns=["paths", "counts"])

    # Compute the quantile value
    val = df["counts"].quantile(quantile)

    # Filter and reset the index in one step
    top = df[df["counts"] >= val].reset_index(drop=True)

    return top


def get_new_steps_mappings(old_dr, wafer_traveler_dir, quantile):
    """
    Creates a mapping of new steps based on the specified quantile and updates them with data from old steps.
    Parameters:
    - old_dr (dict): Original dictionary containing step data.
    - wafer_traveler_dir (str): Directory containing .parquet files.
    - quantile (float): Quantile threshold to determine the top steps.

    Returns:
    - dict: A dictionary with new step mappings and updated data.
    """

    # Get the top steps DataFrame based on the quantile

    top = get_top_steps(wafer_traveler_dir, quantile)
    top_steps = set(top["paths"])

    # Create a new dictionary with deep copies of the old dictionary entries for the top steps
    dr_new = {step: deepcopy(old_dr[step]) for step in top_steps if step in old_dr}

    # Find the highest count step
    highest_count_key = top.loc[top["counts"].idxmax(), "paths"]

    # Precompute loop values for efficient matching
    old_dr_loop = {key.split(" ")[0].split("-")[-1]: key for key in old_dr}
    top_steps_loop = {step.split(" ")[0].split("-")[-1]: step for step in top_steps}

    # Process old dictionary to extend new steps based on matching loops
    for key, value in old_dr.items():
        if key not in top_steps:
            loop1 = key.split(" ")[0].split("-")[-1]
            matched_key = top_steps_loop.get(loop1, highest_count_key)
            dr_new[matched_key].extend(value)
    return dr_new
