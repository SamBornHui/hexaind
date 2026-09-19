import itertools
import logging
from typing import Dict, List

from app.core.services.action.schemas import Action, ActionRunStatus
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import Widget

logger = logging.getLogger(__package__)

class ActionUtils:

    def is_valid_action(self, action: Action) -> bool:
        return True
    
    def get_graph_from_widgets(self, widgets: List[Widget | dict]) -> dict:
        """
        This will return an adjacency matrix from the widgets in the workflow object
        """
        logger.info("Inside get_graph_from_widgets function")
        graph = {}
        for action in widgets:
            if isinstance(action, Widget):
                action = action.model_dump()
                # urn = action.urn 
                # on_success = action.on_success
            urn = action.get("urn")
            on_success = action.get('on_success')
            graph[urn] = on_success
        return graph
    
    def get_predecessors_for_every_widget(self, graph: dict) -> dict:
        """
        This function willr return the prev(reverse/predecessors) dependencies for each node
        """
        logger.info("Inside get_predecessors_for_every_widget function")
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
        logger.info("Inside find_cycle_nodes function")
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
    
    def verify_cycle(self, cycle_path_urns: list= [], widgets_dict: Dict[str, Widget|dict]={}) -> bool:
        """
        1. Every loop should have loop start and loop end. 
        2. count of loop start == loop end
        """
        logger.info("Inside verify_cycle function")
        if not cycle_path_urns:
            return True
        
        if cycle_path_urns and not widgets_dict:
            raise Exception("Widgets dictionary not provided to verify cycles")
        
        loop_start_count, loop_end_count = 0, 0
        for widget_urn in cycle_path_urns:
            widget = widgets_dict.get(widget_urn)
            if widget is None:
                continue
            if isinstance(widget, Widget):
                widget = widget.model_dump()
            #     if widget.type == WidgetType.LOOP_START: loop_start_count += 1
            #     elif widget.type == WidgetType.LOOP_END: loop_end_count += 1
            #     else: pass
            # else:
            if widget.get('type') == WidgetType.LOOP_START: loop_start_count += 1
            elif widget.get('type') == WidgetType.LOOP_END: loop_end_count += 1
            else: pass

        if loop_start_count == 0 and loop_end_count == 0:
            logger.error("Loop detected in workflow. Loop did not created using guidelines. Missing loop start and loop end widgets.")
            raise Exception("Loop detected in workflow. Loop did not created using guidelines. Missing loop start and loop end widgets.")
        elif loop_start_count != loop_end_count:
            logger.error("Loop detected in workflow. Loop did not created using guidelines. Loop start and end widgets did not placed properly.")
            raise Exception("Loop detected in workflow. Loop did not created using guidelines. Loop start and end widgets did not placed properly.")
        else:
            return True
        
    def get_widgets_dict_from_widgets_list(self, widgets: List[Widget | dict]) -> dict:
        """
        build workflow dictionary from list widgets
        so that we can access desired widget using it's associated urn quickly
        """
        logger.info("Inside get_widgets_dict_from_widgets_list function")
        # if not widgets: return dict()
        widgets_dict = {widget.urn if isinstance(widget, Widget) else widget.get('urn'): widget for widget in widgets}
        return widgets_dict
    
    def get_actions_from_widgets(self, run_id: str, actions: List[Widget | dict]) -> List[Action]:

        """
        Convert workflow widget objects to backend compatibale action objects
        Every action is be derived from the actions base class. 
        along with widget class variables, action class have few extra backend needed variables.
        """
        logger.info("Inside get_actions_from_widgets function")
        # build widgets dict 
        widgets_dict = self.get_widgets_dict_from_widgets_list(widgets=actions)

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
        
        if create_actions:
            # inserting activities into activity collection
            action_records_list = []
            for action in actions:
                if isinstance(action, Widget):
                    action_record = Action(
                        run_id=run_id,
                        is_cycle=True if action.urn in cyclic_widget_urns else False,
                        depends_on=prev_dependencies.get(action.urn, []),
                        action_config=action,
                        status=ActionRunStatus.IDLE,
                        result_ids=[]
                    )
                else:
                    # action_record = Action(
                    #     run_id=run_id,
                    #     is_cycle=True if action.get('urn') in cyclic_widget_urns else False,
                    #     depends_on=prev_dependencies.get(action.get('urn'), []),
                    #     action_config=action,
                    #     status=ActionRunStatus.IDLE,
                    #     result_ids=[]
                    # )
                    continue
                action_records_list.append(action_record)
        else:
            logger.error("Unable to create run. Detected cylic issues in the workflow. Please verify workflow")
            raise Exception("Unable to create run. Detected cylic issues in the workflow. Please verify workflow")
        
        return action_records_list
