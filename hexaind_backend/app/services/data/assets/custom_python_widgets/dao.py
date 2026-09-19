from typing import List, Tuple, Optional

from bson import ObjectId

from app.core.dao.dao_base import DaoBase
from app.services.data.assets.custom_python_widgets.schemas import CustomPythonWidget
from app.services.workflows.designer.schemas import Workflow


class CustomPythonWidgetsDao(DaoBase):

    def insert_custom_python_widget(self, custom_python_widget: CustomPythonWidget) -> str:
        existing_record = self.db_sync.custom_python_widgets.find_one(
            {"name": custom_python_widget.name, "widget_version": custom_python_widget.widget_version, "project_ids": { "$in": custom_python_widget.project_ids  }}
        )
        if existing_record and existing_record.get('access_mode', '') == 'EXTERNAL':
            raise Exception(
                f"A widget with name '{custom_python_widget.name}' and widget_version '{custom_python_widget.widget_version}' already exists."
            )

        result = self.db_sync.custom_python_widgets.insert_one(custom_python_widget.model_dump(exclude={"id"}))
        if not result:
            raise Exception("unable able to create custom python widget record")

        custom_python_widget_id = str(result.inserted_id)

        return custom_python_widget_id

    def dump_to_old(self, custom_python_widget: CustomPythonWidget) -> str:
        return self.db_sync.custom_python_widgets_old.insert_one(custom_python_widget.model_dump(exclude={"id"}))

    async def count_widgets(self, widget_name: str):
        return await self.db_async.custom_python_widgets.count_documents({"name": widget_name})

    async def count_widgets_with_recipe_id(self, recipe_id: str):
        return await self.db_async.custom_python_widgets.count_documents({"recipe_id": recipe_id})

    async def get_widgets_with_recipe_id(self, recipe_id: str) -> List[CustomPythonWidget]:
        custom_python_widgets_cursor = self.db_async.custom_python_widgets.find({'recipe_id': recipe_id})
        custom_python_widgets = []
        async for cpw in custom_python_widgets_cursor:
            cpw['_id'] = str(cpw['_id'])
            custom_python_widgets.append(CustomPythonWidget(**cpw))
        return custom_python_widgets


    async def get_all_custom_python_widgets_async(
        self, project_id: str, search_term: str, page_number: int, page_limit: int, access_mode: Optional[str] = None
    ) -> Tuple[List[CustomPythonWidget], int]:
        offset = (page_number - 1) * page_limit
        query = {"project_ids": {"$in": [project_id]}}
        if access_mode:
            query['access_mode'] = access_mode

        if search_term:
            search_query = {"$regex": search_term, "$options": "i"}  # Case-insensitive search
            query["$or"] = [{"name": search_query}, {"description": search_query}, {"owner_name": search_query}]

        custom_python_widget_cursor = self.db_async.custom_python_widgets.aggregate(
            [
                {"$match": query},
                {
                    "$addFields": {
                        "_id": {"$toString": "$_id"},
                        "published_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S", "date": "$published_at"}},
                    }
                },
                {"$sort": {"name": 1}},
                {"$skip": offset},
                {"$limit": page_limit},
            ]
        )
        custom_python_widgets = await custom_python_widget_cursor.to_list(length=page_limit)
        custom_python_widgets = [CustomPythonWidget(**cpr) for cpr in custom_python_widgets]
        total_count = await self.db_async.custom_python_widgets.count_documents(query)
        return custom_python_widgets, total_count

    async def get_widget_by_id(self, cpr_id: str) -> CustomPythonWidget:
        result = await self.db_async.custom_python_widgets.find_one({"_id": ObjectId(cpr_id)})
        if not result:
            raise Exception("unable to fetch the custom python widget recipe at this moment")
        result["_id"] = str(result["_id"])

        return CustomPythonWidget(**result)

    def get_widget_by_id_sync(self, cpr_id: str) -> CustomPythonWidget:
        result = self.db_sync.custom_python_widgets.find_one({"_id": ObjectId(cpr_id)})
        if not result:
            raise Exception("unable to fetch the custom python widget recipe at this moment")
        result["_id"] = str(result["_id"])

        return CustomPythonWidget(**result)

    async def delete_cpw(self, cpw_id: str):
        result = await self.db_async.custom_python_widgets.delete_one({"_id": ObjectId(cpw_id)})
        if not result:
            raise ValueError("unable to delete the custom python widget at this moment")

        return result.deleted_count > 0

    async def update_cpw(self, cpw_id: str, cpw_dump: CustomPythonWidget) -> bool:
        result = await self.db_async.custom_python_widgets.find_one_and_update(
            {"_id": ObjectId(cpw_id)}, {"$set": cpw_dump.model_dump(exclude=("_id"))}
        )
        if not result:
            raise Exception("Unable to update Custom Python Widget")

        return True
