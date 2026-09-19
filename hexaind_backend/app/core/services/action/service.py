from app.core.schemas.action_result import *
from app.core.dao.action_results.action_results import ActionResultsDao
from app.core.services.action.dao import ActionsDao
from app.core.services.action.schemas import WidgetResultResponse
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict
from .schemas import Action, ActionRunStatus
from app.services.workflows.designer.schemas import Widget
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.data.assets.datasets.service import DatasetsDao
from .dao import ActionsDao
import itertools


class ActionService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        
        self.actions_dao = ActionsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.action_results_dao = ActionResultsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.datasets_dao = DatasetsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
    
    def is_valid_action(self, action: Action) -> bool:
        return True
    
    def get_graph_from_widgets(self, widgets: List[Widget]) -> dict:
        """
        This will return an adjacency matrix from the widgets in the workflow object
        """
        graph = {}
        for action in widgets:
            urn = action.urn
            on_success = action.on_success
            graph[urn] = on_success
        return graph
    
    def get_predecessors_for_every_widget(self, graph: dict) -> dict:
        """
        This function willr return the prev(reverse/predecessors) dependencies for each node
        """
        prev_dependencies = {node: [] for node in graph}
        for node, dependencies in graph.items():
            if dependencies:
                for dependency in dependencies:
                    prev_dependencies[dependency].append(node)
        return prev_dependencies
    
    def find_cycle_nodes(self, graph: dict) -> list:
        """
        Returns a list of nodes that 
        are part of a cycle in the graph.
        """

        visited = set()
        rec_stack = []  # Use a list for tracking the recursion path
        cycle_nodes = []

        def dfs(node):
            nonlocal cycle_nodes
            visited.add(node)
            rec_stack.append(node)

            for neighbor in graph.get(node, []):
                if neighbor in rec_stack:
                    # Cycle detected
                    # Add only the nodes from the current node to the cycle's starting point
                    cycle_nodes.append(rec_stack[rec_stack.index(neighbor):])
                elif neighbor not in visited:
                    dfs(neighbor)

            rec_stack.pop() 

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycle_nodes
    
    def verify_cycle(self, cycle_path_urns: list= [], widgets_dict: dict={}) -> bool:
        """
        1. Every loop should have loop start and loop end. 
        2. count of loop start == loop end
        """
        if not cycle_path_urns:
            return True
        
        if cycle_path_urns and not widgets_dict:
            raise Exception("Widgets dictionary not provided to verify cycles")
        
        loop_start_count, loop_end_count = 0, 0
        for widget_urn in cycle_path_urns:
            widget: Widget = widgets_dict.get(widget_urn)
            if widget.type == WidgetType.LOOP_START: loop_start_count += 1
            elif widget.type == WidgetType.LOOP_END: loop_end_count += 1
            else: pass
        if loop_start_count == 0 and loop_end_count == 0:
            raise Exception("Loop detected in workflow. Loop did not created using guidelines. Missing loop start and loop end widgets.")
        elif loop_start_count != loop_end_count:
            raise Exception("Loop detected in workflow. Loop did not created using guidelines. Loop start and end widgets did not placed properly.")
        else:
            return True
        
    def get_widgets_dict_from_widgets_list(self, widgets: List[Widget]) -> dict:
        """
        build workflow dictionary from list widgets
        so that we can access desired widget using it's associated urn quickly
        """
        if not widgets: return dict()
        widgets_dict = {widget.urn: widget for widget in widgets}
        return widgets_dict
    
    def get_actions_from_widgets(self, run_id: str, actions: List[Widget]) -> List[Action]:

        """
        Convert workflow widget objects to backend compatibale action objects
        Every action is be derived from the actions base class. 
        along with widget class variables, action class have few extra backend needed variables.
        """

        # build widgets dict 
        widgets_dict: Dict[str, Widget] = self.get_widgets_dict_from_widgets_list(widgets=actions)

        # Create a dependency graph
        graph = self.get_graph_from_widgets(widgets=actions)

        # Extract prev(reverse) dependencies for each node
        prev_dependencies = self.get_predecessors_for_every_widget(graph=graph)

        # Extract all cylic paths from the graph
        cyclic_paths = self.find_cycle_nodes(graph=graph)

        # verify every cycle 
        create_actions = all(self.verify_cycle(cycle_path_urns=path, widgets_dict=widgets_dict) for path in cyclic_paths)

        # list of all urns which are part of cycles.
        cyclic_widget_urns = list(itertools.chain.from_iterable(cyclic_paths)) # list of lists flattening   

        # filling on_loop and on_termination for loop end widget (lot of TODO clean up required)
        end_widget_urn = ""
        for cyclic_widget_urn in cyclic_widget_urns:
            if widgets_dict[cyclic_widget_urn].type == WidgetType.LOOP_END:
                end_widget_urn = cyclic_widget_urn
                break
            continue

        for action in actions:
            if action.urn == end_widget_urn:
                action.config.on_loop = list(set(action.on_success).intersection(set(cyclic_widget_urns)))
                action.config.on_termination = list(set(action.on_success) - set(cyclic_widget_urns))
                break
        
        if create_actions:
            # inserting activities into activity collection
            action_records_list = []
            for action in actions:
                action_record = Action(
                    run_id=run_id,
                    is_cycle=True if action.urn in cyclic_widget_urns else False,
                    depends_on=prev_dependencies.get(action.urn, []),
                    action_config=action,
                    status=ActionRunStatus.IDLE,
                    result_id=None
                )
                action_records_list.append(action_record)
        else:
            raise Exception("Unable to create run. Detected cylic issues in the workflow. Please verify workflow")
        
        return action_records_list

    async def create_action_async(self, action: Action) -> str:

        if not self.is_valid_action(action):
            raise Exception("Invalid Action")

        return await self.actions_dao.create_action(action)
    
    def create_actions_sync(self, actions: List[Action]) -> List[str]:
        
        return self.actions_dao.create_actions_sync(actions=actions)

    def get_action(self, action_id: str) -> Action:

        return self.actions_dao.get_action_by_id(action_id)
    
    async def get_actions_by_run_id_async(self, run_id: str) -> List[Action]:

        return await self.actions_dao.get_actions_by_run_id_async(run_id)
    
    def get_action_by_urn(self, run_id: str, urn: str) -> Action:

        return self.actions_dao.get_action_by_urn(run_id=run_id, urn=urn)
    
    async def get_action_result_by_run_id_and_urn_async(self, run_id: str, urn: str) -> List[WidgetResultResponse]:

        action_record = await self.actions_dao.get_action_record_by_run_id_and_urn_async(run_id=run_id, urn=urn)

        if action_record.status not in [ActionRunStatus.SUCCEEDED, ActionRunStatus.FAILED]:
            raise Exception("Action not yet completed")

        if not action_record.result_ids:
            raise Exception("Action does not have any results")
        
        if action_record.status == ActionRunStatus.FAILED:
            failure_result_id = action_record.result_ids[0]
            failure_result_record = await self.action_results_dao.get_action_result_by_id_async(result_id=failure_result_id)
            failure_details: FailureActionResult = failure_result_record.result
            result = WidgetResultResponse(result_type=failure_result_record.type, result_value=failure_details)
            return [result]
        
        if isinstance(action_record.result_ids, list):
            action_result_records = await self.action_results_dao.get_action_results_by_ids_async(action_record.result_ids)
            results = []

            for action_result_record in action_result_records:
                if action_result_record.type == ActionResultType.DATASET:
                    dataset = await self.datasets_dao.get_dataset_by_id_async(dataset_id=action_result_record.result.dataset_id)
                    dataset.dataset_information[0].dataset_schema = None
                    dataset.metadata = {}
                    results.append(WidgetResultResponse(result_type=action_result_record.type, result_value=dataset, output_name=action_result_record.output_name))

                elif action_result_record.type in [ActionResultType.VISUALIZATION]:
                    plot_details: StringActionResult = action_result_record.result
                    print(f"action record: {action_result_record}, plot_details: {plot_details}")
                    # plot_data: Visualization = await self.datasets_dao.get_visualization_by_id_async(visualization_id=action_result_record.result.visualization_id)
                    # print(f"Visualization: {plot_data.dataset_location}")
                    results.append(WidgetResultResponse(result_type=action_result_record.type, result_value=plot_details, output_name=action_result_record.output_name))
                
                    print(f"RESULTS: {results}")
                
                # extend with other result data types
                    
            return results
        
    def get_action_results_by_action_record(self, action_record:Action) -> List[WidgetResultResponse]:

        if action_record.status not in [ActionRunStatus.SUCCEEDED, ActionRunStatus.FAILED]:
            raise Exception("Action not yet completed")

        if not action_record.result_ids:
            raise Exception("Action does not have any results")
        
        if action_record.status == ActionRunStatus.FAILED:
            failure_result_id = action_record.result_ids[0]
            failure_result_record = self.action_results_dao.get_action_result_by_id(result_id=failure_result_id)
            failure_details: FailureActionResult = failure_result_record.result
            result = WidgetResultResponse(result_type=failure_result_record.type, result_value=failure_details, output_name=failure_result_record.output_name)
            return [result]
        
        if isinstance(action_record.result_ids, list):
            action_result_records = self.action_results_dao.get_action_results_by_ids(action_record.result_ids)
            results = []

            for action_result_record in action_result_records:

                if action_result_record.type == ActionResultType.DATASET:
                    dataset = self.datasets_dao.get_dataset_by_id(dataset_id=action_result_record.result.dataset_id)
                    results.append(WidgetResultResponse(result_type=action_result_record.type, result_value=dataset, output_name=action_result_record.output_name))
                    
                else:
                    results.append(WidgetResultResponse(result_type=action_result_record.type, result_value=action_result_record.result, output_name=action_result_record.output_name))
                 
            return results
    
    def get_action_result_by_action_id(self, action_id: str) -> List[WidgetResultResponse]:

        action_record: Action = self.actions_dao.get_action_by_id(id=action_id)
        return self.get_action_results_by_action_record(action_record=action_record)

    
    def get_action_result_by_run_id_and_urn(self, run_id: str, urn: str) -> List[WidgetResultResponse]:

        action_record = self.actions_dao.get_action_record_by_run_id_and_urn(run_id=run_id, urn=urn)
        return self.get_action_results_by_action_record(action_record=action_record)

    def update_action_status_atomic(self, action_id: str, expected_status: ActionRunStatus, actual_status: ActionRunStatus):

        return self.actions_dao.update_action_status_atomic(action_id=action_id, expected_status=expected_status, actual_status=actual_status)
    
    def update_celery_task_id_in_action_record_sync(self, action_id: str, celery_task_id: str):
        
        return self.actions_dao.update_celery_task_id_in_action_record_sync(action_id=action_id, celery_task_id=celery_task_id)
    
    def update_sub_actions_sync(self, action_id: str, sub_action_ids: List[str]) -> bool:

        return self.actions_dao.update_sub_actions_sync(action_id=action_id, sub_action_ids=sub_action_ids)
