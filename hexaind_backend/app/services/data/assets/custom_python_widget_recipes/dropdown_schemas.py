from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class DropDownType(str, Enum):
 
    SINGLE_SELECT = "SINGLE_SELECT"
 
    MULTI_SELECT = "MULTI_SELECT"
 
class DropDownSourceType(str, Enum):
    
    STATIC = "STATIC"
 
    DYNAMIC = "DYNAMIC"

class DynamicDropDownSubType(str, Enum):
    
    COLUMN_NAMES = "COLUMN_NAMES"
 
class DropDownSourceDetails(BaseModel):

    drop_down_source_type: DropDownSourceType = Field(default=DropDownSourceType.STATIC, description="static or dynamic values for the dropdown")

    drop_down_values: List = Field(default=[], description="All values entered(are gonna populate) into dropdwon")

    dynamic_sub_type: Optional[DynamicDropDownSubType] = Field(default=None, description="If it is a dynamic dropdown then user should select type of dynamic values, ex: columns names, uniques, etc.")

    dynamic_drop_down_source_data_name: Optional[str] = Field(default=None, description="user selected dataset from prev widget.")

    dynamic_drop_down_source_data_output_name: Optional[str] = Field(default="",
                                                                     description="user selected dataset from prev widget.") #UI sending here outputname

    drop_down_selected_values: Union[List[str], str] = Field(default="", description="user selected values for the dropdown.")

class DropDownDetails(BaseModel):

    is_dropdown: Optional[bool] = Field(default=False, description="Indicates if the parameter is a dropdown")

    drop_down_type: Optional[DropDownType] = Field(default=None, description="Dropdown type: single or multi-select")
    
    drop_down_source_details: Optional[DropDownSourceDetails] = Field(default=None, description="Details for fetching dynamic values, for now support only for the dataframe column names")