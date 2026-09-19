from abc import ABC, abstractmethod
from pathlib import Path

from app.services.data.assets.datasets.schemas import Dataset
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.curation.data.sink.model import DataSinkModel
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.data.datasets_conversion.schemas import DatasetsConversionType
from app.config.env_vars import environment
from uuid import uuid4


class DatasetsConverter(ABC):

    @abstractmethod
    def convert(self, dataset: Dataset, kwargs=None):
        pass


class TabularParquetToTabularCSV(DatasetsConverter):

    def convert(self, dataset: Dataset, kwargs=None):
        data_source = DataSourceModel.from_dataset(dataset)
        dataframe = data_source.root.dataframe
        old_dataset_loc = Path(dataset.dataset_location[0].path).parent
        destination_path = str(old_dataset_loc / f"{uuid4().hex}.csv")
        if kwargs:
            destination_path = kwargs.get('destination_path',destination_path)
        data_sink_model = DataSinkModel.model_validate(
            {"version": "1.0", "data_type": "CSV", "path": destination_path}
        )
        data_sink_model.to_sink(dataframe)
        new_dataset_location = DatasetsService.get_file_info(
            destination_path, kwargs.get("last_modified_by")
        )

        return Dataset(
            **dataset.model_dump(
                exclude=("_id", "name", "dataset_location", "dataset_information")
            ),
            dataset_information=[],
            dataset_location=[new_dataset_location],
            name=kwargs.get("name", dataset.name),
        )



class TabularCSVToTabularParquet(DatasetsConverter):

    def convert(self, dataset: Dataset, kwargs=None):        
        
        data_source = DataSourceModel.from_dataset(dataset)
        dataframe = data_source.root.dataframe
        destination_path = str(environment.datasets_folder / f"{uuid4().hex}.parquet")
        if kwargs:
            destination_path = kwargs.get('destination_path',destination_path)                    
        data_sink_model = DataSinkModel.model_validate(
            {"version": "1.0", "data_type": "PARQUET", "path": destination_path}
        )
        data_sink_model.to_sink(dataframe)
        new_dataset_location = DatasetsService.get_file_info(
            destination_path, kwargs.get("last_modified_by")
        )

        # Return a new Dataset object with updated information
        return Dataset(
            **dataset.model_dump(
                exclude=("_id", "name", "dataset_location", "dataset_information")
            ),
            dataset_information=[],
            dataset_location=[new_dataset_location],
            name=kwargs.get("name", dataset.name),
        )


class DatasetsConversionAbstractFactory(ABC):
    @abstractmethod
    def get_factory(self, conversion_type: DatasetsConversionType):
        pass


class DatasetsConversionFactory(DatasetsConversionAbstractFactory):

    def get_factory(self, conversion_type: DatasetsConversionType):
        if conversion_type == DatasetsConversionType.TABULAR_PARQUET_TO_CSV:
            return TabularParquetToTabularCSV()
        if conversion_type == DatasetsConversionType.TABULAR_CSV_TO_PARQUET:
            return TabularCSVToTabularParquet()
        else:
            raise ValueError(
                f"Factory created only {DatasetsConversionType.TABULAR_PARQUET_TO_CSV}"
            )
