import copy
import json
from pathlib import Path
from typing import Dict, List, Union, Optional
from uuid import uuid4

from app.config.env_vars import environment
from app.services.workflows.designer.schemas import Widget, WidgetConfig_


class WFConfigService:
    def __init__(self):
        self.output_dir = environment.wf_configs_folder
        # self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _dump_widget_dict_config_to_json(self, widget: dict) -> dict:
        widget = copy.deepcopy(widget)

        if widget.get("config"):
            config_file_path =  widget.get("config_file_path", None)
            if not config_file_path:
                config_file_path = self.output_dir / f"{widget['type']}_{widget['urn']}_{uuid4().hex}_config.json"
            
            with open(config_file_path, "w") as file:
                file.write(json.dumps(widget["config"], indent=4))

            widget["config_file_path"] = str(config_file_path)
            widget["config"] = None
            
        return widget

    def dump_config_to_json(self, widget: Union[Widget, dict]) -> Union[Widget, dict]:

        # with open(config_file_path, "w") as file:
        #     json.dump(widget.config.model_dump(mode="json"), file)
        if isinstance(widget, dict):
            return self._dump_widget_dict_config_to_json(widget)
        
        widget = copy.deepcopy(widget)

        if widget.config:
            config_file_path = self.output_dir / f"{widget.type}_{widget.urn}_{uuid4().hex}_config.json"
            if widget.config_file_path:
                config_file_path = Path(widget.config_file_path)
        
            with open(config_file_path, "w") as file:
                file.write(widget.config.model_dump_json(indent=4))

            widget.config_file_path = str(config_file_path)
            widget.config = None  # Clear config after saving

        return widget

    
    def load_widget_from_json(self, widget: Union[Widget, dict]) -> Widget:

        if type(widget) == dict:
            widget = Widget(**widget)

        if widget.config_file_path:
            print(f"Widget config file path: {widget.config_file_path}")
            file_path = Path(widget.config_file_path)

            with open(file_path, "r") as file:
                # config_data = json.load(file)
                widget.config = WidgetConfig_.model_validate_json(file.read()).root
                widget.config_file_path = None

        return widget
    
    
    def update_widget_config_paths(self, widgets: List[Union[Widget, dict]], urn_mappings: Optional[Dict] = None) -> List[Union[Widget, dict]]:
        """
        Copies the content of each widget's JSON configuration file to a new file
        and updates the `config_file_path` in each widget.

        Args:
            widgets (List[Union[Widget, dict]]): List of widget objects or dictionaries.
            urn_mappings (dict): Mapping of old URNs to new URNs.

        Returns:
            List[Union[Widget, dict]]: Updated widgets with new `config_file_path`.
        """
        def get_attr(widget, attr_name):
            """Helper function to get attribute from widget."""
            if isinstance(widget, dict):
                return widget.get(attr_name)
            else:
                return getattr(widget, attr_name, None)

        def set_attr(widget, attr_name, value):
            """Helper function to set attribute on widget."""
            if isinstance(widget, dict):
                widget[attr_name] = value
            else:
                setattr(widget, attr_name, value)

        # urn mappings is a dictionary of old URNs to new URNs
        # it is passed during workflow duplication and can be used to get the old widget's config file path.
        if not urn_mappings:
            urn_mappings = {}

        new_directory = Path(self.output_dir)
        for widget in widgets:
            urn = get_attr(widget, 'urn')
            widget_type = get_attr(widget, 'type')
            
            config_file_path = get_attr(widget, 'config_file_path')

            if config_file_path:
                old_urn = urn_mappings.get(urn, urn)
                config_file_path = config_file_path.replace(urn, old_urn) # Update URN in config file path to get old file path
                old_file_path = Path(config_file_path)
                if not old_file_path.exists():
                    raise FileNotFoundError(f"Config file {old_file_path} does not exist.")

                # Read the existing config data
                with open(old_file_path, "r") as file:
                    config_data = json.load(file)

                new_file_name = f"{widget_type}_{urn}_{uuid4().hex}_config.json"
                new_file_path = new_directory / new_file_name

                # Write config data to the new file
                with open(new_file_path, "w") as new_file:
                    json.dump(config_data, new_file, indent=4)

                # Update the widget's config_file_path
                set_attr(widget, 'config_file_path', str(new_file_path))   
            else:
                widget = self.dump_config_to_json(widget)

        return widgets
