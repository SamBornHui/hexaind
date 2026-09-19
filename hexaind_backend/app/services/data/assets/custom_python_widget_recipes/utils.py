from datetime import datetime, timezone

from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomPythonWidgetRecipe,
    CustomPythonWidgetRecipeUpdateRequest,
)


def get_custom_python_widget_recipe(
    cpwr_update_request: CustomPythonWidgetRecipeUpdateRequest,
    site_id: str,
    project_id: str,
    last_modified_by: str = "",
):

    recipe = CustomPythonWidgetRecipe(
        version=cpwr_update_request.version,
        name=cpwr_update_request.name,
        recipe_name=cpwr_update_request.recipe_name,
        description=cpwr_update_request.description,
        reference_links=cpwr_update_request.reference_links,
        tags=cpwr_update_request.tags,
        widget_inputs_rules=cpwr_update_request.widget_inputs_rules,
        widget_outputs_rules=cpwr_update_request.widget_outputs_rules,
        module_id=cpwr_update_request.module_id,
        inputs_map=cpwr_update_request.inputs_map,
        outputs_map=cpwr_update_request.outputs_map,
        settings=cpwr_update_request.settings,
        help_details=cpwr_update_request.help_details,
        project_id=project_id,
        site_id=site_id,
        access_mode=cpwr_update_request.access_mode,
        created_by=cpwr_update_request.created_by,
        created_at=cpwr_update_request.created_at,  # Set the current timestamp for created_at
        last_modified_by=last_modified_by,
        last_modified_at=datetime.now(timezone.utc),  # Set the current timestamp for last_modified_at
    )
    return recipe
