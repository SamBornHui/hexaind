import dask.dataframe as dd
import pandas as pd
from app.services.data.assets.datasets.schemas import Dataset
from app.services.workflows.designer.schemas import RenameConfig
from app.services.data.curation.data.sink.model import DataSinkModel  # This is used to store the return data
from app.services.data.curation.data.source.model import DataSourceModel  # This is used to store the return data
from logging import getLogger
from pandas.errors import EmptyDataError

logger = getLogger(__package__)

class RenameService:

    def __init__(self) -> None:
        pass

    def rename_columns_handler(
        self, rename_columns_config: RenameConfig, dataset: Dataset, dest_path: str
    ) -> str:
        """
        Rename the selected column names

        """
        
        # Assuming this indirectly uses dask
        dataframe = DataSourceModel.from_dataset(dataset).dataframe  # Fetching tabular dataset #Dask is similar to pandas but just that it doesn't load complete data
        if dataframe is None or not isinstance(dataframe, dd.DataFrame):
            raise ValueError("Expected a Dask DataFrame")
        
        if len(dataframe) == 0:
            logger.info("DataFrame is empty")
       
        columns_to_rename = {}
        # Extract the selected columns from the drop_config
        
        if rename_columns_config.columns_to_rename:
        
            columns_to_rename = (
        
                rename_columns_config.columns_to_rename
        
                if len(rename_columns_config.columns_to_rename) != 0
        
                else None
            )

        try:
           
            if columns_to_rename is not None:
           
                dataframe = dataframe.rename(columns=columns_to_rename)
           
            else:
           
                logger.info("No columns were selected for renaming. Skipping the drop operation.")

        except EmptyDataError as e:
            
            logger.error(f"Failed to process drop columns: {e}")

        # Save the DataFrame using DataSinkModel 
        data_sink_model = DataSinkModel.model_validate( #Pydantic validation is done
           
            {"version": "1.0", "data_type": f"{dest_path.split('.')[-1].upper()}", "path": dest_path}
        )
        data_sink_model.to_sink(dataframe)
        
        return dest_path