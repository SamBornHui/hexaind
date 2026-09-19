from click import File
from pydantic import BaseModel, Field, RootModel
from enum import Enum
from typing import Dict, List, Union, Optional, Literal
from datetime import datetime, timezone
from pathlib import Path

class Datasheet(BaseModel):

    tensile_files: List[str] = Field(default=None)
    tensile_sample_data: str = Field(default=None)
    tensile_combined_data: str = Field(default=None)
    bulge_files: List[str] = Field(default=None)
    tensile_plot_data_path: str = Field(default=None)
    bulge_plot_data_path: str = Field(default=None)
    hss_complete_params: dict = Field(default=None)
    corrected_tensile_results: str = Field(default=None)
    bulge_scale_factor: dict = Field(default=None)
    # corrected_tensile_results: dict = Field(default=None)
    hss_weights_object: dict = Field(default=None)
    new_fit_params: dict = Field(default=None)
    initial_fit_params: dict = Field(default=None)
    preview:bool = Field(default=False)
    pdf_path:str = Field(default=None)
    metadata: dict = Field(default=None)

class ExportDatasheetResponse(BaseModel):
    datasheet_path: dict

class ComputeDatasheetResponse(BaseModel):
    datasheet: Optional[List[Datasheet]] = None

class CSVDataResponse(BaseModel):
    csv_data: list[dict]

class TensileSampleDataResponse(BaseModel):
    csv_data: dict

class ReadCsv(BaseModel):
    project_id: str = Field(default=None, description="project id")
    datasheet: str = Field(default=None, description="datasheet name")
    nominal_age: str = Field(default=None, description="nominal age")
    file_path: str = Field(default=None, description="file path")

class TensileSamples(BaseModel):
    tensile_sample_path: str = Field(default=None, description="file path for tensile sample")
    tensile_combined_path: str = Field(default=None, description="file path")

class BasePath(BaseModel):
    base_path: str = Field(default=None, description="datasheet name")

class FileDetails(BaseModel):
    project_id: str = Field(default=None, description="project id")
    datasheet: str = Field(default=None, description="datasheet name")
    nominal_age: str = Field(default=None, description="nominal age")
    file_path: str = Field(default=None, description="file path")

class AdjustedParams(BaseModel):
    project_id: str = Field(default=None, description="project id")
    datasheet: int = Field(default=None, description="datasheet name")
    nominal_age: int = Field(default=None, description="nominal age")
    params: dict = Field(default=None, description="file path")
    recompute: bool = Field(default=None, description="recompute otion")

class FlcParams(BaseModel):
    raw_file: str = Field(default=None, description="raw file")
    fit_file: str = Field(default=None, description="fit file")
    params: dict = Field(default=None, description="params")

class TensileParams(BaseModel):
    tensile_file: str = Field(default=None, description="tensile file")
    params: dict = Field(default=None, description="params")

class TensileConvertorResponse(BaseModel):
    tensile_data: dict = Field(default=None)


class CorrectTensileResponse(BaseModel):
    correct_data: dict = Field(default=None)

class CorrectTensile(BaseModel):
    project_id: str = Field(default=None, description="project id") 
    datasheet: int = Field(default=None, description="datasheet name")
    nominal_age: int = Field(default=None, description="nominal age")
    selected_sample: str = Field(default=None, description="selected file sample")
    corrected_tensile_results: dict = Field(default=None)
    s_min: float = Field(default=None)
    s_max: float = Field(default=None)
    recompute_Rp02: bool =  Field(default=False)

class CompareTensile(BaseModel):
    project_id: str = Field(default=None, description="project id") 
    datasheet: int = Field(default=None, description="datasheet name")
    nominal_age: int = Field(default=None, description="nominal age")

class LocalFitResponse(BaseModel):
    local_fit: dict

class SaveASCIIResponse(BaseModel):
    ascii: dict

class IngestDataResponse(BaseModel):
    ingestion_results: dict

class ConvertorUploadResponse(BaseModel):
    convertor_results: dict = Field(default=None)

class DownloadResultResponse(BaseModel):
    download_result: str

class FilePreviewResponse(BaseModel):
    file_name: str
    file_url: str  # Representing the URL/path to the PDF file

    class Config:
        from_attributes = True

class Datasheets(BaseModel):
    id: Optional[str] =  Field(default=None, description="datasheet id")
    project_id: str = Field(..., description="The ID of the project")
    user_id: str = Field(..., description="The ID of the user")
    datasheet: str = Field(..., description="The name or identifier of the datasheet")
    tensile_ages: List[int] = Field(default_factory=list, description="List of tensile ages")
    bulge_ages: List[int] = Field(default_factory=list, description="List of bulge ages")
    datasheet_path: str = Field(..., description="The full path to the datasheet")
    tensile_files: List[str] = Field(default_factory=list, description="List of tensile file paths")
    bulge_files: List[str] = Field(default_factory=list, description="List of bulge file paths")
    flc_files: List[str] = Field(default_factory=list, description="List of FLC file paths")
    locked: bool = Field(False, description="Indicates if the datasheet is locked")
    created_at: Optional[datetime] = Field(default=None,description="Created/Added time to platform")

class UpdateDatasheetRequest(BaseModel):
    datasheet: Optional[str] = None  # Optional field with default value None
    tensile_ages: Optional[List[int]] = None  # Optional field with default value None
    bulge_ages: Optional[List[int]] = None  # Optional field with default value None
    datasheet_path: Optional[str] = None  # Optional field with default value None
    tensile_files: Optional[List[str]] = None  # Optional field with default value None
    bulge_files: Optional[List[str]] = None  # Optional field with default value None
    flc_files: Optional[List[str]] = None  # Optional field with default value None
    locked: Optional[bool] = None  

class GetDatasheetsResponse(BaseModel):
    datasheets: List[Datasheets]

class GetDatasheetsDetailResponse(BaseModel):
    datasheets: List[Union[str, dict]]

class UpdateDatasheetResponse(BaseModel):
    datasheet: Datasheets = Field(default=None)
class SaveChangesResponse(BaseModel):
    status_code: int
    message: str
    save_id: str

class SaveChangesRequest(BaseModel):
    """
    Generic schema for datasheet_params save changes.
    """
    data: Optional[Dict] = Field(default_factory=dict)
