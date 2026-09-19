from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import ast

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config.env_vars import environment
from app.core.schemas.action_result import (
    ActionResult,
    ActionResultType,
    DatasetActionResult,
    FileActionResult,
    StringActionResult,
    IntegerActionResult,
    FloatActionResult,
    ListOfIntegersActionResult,
    ListOffloatsActionResult,
    ListOfStringsActionResult,
    DictionaryActionResult
)
from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomCodePythonWidgetInputsMap,
    CustomPythonWidgetRecipe,
    WidgetInputSourceType,
)
from app.services.data.assets.custom_python_widgets.schemas import CustomPythonWidget
from app.services.data.assets.datasets.service import DatasetsService
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import (
    CustomCodeActivityConfig,
    CustomFunctionAcceptedPythonClasses,
    CustomFunctionInputs,
    CustomFunctionOutputs,
    CustomFunctionParameters,
    InputOutputConfig,
    WidgetParameterDetails,
)
from app.utils.file_utils import FileUtils


class CustomPythonWidgetServiceHelper:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None):
        self.datasets_service = DatasetsService(db_sync_client=db_sync_client, db_async_client=db_async_client)

    def convert_file_to_dataset(self, file_path_str: str, project_id: str, user_id: str, site_id: str, name: str,
                                **kwargs):
        file_path = Path(file_path_str)
        if not file_path.exists():
            raise ValueError(f"No such path exists {file_path_str}")

        if kwargs.get('dry_run',False):
            return "DryRunDatasetId" # for dry run we are not creating actual dataset

        if file_path_str.endswith(".csv"):
            copy_file_location = f"{environment.custom_python_code_datasets_location}/{uuid4()}_{file_path.name}"
            FileUtils.createDeepCopyOfFile(file_path_str, copy_file_location)
            return self.datasets_service.save_tabular_dataset_helper_sync(
                input_data=copy_file_location,
                project_id=project_id,
                user_id=user_id,
                site_id=site_id,
                name=name
            )
        elif file_path_str.endswith(".json"):
            copy_file_location = f"{environment.custom_python_code_datasets_location}/{uuid4()}_{file_path.name}"
            FileUtils.createDeepCopyOfFile(file_path_str, copy_file_location)
            return self.datasets_service.save_tabular_dataset_helper_sync(
                input_data=copy_file_location,
                project_id=project_id,
                user_id=user_id,
                site_id=site_id,
                name=name
            )

        raise Exception("Only .csv and .json type files are allowed")

    def convert_widget_inputs_map_to_action_result(self, widget_inputs_map: CustomCodePythonWidgetInputsMap,
                                                   dataset_kwargs: dict):
        if widget_inputs_map.source == WidgetInputSourceType.INPUT_ENTERED_MANUALLY_ON_WIDGET or (widget_inputs_map.drop_down_details is not None and widget_inputs_map.drop_down_details.is_dropdown == True):
            if widget_inputs_map.default_value is None:
                return None
            
            if widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.STRING: # or widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.PATHLIB_PATH:
                return ActionResult(
                    type=ActionResultType.STRING,
                    result=StringActionResult(string_value=widget_inputs_map.default_value)
                )
            
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.PATHLIB_PATH:
                return ActionResult(
                    type=ActionResultType.FILE_OR_FOLDER_PATH,
                    result=FileActionResult(file_path_value=widget_inputs_map.default_value)
                )
            
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.INTEGER:
                return ActionResult(
                    type=ActionResultType.INTEGER, #TODO - Update default value
                    result=IntegerActionResult(integer_value=int(widget_inputs_map.default_value) if widget_inputs_map.default_value else 0) #widget_inputs_map.default_value)
                )
            
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.FLOAT:
                return ActionResult(
                    type=ActionResultType.FLOAT, #TODO - Update default value
                    result=FloatActionResult(float_value=float(widget_inputs_map.default_value) if widget_inputs_map.default_value else 0.0) #widget_inputs_map.default_value)
                )
            
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.STRINGS_LIST:

                if widget_inputs_map.default_value:
                    list_string_value = ast.literal_eval(widget_inputs_map.default_value)
                    string_list = [str(element) for element in list_string_value]
                else:
                    string_list = []

                return ActionResult(
                    type=ActionResultType.STRINGS_LIST,
                    result=ListOfStringsActionResult(
                        strings_list_value=string_list
                    )
                )
            
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.FLOATS_LIST:

                if widget_inputs_map.default_value:
                    list_value = ast.literal_eval(widget_inputs_map.default_value)
                    float_list = [float(num) for num in list_value]
                else:
                    float_list = [0.0]

                return ActionResult(
                    type=ActionResultType.FLOATS_LIST, #TODO - Update default value
                    result=ListOffloatsActionResult(
                        floats_list_value=float_list
                    )
                )
            
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.INTEGERS_LIST:
                
                if widget_inputs_map.default_value:
                    list_value = ast.literal_eval(widget_inputs_map.default_value)
                    int_list = [int(num) for num in list_value]
                else:
                    int_list = [0]

                return ActionResult(
                    type=ActionResultType.INTEGERS_LIST, #TODO - Update default value
                    result=ListOfIntegersActionResult(
                        integers_list_value=int_list
                    )
                )
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.PANDAS:
                dataset_id = self.convert_file_to_dataset(widget_inputs_map.default_value, **dataset_kwargs)
                return ActionResult(
                    type=ActionResultType.DATASET,
                    result=DatasetActionResult(dataset_id=dataset_id)
                )
            
            elif widget_inputs_map.type == CustomFunctionAcceptedPythonClasses.DICTIONARY:
                return ActionResult(
                    type=ActionResultType.DICTIONARY,
                    result=DictionaryActionResult(dict_value= widget_inputs_map.default_value if widget_inputs_map.default_value else "{}")
                )

            raise ValueError(f"Unable to find {widget_inputs_map.type} conversion")
        else:
            raise ValueError(f"Only {WidgetInputSourceType.INPUT_ENTERED_MANUALLY_ON_WIDGET} source is allowed")

    @staticmethod
    def get_dummy_value(python_class_type: str):
        
        if python_class_type == CustomFunctionAcceptedPythonClasses.STRING: # or python_class_type == CustomFunctionAcceptedPythonClasses.PATHLIB_PATH :
            return ActionResult(
                type=ActionResultType.STRING,
                result=StringActionResult(
                    string_value="<ToBeModifiedDuringWidgetRunTimeByUI>"
                )
            )
        
        elif python_class_type == CustomFunctionAcceptedPythonClasses.PATHLIB_PATH :
            return ActionResult(
                type=ActionResultType.FILE_OR_FOLDER_PATH,
                result=FileActionResult(
                    file_path_value="<ToBeModifiedDuringWidgetRunTimeByUI>"
                )
            )
        
        elif python_class_type == CustomFunctionAcceptedPythonClasses.INTEGER:
            return ActionResult(
                type=ActionResultType.INTEGER,
                result=IntegerActionResult(
                    integer_value=0
                )
            )
        
        elif python_class_type == CustomFunctionAcceptedPythonClasses.FLOAT:
            return ActionResult(
                type=ActionResultType.FLOAT,
                result=FloatActionResult(
                    float_value=0
                )
            )
        
        elif python_class_type == CustomFunctionAcceptedPythonClasses.STRINGS_LIST:
            return ActionResult(
                type=ActionResultType.STRINGS_LIST,
                result=ListOfStringsActionResult(
                    strings_list_value=["<ToBeModifiedDuringWidgetRunTimeByUI>"]
                )
            )
        
        elif python_class_type == CustomFunctionAcceptedPythonClasses.FLOATS_LIST:
            return ActionResult(
                type=ActionResultType.FLOATS_LIST,
                result=ListOffloatsActionResult(
                    floats_list_value=[0]
                )
            )
        
        elif python_class_type == CustomFunctionAcceptedPythonClasses.INTEGERS_LIST:
            return ActionResult(
                type=ActionResultType.INTEGERS_LIST,
                result=ListOfIntegersActionResult(
                    integers_list_value=[1]
                )
            )
        
        elif python_class_type == CustomFunctionAcceptedPythonClasses.PANDAS:
            return ActionResult(
                type=ActionResultType.DATASET,
                result=DatasetActionResult(
                    dataset_id="<ToBeModifiedDuringWidgetRunTimeByUI>"
                )
            )
        elif python_class_type == CustomFunctionAcceptedPythonClasses.DICTIONARY:
            return ActionResult(
                type=ActionResultType.DICTIONARY,
                result=DictionaryActionResult(
                    dict_value="{}"
                )
            )
        
        raise ValueError(f"Cannot create dummy value for type {python_class_type}")

    def convert_recipe_to_widget(self, recipe: CustomPythonWidgetRecipe, widget_version: str,
                                 dataset_kwargs: dict, dry_run: bool =False) -> CustomPythonWidget:
        # dry run => doesnt create datasets
        function_inputs = []
        widget_parameters = []
        function_outputs = []
        inputs_ = []  # inside widget
        outputs_ = []  # outputs widget
        for input_map in recipe.inputs_map:
            if input_map.source == WidgetInputSourceType.INPUT_SELECTED_FROM_PRIOR_WIDGET:
                if input_map.drop_down_details is None or (input_map.drop_down_details is not None and input_map.drop_down_details.is_dropdown == False):
                    function_inputs.append(CustomFunctionInputs(
                    type=input_map.type,
                    arg_name=input_map.arg_name
                    ))
                    inputs_.append(InputOutputConfig(
                        urn="<ToBeModifiedDuringWidgetRunTimeByUI>",
                        map_to_argument=input_map.arg_name,
                        name="<ToBeModifiedDuringWidgetRunTimeByUI>"
                    ))
                    continue

            dataset_kwargs['dry_run'] = dry_run
            default_value = self.convert_widget_inputs_map_to_action_result(widget_inputs_map=input_map,
                                                                            dataset_kwargs=dataset_kwargs)
            value = default_value if default_value is not None else CustomPythonWidgetServiceHelper.get_dummy_value(
                input_map.type)
            widget_parameters.append(CustomFunctionParameters(
                type=input_map.type,
                arg_name=input_map.arg_name,
                default_value=default_value,
                value=value,
                is_mandatory=input_map.is_mandatory,
                drop_down_details=input_map.drop_down_details,
                ui_details=WidgetParameterDetails(
                    ui_type=input_map.mapped_input.ui_type,
                    ui_config=input_map.mapped_input.ui_config
                ) if input_map.mapped_input else None
            ))
        for index, out_map in enumerate(recipe.outputs_map):
            function_outputs.append(
                CustomFunctionOutputs(
                    type=out_map.type,
                    arg_name=out_map.mapped_output.reference_name
                )
            )
            action_result_type = out_map.mapped_output.type
            outputs_.append(InputOutputConfig(
                urn="<ToBeModifiedDuringWidgetRunTimeByUI>",
                type=action_result_type,
                map_to_argument=out_map.mapped_output.reference_name,
                name="<ToBeModifiedDuringWidgetRunTimeByUI>"
            ))

        custom_code_config = CustomCodeActivityConfig(
            version="1.0",
            widget_type=WidgetType.CUSTOM_CODE,
            module_id=recipe.module_id,
            function_inputs=function_inputs,
            widget_parameters=widget_parameters,
            function_outputs=function_outputs
        )

        custom_python_widget = CustomPythonWidget(
            version="1.0",
            name=recipe.name,
            widget_version=widget_version,
            description=recipe.description,
            reference_links=recipe.reference_links,
            recipe_id=recipe.id,
            tags=recipe.tags,
            widget_inputs_rules=recipe.widget_inputs_rules,
            widget_outputs_rules=recipe.widget_outputs_rules,
            widget_settings=recipe.settings,
            help_details=recipe.help_details,
            inputs=inputs_,
            outputs=outputs_,
            config=custom_code_config,
            published_by=dataset_kwargs["user_id"],
            published_at=datetime.now(timezone.utc),
            project_ids=[dataset_kwargs["project_id"]],
            site_ids=[dataset_kwargs["site_id"]],
            access_mode=recipe.access_mode,
            usage_count=0
        )

        return custom_python_widget
