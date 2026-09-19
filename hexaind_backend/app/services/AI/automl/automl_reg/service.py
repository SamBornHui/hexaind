# Original code with MLflow integration
from pathlib import Path
import pandas as pd
from typing import List
from app.services.data.assets.datasets.schemas import Dataset
from app.services.data.curation.data.source.model import DataSourceModel
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from sklearn.preprocessing import StandardScaler

from app.services.AI.models.utils.model_utils import ModelUtils

class AutoMLRegService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:  # type: ignore
        pass

    
    @staticmethod
    def preprocess_automl_reg(
        data_path: Path,
        input_cols: List[str],
        output_col: str,
        split_ratio: int,
        dataset_record:Dataset =None,

    ):
        data = ModelUtils.read_data_for_training(dataset_record=dataset_record,data_path=data_path)

        if data.empty:
            raise ValueError("Loaded data is empty")

        data = ModelUtils.check_and_drop_nan(data, input_cols + [output_col])
        total_cols = list(input_cols)
        total_cols.append(output_col)

        data = data[total_cols]
        data = data.sample(frac=1).reset_index(drop=True)
        train_data, test_data = ModelUtils.test_train_split(data, split_ratio)
        
        # numeric_features = train_data.select_dtypes(
        #     include="number"
        # ).columns.tolist()  # detect numeric columns

        # Standardize numeric columns as auto feature engineering does not
        # scaler = StandardScaler()
        # train_data[numeric_features] = scaler.fit_transform(
        #     train_data[numeric_features]
        # )
        # test_data[numeric_features] = scaler.transform(test_data[numeric_features])
            
        return data, train_data, test_data

    