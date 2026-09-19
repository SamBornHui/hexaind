import pandas as pd
import dask.dataframe as dd
from app.services.data.assets.datasets.schemas import Dataset
from app.services.workflows.designer.schemas import DataTypeConversionConfig, DTypeConversion
from app.services.data.curation.data.sink.model import DataSinkModel
from app.services.data.curation.data.source.model import DataSourceModel
from logging import getLogger
from pandas.errors import EmptyDataError

logger = getLogger(__package__)

class DataTypeConversionService:
    def __init__(self) -> None:
        pass

    def datatype_conversion_handler(
        self,
        datatype_conversion_config: DataTypeConversionConfig,
        dataset: Dataset,
        dest_path: str
    ) -> str:
        """Converts the datatypes of selected columns"""
        dataframe = DataSourceModel.from_dataset(dataset).dataframe  # Fetching tabular dataset

        if dataframe is None or not isinstance(dataframe, dd.DataFrame):
            raise ValueError("Expected a Dask DataFrame")
        # Map frontend inputs to actual data types
        frontend_to_dtype = {
            "INTEGER": DTypeConversion.INTEGER,
            "FLOAT": DTypeConversion.FLOAT,
            "STRING": DTypeConversion.STRING,
            "DATE": DTypeConversion.DATE,
            "DATETIME" : DTypeConversion.DATETIME
        }

        # Prepare the mapping of columns to their new data types
        column_type_mapping = {
            col: frontend_to_dtype.get(dtype, dtype)
            for col, dtype in datatype_conversion_config.column_type_mapping.items()
        }

        # Apply the datatype conversion directly
        try:
                logger.info("Before Data type Conversion")
    
                for col, dtype in column_type_mapping.items():
                    if dtype == DTypeConversion.INTEGER and dataframe[col].dtype == 'float': #Inorder to perform perfect round() before float to int conversion
                        dataframe[col] = dataframe[col].round().astype(dtype)
                    elif dtype == DTypeConversion.DATETIME and (dataframe[col].dtype == 'string' or dataframe[col].dtype == 'object'):
                        dataframe[col] = dataframe[col].map_partitions(lambda df: pd.to_datetime(df, errors='coerce'),meta=(col, 'datetime64[ns]'))
                    elif dtype == DTypeConversion.DATE and (dataframe[col].dtype == 'string' or dataframe[col].dtype == 'object'):
                        dataframe[col] = dataframe[col].map_partitions(lambda df: pd.to_datetime(df, errors='coerce').dt.date,meta=(col, 'datetime64[ns]'))
                    else:
                        dataframe[col] = dataframe[col].astype(dtype)
                logger.info("After Data type Conversion")
        
        except (EmptyDataError, TypeError, ValueError) as e:
            logger.error(f"Failed to process datatype conversion: {e}")
            raise

        # Save the converted DataFrame using DataSinkModel
        data_sink_model = DataSinkModel.model_validate(
            {
                "version": "1.0",
                "data_type": "PARQUET",
                "path": dest_path
            }
        )
        data_sink_model.to_sink(dataframe)

        return dest_path
