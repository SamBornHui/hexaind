from datetime import datetime, timezone
import os
import pandas as pd
from pathlib import Path
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.assets.datasets.schemas import (DatasetType, Dataset, UploadStatus, UploadStats, AccessMode,
                                                       DatasetLocation, DatasetMetadata, TabularDatasetInformation)

def get_folder_size(folder_path: str) -> int:
    return sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(folder_path)
        for filename in filenames
    )

def generate_dataset_location_object(file_path: str = "", size="", extension=".csv", is_folder=False, last_modified_by=None):

    if os.path.isdir(file_path):
        is_folder = True
        size = get_folder_size(file_path)
    else:
        size = os.path.getsize(file_path)
    
    if str(file_path).endswith(".csv"):
        extension = ".csv"
    else:
        extension = ".parquet"

    return DatasetLocation(
        isfolder=is_folder,
        size=str(size),
        extension=extension,
        path=file_path,
        last_modified_by=last_modified_by,
        last_modified_at=datetime.now(timezone.utc)
    )


def generate_dataset_object(file_path: str = "", dataset_location=None, name="", user_id="", site_id="", project_id="",
                            action_id="", dataset_type=DatasetType.TABULAR, description="", access_mode = AccessMode.INTERNAL, **kwargs):
    
    if dataset_location is None:
        dataset_location = generate_dataset_location_object(file_path)

    result = DatasetsService.get_column_statistics_from_tabular_data(
                                                                    file_path=file_path,
                                                                    preview=True, 
                                                                    column_data_types=True
                                                                    )
    
    column_statistics, total_rows = DatasetsService.convert_statistics_from_client_supported_format_to_db_record_format(result["column_statistics"]), result["total_rows"]

    # write stats to the file
    numeric_stats_file, categorical_stats_file = DatasetsService.write_statistics_to_file(statistics=column_statistics, 
                                                                                          result_file_location=str(Path(file_path).parent)
                                                                                          )
    
    
    preview, col_type_data = result["preview"], result["column_data_types"]

    # write preview to the file
    preview_file_path = DatasetsService.write_preview_to_file(preview_data=preview,
                                                              result_file_location=str(Path(file_path).parent)
                                                              ) 

    columns_metadata_file = DatasetsService.write_column_metadata_to_file(column_metadata=col_type_data, result_file_location=str(Path(file_path).parent))
    metadata = DatasetMetadata(data_source=None, columns_metadata=None, columns_metadata_file=columns_metadata_file)
    
    
    return Dataset(
        user_id=user_id,
        project_id=project_id,
        site_id=site_id,
        action_id=action_id,
        name=name,
        description=description,
        dataset_type=dataset_type,
        dataset_information=[TabularDatasetInformation(
                                                        preview=None,
                                                        statistics=None,
                                                        numerical_statistics_file=numeric_stats_file,
                                                        categorical_statistics_file=categorical_stats_file,
                                                        preview_file=preview_file_path,
                                                        row_count=total_rows,
                                                        visualize=None,
                                                        dataset_schema=None,
                                                        )],
        upload_status=UploadStatus.COMPLETED,
        upload_stats=UploadStats(percentage="100%"),
        metadata=metadata,
        created_at=datetime.now(timezone.utc),
        dataset_location=[dataset_location],
        access_mode=access_mode,
        tags=[],
        custom_information=None
    )
