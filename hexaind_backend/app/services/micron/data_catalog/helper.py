import pandas as pd
from google.cloud import bigquery


def ingest_data_interactive(sql: str, bigquery_client: bigquery.Client) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(dry_run=False)
    record = bigquery_client.query(sql, job_config=job_config)
    result = record.result()
    total_rows = result.total_rows

    if total_rows == 0:
        raise ValueError(f"Query did not return any data.")
    return result.to_dataframe()

def get_excel_columns(file_path) -> pd.DataFrame:
    all_columns = []
    excel_file = pd.ExcelFile(file_path)
    for sheet_name in excel_file.sheet_names:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=0)
            columns = df.columns.tolist()
            for column in columns:
                all_columns.append({"SHEET_NAME": sheet_name, "COLUMNS": column})
        except Exception as e:
            print(f"Error processing sheet {sheet_name}: {e}")
    return pd.DataFrame(all_columns)

