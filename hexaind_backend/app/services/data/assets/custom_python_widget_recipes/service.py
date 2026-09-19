import logging
from datetime import datetime, timezone
from typing import List, Tuple

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.services.data.assets.custom_python_widget_recipes.dao import (
    CustomPythonWidgetRecipeDao,
)
from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomPythonWidgetRecipe,
    CustomPythonWidgetRecipeUpdateRequest, CustomPythonWidgetRecipeStatus,
)
from app.services.data.assets.custom_python_widget_recipes.utils import (
    get_custom_python_widget_recipe,
)
from app.services.data.assets.custom_python_widgets.dao import CustomPythonWidgetsDao
from app.services.data.assets.modules.schemas import AccessMode

logger = logging.getLogger(__package__)


class CustomPythonWidgetRecipeService:

    def __init__(
            self,
            db_sync_client: MongoClient = None,
            db_async_client: AsyncIOMotorClient = None,  # type: ignore
    ) -> None:

        self.custom_python_widget_dao = CustomPythonWidgetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        logger.info("Initialized Custom Python Widget Dao")

        self.custom_python_widget_recipe_dao = CustomPythonWidgetRecipeDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        logger.info("Initialized Custom Python Widget Recipe Dao")

    async def get_widgets_based_on_recipe_id(self, recipe_id: str):
        return await self.custom_python_widget_dao.get_widgets_with_recipe_id(recipe_id)

    async def update_custom_python_widget_recipe(self, cpwr: CustomPythonWidgetRecipe):
        logger.info("Updating the Custom Python Widget Recipe")
        await self.custom_python_widget_recipe_dao.update_custom_python_widget_recipe(cpwr)

    async def insert_or_update(
            self,
            cpwr_update_request: CustomPythonWidgetRecipeUpdateRequest,
            site_id: str,
            project_id: str,
            user_id: str,
    ):
        logger.info("Inserting or Updating the Custom Python Widget Recipe")

        if cpwr_update_request.id and cpwr_update_request.id != "":
            logger.info("Updating the CP Widget Recipe")
            # update
            recipe = get_custom_python_widget_recipe(
                cpwr_update_request,
                site_id=site_id,
                project_id=project_id,
                last_modified_by=user_id,
            )
            recipe.id = cpwr_update_request.id
            return await self.custom_python_widget_recipe_dao.update_custom_python_widget_recipe(
                recipe
            )

        else:
            logger.info("Inserting the CP Widget Recipe")
            # insert
            cpwr_update_request.created_at = datetime.now(timezone.utc)
            cpwr_update_request.created_by = user_id
            recipe = get_custom_python_widget_recipe(
                cpwr_update_request,
                site_id=site_id,
                project_id=project_id,
                last_modified_by=user_id,
            )
            return (
                self.custom_python_widget_recipe_dao.insert_custom_python_widget_recipe(
                    recipe
                )
            )

    async def fetch_recipes(
            self, project_id, name_prefix, page_limit, page_number, access_mode=None
    ) -> Tuple[List[CustomPythonWidgetRecipe], int]:

        logger.info("Fetching the available recipes")
        return await self.custom_python_widget_recipe_dao.get_all_custom_python_widget_recipes_async(
            project_id=project_id,
            search_term=name_prefix,
            page_number=page_number,
            page_limit=page_limit,
            access_mode=access_mode
        )

    async def get_recipe(
            self, custom_python_widget_recipe_id: str
    ) -> CustomPythonWidgetRecipe:

        logging.info(
            f"Getting recipe based on the provided id {custom_python_widget_recipe_id}"
        )
        return await self.custom_python_widget_recipe_dao.get_custom_python_widget_recipe_by_id_async(
            custom_python_widget_recipe_id
        )

    async def delete_recipe(self, custom_python_widget_recipe_id: str, user_id: str, is_soft_delete: bool = True):
        if not is_soft_delete:
            raise NotImplementedError(f"Hard deleting of recipe is not yet implemented")
        recipe = await  self.get_recipe(custom_python_widget_recipe_id)
        recipe.access_mode = AccessMode.INTERNAL
        recipe.last_modified_by = user_id
        recipe.last_modified_at = datetime.now(timezone.utc)
        await self.custom_python_widget_recipe_dao.update_custom_python_widget_recipe(
            recipe
        )

    async def clone_cpw_recipe(
            self,
            recipe_id: str,
            user_id: str,
            module_id: str,
            recipe_name: str,
    ) -> str:
        existing_recipe = await self.get_recipe(
            custom_python_widget_recipe_id=recipe_id
        )

        existing_recipe.id = None
        existing_recipe.name = recipe_name
        existing_recipe.recipe_name = f"CLONED_{recipe_name}"
        existing_recipe.created_at = datetime.now(timezone.utc)
        existing_recipe.last_modified_at = datetime.now(timezone.utc)
        existing_recipe.created_by = user_id
        existing_recipe.last_modified_by = user_id
        existing_recipe.module_id = module_id
        existing_recipe.access_mode = AccessMode.EXTERNAL
        existing_recipe.recipe_status = CustomPythonWidgetRecipeStatus.DRAFT

        return await self.custom_python_widget_recipe_dao.insert_custom_python_widget_recipe_async(
            existing_recipe
        )

    async def get_custom_python_widget_recipes_by_module_ids_async(self, module_ids: List[str],ignore_empty_results: bool = False) -> List[CustomPythonWidgetRecipe]:
        return await self.custom_python_widget_recipe_dao.get_custom_python_widget_recipes_by_module_ids_async(
            module_ids, ignore_empty_results=ignore_empty_results
        )