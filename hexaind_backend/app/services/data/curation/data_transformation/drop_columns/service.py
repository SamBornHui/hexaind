import dask.dataframe as dd
import pandas as pd
from app.services.data.assets.datasets.schemas import Dataset
from app.services.workflows.designer.schemas import DropColumnsConfig
from app.services.data.curation.data.sink.model import DataSinkModel  # This is used to store the return data
from app.services.data.curation.data.source.model import DataSourceModel  # This is used to store the return data
from logging import getLogger
from pandas.errors import EmptyDataError

logger = getLogger(__package__)

class DropColumnsService:

    def __init__(self) -> None:
        pass

    def drop_columns_handler(
        self, drop_columns_config: DropColumnsConfig, dataset: Dataset, dest_path: str
    ) -> str:
        """
        Drops selected columns
        """
        
        # Assuming this indirectly uses dask
        dataframe = DataSourceModel.from_dataset(dataset).dataframe  # Fetching tabular dataset #Dask is similar to pandas but just that it doesn't load complete data
        if dataframe is None or not isinstance(dataframe, dd.DataFrame):
            raise ValueError("Expected a Dask DataFrame")
        
        if len(dataframe) == 0:
            logger.info("DataFrame is empty")
       
        selected_columns = None
        # Extract the selected columns from the drop_config
        if drop_columns_config.selected_columns:
            selected_columns = (
                drop_columns_config.selected_columns
                if len(drop_columns_config.selected_columns) != 0
                else None
            )
 
        try:
            if selected_columns is not None:
                if set(selected_columns) == set(dataframe.columns):
                    logger.info("All columns are selected so the resultant is an empty dataset.")
                    raise ValueError("All columns are selected so the resultant is an empty dataset.")
                    dataframe = dataframe.drop(columns=selected_columns)
                else:
                    dataframe = dataframe.drop(columns=selected_columns)
            else:
                logger.info("No columns were selected for dropping. Skipping the drop operation.")
        except EmptyDataError as e:
            logger.error(f"Failed to process drop columns: {e}")

        # Save the DataFrame using DataSinkModel 
        data_sink_model = DataSinkModel.model_validate( #Pydantic validation is done
            {"version": "1.0", "data_type": f"{dest_path.split('.')[-1].upper()}", "path": dest_path}
        )
        data_sink_model.to_sink(dataframe)
        return dest_path
