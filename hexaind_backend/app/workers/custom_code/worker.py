import pandas as pd
from app.core.services.action_handler.handler import *
from app.services.admin.projects.service import ProjectService
from app.services.data.assets.custom_python_widgets.service import (
    CustomPythonWidgetService,
)
from app.services.data.assets.datasets.schemas import (
    DatasetMetadata,
    DatasetSourceFormats,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.workflows.designer.schemas import *
from app.services.data.assets.modules.service import *
from app.services.data.assets.modules.helper import ConversionHelper
from app.core.celery.celery_worker import create_celery_app
from app.services.workflows.designer.service import WorkflowDesignerService
from app.workers.utils import common_widget_manager
from app.config.env_vars import environment
from app.core.celery.global_config import CUSTOM_CODE_ACTION_WORKER_DEFAULT_QUEUE

logger = logging.getLogger(__package__)

app = create_celery_app(
    name="custom_code_action_worker",
    default_queue=CUSTOM_CODE_ACTION_WORKER_DEFAULT_QUEUE,
    tasks=["app.workers.custom_code.worker"],
)


def get_custom_code_function_inputs(action_handler: ActionHandler, widget: Widget):
    res = {}
    if len(action_handler.action_record.depends_on) > 0:
        name_response_map: Dict[str, WidgetResultResponse] = (
            action_handler.get_widget_inputs_from_prev_actions(widget.inputs)
        )
        for input_output_config in widget.inputs:
            res[input_output_config.map_to_argument] = name_response_map[
                input_output_config.name
            ]

    return res


def detailed_type(value):
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return "list[str]"
        elif all(isinstance(item, int) for item in value):
            return "list[int]"
        elif all(isinstance(item, float) for item in value):
            return "list[float]"
        else:
            raise Exception("Not supported mixed types in List")
    return str(type(value))


def generate_action_results_from_results(
    action_handler: ActionHandler,
    outputs: List[InputOutputConfig],
    results,
    conversion_kwargs,
    run_record: Run,
):
    logger.info(f"generating action results from results ")
    action_results = []
    if len(results) != len(outputs):
        logger.exception("length of results is not equal to length of outputs.")
        raise Exception("Output count from function and config doesnt match")

    image_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".tiff",
        ".svg",
        ".html",
    )

    for i, output in enumerate(outputs):

        conversion_kwargs["name"] = output.name

        converted_output = ConversionHelper.convert_to_action_result_type(
            results[i], output.type, detailed_type(results[i]), conversion_kwargs
        )

        if output.type == ActionResultType.DATASET:
            # converted_output.metadata = DatasetMetadata(
            #     data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
            #         WidgetType.CUSTOM_CODE.value.lower()
            #     )
            # )
            # dataset_id = (
            #     action_handler.datasets_handler.datasets_dao.insert_dataset_record(
            #         converted_output
            #     )
            # )
            dataset_id = (
                action_handler.datasets_handler.save_tabular_dataset_helper_sync(
                    input_data=converted_output.dataset_location[0].path,
                    project_id=converted_output.project_id,
                    user_id=converted_output.user_id,
                    site_id=converted_output.site_id,
                    name=output.name,
                    workflow_id=conversion_kwargs["workflow_id"],
                    run_id=conversion_kwargs["run_id"],
                    action_id=converted_output.action_id,
                    description=converted_output.description,
                )
            )
            result = DatasetActionResult(dataset_id=dataset_id)

        elif (
            output.type == ActionResultType.STRING
            and converted_output.string_value.endswith(image_extensions)
        ) or (
            output.type == ActionResultType.STRINGS_LIST
            and converted_output.strings_list_value
            and converted_output.strings_list_value[0].endswith(image_extensions)
        ):
            if output.type == ActionResultType.STRING:
                result = StringActionResult(
                    string_value=converted_output.string_value  # , visualization_id=dataset_id
                )
            elif output.type == ActionResultType.STRINGS_LIST:
                result = ListOfStringsActionResult(
                    strings_list_value=converted_output.strings_list_value
                )

            output.type = ActionResultType.VISUALIZATION
        elif (
            output.type == ActionResultType.STRING
            or output.type == ActionResultType.INTEGER
            or output.type == ActionResultType.FLOAT
            or output.type == ActionResultType.INTEGERS_LIST
            or output.type == ActionResultType.FLOATS_LIST
            or output.type == ActionResultType.STRINGS_LIST
            or output.type == ActionResultType.DICTIONARY
        ):

            result = converted_output

        else:
            raise ValueError(
                "Unable to match valid widget output type for function output"
            )
        action_results.append(
            ActionResult(output_name=output.name, type=output.type, result=result)
        )
    logger.info("generated and returning the action results ")
    return action_results


def generate_function_inputs(
    action_handler,
    function_inputs,
    widget_parameters,
    input_name_results_map,
    conversion_kwargs,
):
    logger.info("generating function inputs.")
    logger.info(f"function inputs: {function_inputs}")

    # converting ActionResult to Python Data types
    required_widget_inputs = {  # from workflow run time
        custom_function_input.arg_name: ConversionHelper.convert_from_widget_result_response(
            input_name_results_map.get(custom_function_input.arg_name),
            custom_function_input.type,
            conversion_kwargs,
        )
        for custom_function_input in function_inputs
        if custom_function_input.arg_name in input_name_results_map
    }

    # converting user entered values to Python Data types
    logger.info("generated widget inputs")
    required_widget_parameters = {  # from workflow design time
        widget_parameter.arg_name: ConversionHelper.convert_from_custom_function_parameters(
            widget_parameter, action_handler.datasets_handler, conversion_kwargs
        )
        for widget_parameter in widget_parameters
    }

    logger.info("generated widget parameters.")
    logger.info("returning all the function and widget inputs.")
    return {**required_widget_inputs, **required_widget_parameters}


def validate_updated_inputs_outputs(
    existing_widget_inputs, updated_widget_inputs, name
):

    if len(existing_widget_inputs) != len(updated_widget_inputs):
        raise ValueError(
            f"Widget expected {len(existing_widget_inputs)} however gave only {len(updated_widget_inputs)} widget parameters"
        )
    existing_parameters_map = {
        parameter.arg_name: parameter.type for parameter in existing_widget_inputs
    }
    replacing_parameters_map = {
        parameter.arg_name: parameter.type for parameter in updated_widget_inputs
    }
    for key in replacing_parameters_map:
        if key not in existing_parameters_map:
            raise ValueError(
                f"In {name}, Widget expected {key} argument as input entered manually on widget."
            )
        if existing_parameters_map[key] != replacing_parameters_map[key]:
            raise ValueError(
                f"In {name}, Widget expected {key} type to be {replacing_parameters_map[key]} but found {existing_parameters_map[key]}"
            )


@app.task(name="task_custom_code")
def task_custom(action_id: str):
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.CUSTOM_CODE:
            raise Exception("Invalid action submitted to CUSTOM_CODE worker")

        if widget.config.propagate_widget_changes:
            custom_python_widget_service = CustomPythonWidgetService(
                db_sync_client=action_handler.db_client
            )
            custom_python_widget = custom_python_widget_service.get_widget_by_id_sync(
                widget.config.widget_id
            )
            # update config - function inputs
            validate_updated_inputs_outputs(
                widget.config.function_inputs,
                custom_python_widget.config.function_inputs,
                "Widget Inputs",
            )
            validate_updated_inputs_outputs(
                widget.config.function_outputs,
                custom_python_widget.config.function_outputs,
                "Widget Outputs",
            )
            # currently we are ignoring changes in default values
            validate_updated_inputs_outputs(
                widget.config.widget_parameters,
                custom_python_widget.config.widget_parameters,
                "Widget Parameters",
            )

            config = CustomCodeActivityConfig(
                version="1.0",
                widget_type=WidgetType.CUSTOM_CODE,
                module_id=custom_python_widget.config.module_id,
                function_inputs=widget.config.function_inputs,
                widget_parameters=widget.config.widget_parameters,
                function_outputs=widget.config.function_outputs,
            )
            # replacing widget config
            widget.config = config

        module_service = ModuleService(db_sync_client=action_handler.db_client)

        # get custom code function inputs from prev actions
        input_name_results_map = get_custom_code_function_inputs(
            action_handler=action_handler, widget=widget
        )

        kwargs = generate_function_inputs(
            action_handler,
            widget.config.function_inputs,
            widget.config.widget_parameters,
            input_name_results_map,
            {},
        )

        # convert results to widget outputs
        results_prefix = Path(new_dataset_dir)
        custom_results_dir = str(environment.cpw_results_folder).format(run_record.id)
        Path(custom_results_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"formed kwargs keys {kwargs.keys()}")
        # run the module with the inputs
        logger.info(f"Running Custom code {widget.config.module_id}")
        additional_params = {
            "RESULTS_DIR": str(results_prefix),
            "CURRENT_PROJECT_ID": run_record.project_id,
            "CUSTOM_RESULTS_DIR": str(custom_results_dir),
        }
        logger.info(f"kwargs PARAMS: {kwargs}")
        results_list = module_service.run_module(
            module_id=widget.config.module_id,
            kwargs=kwargs,
            additional_params=additional_params,
        )

        conversion_kwargs = {
            "file_prefix": str(results_prefix),
            "action_id": action_handler.action_id,
            "user_id": run_record.owner_id,
            "workflow_id": run_record.workflow_id,
            "project_id": run_record.project_id,
            "site_id": run_record.site_id,
            "run_id": run_record.id,
        }
        logger.info("converted to kwargs")

        action_results = generate_action_results_from_results(
            action_handler, widget.outputs, results_list, conversion_kwargs, run_record
        )
        logger.info(f"ACTION RESULTS: {action_results}")
        action_result_ids = [
            action_handler.create_action_result_record(action_result)
            for action_result in action_results
        ]
        logger.info(f"Created action result records. {action_result_ids}")

        # update mongo with all the result ids at once for the Action
        for action_result_id in action_result_ids:
            # save the results (attaching result record id to the action record)
            action_handler.action_success_handler(action_result_id=action_result_id)
