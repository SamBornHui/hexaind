import os
from pathlib import Path
from uuid import uuid4
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import pandas as pd
import logging
import dask.dataframe as dd
import re
from word2number import w2n
from typing import List, Tuple

from app.services.workflows.designer.schemas import JoinType
from app.core.services.data_transformation.tabular.schemas import AppendModel, JoinModel, DatasetDataframe, AppendMismatchCheckResponse, ColumnAndType, ObjectIdAsStr
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.data.curation.data.sink.model import DataSinkModel
from app.config.env_vars import environment
from app.services.data.assets.datasets.dao import DatasetsDao

logger = logging.getLogger(__package__)

class DataTransformAppendService:
    
    def __init__(self) -> None:
        self.ordinal_map = {
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
            "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19,
            "twentieth": 20, "thirtieth": 30, "fortieth": 40, "fiftieth": 50, "sixtieth": 60, "seventieth": 70, "eightieth": 80, "ninetieth": 90,
            "hundredth": 100, "thousandth": 1000, "millionth": 1000000, "billionth": 1000000000
        }

    async def transform_append(self, append_model: AppendModel, user_id: str, output_name: str, dir_path, use_gpu = True, output_format = 'csv'):
        dataframes_list = []
        for dataset in append_model.datasets_list:
            dataframes_list.append(DataSourceModel.from_dataset(dataset).dataframe)

        dataframe = await self.append_data(dataframes_list, max_rows = append_model.max_rows, 
                                           column_type_pref_list= append_model.column_type_pref_list,
                                           convert_words_to_number = append_model.convert_words_to_number)
        # writing to a file path
        file_name = f"APPEND_{str(output_name)}_{uuid4()}.{output_format}"
        file_path = os.path.join(dir_path, file_name)
        os.makedirs(dir_path, exist_ok=True)
       
        if output_format == 'csv':
            show_index = True
            if append_model.ignore_index:
                show_index = False
            dataframe.compute().to_csv(file_path, index=show_index)
        else:
            dataframe.to_parquet(str(file_path))
        return file_path

    async def append_data(self,
        df_list: List[dd.DataFrame],
        max_rows = 0, column_type_pref_list: List[ColumnAndType] = None,
        convert_words_to_number: bool = True
    ) -> dd.DataFrame:
        """
        Append data
        - This is less restrictive in terms of allowable operations
        - TODO: we should provide a warning if there are 0 common columns
        """

        df = None
        if max_rows > 0:
            df = dd.concat(df_list).repartition(npartitions=1).head(n=max_rows, npartitions=-1, compute=False).reset_index(drop=True)
        else:
             df = dd.concat(df_list).repartition(npartitions=1).reset_index(drop=True)

        if column_type_pref_list != None:
            #df = df.compute()
            for col_type in column_type_pref_list:
                if col_type != None and col_type.column_name in df.columns and col_type.pref_type != "object":
                    df = self.convert_df_column(df, col_type.column_name, col_type.pref_type, convert_words_to_number)

        return df
    
    def convert_df_column(self, df: dd.DataFrame, column: str, to_type: str, convert_words_to_number: bool) -> dd.DataFrame:
        def convert_value(value):
            if to_type.lower() in ['object',  'none', '']:
                return value
            elif to_type == 'int64':
                try:
                    return int(float(value))
                except ValueError:
                    if convert_words_to_number:
                        try:
                            return self.convert_words_to_number(value)
                        except Exception as e:
                            return 0
                    else:
                        return 0
            elif to_type == 'float64':
                try:
                    return float(value)
                except ValueError:
                    if convert_words_to_number:
                        try:
                            return float(self.convert_words_to_number(value))
                        except Exception as e:
                            return 0.0
                    else:
                        return 0.0
            elif to_type == "bool":
                try:
                    if pd.isna(value):
                        return False
                    return bool(value)
                except ValueError:
                    return False
            else:
                raise ValueError(f"Unsupported type: {to_type}")

        # Apply the conversion to the specified column
        df[column] = df[column].apply(convert_value, meta=(column, to_type))
        
        return df

    def convert_ordinal(self, word):
        word = word.lower()
        if word in self.ordinal_map:
            return self.ordinal_map[word]
        if word.endswith("st") or word.endswith("nd") or word.endswith("rd") or word.endswith("th"):
            base_word = re.sub(r'(st|nd|rd|th)$', '', word)
            if base_word.isdigit():
                return int(base_word)
            try:
                return w2n.word_to_num(base_word)
            except ValueError:
                return None
        return None
    
    def convert_words_to_number(self, words):
        words = words.lower()
        try:
            return w2n.word_to_num(words)
        except ValueError:
            pass

        parts = words.split()
        result = 0
        current = 0
        for part in parts:
            if part in ["and", ""]:
                continue
            if part in self.ordinal_map:
                result += self.ordinal_map[part]
                current = 0
            elif re.match(r'^\d+(st|nd|rd|th)?$', part):
                number = self.convert_ordinal(part)
                if number is not None:
                    result += number
                    current = 0
            else:
                try:
                    number = w2n.word_to_num(part)
                    current += number
                except ValueError:
                    result += current
                    current = 0
        result += current
        return result

class DataTransformJoinService:
    
    def __init__(self) -> None:
        self.join_dict = { JoinType.INNER.value: 'inner', JoinType.LEFT.value:  'left', JoinType.RIGHT.value: 'right', JoinType.OUTER.value: 'outer'}

    async def transform_join(self, output_name: str, join_model: JoinModel, user_id: str, file_path_prefix: str, use_gpu = True, output_format='parquet'):
        left_dataframe  = DataSourceModel.from_dataset(join_model.left_dataset).dataframe
        right_dataframe  = DataSourceModel.from_dataset(join_model.right_dataset).dataframe

        dataframe = await self.join_data(
                left_df=left_dataframe,
                right_df=right_dataframe,
                left_columns=join_model.left_columns,
                right_columns=join_model.right_columns,
                method=self.join_dict[join_model.join_type.value]
            )

        file_name = f"JOIN_{output_name}_{uuid4()}.{output_format}"
        file_path = str(Path(file_path_prefix, file_name))
        Path(file_path).parent.mkdir(exist_ok=True, parents=True)

        data_sink_model = DataSinkModel.model_validate(
            {"version": "1.0", "data_type": output_format.upper(), "path": str(file_path)}
        )
        data_sink_model.to_sink(dataframe)

        return file_path

    def columns_exists(self, dataset: dd.DataFrame, columns_list: List[str]) -> Tuple[bool, List[str]]:
        na_cols = []
        final_res = True
        ds_cols = dataset.columns
        for col in columns_list:
            if col not in ds_cols:
                na_cols.append(col)
                final_res =  False
        return final_res, na_cols
    
    def conv_obj_to_str_and_check_valid(self, left_ds: dd.DataFrame, right_ds: dd.DataFrame, left_columns: List[str], right_columns: List[str]) -> Tuple[bool, List[str]]:
        non_matching_cols = []
        final_res = True
        for left_col, right_col in zip(left_columns, right_columns):
            l_type = left_ds[left_col].dtype
            r_type = right_ds[right_col].dtype

            if l_type in ["object", " string"]  or r_type in ["object", "string"]:
                left_ds[left_col] = left_ds[left_col].astype(str)
                right_ds[right_col] = right_ds[right_col].astype(str)
                l_type = "string"
                r_type = "string"
            else:
                comb_allowed  = ["int", "int64", "float", "float64"]

                if l_type not in comb_allowed or r_type not in comb_allowed:
                    non_matching_cols.append(f"{left_col}({l_type})-{right_col}({r_type})")
                    final_res = False

        return final_res, non_matching_cols
    
    def check_datasets_for_cols_errors(self, left_df: dd.DataFrame, right_df: dd.DataFrame, left_columns: List[str], right_columns: List[str]) -> Tuple[bool, str]:
        columns_ok, err_cols_list = self.columns_exists(left_df, left_columns)
        if columns_ok == False:
            error = f"The JOIN resulted in a Error. Requested column(s) {err_cols_list} not found in left dataset"
            return columns_ok, error
        
        columns_ok, err_cols_list = self.columns_exists(right_df, right_columns)
        if columns_ok == False:
            error = f"The JOIN resulted in a error. Requested column(s) {err_cols_list} not found in right dataset"
            return columns_ok, error
        
        columns_ok, err_cols_list = self.conv_obj_to_str_and_check_valid(left_df, right_df, left_columns, right_columns)
        if columns_ok == False:
            error = f"The JOIN resulted in a error. Columns {err_cols_list} are not same type"
            return columns_ok, error
        
        return True, ""
        

    async def join_data(self,
        left_df: dd.DataFrame,
        right_df: dd.DataFrame,
        left_columns: List[str],
        right_columns: List[str],
        method: str = 'inner'
    ) -> dd.DataFrame:
        """
        Join data
        - Only allow joining of 2 tables for now
        - Separate out the left and right dataframes because we will be enabling left join
        - Methods allows for now: 'inner', 'left', right and 'outer'
        - User should be able to provide one column from each for reference
        - In the simplified design, these columns names will be required to be identical
        -- But the left and right columns are defined separately for a more future-proof function
        """
        join_methods = list(self.join_dict.values())
        join_method_keys = list(self.join_dict.keys())
        if method not in join_methods:
            raise ValueError(
                f"Currently supported join methods are {join_method_keys}. Other methods will be added in a future release."
            )

        if len(left_columns) != len(right_columns):
            error = f"The JOIN resulted in non equalant number of columns to comapre"
            logger.error(error)
            raise ValueError(error)
        
        if len(left_columns) > 0:

            columns_ok, error = self.check_datasets_for_cols_errors(left_df, right_df, left_columns, right_columns)
            if columns_ok == False:
                logger.error(error)
                raise ValueError(error)

            df = left_df.merge(right_df, left_on=left_columns, right_on=right_columns, how=method, suffixes=("","_right"))
            right_explict_cols = []
            for left_col, right_col in zip(left_columns, right_columns):
                if left_col != right_col:
                    right_explict_cols.append(right_col)
            df = df.drop(columns=right_explict_cols)
        else:
            #Merge 1st row to 1st row (not with matching columns)
            common_cols = list(set(left_df.columns) & set(right_df.columns))
            if len(common_cols) > 0:
                right_cols_ren_dict = {}
                for col in common_cols:
                    right_cols_ren_dict[col] = col + "_right"
                right_df = right_df.rename(columns=right_cols_ren_dict)
            df = left_df.merge(right_df, how=method)
       

        if len(df) == 0:
            raise ValueError(f"The JOIN resulted in empty data. Re-check data and JOIN parameters.")

        return df

class AppendHelper:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        self.datasets_dao = DatasetsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        logger.info("inside AppendHelper service")
    
    def get_append_mismatches(self, dataset_ids_list: List[ObjectIdAsStr]) -> AppendMismatchCheckResponse:
        response = self.datasets_dao.get_datasets_by_qry_sync({"_id": {"$in":dataset_ids_list}})
        if response == None or len(response) == 0:
            error = "Could not found any datasets with provided dataset ids"
            logger.error(error)
            raise ValueError(error)
        
        if len(response) == 1:
            error = "Found only one dataset with provided ids. can't compare"
            logger.error(error)
            raise ValueError("Found only one dataset with provided ids. can't compare")
        
        dataset_objs_list: List[DatasetDataframe] = []
        dataframes = []
        for dataset in response:
            dataframe = DataSourceModel.from_dataset(dataset).dataframe
            dataframes.append(dataframe)
            dataset_objs_list.append(DatasetDataframe(id=dataset.id, name = dataset.name, dataframe=dataframe))
        
        all_columns = set()
        for ddf in dataframes:
            all_columns.update(ddf.columns)
        
        common_columns = set.intersection(*(set(ddf.columns) for ddf in dataframes))
        dtype_mismatches = {}
        for column in common_columns:
                dtypes = set(ddf[column].dtype for ddf in dataframes if column in ddf.columns)
                if len(dtypes) > 1:
                    dtype_mismatches[column] = dtypes
        mismatch_datatype_columns = []#{}
        if dtype_mismatches:
            for mismatch_column in dtype_mismatches:
                mis_match_type_dict = {"column": mismatch_column, "details":[]}
                mismatch_datatype_columns.append(mis_match_type_dict)
                for dataset in dataset_objs_list:
                    if mismatch_column in dataset.dataframe.columns:
                        column_type  = str(dataset.dataframe[str(mismatch_column)].dtype)
                        mis_match_type_dict["details"].append({"dataset_id": dataset.id, "name":dataset.name, "data_type":column_type})

        missing_column_datasets = []
        missing_columns = all_columns - common_columns
        for column in missing_columns:
            missing_cols_dict = {"column": column, "details":[]}
            missing_column_datasets.append(missing_cols_dict)
            for dataset in dataset_objs_list:
                if column not in dataset.dataframe.columns:
                    missing_cols_dict["details"].append(dataset.name)

        if len(missing_column_datasets) == 0 and len(mismatch_datatype_columns) == 0:
            info_msg = f"Datasets found {len(response)}. Could not found any mismatches between the datasets"
            logger.info(info_msg)
            response_dict =  {"status": True, "detail": info_msg}
        
        else:
            logger.info("Found mismatches. Going to send response")
            response_dict = {"status": False, 
                         "detail": {
                             "mismatch_datatype_columns": mismatch_datatype_columns,
                             "missing_columns": missing_column_datasets
                             }
                        }
        return  AppendMismatchCheckResponse(**response_dict)