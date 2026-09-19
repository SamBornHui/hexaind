import pandas as pd
import pandas as pdd


def join_dataframes_if_columns_exist(df1, df2, column_names, how='inner'):
    if all(col in df1.columns and col in df2.columns for col in column_names):
        # Perform the join operation
        return pd.merge(df1, df2, on=column_names, how=how)
    else:
        print("One or more specified columns do not exist in both DataFrames.")
        return None


def hexaind_custom_widget_function(df1: pd.DataFrame, df2: pd.DataFrame, column_names: str, how: str) -> pdd.DataFrame:
    column_names_list = column_names.split(',')
    return join_dataframes_if_columns_exist(df1, df2, column_names_list, how)
