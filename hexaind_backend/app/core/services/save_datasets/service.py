import logging as logger
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config.env_vars import environment
from app.services.admin.authentication.service import AuthenticationService
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.assets.datasets.schemas import (
    AccessMode,
    Dataset,
    DatasetLocation,
    DatasetType,
    TabularDatasetInformation,
    UploadStats,
    UploadStatus,
    DatasetMetadata,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.datasets_conversion.helper import (
    DatasetsConversionFactory,
    TabularCSVToTabularParquet,
)
from app.services.data.datasets_conversion.schemas import DatasetsConversionType
from app.services.workflows.designer.schemas import (
    DatasetConfiguration,
    FileFormatOptions,
    FileSaveOptions,
    ReplaceConfig,
    SaveAsConfig,
)
from app.utils.file_utils import FileUtils


class SaveService:

    def __init__(
        self,
        user_id: str,
        project_id: str,
        old_dataset_id: str,
        site_id: str,
        action_id: str,
        workflow_id: str,
        run_id: str,
        new_dataset_dir: str,
        dataset_dao: DatasetsDao | None = None,
    ) -> None:
        if dataset_dao is None:
            dataset_dao = DatasetsDao()
        self.dataset_dao = dataset_dao
        self.old_dataset = self.dataset_dao.get_dataset_by_id(old_dataset_id)
        if self.old_dataset is None:
            raise KeyError(f"Dataset not found for {old_dataset_id=}")
        elif any(location.isfolder for location in self.old_dataset.dataset_location):
            raise NotImplementedError("Saving not implemented for folders")
        elif (num_locations := len(self.old_dataset.dataset_location)) != 1:
            raise NotImplementedError(f"Saving not implemented for {num_locations=}")

        authentication_service = AuthenticationService()
        self.dataset_service = DatasetsService()
        user = authentication_service.get_user_sync(user_id=user_id)
        self.user_id = user_id
        self.user_name = user.name
        self.project_id = project_id
        self.site_id = site_id
        self.action_id = action_id
        self.run_id = run_id
        self.workflow_id = workflow_id
        self.new_dataset_dir = Path(new_dataset_dir)
        # self.new_dataset_dir = Path(
        #     environment.data_folder_format_string.format(
        #         project_id, workflow_id, run_id
        #     )
        # )
        self.run_id = run_id
        self.workflow_id = workflow_id
        self.new_dataset_dir.mkdir(exist_ok=True, parents=True)
        self.datasets_converter = DatasetsConversionFactory()

    @staticmethod
    def save_dataset_save_as(old_dataset: Dataset, new_dataset: Dataset):
        logger.info("doing 'save as' on dataset")
        for old_location, new_location in zip(
            old_dataset.dataset_location, new_dataset.dataset_location
        ):
            old_path, new_path = old_location.path, new_location.path
            if old_location.isfolder:
                logger.debug(f"copying folder {old_path} into {new_path}")
                shutil.copytree(old_path, new_path)
            else:
                logger.debug(f"copying file {old_path} into {new_path}")
                shutil.copy(old_path, new_path)
        logger.info("copied data into new location")

    @staticmethod
    def save_dataset_replace(
        old_dataset: Dataset,
        new_dataset: Dataset,
        new_dataset_dir: Path,
        last_modified_by: Optional[str] = None,
    ):
        logger.info("doing 'replace' on dataset")
        if (old_type := old_dataset.dataset_type) != (
            new_type := new_dataset.dataset_type
        ):
            raise ValueError(f"Cannot replace {old_type} into {new_type}")
        for location in new_dataset.dataset_location:
            if location.isfolder:
                logger.debug(f"removing folder {location.path}")
                shutil.rmtree(location.path, ignore_errors=True)
            else:
                logger.debug(f"removing file {location.path}")
                Path(location.path).unlink(missing_ok=True)
            logger.info("removed data of new dataset")
        new_dataset_cache_dir = environment.datasets_cache_folder / str(new_dataset.id)
        logger.debug(f"removing cache from {new_dataset_cache_dir}")
        shutil.rmtree(new_dataset_cache_dir, ignore_errors=True)
        logger.info("removed cache data of new dataset")
        new_locations = []
        for old_location in old_dataset.dataset_location:
            old_path = old_location.path
            new_location = old_location.copy()
            new_location.path = str(new_dataset_dir / Path(old_path).name)
            new_location.last_modified_at = datetime.now(timezone.utc)
            new_location.last_modified_by = last_modified_by
            if Path(old_path) != Path(new_location.path):
                if old_location.isfolder:
                    logger.debug(f"copying folder {old_path} into {new_location.path}")
                    shutil.copytree(old_path, new_location.path)
                else:
                    logger.debug(f"copying file {old_path} into {new_location.path}")
                    shutil.copy(old_path, new_location.path)
            logger.info("copied data into new location")
            new_locations.append(new_location)
        new_dataset.dataset_location = new_locations
        logger.info("updated new dataset locations")

    def new_save_as_dataset(
        self,
        metadata: DatasetMetadata,
        save_config: SaveAsConfig,
        dataset_name: str,
        custom_information=None,
    ):
        time = datetime.now(timezone.utc)
        # TODO handle multiple dataset locations
        new_path = self.new_dataset_dir / save_config.file_name
        dataset_locations = []
        for location in self.old_dataset.dataset_location:
            new_location = location.copy()
            new_location.last_modified_by = None
            new_location.last_modified_at = time
            new_location.path = str(
                new_path
                if location.isfolder
                else new_path.with_suffix(location.extension.lower())
            )
            dataset_locations.append(new_location)

        return Dataset(
            user_id=self.user_id,
            project_id=self.project_id,
            site_id=self.site_id,
            action_id=self.action_id,
            name=dataset_name,
            description=self.old_dataset.description,
            dataset_type=self.old_dataset.dataset_type,
            metadata=metadata,
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            dataset_information=[],
            created_at=time,
            created_by=self.user_name,
            dataset_location=dataset_locations,
            access_mode=AccessMode.EXTERNAL,
            tags=self.old_dataset.tags,
            custom_information=custom_information,
        )

    def new_replace_dataset(self, save_config: ReplaceConfig):
        return self.dataset_dao.get_dataset_by_id(save_config.existing_dataset_id)

    def convert_dataset_to_desired_fileformat(
        self,
        dataset: Dataset,
        file_format: FileFormatOptions,
        delete_existing_files: bool = True,
        kwargs={},
    ):

        logger.info("converting dataset to desired file format")

        if dataset.dataset_type != DatasetType.TABULAR:
            logger.error(
                "dataset is not tabular, unable to convert (default: existing)"
            )
            return dataset

        dataset_locations = dataset.dataset_location
        if len(dataset_locations) != 1:
            logger.error(
                "dataset has more than 1 file_locations, unable to convert to desired file format(default: existing)"
            )
            return dataset

        if dataset_locations[0].isfolder:
            logger.error("dataset is folder, unable to convert (default: existing)")
            return dataset

        kwargs["name"] = kwargs.get("name", dataset.name)
        desired_extension = "." + file_format.value.lower()
        file_path = (
            self.new_dataset_dir
            / kwargs.get("file_name", Path(dataset_locations[0].path).name)
        ).with_suffix(desired_extension)
        kwargs["destination_path"] = kwargs.get(
            "destination_path", str(file_path.absolute())
        )
        kwargs["last_modified_by"] = kwargs.get("last_modified_by", self.user_id)
        if desired_extension == ".excel":
            desired_extension = (".xlsx", ".xls")

        if dataset_locations[0].path.endswith(desired_extension):
            logger.info("No conversion required")
            return dataset
        if file_format == FileFormatOptions.CSV:

            logger.info("converting to csv")
            if dataset_locations[0].path.endswith(
                "." + FileFormatOptions.PARQUET.value.lower()
            ):
                converter = self.datasets_converter.get_factory(
                    DatasetsConversionType.TABULAR_PARQUET_TO_CSV
                )

                converted_dataset = converter.convert(dataset, kwargs)
                if delete_existing_files:
                    new_locations = [
                        dataset_location.path
                        for dataset_location in converted_dataset.dataset_location
                    ]
                    for previous_dataset_location in dataset_locations:
                        if previous_dataset_location.path not in new_locations:
                            FileUtils.remove_path(previous_dataset_location.path)
                return converted_dataset
            else:
                raise NotImplementedError(
                    "Unable to convert given tabular dataset to csv"
                )
        elif file_format == FileFormatOptions.PARQUET:
            if dataset_locations[0].path.endswith(
                "." + FileFormatOptions.CSV.value.lower()
            ):
                converter = self.datasets_converter.get_factory(
                    DatasetsConversionType.TABULAR_CSV_TO_PARQUET
                )
                converted_dataset = converter.convert(dataset, kwargs)
                if delete_existing_files:
                    new_locations = [
                        dataset_location.path
                        for dataset_location in converted_dataset.dataset_location
                    ]
                    for previous_dataset_location in dataset_locations:
                        if previous_dataset_location.path not in new_locations:
                            FileUtils.remove_path(previous_dataset_location.path)
                return converted_dataset
            else:
                raise NotImplementedError(
                    "Unable to convert given tabular dataset to parquet"
                )

        else:
            logger.error("file_format option unknown,switching to default")
            return dataset

    def save_dataset(
        self, config: DatasetConfiguration, metadata: Optional[DatasetMetadata] = None
    ) -> str:
        # TODO handle conversions
        logger.info("started saving dataset")
        save_config = config.destination_config.save_option_config
        new_dataset_id: str
        match save_type := config.destination_config.save_options:
            case FileSaveOptions.SAVE_AS:
                logger.info("started saving as new dataset")
                save_config: SaveAsConfig
                logger.info(f"save_config: {save_config=}")
                new_dataset = self.new_save_as_dataset(
                    metadata,
                    save_config,
                    config.destination_config.save_option_config.file_name,
                )
                SaveService.save_dataset_save_as(self.old_dataset, new_dataset)

                new_dataset.metadata = metadata
                new_dataset = self.convert_dataset_to_desired_fileformat(
                    new_dataset,
                    config.destination_config.file_Format,
                    kwargs={"file_name": save_config.file_name},
                )
                new_dataset_id = self.dataset_service.save_tabular_dataset_helper_sync(
                    input_data=new_dataset.dataset_location[0].path,
                    project_id=new_dataset.project_id,
                    user_id=new_dataset.user_id,
                    site_id=new_dataset.site_id,
                    action_id=new_dataset.action_id,
                    run_id=self.run_id,
                    workflow_id=self.workflow_id,
                    name=new_dataset.name,
                    description=new_dataset.description,
                    tags=new_dataset.tags,
                    access_mode=new_dataset.access_mode,
                    custom_information=new_dataset.custom_information,
                    metadata=new_dataset.metadata,
                )
                # new_dataset_id = self.dataset_dao.insert_dataset_record(new_dataset) #TODO: Instead of using a dao, why dont we use service here? it clear a lot of clutter
                logger.info(f"new dataset id: {new_dataset_id}")

            case FileSaveOptions.REPLACE:
                logger.info("started replacing dataset")
                save_config: ReplaceConfig
                logger.info(f"SAVE CONFIG: {save_config}")
                new_dataset = self.new_replace_dataset(save_config)
                d_id = new_dataset.id
                logger.info(f"new_dataset: {new_dataset=}")
                SaveService.save_dataset_replace(
                    self.old_dataset, new_dataset, self.new_dataset_dir, self.user_id
                )
                new_dataset.metadata = metadata
                new_dataset = self.convert_dataset_to_desired_fileformat(
                    new_dataset, config.destination_config.file_Format
                )
                new_dataset.id = d_id
                logger.info(f"new_dataset: {new_dataset=}")
                if not self.dataset_dao.replace_dataset_record(new_dataset):
                    raise ValueError(f"unable to replace {new_dataset.id=}")
                new_dataset_id = new_dataset.id
            case _:
                raise NotImplementedError(f"save not implemented for {save_type=}")
        # hexaind drive
        if destination_dir := config.destination_config.destination_folder_path:
            logger.info("started saving in hexaind drive")
            logger.debug(f"started saving in hexaind drive at {destination_dir}")
            destination_dir = Path(destination_dir)
            if (
                destination_dir.resolve()
                .absolute()
                .is_relative_to(environment.hexaind_drive)
            ):
                destination_dir.mkdir(parents=True, exist_ok=True)
                for location in new_dataset.dataset_location:
                    old_path = Path(location.path)
                    new_path = destination_dir / old_path.name
                    if location.isfolder:
                        logger.debug(f"copying folder {old_path} into {new_path}")
                        shutil.copytree(old_path, new_path)
                    else:
                        logger.debug(f"copying file {old_path} into {new_path}")
                        shutil.copy(old_path, new_path)
                logger.info("copied data into new location")
            else:
                logger.warning(f"not saving since {destination_dir=} not in hexaind drive")
        logger.info("completed saving dataset")
        return new_dataset_id
