from app.utils.file_utils import FileUtils
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.config.env_vars import environment
from app.services.data.assets.datasets.schemas import (
    Dataset, DatasetType, DatasetSubType, AccessMode,
    DatasetLocation,DatasetMetadata, DatasetSourceFormats)
from app.services.AI.mobo.service import MOBOService
from app.services.AI.mobo.schemas import MOBOConfig, MOBORunState
from app.core.celery.global_config import ACTIVE_LEARNING_ACTION_WORKER_DEFAULT_QUEUE
from app.workers.utils import common_widget_manager
from app.core.celery.celery_worker import create_celery_app #create_celery_non_global_app #create_celery_app
import os

app = create_celery_app('active_learning_action_worker', default_queue=ACTIVE_LEARNING_ACTION_WORKER_DEFAULT_QUEUE)

@app.task(name="task_active_learning")
def task_active_learning(action_id: str):

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):

        custom_run_state = action_handler.get_custom_run_state()

        if widget.type != WidgetType.ACTIVE_LEARNING:
            raise Exception("Invalid action submited to ACTIVE LEARNING worker")

        dataset_id = None
        dataset_metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                widget.type.value.lower()))
        # setting result directory
        results_folder = Path(new_dataset_dir)
        results_folder.mkdir(parents=True, exist_ok=True)
        results_folder = str(results_folder)

        # check the state of the ACTIVE_LEARNING widget
        if action_handler.action_record.custom_run_state and action_handler.action_record.custom_run_state.total_invoke_count != 0: # executed previously
        
            # if state: triggering second time, load state, read results from cycle widget, update experimet, update the state, new recommendation on the data which is in state variable, check terimination critiria, emit decision also along with mobo result
            prev_action_results_response = action_handler.get_all_inputs_from_prev_action() # Dataset
            prev_action_results: List[WidgetResultResponse] = []
            # iterate over all values (which are lists) in the dictionary and extend the prev_action_results list
            for result_list in prev_action_results_response.values():
                prev_action_results.extend(result_list)
            
            print("Previous action results: ", prev_action_results)
            
            if not prev_action_results or len(prev_action_results) > 1 or prev_action_results[0].result_type != ActionResultType.DATASET:
                raise Exception("ACTIVE_LEARNING action got non-compatible result(s) from it's prev action")
            
            dataset_record: Dataset = prev_action_results[0].result_value
            dataset_path_info: DatasetLocation = dataset_record.dataset_location[0]

            if dataset_record.dataset_type != DatasetType.TABULAR:
                raise Exception("ACTIVE_LEARNING action got non-compatible result(s) from it's prev action. Expected: TABULAR. But got: ", dataset_record.dataset_type)
            
            # initializing the ACTIVE_LEARNING service 
            mobo_config: MOBOConfig = widget.config

            # Building kwargs for MOBO-service
            kwargs = dict(workflow_id=run_record.workflow_id, 
                          workflow_name=run_record.name,
                          project_id=action_id,
                          results_folder=results_folder
                          )
            
            # calling MOBO service class
            mobo_service = MOBOService(db_sync_client=action_handler.db_client)
            if dataset_record.dataset_sub_type == DatasetSubType.THERMOCALC_RESULTS:
                mobo_output = mobo_service.update_mobo_experiment(mobo_config, thermocalc_output=dataset_path_info.path, **kwargs)
            
            elif dataset_record.dataset_sub_type == DatasetSubType.PREDICTION_RESULTS:
                mobo_output = mobo_service.update_mobo_experiment(mobo_config, prediction_output=dataset_path_info.path, **kwargs)
            
            else:
                mobo_output = mobo_service.update_mobo_experiment(mobo_config, rescale_output=dataset_path_info.path, **kwargs)

            if mobo_output.exception_detail:
                raise Exception(f"ACTIVE_LEARNING widget raised exception: {mobo_output.exception_detail}")

            if mobo_output.terminate:
                # save the json result details in mongo record 
                dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(input_data=str(
                    action_handler.action_record.custom_run_state.custom_state["master_source_csv_file_path"]),
                                                                                              project_id=run_record.project_id,
                                                                                              site_id=run_record.site_id,
                                                                                              user_id=run_record.owner_id,
                                                                                              action_id=action_id,
                                                                                              run_id=run_record.id,
                                                                                              workflow_id=run_record.workflow_id,
                                                                                              name=widget.name,
                                                                                              description=widget.description,
                                                                                              access_mode=AccessMode.INTERNAL,
                                                                                              metadata=dataset_metadata)
                
                # saving the action results to the collection
                action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))
                
                
            else:
                # save the json result details in mongo record     
                dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(
                    input_data=str(mobo_output.tabular_path), project_id=run_record.project_id,
                    site_id=run_record.site_id, user_id=run_record.owner_id,
                    action_id=action_id, run_id=run_record.id, workflow_id=run_record.workflow_id,
                    name=widget.name, description=widget.description, access_mode=AccessMode.INTERNAL,
                    metadata=dataset_metadata)
                
                # saving the action results to the collection
                action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))


                custom_run_state.total_invoke_count += 1
                custom_run_state.cycle_intermediate_results.append(CycleIntermediateResults(invocation_num=custom_run_state.total_invoke_count, result_record_ids=[action_result_id]))
                action_handler.update_action_custom_run_state(custom_run_state=custom_run_state) # update the action run state

        else: # executing first time
            # check for dataset, create duplicate of this dataset and update the state variable in action record, initialize the experiment

           # mobo_run_state: CustomRunState = CustomRunState(total_invoke_count=1)

            prev_action_results_response = action_handler.get_all_inputs_from_prev_action() # Dataset

            # Initialize an empty list to store all WidgetResultResponse objects
            prev_action_results: List[WidgetResultResponse] = []

            # iterate over all values (which are lists) in the dictionary and extend the prev_action_results list
            for result_list in prev_action_results_response.values():
                prev_action_results.extend(result_list)
            
            # Check the prev action results are compatible with the filter widget
            if not prev_action_results or len(prev_action_results) > 1 or prev_action_results[0].result_type != ActionResultType.DATASET:
                raise Exception("ACTIVE_LEARNING action got non-compatible result(s) from it's prev action")
            
            # take the prev result
            dataset_record: Dataset = prev_action_results[0].result_value
            dataset_path_info: DatasetLocation = dataset_record.dataset_location[0]

            # assuming getting only one file for now:
            if not dataset_path_info.isfolder:
                dataset_path = dataset_path_info.path
            else:
                # Need to add logic for reading multiple files/fodler. TODO
                raise Exception("ACTIVE_LEARNING action got folder as a result from it's prev action.")
            
            # creating the copy of the original source file
            destination_file_path = f"{environment.hexaind_data}/{action_handler.action_id}/{os.path.basename(dataset_path)}"
            print(f"DATASET PATH IS: {dataset_path}")
            FileUtils.createDeepCopyOfFile(source_file_path=dataset_path, dest_file_path=destination_file_path)

            # initializing the mobo service 
            mobo_config: MOBOConfig = widget.config

            initialize_experiment = True
            if mobo_config.dataset:
                initialize_experiment = False
                
            # Building kwargs for MOBO-service
            kwargs = dict(workflow_id=run_record.workflow_id, 
                          workflow_name=run_record.name,
                          project_id=action_id,
                          training_data_path=destination_file_path,
                          initialize_experiment=initialize_experiment,
                          results_folder=results_folder
                          )
            
            # calling MOBO service class
            mobo_service = MOBOService(db_sync_client=action_handler.db_client)
            mobo_output = mobo_service.run_mobo(mobo_config, **kwargs)

            if mobo_output.exception_detail:
                raise Exception(f"ACTIVE_LEARNING widget raised exception: {mobo_output.exception_detail}")
            
            if mobo_output.terminate:
                raise Exception("ACTIVE_LEARNING widget sends teriminated signal without generating the first batch of recommendations")

            dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(
                input_data=str(mobo_output.tabular_path), project_id=run_record.project_id, site_id=run_record.site_id,
                user_id=run_record.owner_id,
                action_id=action_id, run_id=run_record.id, workflow_id=run_record.workflow_id,
                name=widget.name, description=widget.description, access_mode=AccessMode.INTERNAL,
                metadata=dataset_metadata)
            
            # saving the action results to the collection
            action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))


            # updating mobo states
            mobo_run_state = MOBORunState(source_file_path=destination_file_path, 
                                          master_source_csv_file_path=mobo_service.file_path + ".csv",
                                          master_source_json_file_path=mobo_service.file_path + ".json",
                                          experiment_folder_location=mobo_service.folder_dir) 
            
            mobo_action_run_state = CustomRunState(total_invoke_count=1, custom_state=mobo_run_state.model_dump(), cycle_intermediate_results=[CycleIntermediateResults(invocation_num=1, result_record_ids=[action_result_id])])

            action_handler.update_action_custom_run_state(custom_run_state=mobo_action_run_state) # update the action run state

        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=[action_result_id], append_results=False)
