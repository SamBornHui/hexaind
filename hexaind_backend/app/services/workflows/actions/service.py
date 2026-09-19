import asyncio
import logging
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.core.dao.action_results.action_results import ActionResultsDao
from app.core.services.action.schemas import (
    Action,
    ActionResultType,
    ActionRunStatus,
    FailureActionResult,
    StringActionResult,
    Widget,
    WidgetResultResponse,
)
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.workflows.action_results.service import ActionResultsService

from .dao import ActionsDao

logger = logging.getLogger(__package__)


class ActionServiceNew:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        
        self.actions_dao = ActionsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.action_results_dao = ActionResultsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.action_results_service = ActionResultsService(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.datasets_dao = DatasetsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
    
    def get_graph_from_widgets(self, widgets: List[Widget | dict]) -> dict:
        """
        This will return an adjacency matrix from the widgets in the workflow object
        """
        logger.info("inside get_graph_from_widgets function")
        graph = {}
        for widget in widgets:
            if isinstance(widget, Widget):
                urn = widget.urn
                on_success = widget.on_success
            else:
                urn = widget.get('urn')
                on_success = widget.get('on_success')
                
            graph[urn] = on_success
        return graph
    
    def is_valid_action(self, action: Action) -> bool:
        return True
    
    def find_end_widgets_in_a_workflow(self, graph: dict, start: str) -> List:
        """
        This is an workflow util function, implemented to get end(s) for a given workflow.
        If all of these wnd widget(s) executed successfully we will mark the workflow as success
        """
        logger.info("inside find_end_widgets_in_a_workflow function")
        visited = set()
        queue = [start]
        leaves = []

        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                if node not in graph or not graph[node]:  # Check if it is a leaf node
                    leaves.append(node)
                else:
                    queue.extend(graph.get(node, []))

        return leaves
    
    async def create_action_async(self, action: Action) -> str:

        if not self.is_valid_action(action):
            logger.error("Invalid Action")
            raise Exception("Invalid Action")

        return await self.actions_dao.create_action_async(action)
    
    async def get_action_by_action_id_async(self, action_id: str) -> Action:

        return await self.actions_dao.get_action_by_action_id_async(action_id)
    
    async def delete_action_results_async(self, action_record: Action, force_delete: bool = False):
        logger.info("inside delete_action_results_async function")
        action_result_ids = []
        action_result_ids.extend(action_record.result_ids)
        
        if action_record.custom_run_state:
            intermediate_result_record_ids = []
            for intermediate_record in action_record.custom_run_state.cycle_intermediate_results:
                intermediate_result_record_ids.extend(intermediate_record.result_record_ids)
                action_result_ids.extend(intermediate_result_record_ids)
        
        await asyncio.gather(*[self.action_results_service.delete_action_result_by_id_async(result_id=results_id, force_delete=force_delete) for results_id in action_result_ids])

    async def delete_action_record_by_action_id_async(self, action_id: str, force_delete: bool = False) -> bool:
        """
        This function first removes all action_results associated to the given action_id and finally removes the action record.
        """

        # gather and delete all action_results associated to the current action
        logger.info("inside delete_action_record_by_action_id_async function")
        action_record = await self.get_action_by_action_id_async(action_id=action_id)

        self.delete_action_results_async(action_record=action_record, force_delete=force_delete)

        # Deleting action record from the collection
        return await self.actions_dao.delete_action_record_by_action_id_async(action_id=action_id)
    
    async def update_action_config_by_action_id_async(self, action_id: str, new_action_config: Widget):

        return await self.actions_dao.update_action_config_by_action_id_async(action_id=action_id, new_action_config=new_action_config)
    
    async def reset_action_record_by_action_id_async(self, action_id: str, new_action_record: Action=None, force_delete:bool = False) -> bool:
        """
        This function first removes all action_results associated to the given action_id and finally reset the action record.
        """

        # gather and delete all action_results associated to the current action
        logger.info("inside reset_action_record_by_action_id_async function")
        action_record = await self.get_action_by_action_id_async(action_id=action_id)

        # removing all action results
        await self.delete_action_results_async(action_record=action_record, force_delete=force_delete)

        # removing all sub-actions results
        if action_record.sub_action_ids:
            for sub_action_id in action_record.sub_action_ids:
                sub_action_record = await self.get_action_by_action_id_async(action_id=sub_action_id)
                await self.delete_action_results_async(action_record=sub_action_record, force_delete=force_delete)

        if new_action_record:
            # Deleting action record from the collection
            return await self.actions_dao.update_action_record_by_action_id_async(action_id=action_id, action_record=new_action_record)
        else:
            action_record.status = ActionRunStatus.IDLE
            action_record.sub_action_ids = []
            action_record.result_ids = []
            action_record.custom_run_state = None
            action_record.celery_task_id = None


            return await self.actions_dao.update_action_record_by_action_id_async(action_id=action_id, action_record=action_record)

    async def update_action_record_by_action_id_async(self, action_id: str, action_record: Action) -> bool:

        return await self.actions_dao.update_action_record_by_action_id_async(action_id=action_id, action_record=action_record)
    
    async def update_action_record_delete_on_complete_async(self, action_id: str,  delete_on_complete: bool):

        return await self.actions_dao.update_action_record_delete_on_complete_async(action_id=action_id, delete_on_complete=delete_on_complete)
    
    async def update_action_record_status_async(self, action_id: str, status: ActionRunStatus):

        return await self.actions_dao.update_action_record_status_async(action_id=action_id, status=status)
    
    async def get_actions_by_run_id_async(self, run_id: str) -> List[Action]:

        return await self.actions_dao.get_actions_by_run_id_async(run_id)
    
    async def get_action_by_urn_async(self, run_id: str, urn: str) -> Action:

        return await self.actions_dao.get_action_by_urn_async(run_id=run_id, urn=urn)
    
    async def get_action_result_by_run_id_and_urn_async(self, run_id: str, urn: str, output_name: Optional[str] = None) -> List[WidgetResultResponse]:
        logger.info("inside get_action_result_by_run_id_and_urn_async function")
        action_record = await self.actions_dao.get_action_record_by_run_id_and_urn_async(run_id=run_id, urn=urn)

        if action_record.status not in [ActionRunStatus.SUCCEEDED, ActionRunStatus.FAILED]:
            logger.error("Action not yet completed")
            raise Exception("Action not yet completed")

        if not action_record.result_ids:
            logger.error("Action does not have any results")
            raise Exception("Action does not have any results")
        
        if action_record.status == ActionRunStatus.FAILED:
            failure_result_id = action_record.result_ids[0]
            failure_result_record = await self.action_results_dao.get_action_result_by_id_async(result_id=failure_result_id)
            failure_details: FailureActionResult = failure_result_record.result
            result = WidgetResultResponse(result_type=failure_result_record.type, result_value=failure_details)
            return [result]
        
        if isinstance(action_record.result_ids, list):

            action_result_records = await self.action_results_dao.get_action_results_by_ids_async(action_record.result_ids)
            print(f"Action Records: {action_result_records}, IDs: {action_record.result_ids}")
            
            results = []
            for action_result_record in action_result_records:

                if output_name:
                    if action_result_record.output_name != output_name:
                        continue #only get result matched with output name # TODO: OPTIMIZE

                if action_result_record.type in [ActionResultType.DATASET, ActionResultType.MODEL]:
                    dataset = await self.datasets_dao.get_dataset_by_id_async(dataset_id=action_result_record.result.dataset_id)
                    dataset.dataset_information[0].dataset_schema = None
                    dataset.metadata = {}
                    results.append(WidgetResultResponse(result_type=action_result_record.type, result_value=dataset, output_name=action_result_record.output_name))

                elif action_result_record.type in [ActionResultType.VISUALIZATION]:
                    plot_details: StringActionResult = action_result_record.result
                    # plot_data: Visualization = await self.datasets_dao.get_visualization_by_id_async(visualization_id=action_result_record.result.visualization_id)
                    # print(f"Visualization: {plot_data.dataset_location}")
                    results.append(WidgetResultResponse(result_type=action_result_record.type, result_value=plot_details, output_name=action_result_record.output_name))
                
                elif action_result_record.type in [
                        ActionResultType.FAILURE,
                        ActionResultType.STRING,
                        ActionResultType.INTEGER,
                        ActionResultType.FLOAT,
                        ActionResultType.STRINGS_LIST,
                        ActionResultType.INTEGERS_LIST,
                        ActionResultType.FLOATS_LIST,
                        ActionResultType.DICTIONARY,
                        ActionResultType.FILE_OR_FOLDER_PATH,
                    ]:
                    results.append(WidgetResultResponse(result_type=action_result_record.type, result_value=action_result_record.result, output_name=action_result_record.output_name))
                
                # extend with other result data types
                print(f"No of results: {len(results)}")
            return results
        
    async def get_actions_from_list_of_action_ids_async(self, action_ids: List[str]) -> List[Action]:
        """Get actions from list of action ids

        Args:
            action_ids (List[str]): List of action ids

        Returns:
            List[Action]: List of actions
        """
        
        return await self.actions_dao.get_actions_from_list_of_action_ids_async(action_ids)