from typing import Optional
import os, traceback
from app.core.db.db_utils import get_db_sync
from app.core.services.action.service import ActionService, ActionRunStatus, Action
from app.services.workflows.runner.schemas import RunSource
from app.services.workflows.runner.service import RunService, RunStatus, Run
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.designer.base_schemas import WidgetType

from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import (
    ACTION_MANAGER_DEFAULT_QUEUE,
    MOBO_ACTION_WORKER_DEFAULT_QUEUE,
    RESCALE_ACTION_WORKER_DEFAULT_QUEUE,
    MOBO_ACTION_WORKER_RK,
    RESCALE_ACTION_WORKER_RK,
    ACTIVE_LEARNING_ACTION_WORKER_DEFAULT_QUEUE,
    ACTIVE_LEARNING_ACTION_WORKER_RK,
    THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE,
    THERMOCALC_ACTION_WORKER_RK,
    AUTOML_ACTION_WORKER_RK,
    AUTOML_ACTION_WORKER_DEFAULT_QUEUE,
    GPR_ACTION_WORKER_DEFAULT_QUEUE,
    GPR_ACTION_WORKER_RK,
    RF_ACTION_WORKER_DEFAULT_QUEUE,
    RF_ACTION_WORKER_RK,
    LINEAR_REGRESSION_ACTION_WORKER_DEFAULT_QUEUE,
    LINEAR_REGRESSION_ACTION_WORKER_RK,
    LGBM_ACTION_WORKER_DEFAULT_QUEUE,
    LGBM_ACTION_WORKER_RK,
    XGB_ACTION_WORKER_DEFAULT_QUEUE,
    XGB_ACTION_WORKER_RK,
    CATBOOST_ACTION_WORKER_DEFAULT_QUEUE,
    CATBOOST_ACTION_WORKER_RK,
    NNFASTAI_ACTION_WORKER_DEFAULT_QUEUE,
    NNFASTAI_ACTION_WORKER_RK,
    KNN_ACTION_WORKER_DEFAULT_QUEUE,
    KNN_ACTION_WORKER_RK,
    EXTRA_TREES_ACTION_WORKER_DEFAULT_QUEUE,
    EXTRA_TREES_ACTION_WORKER_RK,
    NN_TORCH_ACTION_WORKER_DEFAULT_QUEUE,
    NN_TORCH_ACTION_WORKER_RK,
    GPC_ACTION_WORKER_DEFAULT_QUEUE,
    GPC_ACTION_WORKER_RK,
    SVM_ACTION_WORKER_DEFAULT_QUEUE,
    SVM_ACTION_WORKER_RK,
    EVENTS_QUEUE,
    EVENTS_RK,
    PREDICTION_ACTION_WORKER_RK,
    PREDICTION_ACTION_WORKER_DEFAULT_QUEUE, ML_ACTIONS_DEFAULT_QUEUE, ML_ACTIONS_WORKER_RK, ML_ACTIONS_DEFAULT_2_QUEUE,
    ML_ACTIONS_2_WORKER_RK,
    CUSTOM_CODE_ACTION_WORKER_DEFAULT_QUEUE,
    CUSTOM_CODE_ACTION_WORKER_RK,
    MPR_ACTION_WORKER_DEFAULT_QUEUE,
    MPR_ACTION_WORKER_RK
)
from app.services.workflows.scheduling.service import ScheduleService

app = create_celery_app("action_scheduler", default_queue=ACTION_MANAGER_DEFAULT_QUEUE)

# loading the database client
global db_client
db_client = get_db_sync()

def send_task_helper(task_name: str, config: dict, queue_name: str, routing_key: str) -> Optional[str]:

    """
    Function to send a task to a specified queue.

    :param task_name: Name of the task to be executed.
    :param action_urn: The unique resource identifier for the action.
    :param queue_name: The name of the queue to which the task is to be sent.
    :param routing_key: The routing key for the task.
    """
    try:
        if "mobo" in task_name.lower():
            queue_name = MOBO_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = MOBO_ACTION_WORKER_RK

        elif "active_learning" in task_name.lower():
            queue_name = ACTIVE_LEARNING_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = ACTIVE_LEARNING_ACTION_WORKER_RK

        elif "rescale" in task_name.lower():
            queue_name = RESCALE_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = RESCALE_ACTION_WORKER_RK

        elif "thermocalc" in task_name.lower():
            queue_name = THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = THERMOCALC_ACTION_WORKER_RK

        elif "automl" in task_name.lower():
            queue_name = AUTOML_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = AUTOML_ACTION_WORKER_RK

        elif "task_rf" in task_name.lower():
            queue_name = RF_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = RF_ACTION_WORKER_RK

        elif "linear_regression" in task_name.lower():
            queue_name = LINEAR_REGRESSION_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = LINEAR_REGRESSION_ACTION_WORKER_RK

        elif "lgbm" in task_name.lower():
            queue_name = LGBM_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = LGBM_ACTION_WORKER_RK

        elif "gpr" in task_name.lower():
            queue_name = GPR_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = GPR_ACTION_WORKER_RK

        elif "gpc" in task_name.lower():
            queue_name = GPC_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = GPC_ACTION_WORKER_RK

        elif "xgboost" in task_name.lower():
            queue_name = XGB_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = XGB_ACTION_WORKER_RK

        elif "catboost" in task_name.lower():
            queue_name = CATBOOST_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = CATBOOST_ACTION_WORKER_RK

        elif "extra_trees" in task_name.lower():
            queue_name = EXTRA_TREES_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = EXTRA_TREES_ACTION_WORKER_RK

        elif "nn_torch" in task_name.lower():
            queue_name = NN_TORCH_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = NN_TORCH_ACTION_WORKER_RK

        elif "nnfastai" in task_name.lower():
            queue_name = NNFASTAI_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = NNFASTAI_ACTION_WORKER_RK

        elif "kneighbors" in task_name.lower():
            queue_name = KNN_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = KNN_ACTION_WORKER_RK

        elif "svm" in task_name.lower():
            queue_name = SVM_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = SVM_ACTION_WORKER_RK

        elif "schedule_workflows" in task_name.lower():
            queue_name = EVENTS_QUEUE
            routing_key = EVENTS_RK
        
        elif "prediction" in task_name.lower():
            queue_name = PREDICTION_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = PREDICTION_ACTION_WORKER_RK
        
        elif "custom_code" in task_name.lower():
            queue_name = CUSTOM_CODE_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = CUSTOM_CODE_ACTION_WORKER_RK
        
        elif "mpr" in task_name.lower():
            queue_name = MPR_ACTION_WORKER_DEFAULT_QUEUE
            routing_key = MPR_ACTION_WORKER_RK

        # overwrite queue name and rk if aggregation is enabled
        if os.getenv('AGGREGATE_ML_CONTAINERS', 'false') == 'true':
            ml_actions_queue_tasks = ["task_automl",
                                      "task_catboost",
                                      "task_extra_trees",
                                      "task_kneighbors",
                                      "task_lgbm",
                                      "task_linear_regression",
                                      "task_nn_torch",
                                      "task_nnfastai",
                                      "task_rf",
                                      "task_xgboost"]

            if task_name.lower() in ml_actions_queue_tasks:
                queue_name = ML_ACTIONS_DEFAULT_QUEUE
                routing_key = ML_ACTIONS_WORKER_RK
            elif task_name.lower() in ['task_gpr', 'task_gpc', 'task_svm', 'task_prediction',"task_mpr"]:
                queue_name = ML_ACTIONS_DEFAULT_2_QUEUE
                routing_key = ML_ACTIONS_2_WORKER_RK

        task_id = app.send_task(
            task_name, kwargs=config, queue=queue_name, routing_key=routing_key
            )

        action_id = config["action_id"]
        print(
            f"Task {task_name} with Action ID {action_id} sent to queue {queue_name}, config object is: {config}"
        )

        return task_id

    except Exception as e:
        print(
            f"Exception occurred while sending task {task_name} with Action ID {action_id}: ",
            traceback.print_exc(),
        )


def check_and_trigger_dependencies(action: Action) -> bool:
    """
    Logic to check the prev_actions are satisfied for the given current action
    """
    action_service = ActionService(db_sync_client=db_client)

    if not action.depends_on:
        return True

    if action.action_config.type == WidgetType.LOOP_START:
        satisfied = []
        for prev_action_urn in action.depends_on:
            current_action = action_service.get_action_by_urn(
                run_id=action.run_id, urn=prev_action_urn
            )
            if current_action.status == ActionRunStatus.SUCCEEDED:
                satisfied.append(True)
            else:
                satisfied.append(False)
        return True in satisfied

    else:
        for prev_action_urn in action.depends_on:

            current_action = action_service.get_action_by_urn(
                run_id=action.run_id, urn=prev_action_urn
            )

            if current_action.status == ActionRunStatus.SUCCEEDED:
                continue

            elif current_action.status in [
                ActionRunStatus.FAILED,
                ActionRunStatus.PAUSED,
                ActionRunStatus.RUNNING,
                ActionRunStatus.SCHEDULED,
            ]:
                return False

            elif current_action.status == ActionRunStatus.IDLE:
                send_task_helper(
                    "start_action",
                    {"action_id": current_action.id},
                    "start_end",
                    "start",
                )
                return False

    return True


@app.task(name="start_action")
def schedule_action(**kwargs):
    try:
        action_id = kwargs.get("action_id")

        action_service = ActionService(db_sync_client=db_client)
        action: Action = action_service.get_action(action_id=action_id)
        run_service = RunService(db_sync_client=db_client)
        workflow_service = WorkflowDesignerService(db_sync_client=db_client)
        run: Run = run_service.get_run_by_id(action.run_id)

        if action.status != ActionRunStatus.IDLE and action.is_cycle == False:
            raise Exception(
                "Not able to run the action, since the state of the action is not idle."
            )

        # verify any dependencies
        if not check_and_trigger_dependencies(action):
            raise Exception(
                "Action still kept in idle. Since all the dependecies are not resolved"
            )

        if action.is_cycle == True:
            if action.custom_run_state is None:
                expected_status = ActionRunStatus.IDLE
            elif action.custom_run_state.total_invoke_count > 0:
                expected_status = ActionRunStatus.SUCCEEDED
        else:
            expected_status = ActionRunStatus.IDLE

        action_service.update_action_status_atomic(
            action_id=action_id,
            expected_status=expected_status,
            actual_status=ActionRunStatus.SCHEDULED,
        )

        task_name = "task_" + action.action_config.type.value.lower()

        invoked_by_action_id = kwargs.get("invoked_by_action_id", None)

        if invoked_by_action_id:
            task_id = send_task_helper(
                task_name,
                {"action_id": action_id, "invoked_by_action_id": invoked_by_action_id},
                "actions",
                "perform_action",
            )
        else:
            task_id = send_task_helper(
                task_name, {"action_id": action_id}, "actions", "perform_action"
                )
        
        # Assigning the celery task_id to the action, since to stop the task execision we need the celery task_id
        if task_id is not None:
            action_service.update_celery_task_id_in_action_record_sync(
                action_id=action_id,
                celery_task_id=task_id.id
                )

    except Exception as e:
        print("Exception occured: ", traceback.print_exc())


@app.task(name="end_action")
def schedule_next_action(**kwargs):
    try:
        action_id = kwargs.get("action_id")

        run_service = RunService(db_sync_client=db_client)
        action_service = ActionService(db_sync_client=db_client)
        workflow_service = WorkflowDesignerService(db_sync_client=db_client)

        action = action_service.get_action(action_id=action_id)
        run = run_service.get_run_by_id(action.run_id)

        if action.delete_on_complete:
            action_service.update_action_status_atomic(
                action_id=action_id,
                expected_status=action.status,
                actual_status=ActionRunStatus.STOPPED,
            )
            return

        if action.sub_action_config:  # it is a sub-action just skip it
            return

        elif action.status == ActionRunStatus.SUCCEEDED:

            if (
                run.interactive_mode and run.is_single_widget_run
            ):  # For Interactive Single Widget Execution Workflows
                run_service.update_run_status(
                    run_id=action.run_id, status=RunStatus.SUCCEEDED
                )
                return

            #  Fetch next_actions_urn to be scheduled
            if action.action_config.type == WidgetType.LOOP_END:
                if action.custom_run_state.custom_state.get("terminate", True):
                    next_actions_urn = action.action_config.config.on_termination
                else:
                    next_actions_urn = action.action_config.config.on_loop
            else:
                next_actions_urn = action.action_config.on_success

            # Schedule next actions
            for next_action_urn in next_actions_urn:
                # get action id from urn and run_id
                next_action = action_service.get_action_by_urn(
                    run_id=action.run_id, urn=next_action_urn
                )
                if next_action.action_config.type in [
                    WidgetType.LOOP_START,
                    WidgetType.LOOP_END,
                ]:
                    send_task_helper(
                        "start_action",
                        {
                            "action_id": next_action.id,
                            "invoked_by_action_id": action_id,
                        },
                        "start_end",
                        "start",
                    )
                else:
                    send_task_helper(
                        "start_action",
                        {"action_id": next_action.id},
                        "start_end",
                        "start",
                    )

            # Mark the run as SUCCEEDED if the current action is the last widget(end in workflow)
            workflow = workflow_service.get_workflow_by_id(run.workflow_id)
            if workflow.end[0] == action.action_config.urn:
                run_service.update_run_status(
                    run_id=action.run_id, status=RunStatus.SUCCEEDED
                )
                # check if some other wf's need to be scheduled after completing this wf
                #if run.run_source == RunSource.SCHEDULE:
                send_task_helper(
                    "task_schedule_workflows",
                    {
                        "workflow_id": workflow.id,
                        "run_id": action.run_id,
                        "action_id": None,
                    },
                    "events_queue",
                    "start",
                )

        elif action.status == ActionRunStatus.FAILED:
            run_service.update_run_status(run_id=action.run_id, status=RunStatus.FAILED)

    except Exception as e:
        print(
            f"Exception occured in Action Manager while scheduling downstream actions: {traceback.print_exc()}. Current action id is {action_id}"
        )
