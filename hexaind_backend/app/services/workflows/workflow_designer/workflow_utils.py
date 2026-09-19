from typing import Dict, List, Set
import json
import logging
from .schemas import WorkflowChanges

logger = logging.getLogger(__package__)

class WorkflowChangeDetector:
    """Detects changes in workflow elements and identifies affected widgets."""
    
    def __init__(self, previous_workflow: Dict, current_workflow: Dict):
        self.previous_workflow = previous_workflow
        self.current_workflow = current_workflow
        self.current_widgets = {w['urn']: w for w in self.current_workflow.get("widgets", [])}
        self.previous_widgets = {w['urn']: w for w in self.previous_workflow.get("widgets", [])}

    def detect_changes(self) -> WorkflowChanges:
        """Detects changes including new and deleted widgets, removed connections, and config changes.

        Returns:
            Dict: Contains detected changes:
                - new_widgets: New widget URNs.
                - removed_connections: Removed connections (widget URN to removed input URNs).
                - deleted_widgets: Deleted widget URNs.
                - config_changed_widgets: Modified widget URNs.
                - affected_widgets: Widgets potentially impacted by changes.
        """
        logger.info("Inside detect_changes function")


        changes = {
            "new_widgets": self.detect_new_widgets(),
            "removed_connections": self.detect_removed_connections(),
            "deleted_widgets": self.detect_deleted_widgets(),
            "config_changed_widgets": self.detect_widget_changes(),
            "affected_widgets": set(),
        }

        # Update affected_widgets based on removed connections, deleted widgets, config changed widgets
        direct_affected_widgets = set()
        direct_affected_widgets.update(changes["removed_connections"].keys(), 
                                       changes["config_changed_widgets"]
                                      )
        changes["affected_widgets"].update(self.find_downstream_widgets(direct_affected_widgets))
        changes["affected_widgets"] = changes["affected_widgets"] - changes["new_widgets"]
        
        return WorkflowChanges(**changes)

    def detect_new_widgets(self) -> Set[str]:
        """Identifies newly added widgets.

        Returns:
            Set[str]: URNs of new widgets.
        """
        logger.info("Inside detect_new_widgets function")
        previous_urns = {w["urn"] for w in self.previous_workflow.get("widgets", [])}
        current_urns = {w["urn"] for w in self.current_workflow.get("widgets", [])}
        return current_urns - previous_urns

    def detect_deleted_widgets(self) -> Set[str]:
        """Detects removed widgets.

        Returns:
            Set[str]: URNs of deleted widgets.
        """
        logger.info("Inside detect_deleted_widgets function")
        previous_urns = {w["urn"] for w in self.previous_workflow.get("widgets", [])}
        current_urns = {w["urn"] for w in self.current_workflow.get("widgets", [])}
        return previous_urns - current_urns

    def detect_removed_connections(self) -> Dict[str, Set[str]]:
        """Identifies removed connections between widgets.

        Returns:
            Dict[str, Set[str]]: Removed connections (widget URN to removed input URNs).
        """
        logger.info("Inside detect_removed_connections function")
        # Construct predecessor mappings for both workflows
        prev_predecessors = self.construct_predecessors(self.previous_workflow)
        curr_predecessors = self.construct_predecessors(self.current_workflow)

        removed_connections = {}
        for widget_urn, curr_preds in curr_predecessors.items():
            prev_preds = prev_predecessors.get(widget_urn, set())
            removed_preds = prev_preds - curr_preds
            if removed_preds:
                removed_connections[widget_urn] = removed_preds

        return removed_connections

    def detect_widget_changes(self) -> Set[str]:
        """Detects changes in widget's input, output, parameters.

        Returns:
            Set[str]: A set of modified config widget URNs
        """

        logger.info("Inside detect_widget_changes function")
        changed_widgets = set()
        
        for urn, current_widget in self.current_widgets.items():
            previous_widget = self.previous_widgets.get(urn)
            if not previous_widget:
                continue  # This widget is new, so its changes are already accounted for

            # Check for changes in config, inputs, and outputs
            if (current_widget.get("config") != previous_widget.get("config") or
                not self.are_lists_of_dicts_equal(current_widget.get("inputs"), previous_widget.get("inputs")) or
                not self.are_lists_of_dicts_equal(current_widget.get("outputs"), previous_widget.get("outputs"))):
                changed_widgets.add(urn)

        return changed_widgets

    def are_lists_of_dicts_equal(self, list1, list2) -> bool:
        """Compares two lists of dictionaries ignoring order."""
        logger.info("Inside are_lists_of_dicts_equal function")
        if len(list1) != len(list2):
            return False

        sorted_list1 = sorted([json.dumps(d, sort_keys=True) for d in list1])
        sorted_list2 = sorted([json.dumps(d, sort_keys=True) for d in list2])
        return sorted_list1 == sorted_list2
        
    def find_downstream_widgets(self, start_widgets: Set[str]) -> Set[str]:
        logger.info("Inside find_downstream_widgets function")
        """Finds all widgets downstream of the given start widgets, indicating potential impact."""
        visited = set()  # Track visited widgets to avoid cycles
        to_visit = list(start_widgets)  # Queue for widgets to visit
    
        while to_visit:
            current_widget = to_visit.pop(0)  # Get the first widget (FIFO for BFS)
            if current_widget not in visited:
                visited.add(current_widget)
                # Get successors (on_success) of the current widget and add them to to_visit
                current_widget_successors = self.get_successors(current_widget)
                to_visit.extend(current_widget_successors)
    
        return visited

    def get_successors(self, widget_urn: str) -> Set[str]:
        logger.info("Inside get_successors function")
        """Returns the set of widgets that are directly downstream of the given widget."""
        successors = set()
        successors.update(self.current_widgets.get(widget_urn, {}).get("on_success", []))
        return successors

    def construct_predecessors(self, workflow: Dict) -> Dict[str, Set[str]]:
        logger.info("Inside construct_predecessors function")
        """Constructs a mapping from widget URNs to their predecessors based on 'on_success' links."""
        predecessors = {widget['urn']: set() for widget in workflow.get('widgets', [])}
        for widget in workflow.get('widgets', []):
            for successor_urn in widget.get('on_success', []):
                predecessors.setdefault(successor_urn, set()).add(widget['urn'])
        return predecessors
