import dask.dataframe as dd
import operator
import pandas as pd
from app.services.workflows.designer.schemas import (
    FilterActivityConfig,
    FilterType,
    FilterOperator,
    StringFilterOperator,
)
from app.services.data.curation.data.sink.model import DataSinkModel
from datetime import datetime


def operator_between(series, value):
    minimum, maximum = value
    return (minimum <= series) & (series <= maximum)


def filter_data_by_column_handler(
    dataframe: dd.DataFrame, filter_config: FilterActivityConfig, dest_path: str
) -> str:
    """
    This function applies filters based on the criteria in filter_config
    and saves the filtered dataframe to the destination path.
    """
    if dataframe is None or not isinstance(dataframe, dd.DataFrame):
        raise Exception("A valid Dask DataFrame is required.")

    if dataframe.shape[0].compute() == 0:
        raise Exception("The DataFrame has no records to apply filters to.")

    if filter_config.type != FilterType.FILTER_BY_COLUMN_VALUES:
        raise Exception("Unsupported filter configuration for column filtering.")

    # Supported numeric operators
    supported_operators = {
        FilterOperator.LT: operator.lt,
        FilterOperator.LTE: operator.le,
        FilterOperator.GT: operator.gt,
        FilterOperator.GTE: operator.ge,
        FilterOperator.EQ: operator.eq,
        FilterOperator.NE: operator.ne,
        FilterOperator.BETWEEN: operator_between,
    }

    # Supported string operators
    supported_string_operators = {
        StringFilterOperator.STARTS_WITH: lambda col, val: col.str.startswith(
            val, na=False
        ),
        StringFilterOperator.ENDS_WITH: lambda col, val: col.str.endswith(
            val, na=False
        ),
        StringFilterOperator.EXACT_MATCH: lambda col, val: col == val,
        StringFilterOperator.PARTIAL_MATCH: lambda col, val: col.str.contains(
            val, na=False
        ),
    }

    filter_operands = filter_config.config.filter_operands
    filter_values = filter_config.config.filter_values

    if len(filter_operands) < (len(filter_values) - 1):
        raise Exception("Insufficient filter operands for the requested filters.")

    table_schema = dataframe.dtypes.to_dict()

    group_mask = None

    for i, filter_value in enumerate(filter_values):
        column_name = filter_value.column_name
        column_type = table_schema[column_name]
        value = filter_value.value
        operator_type = filter_value.operator

        # Determine if the column is a string, numeric, or date type
        if pd.api.types.is_string_dtype(column_type):
            filter_op = supported_string_operators.get(operator_type)
            if not filter_op:
                raise Exception(f"Unsupported string operation: {operator_type}")
            current_mask = filter_op(dataframe[column_name], value)

        elif pd.api.types.is_numeric_dtype(column_type):
            filter_op = supported_operators.get(operator_type)
            if not filter_op:
                raise Exception(f"Unsupported numeric operation: {operator_type}")
            value = column_type.type(value)
            current_mask = filter_op(dataframe[column_name], value)

        elif pd.api.types.is_datetime64_any_dtype(column_type):
            value = pd.to_datetime(value)
            filter_op = supported_operators.get(operator_type)
            if not filter_op:
                raise Exception(f"Unsupported date operation: {operator_type}")
            current_mask = filter_op(
                dataframe[column_name], value
            )  # UI -> ["2024-09-09", "2024-10-09"]

        else:
            raise Exception(f"Unsupported column type: {column_type}")

        # Combine filters using the specified operands
        if group_mask is None:
            group_mask = current_mask
        else:
            if filter_operands[i - 1] == "AND":
                group_mask &= current_mask
            elif filter_operands[i - 1] == "OR":
                group_mask |= current_mask
            elif filter_operands[i - 1] == "XOR":
                group_mask ^= current_mask

    # Filter the DataFrame based on the mask
    filtered_df = dataframe[group_mask]

    data_type = dest_path.split(".")[-1].upper()

    data_sink_model = DataSinkModel.model_validate(
        {"version": "1.0", "data_type": data_type, "path": dest_path}
    )
    data_sink_model.to_sink(filtered_df)

    return dest_path
