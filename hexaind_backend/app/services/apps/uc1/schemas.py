from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class ModelRelatedInfo(BaseModel):
    file_path: str  # pickleFile


class UC1AggregatedData(BaseModel):
    all_trained_dids: List[str] = Field(
        default=[], description="contains all trained dId's"
    )
    unique_ids: List[str] = Field(default=[], description="contains all unique id's")
    models_map: Dict[str, ModelRelatedInfo] = Field(
        default={}, description="models map {uniqueId: modelrelateddata}"
    )


class UC1SetTrainConfig(BaseModel):
    # comes from uploaded zip
    raw_data_file_path: str
    all_dids: List[str] = Field(default=[])
    all_design_measurements: Optional[List[List[str]]] = None

    # selected by customer
    selected_train_dids: Optional[List[str]] = Field(default=None)
    selected_test_dids: Optional[List[str]] = Field(default=None)

    skip_if_exist: bool = Field(default=True)
    save_plots: bool = Field(default=True)
    scaling_coefficient_overloads: dict = Field(default={})
    target_material_designation: List[str] = Field(default=[])

    unique_id: str

    user_id: str
    updated_at: Optional[datetime] = None


class UC1SetPredictionConfig(BaseModel):
    # comes from uploaded zip
    raw_data_file_path: str
    all_dids: List[str] = Field(default=[])
    all_design_measurements: Optional[List[List[str]]] = None

    prediction_did: str
    selected_unique_id: str
    prediction_unique_id: Optional[str] = None
    predict_points_df: Optional[Any] = None
    grid_definition: Optional[Any] = None
    plot_predictions: Optional[bool] = True
    apply_photomask_scalars: Optional[bool] = True
    do_sanity_check: Optional[bool] = True

    user_id: str
    updated_at: Optional[datetime] = None


class UC1FilesResponse(BaseModel):
    file_name: str
    file_path: str
    all_dids: List[str] = Field(default=[])
    all_design_measurements: Optional[List[List[str]]] = None
    selected_train_dids: Optional[List[str]] = Field(default=[])
    selected_test_dids: Optional[List[str]] = Field(default=[])
    target_material_designation: List[str] = Field(default=[])


class UC1ZipUploadResponse(BaseModel):
    files: List[UC1FilesResponse]
