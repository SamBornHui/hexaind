from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional, Dict, Union


class FormatBaselineResponse(BaseModel):

    scrap_alloys: List

    sources: List

    demand_alloys: List

    furnaces: List

    scrap_file_path: str

    demand_file_path: str


class ExtractAlloyRequest(BaseModel):

    alloys: List[str]

    file_path: str

    baseline_file: str


class ExtractAlloyResponse(BaseModel):

    extracted_data: Dict


class LIMITS(str, Enum):

    PLANT = "PLANT"

    DEMAND = "DEMAND"

    SCRAP = "SCRAP"
    
    NONE = "NONE"


class ScenarioDetail(BaseModel):

    scenario_name: str

    scraps: Optional[Dict] = Field(default_factory=dict)

    demands: Optional[Dict] = Field(default_factory=dict)

    limits: Optional[Dict] = Field(default_factory=dict)

    results: Optional[Dict] = Field(default_factory=dict)

    limit_by: LIMITS = Field(default=LIMITS.NONE)


class SAMVisualization(BaseModel):

    alloy: str

    plots: List[str]

    furnaces: List[str]


class SAMUseCase(BaseModel):

    baseline_file: str

    usecase_name: str

    usecase_desc: Optional[str] = ""

    scenarios: List[ScenarioDetail]

    user_id: str

    usecase_id: Optional[str] = Field(
        default=None,
        description="Usecase Id",
        validation_alias=AliasChoices("_id", "usecase_id"),
    )

    created_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Created Date",
    )

    modified_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Modified Date",
    )

    config_content: Optional[str] = ""

    unit: Optional[str] = Field(default="lbs")

    visualizations: Optional[List[SAMVisualization]] = Field(default=None)


class ScenariosResponse(BaseModel):

    message: str

    usecase_id: str

    usecase_data: Union[SAMUseCase, str] = ""


class Scenarios_INFO(BaseModel):

    name: str

    file_path: str


class SAMViz(BaseModel):

    scenarios: List[Scenarios_INFO]

    alloy_name: str

    unit: Optional[str] = Field(default="lbs")

    config_path: str

    baseline: Optional[str] = ""


class SAMCustomInformation(BaseModel):

    sam_result: str

    furnace_name: str

    config_path: str


class DeleteSAMResponse(BaseModel):

    message: str

    sam_id: str


class GetLimitsResponse(BaseModel):

    limits: Optional[List[Dict]] = Field(default_factory=list)

    demands: Optional[List] = Field(default_factory=list)

    message: str
