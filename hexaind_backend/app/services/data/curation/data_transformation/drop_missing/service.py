import dask.dataframe as dd
import os
import pandas as pd
from app.services.data.assets.datasets.schemas import Dataset
from app.services.workflows.designer.schemas import DropMissingConfig
from app.services.data.curation.data.sink.model import (
    DataSinkModel,
)  # This is used to store the return data
from app.services.data.curation.data.source.model import (
    DataSourceModel,
)  # This is used to store the return data
import logging

logger = logging.getLogger(__package__)


class DropMissingService:

    def __init__(self) -> None:
        pass

    def drop_missing_by_column_handler(
        self, drop_config: DropMissingConfig, dataset: Dataset, dest_path: str
    ) -> str:
        """
        Drops missing from the DataFrame where any of the selected columns have missing values
        and saves the resulting DataFrame to the specified path.
        """
        
        # Assuming this indirectly uses dask
        dataframe = DataSourceModel.from_dataset(dataset).dataframe  # Metadata
        if dataframe is None or not isinstance(dataframe, dd.DataFrame):
            raise ValueError("Expected a Dask DataFrame")
        
        if len(dataframe) == 0:
            #raise ValueError("DataFrame is empty")
            logger.info("The dataset is empty")
       
        selected_columns = None
        # Extract the selected columns from the drop_config
        if drop_config.selected_columns:
            selected_columns = (
                drop_config.selected_columns
                if len(drop_config.selected_columns) != 0
                else None
            )

        # Drop missing where any of the selected columns have missing values
        drop_data = dataframe.dropna(
            subset=selected_columns
        )  # subset handles with and without column names

        # Save the filtered DataFrame using DataSinkModel #Need to check the modification in terms of datasource

        data_sink_model = DataSinkModel.model_validate(
            {"version": "1.0", "data_type": f"{dest_path.split('.')[-1].upper()}", "path": dest_path}
        )
        data_sink_model.to_sink(drop_data)
        return dest_path
