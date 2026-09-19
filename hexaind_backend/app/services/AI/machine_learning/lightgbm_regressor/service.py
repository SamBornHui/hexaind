import pandas as pd
import numpy as np
import sklearn, pickle
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split, RandomizedSearchCV,GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from lightgbm import LGBMRegressor
import os
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple
from datetime import datetime, timezone
from .dao import LightGbmModelBuilderDao
from app.services.workflows.designer.schemas import ModelBuilderConfig, ModelType, ScalingMethod, OptimizationMethod
from app.core.db.db_utils import get_db_sync

class LightGbmModelBuilder:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        
        self.lightgbm_model_builer_dao = LightGbmModelBuilderDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
    
    
    def validate_and_load_dataset(self, datapath: str) -> pd.DataFrame:
         """
         This is the helper function to load the dataset
         """

         if not (os.path.isfile(datapath) or os.path.isdir(datapath)):
              raise ValueError("The provided data path does not exist.")
        
         # If it's a file, check if it's a CSV or Parquet file
         if os.path.isfile(datapath) and not (datapath.endswith('.csv') or datapath.endswith('.parquet')):
              raise ValueError("The file must be a CSV or Parquet file.")
        
        # assuming for now we have a flat single file, can be extended for parquet (folders)
        
         if datapath.endswith('.csv'):
              dataframe = pd.read_csv(datapath)
        
         elif datapath.endswith(".parquet"):
              dataframe = pd.read_parquet(datapath)

        # TODO for parquet folders 

         if dataframe.empty:
             raise Exception("Dataframe is not having any records to train LightGbm model")
         
         return dataframe
        
    def features_scaling_helper(self, train_dataframe: pd.DataFrame, test_dataframe: pd.DataFrame=None, scaling_method: ScalingMethod=ScalingMethod.MIN_MAX):
        """
        This helper fucntion will be used to scale the dataset. (Ideally we will move this function to common place for models) 
        """
        if not isinstance(train_dataframe, pd.DataFrame) or train_dataframe.empty:
            raise Exception("features_scaling_helper is expecting dataframe of type Pandas.Dataframe")
        
        if scaling_method == ScalingMethod.STANDARD:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(train_dataframe)
            X_test_scaled = scaler.transform(test_dataframe) if isinstance(test_dataframe, pd.DataFrame) else None
            return X_train_scaled, X_test_scaled

        elif scaling_method == ScalingMethod.MIN_MAX:
            # TODO Need to implement
            pass
        elif scaling_method == ScalingMethod.ROBUST:
            # TODO Need to implement
            pass

        else:
            raise Exception(f"scaling method provided is not available: {scaling_method}")

    def preprocess_dataset_helper(self, dataframe: pd.DataFrame, config: ModelBuilderConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        This helper function is responsible for pre-processing the data(splitting, scaling, transformation etc)
        """

        # Ensuring the dataset have all required features
        required_columns = config.input_columns + [config.output_column]
        if not all(column in dataframe.columns for column in required_columns):
            missing_columns = set(required_columns) - set(dataframe.columns)
            raise ValueError(f"The dataset is missing the following required columns: {missing_columns}")
        
        X, y = dataframe[config.input_columns], dataframe[config.output_column]

        return X, y
    
    def split_dataset_helper(self, X, y, config: ModelBuilderConfig):
        """
        this helper function is repsonsible for splitting the dataset as train and test
        """
        return train_test_split(X, y, np.arange(X.shape[0]), test_size=config.test_data_split_ratio / 100, random_state=config.random_state)
    
    def build_and_train_model_helper(self, X_train, y_train, config: ModelBuilderConfig):
        """
        this helper fucntion is repsonsible for buidling the lightGBM regressor model
        """
        # Define the parameter grid based on LGBMModelParameters
        parameter_grid_lgbm = {
            'max_depth': np.linspace(config.parameters.min_depth, config.parameters.max_depth, config.parameters.sample_no_depth, dtype=np.int16),
            'num_leaves': np.linspace(config.parameters.min_num_leaves, config.parameters.max_num_leaves, config.parameters.sample_no_num_leaves ,dtype=np.int16),
            'min_child_samples': np.linspace(config.parameters.max_child_samples, config.parameters.sample_no_child_samples,dtype=np.int16)
            }

        # Initialize GridSearchCV
        if config.hyper_parameter_optimization_method == OptimizationMethod.GRID_SEARCH:
            search_lgbm = GridSearchCV(LGBMRegressor(n_jobs=-1), 
                                       param_grid=parameter_grid_lgbm, 
                                       cv=config.n_folds,
                                       )
            
        elif config.hyper_parameter_optimization_method == OptimizationMethod.RANDOM_SEARCH:
            search_lgbm = RandomizedSearchCV(LGBMRegressor(n_jobs=-1),
                                             param_distributions=parameter_grid_lgbm, 
                                             cv=config.n_folds, 
                                             random_state=config.random_state,
                                             n_iter=config.random_search_params.n_iter,
                                             verbose=1)



        # Fit GridSearchCV
        search_lgbm.fit(X_train, y_train)

        # Best estimator
        best_model = search_lgbm.best_estimator_

        return best_model
    
    def get_machine_learning_model_metrics_helper(self, machine_learning_model, X_train, X_test, y_train, y_test) -> dict:

        """
        This helper is used to get the model metrics
        """
        metrics = {
            "Train_MAE": mean_absolute_error(y_train, machine_learning_model.predict(X_train)),
            "Train_MSE": mean_squared_error(y_train, machine_learning_model.predict(X_train), squared=False),
            "CV_MAE": -np.mean(cross_val_score(machine_learning_model, X_train, y_train, cv=10, scoring='neg_mean_absolute_error')),
            "CV_MSE": np.sqrt(-np.mean(cross_val_score(machine_learning_model, X_train, y_train, cv=10, scoring='neg_mean_squared_error'))),
            "Test_MAE": mean_absolute_error(y_test, machine_learning_model.predict(X_test)),
            "Test_MSE": mean_squared_error(y_test, machine_learning_model.predict(X_test), squared=False),
            "Test_Rsquared": r2_score(y_test, machine_learning_model.predict(X_test)),
            "Train_Rsquared": r2_score(y_train, machine_learning_model.predict(X_train)),
        }
        return metrics


    def light_gbm_model_builder_handler(self, datapath: str, model_config: ModelBuilderConfig, results_path: str) -> str:

        """
        This service will build the Lgbm regressor model and returns the model objects
        """

        if model_config.model != ModelType.LIGHT_GBM:
            raise Exception("ModelType: LIGHT_GBM is expected by light_gbm_model_builder_handler service")
        
        # load the data from the file
        data = self.validate_and_load_dataset(datapath)

        # Preprocess dataset
        X, y = self.preprocess_dataset_helper(dataframe=data, config=model_config)

        # split the dataset as train and test
        X_train, X_test, y_train, y_test, train_indices, test_indices = self.split_dataset_helper(X= X, y=y, config=model_config)

        # scaling the features
        if model_config.scaling_method:
            X_train, X_test = self.features_scaling_helper(train_dataframe=X_train, test_dataframe=X_test, scaling_method=model_config.scaling_method)




        # build and train the model
        best_model = self.build_and_train_model_helper(X_train=X_train, y_train=y_train, config=model_config)

       # Calculate metrics
        metrics = self.get_machine_learning_model_metrics_helper(machine_learning_model=best_model, X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test)
        

        # Save model and metrics to a pickle file
        with open(results_path, 'wb') as file:
            pickle.dump({
                'best_model': best_model,
                'metrics': metrics,
                'input_features': model_config.input_columns,
                'output_features': [model_config.output_column] if isinstance(model_config.output_column, str) else model_config.output_column,
                'train_indices': train_indices,
                'test_indices': test_indices,
                
            }, file)

        return results_path
    

    

    

    


