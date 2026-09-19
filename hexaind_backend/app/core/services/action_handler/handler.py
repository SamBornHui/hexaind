from app.services.workflows.runner.schemas import *
from app.core.schemas.action_result import *
from app.core.services.action.schemas import *
from app.core.services.action.service import ActionService
from app.services.admin.connectors.service import Connector, ConnectorService
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.assets.datasets.schemas import AccessMode
from app.core.dao.action_results.action_results import ActionResultsDao
from app.services.workflows.designer.schemas import InputOutputConfig
from app.core.services.action.dao import ActionsDao
from app.services.workflows.runner.dao import RunDao
from app.core.db.db_utils import get_db_sync
from typing import Tuple, Dict
from pymongo import MongoClient


class ActionHandler:
    
    def __init__(self, id: str):

        self.db_client = get_db_sync()
        self.actions_dao_obj = ActionsDao(db_sync_client=self.db_client)
        self.workflow_runs_dao_obj = RunDao(db_sync_client=self.db_client)
        self.action_service = ActionService(db_sync_client=self.db_client)
        self.action_results_dao = ActionResultsDao(db_sync_client=self.db_client)
        self.datasets_handler = DatasetsService(db_sync_client=self.db_client)

        self.action_id = id
        self.action_record: Action = self.get_updated_action_record()

    def initialize(self) -> Tuple[Action, Run]:
        
        action_record: Action = self.get_action_record()
        
        run_record: Run = self.get_run_record()

        if not self.is_allowed_to_run(run_record):
            raise Exception("RUN state is not START")
        
        return (action_record, run_record)

    def get_updated_action_record(self) -> Action:
        self.action_record = self.actions_dao_obj.get_action_by_id(self.action_id)
        return self.action_record
    
    def update_action_custom_run_state(self, custom_run_state: CustomRunState) -> Action:
        self.action_record = self.actions_dao_obj.update_action_custom_run_state(action_id=self.action_id, custom_run_state=custom_run_state)
        return self.action_record

    def update_run_status(self, status: ActionRunStatus) -> Action:
        self.action_record = self.actions_dao_obj.update_and_get_action_status(self.action_id, status=status)
        return self.action_record

    def create_action_result_record(self, action_result: ActionResult) -> str:
        return self.action_results_dao.create_result(action_result)

    def create_action_result_records(self, action_results: List[ActionResult], outputs: List[InputOutputConfig]) -> List[str]:
        action_result_ids = []
        for action_result, output in zip(action_results, outputs):
            action_result.output_name = output.name
            action_result_id = self.action_results_dao.create_result(action_result)
            action_result_ids.append(action_result_id)
        return action_result_ids

    def get_widget_config(self) -> Widget:
        return self.action_record.action_config

    def get_action_record(self) -> Action:
        return self.action_record
    
    def get_run_record(self) -> Run:

        run_record: Run = self.workflow_runs_dao_obj.get_runs_by_id(self.action_record.run_id)

        if not run_record:
            raise Exception("Run Record not found")
        
        return run_record
    
    def is_allowed_to_run(self, run_record: Run = None) -> bool:

        if run_record is None:
            run_record = self.get_run_record()

        if run_record.run_state != RunState.START:
            return False

        return True
    
    def processed_subactions_update(self, action_id: str, processed_subactions: List=[]):

        result = self.actions_dao_obj.processed_subactions_update(action_id=action_id, processed_subactions=processed_subactions)
        if not result:
            raise Exception("Failed to update the processed subactions in actions collection")

    def action_success_handler(self, action_result_id: str, append_results: bool=True):
        result = self.actions_dao_obj.update_action_status_and_result(self.action_id, ActionRunStatus.SUCCEEDED, action_result_id=action_result_id, append_results=append_results)
        if not result:
            raise Exception("Failed to update the result in action collection")
        return result

    def action_failure_handler(self, action_id, exception_msg, traceback_msg):

        action_result = ActionResult(type=ActionResultType.FAILURE, result=FailureActionResult(error_code="EXCEPTION", error_description=f'Exception: {exception_msg} \n\n Traceback: {traceback_msg}'))
        action_result_id = self.action_results_dao.create_result(action_result)
        result = self.actions_dao_obj.update_action_status_and_result(action_id, ActionRunStatus.FAILED, action_result_id=action_result_id)

    def get_connector(self, connector_id: str) -> Connector:
        
        connector_service = ConnectorService(db_sync_client=self.db_client)

        return connector_service.get_connector_by_id(connector_id=connector_id)
    
    def get_all_inputs_from_prev_action(self) -> Dict[str, List[WidgetResultResponse]]:

        if not self.action_record.depends_on:
            return dict()
        
        result = dict()
        for urn in self.action_record.depends_on:
            result[urn] = self.action_service.get_action_result_by_run_id_and_urn(run_id=self.action_record.run_id, urn=urn)
        
        return result

    def get_widget_inputs_from_prev_actions(self, widget_inputs: List[InputOutputConfig]) -> Dict[str, WidgetResultResponse]:
        run_id = self.action_record.run_id
        res = {
            input.name: next(
                (wres for wres in self.action_service.get_action_result_by_run_id_and_urn(run_id, input.urn)
                    if wres.output_name == input.name), None)
            for input in widget_inputs
        }
        return res
    
    def get_all_inputs_from_prev_action_as_list(self) -> List[List[WidgetResultResponse]]:

        if not self.action_record.depends_on:
            return []
        
        results = []
        for urn in self.action_record.depends_on:
            results.append(self.action_service.get_action_result_by_run_id_and_urn(run_id=self.action_record.run_id, urn=urn))
        
        return results
    
    def update_dataset_record_access_mode(self, dataset_id: str, name: str, description: str, access_mode: AccessMode) -> bool:

        return self.datasets_handler.update_dataset_record_access_mode(dataset_id=dataset_id, name=name, description=description, access_mode=access_mode)
    
    def get_custom_run_state(self) -> CustomRunState:

        if self.action_record.custom_run_state is None:
            return CustomRunState(total_invoke_count=0, custom_state={}, cycle_intermediate_results=[])
        else:
            return self.action_record.custom_run_state
    
    def get_sub_actions_status(self, action_id: str) -> List[ActionRunStatus]:
        """
        To get the status of all sub actions under the current action
        """
        sub_action_status = self.actions_dao_obj.get_sub_actions_status(action_id=action_id)
        return sub_action_status
        

        

