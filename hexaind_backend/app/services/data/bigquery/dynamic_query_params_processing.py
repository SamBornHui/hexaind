# For BigQuery specific error types, go here: https://googleapis.dev/python/google-api-core/latest/exceptions.html
from datetime import timedelta
from typing import List

from app.services.data.bigquery.schemas import (
    BigQueryDatasetQueryConfig,
    DateListQueryParam,
    DateQueryParam,
    DateRangeQueryParam,
)


def process_query_parameters(config: BigQueryDatasetQueryConfig) -> List[str]:
    if not config.query_params:
        return [config.query]

    # seperating non date params
    date_params = []
    non_date_params = []
    for name, param in config.query_params.items():
        match param.root:
            case DateQueryParam():
                date_params.append(name)
            case _:
                non_date_params.append(name)

    # processed query string
    processed_query_string = config.query

    # processing non-date params
    for name in non_date_params:
        param = config.query_params[name]
        data = param.root.value.root.data
        replace_str = "null" if data is None else repr(data)
        processed_query_string = processed_query_string.replace(f"@{name}", replace_str)

    # processing optional params
    for name in non_date_params:
        param = config.query_params[name]
        data = param.root.value.root.data
        # markers
        optional_start_marker = f"#OPTIONAL_START_{name}"
        optional_end_marker = f"#OPTIONAL_END_{name}"
        while True:
            start, end = map(
                processed_query_string.find,
                (optional_start_marker, optional_end_marker),
            )
            if start == -1 or end == -1:
                break
            if data is None:
                # remove the entire optional section
                processed_query_string = (
                    processed_query_string[:start]
                    + processed_query_string[end + len(optional_end_marker) :]
                )
            else:
                # remove only the markers, keep the content
                processed_query_string = (
                    processed_query_string[:start]
                    + processed_query_string[start + len(optional_start_marker) : end]
                    + processed_query_string[end + len(optional_end_marker) :]
                )
    # trimming
    processed_query_string = processed_query_string.strip().lstrip("\n").rstrip("\n")

    # processing date params
    if not date_params:
        return [processed_query_string]

    for name in date_params:
        param = config.query_params[name]
        dates = []
        match param.root.value.root:
            case DateListQueryParam() as param_value:
                dates = param_value.data
            case DateRangeQueryParam() as param_value:
                start, end = param_value.data
                dates = [start + timedelta(days=i) for i in range((end - start).days)]
        return [
            processed_query_string.replace(
                f"@{name}", f"""'{date.strftime("%Y-%m-%d")}'"""
            )
            for date in dates
        ]
