from typing import List, Optional, Tuple

from bson import ObjectId

from app.core.dao.dao_base import DaoBase
from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomPythonWidgetRecipe,
)


class CustomPythonWidgetRecipeDao(DaoBase):

    def insert_custom_python_widget_recipe(
        self, custom_python_widget_recipe: CustomPythonWidgetRecipe
    ) -> str:

        # existing_record = self.db_sync.custom_python_widget_recipes.find_one(
        #     {"name": custom_python_widget_recipe.name}
        # )
        existing_record = self.db_sync.custom_python_widget_recipes.find_one(
            {"name": custom_python_widget_recipe.name, 'project_id': custom_python_widget_recipe.project_id}
        )
        # raise error only if an external existing record present.
        if existing_record and existing_record.get('access_mode', '') == 'EXTERNAL':
            raise ValueError(
                f"A recipe with name '{custom_python_widget_recipe.name}' already exists."
            )

        result = self.db_sync.custom_python_widget_recipes.insert_one(
            custom_python_widget_recipe.model_dump(exclude={"id"})
        )
        if not result:
            raise ValueError("not able to create CustomPythonWidgetRecipe record")

        custom_python_widget_recipe_id = str(result.inserted_id)

        return custom_python_widget_recipe_id
    
    async def insert_custom_python_widget_recipe_async(
        self, custom_python_widget_recipe: CustomPythonWidgetRecipe
    ) -> str:

        existing_record = await self.db_async.custom_python_widget_recipes.find_one(
            {"name": custom_python_widget_recipe.name, 'project_id': custom_python_widget_recipe.project_id}
        )
        print("Original: ", existing_record)
        if existing_record:
            raise ValueError(
                f"A recipe with name '{custom_python_widget_recipe.name}' already exists."
            )

        result = await self.db_async.custom_python_widget_recipes.insert_one(
            custom_python_widget_recipe.model_dump(exclude={"id"})
        )
        if not result:
            raise ValueError("not able to create CustomPythonWidgetRecipe record")

        custom_python_widget_recipe_id = str(result.inserted_id)

        return custom_python_widget_recipe_id

    async def update_custom_python_widget_recipe(
        self, custom_python_widget_recipe: CustomPythonWidgetRecipe
    ) -> str:
        result = await self.db_async.custom_python_widget_recipes.update_one(
            {"_id": ObjectId(custom_python_widget_recipe.id)},
            {"$set": custom_python_widget_recipe.model_dump(exclude={"id"})},
        )
        if result.matched_count == 0:
            raise KeyError("No custom python widget recipe is found")
        if result.modified_count == 0:
            raise KeyError("No custom python widget recipe is Modified")
        return custom_python_widget_recipe.id

    async def get_all_custom_python_widget_recipes_async(
        self, project_id: str, search_term: str, page_number: int, page_limit: int, access_mode: Optional[str] = None
    ) -> Tuple[List[CustomPythonWidgetRecipe], int]:

        offset = (page_number - 1) * page_limit
        query = {"project_id": project_id}
        if access_mode:
            query["access_mode"] = access_mode

        if search_term:
            search_query = {
                "$regex": search_term,
                "$options": "i",
            }  # Case-insensitive search
            query["$or"] = [
                {"name": search_query},
                {"description": search_query},
                {"owner_name": search_query},
            ]

        custom_code_widget_recipes_curser = (
            self.db_async.custom_python_widget_recipes.aggregate(
                [
                    {"$match": query},
                    {
                        "$addFields": {
                            "_id": {"$toString": "$_id"},
                            "created_at": {
                                "$dateToString": {
                                    "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                    "date": "$created_at",
                                }
                            },
                            "last_modified_at": {
                                "$dateToString": {
                                    "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                    "date": "$last_modified_at",
                                }
                            },
                        }
                    },
                    {"$skip": offset},
                    {"$limit": page_limit},
                ]
            )
        )

        custom_code_widget_recipes = await custom_code_widget_recipes_curser.to_list(
            length=page_limit
        )
        custom_code_widget_recipes_list = [
            CustomPythonWidgetRecipe(**custom_code_widget_recipe)
            for custom_code_widget_recipe in custom_code_widget_recipes
        ]

        total_count = await self.db_async.custom_python_widget_recipes.count_documents(
            query
        )
        return custom_code_widget_recipes_list, total_count

    async def get_custom_python_widget_recipe_by_id_async(
        self, custom_python_widget_recipe_id: str
    ) -> CustomPythonWidgetRecipe:

        result = await self.db_async.custom_python_widget_recipes.find_one(
            {"_id": ObjectId(custom_python_widget_recipe_id)}
        )
        if not result:
            raise ValueError(
                "unable to fetch the custom python widget recipe at this moment"
            )

        result["_id"] = str(result["_id"])

        return CustomPythonWidgetRecipe(**result)
    

    async def delete_custom_python_widget_recipe_by_id_async(
        self, custom_python_widget_recipe_id: str
    ) -> CustomPythonWidgetRecipe:

        result = await self.db_async.custom_python_widget_recipes.delete_one(
            {"_id": ObjectId(custom_python_widget_recipe_id)}
        )
        if not result:
            raise ValueError(
                "unable to delete the custom python widget recipe at this moment"
            )

        return result.deleted_count > 0
    
    async def get_custom_python_widget_recipes_by_module_ids_async(self, module_ids: List[str],ignore_empty_results:bool=False) -> List[CustomPythonWidgetRecipe]:
        """Get Custom Python Widget Recipes for a list of module ids
        Args:
            module_ids (List[str]): List of module ids
        Returns:
            List[CustomPythonWidgetRecipe]: List of Custom Python Widget Recipe objects
        """
        result = await self.db_async.custom_python_widget_recipes.find(
            {"module_id": {"$in": module_ids}}
        ).to_list(None)
        if not result:
            if ignore_empty_results is False:
                raise ValueError(
                    "unable to fetch the custom python widget recipes at this moment"
                )
        for r in result:
            r["_id"] = str(r["_id"])
        return [CustomPythonWidgetRecipe(**r) for r in result]