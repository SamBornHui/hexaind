import ast
import logging
import shutil
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.actions import Actions
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import get_db_async, get_db_sync
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.access_controls.user_projects.service import (
    UsersProjectsMappingsService,
)
from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CPWRCloneRequest,
    CPWRCloneResponse,
    CPWUsedInAssetNames,
    CustomPythonWidgetGetDetailsRequest,
    CustomPythonWidgetRecipe,
    CustomPythonWidgetRecipePublishRequest,
    CustomPythonWidgetRecipePublishResponse,
    CustomPythonWidgetRecipesResponse,
    CustomPythonWidgetRecipeStatus,
    CustomPythonWidgetRecipeUpdateRequest,
    CustomPythonWidgetRecipeUpdateResponse,
    CustomPythonWidgetRecipeValidationResponse,
    CustomPythonWidgetRecipeViewDetails,
    CustomPythonWidgetUsage,
    CustomPythonWidgetUsages,
)
from app.services.data.assets.custom_python_widget_recipes.service import (
    CustomPythonWidgetRecipeService,
)
from app.services.data.assets.custom_python_widget_recipes.utils import (
    get_custom_python_widget_recipe,
)
from app.services.data.assets.custom_python_widgets.helper import (
    CustomPythonWidgetServiceHelper,
)
from app.services.data.assets.custom_python_widgets.schemas import (
    CPWGenericResponse,
    CPWUpdateRequest,
    CustomPythonWidget,
    CustomPythonWidgetsResponse,
    CPWFileUpdateResponse,
    CodeRequest,
    LintError,
)
from app.services.data.assets.custom_python_widgets.service import (
    CustomPythonWidgetService,
)
from app.services.data.assets.modules.schemas import AccessMode
from app.services.data.assets.modules.service import ModuleService

logger = logging.getLogger(__package__)

custom_python_router = APIRouter(
    tags=["Custom Python Widget Recipe"], route_class=CheckNameRoute
)


class CustomPythonRouter:
    def __init__(self):
        """class initialization"""
        pass

    @staticmethod
    @custom_python_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_python_widget_recipe/update_or_insert",
        response_model=CustomPythonWidgetRecipeUpdateResponse,
        openapi_extra={"actions": Actions.Create_CPW.value},
    )
    async def save_custom_python_widget_recipe(
        siteId: str,
        projectId: str,
        custom_python_widget_recipe_update_request: CustomPythonWidgetRecipeUpdateRequest,
        sync_client: MongoClient = Depends(get_db_sync),
        async_client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
        token: str = "",
    ) -> CustomPythonWidgetRecipeUpdateResponse:
        try:
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_sync_client=sync_client, db_async_client=async_client
            )

            user = decodeJWT(token=token)
            try:
                result = await custom_python_widget_recipe_service.insert_or_update(
                    custom_python_widget_recipe_update_request,
                    site_id=siteId,
                    project_id=projectId,
                    user_id=user["user_id"],
                )
                return CustomPythonWidgetRecipeUpdateResponse(
                    succeeded=True,
                    custom_python_widget_recipe_id=result,
                    message="Successfully saved custom python recipe",
                )
            except Exception as e:
                return CustomPythonWidgetRecipeUpdateResponse(
                    succeeded=False,
                    custom_python_widget_recipe_id=None,
                    message=f"Unable to insert/update data : {e}",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_python_widget_recipes",
        response_model=CustomPythonWidgetRecipesResponse,
    )
    async def fetch_custom_python_widget_recipes(
        siteId: str,
        projectId: str,
        search_term: str = Query(default=None),
        page_limit: int = Query(default=100),
        page_number: int = Query(default=1),
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CustomPythonWidgetRecipesResponse:
        try:
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_async_client=client
            )
            try:
                (
                    results,
                    count,
                ) = await custom_python_widget_recipe_service.fetch_recipes(
                    project_id=projectId,
                    name_prefix=search_term,
                    page_limit=page_limit,
                    page_number=page_number,
                    access_mode=AccessMode.EXTERNAL,
                )

                # fetch user names
                fetched_user_ids = []
                for result in results:
                    fetched_user_ids.append(result.created_by)
                    fetched_user_ids.append(result.last_modified_by)
                user_access_controls_service = UsersProjectsMappingsService(
                    db_async_client=client
                )
                users_dict = await user_access_controls_service.get_users_dict(
                    fetched_user_ids
                )
                users_names_dict = {key: users_dict[key].name for key in users_dict}
                final_results = [
                    CustomPythonWidgetRecipeViewDetails(
                        **result.model_dump(by_alias=True),
                        created_by_name=users_names_dict.get(
                            result.created_by, "Not Found"
                        ),
                        last_modified_by_name=users_names_dict.get(
                            result.last_modified_by, "Not Found"
                        ),
                    )
                    for result in results
                ]

                return CustomPythonWidgetRecipesResponse(
                    succeeded=True,
                    results=final_results,
                    count=count,
                    message="Successfully Fetched",
                )
            except Exception as e:
                return CustomPythonWidgetRecipesResponse(
                    succeeded=False,
                    message=f"Unable to fetch custom python widget recipes : {e}",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_python_widget_recipe/get",
        response_model=CustomPythonWidgetRecipe,
    )
    async def fetch_custom_python_widget_recipe(
        siteId: str,
        projectId: str,
        custom_python_widget_recipe_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CustomPythonWidgetRecipe:
        try:
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_async_client=client
            )
            results = await custom_python_widget_recipe_service.get_recipe(
                custom_python_widget_recipe_id
            )
            return results

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_python_widget_recipe/get_widget_details",
        response_model=List[CustomPythonWidgetUsages],
    )
    async def get_widget_details(
        siteId: str,
        projectId: str,
        request: CustomPythonWidgetGetDetailsRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> List[CustomPythonWidgetUsages]:
        try:
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_async_client=client
            )
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            if request.widget_id is None:
                widgets = await custom_python_widget_recipe_service.get_widgets_based_on_recipe_id(
                    request.recipe_id
                )
                widget_ids_map = {widget.id: widget for widget in widgets}
            else:
                widget_ids_map = {
                    request.widget_id: await custom_python_widget_service.get_widget_by_id(
                        request.widget_id
                    )
                }

            all_usages = []
            for widget_id in widget_ids_map:
                usages = []
                widget = widget_ids_map[widget_id]
                workflows = (
                    await custom_python_widget_service.get_workflows_with_widget(
                        widget_id=widget_id
                    )
                )
                for wf in workflows:
                    # TODO: Check if deleted wf's need to be removed.
                    usages.append(
                        CustomPythonWidgetUsage(
                            name=wf.name,
                            id=wf.id,
                            type=CPWUsedInAssetNames.WORKFLOW,
                            version=wf.workflow_version,
                        )
                    )
                    wf_schedules = (
                        await custom_python_widget_service.get_schedules_with_workflows(
                            workflow_id=wf.id
                        )
                    )
                    for wf_schedule in wf_schedules:
                        usages.append(
                            CustomPythonWidgetUsage(
                                name=wf_schedule.name,
                                id=wf_schedule.dag_id,
                                type=CPWUsedInAssetNames.SCHEDULE,
                                status=str(wf_schedule.is_active),
                            )
                        )
                all_usages.append(
                    CustomPythonWidgetUsages(
                        widget_id=widget.id,
                        widget_name=widget.name,
                        widget_version=widget.widget_version,
                        widget_usage_response=usages,
                    )
                )

            return all_usages
        except Exception as e:
            logger.exception(f"failed with exception : {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_python_widget_recipe/preview",
        response_model=CustomPythonWidget,
    )
    async def preview_recipe(
        siteId: str,
        projectId: str,
        custom_python_widget_recipe_update_request: CustomPythonWidgetRecipeUpdateRequest,
        sync_client: MongoClient = Depends(get_db_sync),
        async_client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
        token: str = "",
    ) -> CustomPythonWidget:
        try:
            decoded_token = decodeJWT(token=token)
            custom_python_widget_service_helper = CustomPythonWidgetServiceHelper(
                db_sync_client=sync_client, db_async_client=async_client
            )

            logger.info("inside preview custom python widget")
            # TODO: get last modified by from token instead of keeping as empty
            recipe = get_custom_python_widget_recipe(
                custom_python_widget_recipe_update_request,
                siteId,
                projectId,
                decoded_token.get("user_id", ""),
            )
            logger.info("converted recipe to widget", recipe)
            recipe.id = ""
            dataset_kwargs = {
                "user_id": decoded_token.get("user_id", ""),
                "project_id": projectId,
                "site_id": siteId,
            }
            logger.info("calling convert_recipe_to_widget")
            widget = custom_python_widget_service_helper.convert_recipe_to_widget(
                recipe, widget_version="v0", dataset_kwargs=dataset_kwargs, dry_run=True
            )
            logger.info("converted recipe to widget", widget)
            return widget

        except Exception as e:
            logger.exception(f"failed with exception : {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.put(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/file/{widget_id}",
        status_code=status.HTTP_200_OK,
    )
    async def put_file(
        widget_id: str,
        body: str = Body(..., media_type="text/plain"),
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ):
        """
        PUT API to update a file in the module corresponding to the widget_id.
        """
        try:
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            module_service = ModuleService(db_async_client=client)

            # Retrieve widget and module details
            widget = await custom_python_widget_service.get_widget_by_id(widget_id)
            module = await module_service.get_module_record_by_id_async(
                widget.config.module_id
            )

            # Use a safe and isolated temporary directory
            temp_dir = Path(f"/tmp/{uuid.uuid4()}")  # Unique temp directory per request
            temp_dir.mkdir(parents=True, exist_ok=True)

            try:
                temp_file_path = temp_dir / "temp_file.py"
                with open(temp_file_path, "w", encoding="utf-8") as file:
                    file.write(body)

                # Extract new metadata
                new_metadata = ModuleService.get_metadata(
                    str(temp_file_path), "hexaind_custom_widget_function"
                )

                # Validate function signature
                if (
                    module.metadata
                    and new_metadata.function_signature
                    != module.metadata.function_signature
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Expected function signature {module.metadata.function_signature} but got {new_metadata.function_signature}",
                    )

                # Write the updated content to the module's file
                with open(module.module_location.path, "w", encoding="utf-8") as file:
                    file.write(body)

                return {"message": f"File in module {widget_id} updated successfully."}
            finally:
                # Clean up the temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update file: {str(e)}",
            )
    @staticmethod
    @custom_python_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/file/update/{widget_id}",
        status_code=status.HTTP_200_OK,
    )
    async def update_widget_module(
        widget_id: str,
        config: CPWFileUpdateResponse,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ):
        """
        PUT API to update a file in the module corresponding to the widget_id.
        """
        try:
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            module_service = ModuleService(db_async_client=client)

            # Retrieve widget and module details
            widget = await custom_python_widget_service.get_widget_by_id(widget_id)
            module = await module_service.get_module_record_by_id_async(
                widget.config.module_id
            )

            module.module_location.path = config.filepath
            result = await module_service.update_module_async(
                module_id=module.id, module=module
            )

            return result

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update file: {str(e)}",
            )

    @staticmethod
    @custom_python_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/file/{widget_id}",
        status_code=status.HTTP_200_OK,
    )
    async def get_file(
        widget_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ):
        """
        GET API to retrieve the file content associated with a widget_id.
        """
        try:
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            module_service = ModuleService(db_async_client=client)

            # Retrieve widget and module details
            widget = await custom_python_widget_service.get_widget_by_id(widget_id)
            module = await module_service.get_module_record_by_id_async(
                widget.config.module_id
            )

            # Read the content of the file
            file_path = module.module_location.path
            # if not file_path.endswith(".py"):
            #     raise ValueError(f"only implemented for py files {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
            except FileNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File for module {widget_id} not found.",
                )

            return {"widget_id": widget_id, "file_content": content}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve file: {str(e)}",
            )

    @staticmethod
    @custom_python_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_python_widget_recipe/validate",
        response_model=CustomPythonWidgetRecipeValidationResponse,
    )
    async def validate_and_get_details(
        siteId: str,
        projectId: str,
        custom_python_widget_recipe_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CustomPythonWidgetRecipeValidationResponse:
        try:
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_async_client=client
            )
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            custom_python_recipe = await custom_python_widget_recipe_service.get_recipe(
                custom_python_widget_recipe_id
            )
            try:
                # validation
                await custom_python_widget_service.validate_widget_recipe(
                    custom_python_recipe, "", projectId, siteId
                )
            except Exception as e:
                logger.exception(
                    f"Widget validation failed as draft cannot be converted to widget: due to {e}"
                )
                raise ValueError(
                    f"Widget validation failed as draft cannot be converted to widget: due to {e}"
                )

            message = (
                f"Widget validation is success with name {custom_python_recipe.name}"
            )

            # get widgets
            widgets = await custom_python_widget_recipe_service.get_widgets_based_on_recipe_id(
                custom_python_widget_recipe_id
            )

            response = CustomPythonWidgetRecipeValidationResponse(
                succeeded=True, validation_status=True, validation_message=message
            )

            all_usages = []
            if widgets:
                for widget in widgets:
                    usages = []
                    workflows = (
                        await custom_python_widget_service.get_workflows_with_widget(
                            widget_id=widget.id
                        )
                    )
                    for wf in workflows:
                        # TODO: Check if deleted wf's need to be removed.
                        usages.append(
                            CustomPythonWidgetUsage(
                                name=wf.name,
                                id=wf.id,
                                type=CPWUsedInAssetNames.WORKFLOW,
                                version=wf.workflow_version,
                            )
                        )
                        wf_schedules = await custom_python_widget_service.get_schedules_with_workflows(
                            workflow_id=wf.id
                        )
                        for wf_schedule in wf_schedules:
                            usages.append(
                                CustomPythonWidgetUsage(
                                    name=wf_schedule.name,
                                    id=wf_schedule.id,
                                    type=CPWUsedInAssetNames.SCHEDULE,
                                    status=wf_schedule.is_active,
                                )
                            )
                    all_usages.append(
                        CustomPythonWidgetUsages(
                            widget_id=widget.id,
                            widget_name=widget.name,
                            widget_version=widget.widget_version,
                            widget_usage_response=usages,
                        )
                    )
            response.widget_details = all_usages
            return response
        except ValueError as e:
            return CustomPythonWidgetRecipeValidationResponse(
                succeeded=True, validation_status=False, validation_message=f"{e}"
            )
        except Exception as e:
            logger.exception(f"failed with exception : {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_code_widget/get",
        response_model=CustomPythonWidget,
    )
    async def fetch_custom_python_widget(
        siteId: str,
        projectId: str,
        widget_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CustomPythonWidget:
        try:
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            results = await custom_python_widget_service.get_widget_by_id(widget_id)
            return results
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_code_widget/fetch_all",
        response_model=CustomPythonWidgetsResponse,
    )
    async def fetch_custom_python_widgets(
        siteId: str,
        projectId: str,
        search_term: str = Query(default=None),
        page_limit: int = Query(default=100),
        page_number: int = Query(default=1),
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CustomPythonWidgetsResponse:
        try:
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            try:
                (
                    results,
                    count,
                ) = await custom_python_widget_service.get_all_widgets_async(
                    project_id=projectId,
                    search_term=search_term,
                    page_limit=page_limit,
                    page_number=page_number,
                    access_mode=AccessMode.EXTERNAL,
                )

                return CustomPythonWidgetsResponse(
                    succeeded=True, results=results, count=count, message=""
                )
            except Exception as e:
                return CustomPythonWidgetsResponse(
                    succeeded=False,
                    message=f"Unable to fetch custom python widget recipes : {e}",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_code_widget/publish",
        response_model=CustomPythonWidgetRecipePublishResponse,
    )
    async def publish_custom_code_recipe(
        siteId: str,
        projectId: str,
        publish_request: CustomPythonWidgetRecipePublishRequest,
        token: str = "",
        sync_client: MongoClient = Depends(get_db_sync),
        async_client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> CustomPythonWidgetRecipePublishResponse:
        try:
            custom_python_widget_recipe_id = (
                publish_request.custom_python_widget_recipe_id
            )
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_sync_client=sync_client, db_async_client=async_client
            )
            custom_python_widget_service = CustomPythonWidgetService(
                db_sync_client=sync_client, db_async_client=async_client
            )

            user = decodeJWT(token=token)

            try:
                custom_python_recipe = (
                    await custom_python_widget_recipe_service.get_recipe(
                        custom_python_widget_recipe_id
                    )
                )

                result = await custom_python_widget_service.publish_as_widget(
                    custom_python_widget_recipe=custom_python_recipe,
                    project_id=projectId,
                    site_id=siteId,
                    user_id=user["user_id"],
                    widget_id=publish_request.custom_python_widget_id,
                    widget_version=publish_request.widget_version,
                )

                # update recipe to published
                custom_python_recipe.recipe_status = (
                    CustomPythonWidgetRecipeStatus.PUBLISHED
                )
                custom_python_recipe.last_modified_by = user["user_id"]
                custom_python_recipe.last_modified_at = datetime.now(timezone.utc)
                await custom_python_widget_recipe_service.update_custom_python_widget_recipe(
                    custom_python_recipe
                )

                return CustomPythonWidgetRecipePublishResponse(
                    succeeded=True,
                    custom_python_widget_id=result,
                    message="Successfully saved custom python recipe",
                )
            except Exception as e:
                return CustomPythonWidgetRecipePublishResponse(
                    succeeded=False,
                    custom_python_widget_id=None,
                    message=f"Unable to insert/update data : {e}",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.delete(
        "/v1/sites/{site_id}/projects/{project_id}/custom_python/custom_code_widget/delete/{recipe_id}",
        response_model=CPWGenericResponse,
    )
    async def delete_custom_python_widgets_and_recipes(
        site_id: str,
        project_id: str,
        recipe_id: str,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> CPWGenericResponse:
        try:
            logger.info("inside delete custom python widget")
            decoded_token = decodeJWT(token=token)
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_async_client=client
            )
            # TODO: use token in cpw to have user id
            # removes recipe
            await custom_python_widget_recipe_service.delete_recipe(
                custom_python_widget_recipe_id=recipe_id,
                user_id=decoded_token.get("user_id"),
                is_soft_delete=True,
            )
            logger.info(f"deleted custom python recipe with recipe {recipe_id}")

            # remove widgets if they exist
            widgets = await custom_python_widget_recipe_service.get_widgets_based_on_recipe_id(
                recipe_id
            )
            for widget in widgets:
                widget_id = widget.id
                await custom_python_widget_service.delete_custom_python_widgets(
                    widget_id=widget_id,
                    user_id=decoded_token.get("user_id"),
                    soft_delete=True,
                )

            return CPWGenericResponse(
                success=True, message="Deleted custom widget successfully."
            )

        except Exception as e:
            logger.exception(f"Failed to delete CPW: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/custom_python/custom_code_widget/update}",
        response_model=CPWGenericResponse,
        openapi_extra={"actions": Actions.Update_CPW.value},
    )
    async def update_custom_python_widget(
        site_id: str,
        project_id: str,
        cpw_info: CPWUpdateRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CPWGenericResponse:
        try:
            logger.info("inside update custom python widget")
            custom_python_widget_service = CustomPythonWidgetService(
                db_async_client=client
            )

            user = decodeJWT(token=token)

            result = custom_python_widget_service.update_cpw_async(
                user_id=user["user_id"],
                cpw_id=cpw_info.cpw_id,
                cpw_dump=cpw_info.cpw_data,
            )
            logger.info("update custom python widget and returning the response.")
            return CPWGenericResponse(
                success=result, message="Updated the Custom Python Widget succesfully."
            )

        except Exception as e:
            logger.exception(f"Failed to update CPW: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @custom_python_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/custom_python/custom_python_widget_recipe/clone",
        response_model=CPWRCloneResponse,
    )
    async def clone_custom_python_recipe(
        site_id: str,
        project_id: str,
        request: CPWRCloneRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CPWRCloneResponse:
        try:
            module_service = ModuleService(db_async_client=client)
            custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
                db_async_client=client
            )
            user = decodeJWT(token=token)

            existing_cpwr_record = await custom_python_widget_recipe_service.get_recipe(
                custom_python_widget_recipe_id=request.recipe_id
            )
            module_id = await module_service.create_module_clone(
                module_id=existing_cpwr_record.module_id, user_id=user["user_id"]
            )
            clone_id = await custom_python_widget_recipe_service.clone_cpw_recipe(
                recipe_id=request.recipe_id,
                user_id=user["user_id"],
                module_id=module_id,
                recipe_name=request.recipe_name,
            )
            recipe_details = await custom_python_widget_recipe_service.get_recipe(
                custom_python_widget_recipe_id=clone_id
            )
            module_details = await module_service.get_module_record_by_id_async(
                recipe_details.module_id
            )

            return CPWRCloneResponse(
                clone_id=clone_id,
                message="Custom Python Recipe cloned successfully",
                module_details=module_details,
                recipe_details=recipe_details,
            )
        except Exception as e:
            logger.exception(f"Failed to clone CPW: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )
        
    @custom_python_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/custom_python/lint"
    )
    async def lint_code(request: CodeRequest) :
        code = request.code
        errors = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            # errors.append({"line": e.lineno or 1, "message": e.msg})
            errors.append(LintError(line=e.lineno or 1, message=e.msg))
        
        return errors


custom_python_router_obj = CustomPythonRouter()
