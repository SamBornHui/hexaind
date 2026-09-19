from uuid import uuid4

from app.services.data.assets.modules.helper import ConversionHelper, ComparisonHelper
from app.services.data.assets.modules.schemas import *
from app.services.data.assets.modules.utils import (
    get_custom_code_metadata,
    run_custom_code,
    change_working_directory,
    sys_path_append,
    extract_zip_in_new_location,
    get_function_to_call,
    convert_custom_code_results_to_list,
    find_files_in_zip,
    redirect_print_to_file,
    updated_environ,
)
from app.services.data.assets.modules.dao import ModulesDao
from app.utils.file_utils import FileUtils
from pymongo import MongoClient
from asgi_correlation_id import correlation_id
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple
from datetime import datetime, timezone
import os
import logging

from app.config.env_vars import environment

# HEXAIND_DATA = os.environ.get("HEXAIND_DATA", "/tmp/")

CUSTOM_CODE_FUNCTION_NAME = os.environ.get(
    "CUSTOM_CODE_FUNCTION_NAME", "hexaind_custom_widget_function"
)

logger = logging.getLogger(__package__)


class ModuleService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:
        logger.info("Initializing the Modules Dao")

        self.modules_dao = ModulesDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def get_all_modules_async(
        self,
        projectId: str,
        search_term: str,
        page_number: int,
        page_limit: int,
        access_mode: AccessMode,
    ) -> Tuple[List[Module], int]:
        logger.info(
            f"Getting modules from page number {page_number} with page limit {page_limit}"
        )

        return await self.modules_dao.get_all_modules_async(
            projectId=projectId,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
            access_mode=access_mode,
        )
    
    async def update_module_async(self, module_id: str, module: Module) -> Module:
        logger.info(f"Updating module with module id: {module_id}")
        return await self.modules_dao.update_module_record_async(module_id=module_id, module=module)

    async def save_python_module_helper_async(
        self,
        module_path: str,
        project_id: str,
        user_id: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        created_by: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.EXTERNAL,
        custom_code_metadata: CustomCodeMetadata = None,
    ):
        logger.info(f"Received payload to save python module")

        module = Module(
            user_id=user_id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            run_id=run_id,
            workflow_id=workflow_id,
            name=name,
            description=description,
            module_type=ModuleType.PYTHON,
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata=custom_code_metadata,
            created_at=datetime.now(timezone.utc),
            module_location=ModuleService.get_file_info(module_path, user_id),
            access_mode=access_mode,
            tags=tags,
            created_by=created_by,
        )
        logger.info("designed the module object to be inserted..")
        logger.info("inserting the module record to the db.")

        return await self.modules_dao.insert_module_record_async(module=module)
    
    def save_python_module_helper_sync(
        self,
        module_path: str,
        project_id: str,
        user_id: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        created_by: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.EXTERNAL,
        custom_code_metadata: CustomCodeMetadata = None,
    ):
        logger.info(f"Received payload to save python module")

        module = Module(
            user_id=user_id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            run_id=run_id,
            workflow_id=workflow_id,
            name=name,
            description=description,
            module_type=ModuleType.PYTHON,
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata=custom_code_metadata,
            created_at=datetime.now(timezone.utc),
            module_location=ModuleService.get_file_info(module_path, user_id),
            access_mode=access_mode,
            tags=tags,
            created_by=created_by,
        )
        logger.info("designed the module object to be inserted..")
        logger.info("inserting the module record to the db.")

        return self.modules_dao.insert_module_record_sync(module=module)

    def get_module_record_by_id(self, module_id: str) -> Module:
        logger.info(f"getting specific module with given id {module_id}")

        return self.modules_dao.get_module_record_by_id(module_id=module_id)

    async def get_module_record_by_id_async(self, module_id: str) -> Module:
        logger.info(f"getting specific module with given id {module_id}")
        return await self.modules_dao.get_module_record_by_id_async(module_id=module_id)

    @staticmethod
    def get_files_in_zip(file_path: str) -> List[str]:
        path_ = Path(file_path)
        logger.info(f"Extracting files from zip from the path {path_}")
        if not file_path.endswith(".zip"):
            logger.error(f"given {path_.name} is not a zip file")
            raise ValueError(f"given {path_.name} is not a zip file")

        if not path_.exists():
            logger.error(f"given {path_.name} doesn't exist")
            raise ValueError(f"given {path_.name} doesn't exist")
        return find_files_in_zip(path_)

    @staticmethod
    def get_metadata(
        module_location: str,
        function_name=CUSTOM_CODE_FUNCTION_NAME,
        correlation_id_val=None,
    ) -> CustomCodeMetadata:
        correlation_id.set(correlation_id_val)
        metadata = get_custom_code_metadata(
            module_location, function_name=function_name
        )
        logger.info("Retrieved METADATA of the provided custom code zip")
        return metadata

    @staticmethod
    def validate_custom_code(
        module_file_path: str,
        custom_code_metadata: CustomCodeMetadata,
        validation_inputs: List[CodeValidationParameters],
        validation_outputs: List[CodeValidationParameters],
        correlation_id_val=None,
        additional_params: dict = None,
    ):
        if additional_params is None:
            additional_params = {}
        correlation_id.set(correlation_id_val)
        logs_file_path = (
                environment.validation_logs_folder / f"{correlation_id_val}.log"
        )
        with redirect_print_to_file(logs_file_path) :
            logger.info("Starting to VALIDATE the custom code data provided.")
            print("Starting to VALIDATE the custom code data provided.")

            if module_file_path.endswith(".zip"):
                logger.info(
                    f"Validated that the provided path [{module_file_path}] is a ZIP"
                )
                print(f"Validated that the provided path [{module_file_path}] is a ZIP")

                new_destination = extract_zip_in_new_location(module_file_path)
                logger.info(f"Extracted the ZIP to a new location. [{new_destination}]")
                print(f"Extracted the ZIP to a new location. [{new_destination}]")

                if custom_code_metadata is None or custom_code_metadata.entry_file is None:
                    logger.error(
                        f"Missing elements in custom code metadata: {custom_code_metadata}"
                    )
                    print(f"Missing elements in custom code metadata: {custom_code_metadata}")
                    raise Exception(
                        f"Missing elements in custom code metadata: {custom_code_metadata}"
                    )

                with change_working_directory(new_destination), sys_path_append(new_destination), updated_environ(
                        **additional_params):
                    logger.info(
                        f"Changing the directory to new destination and appending the path to system"
                    )
                    print(f"Changing the directory to new destination and appending the path to system")
                    # since input params can be inside zip, therefore need to extract kwargs inside this directory.
                    kwargs = ConversionHelper.convert_validation_parameters_to_kwargs(
                        validation_inputs
                    )
                    logger.info("converted the validation parameters into arguments...")
                    print("converted the validation parameters into arguments...")

                    entry_file_name = custom_code_metadata.entry_file
                    logger.info(f"Found entry file name: {entry_file_name}")
                    print(f"Found entry file name: {entry_file_name}")

                    custom_function_to_call = get_function_to_call(
                        entry_file_name, custom_code_metadata.function_name, entry_file_name
                    )
                    logger.info("Returning the function to call")
                    print("Returning to the function to call")
                    results = custom_function_to_call(**kwargs)  # actual run
                    logger.info("Called the function and returning the results..")
                    print("Called the function and returning the results..")
                    actual_outputs = convert_custom_code_results_to_list(results)
                    logger.info("Converted custom code results to actual outputs.")
                    print("Converted custom code results to actual outputs.")
                    expected_output_map = (
                        ConversionHelper.convert_validation_parameters_to_kwargs(
                            validation_outputs
                        )
                    )
                    logger.info("converted validation parameters to arguments")
                    print("converted validation parameters to arguments")

                    if len(actual_outputs) == len(expected_output_map.keys()):
                        logger.info(
                            f"Validated the length of actual output and excpected output. Length: {len(actual_outputs)}"
                        )
                        print(f"Validated the length of actual output and excpected output. Length: {len(actual_outputs)}")
                        logger.info("Comparing the actual outputs and expected outputs..")
                        print("Comparing the actual outputs and expected outputs..")
                        for i, expected_output in enumerate(expected_output_map.keys()):
                            if not ComparisonHelper.compare(
                                str(type(expected_output_map[expected_output])),
                                actual_outputs[i],
                                expected_output_map[expected_output],
                            ):
                                logger.error(
                                    f"Validation failed: expected and actual did not match."
                                )
                                print(f"Validation failed: expected and actual did not match.")
                                raise Exception(
                                    f"Validation failed: expected and actual did not match."
                                )
                    else:
                        logger.error(
                            f"Expected {len(expected_output_map.keys())} return values but got only {len(actual_outputs)}"
                        )
                        print(f"Expected {len(expected_output_map.keys())} return values but got only {len(actual_outputs)}")
                        raise Exception(
                            f"Expected {len(expected_output_map.keys())} return values but got only {len(actual_outputs)}"
                        )
                FileUtils.remove_path(str(new_destination.parent))
                logger.info("completed validation of the custom code data provided.")
                print("completed validation of the custom code data provided.")
            else:
                logger.error(
                    f"validation is only allowed for zip files now, not for {module_file_path}"
                )
                print(f"validation is only allowed for zip files now, not for {module_file_path}")
                raise NotImplementedError(
                    f"validation is only allowed for zip files now, not for {module_file_path}"
                )

    def run_module(self, module_id: str, kwargs: dict, additional_params: dict):
        logger.info(f"Starting to run the module with module id: {module_id}")
        module: Module = self.get_module_record_by_id(module_id=module_id)
        logger.info("Received module")
        with updated_environ(**additional_params):
            result = run_custom_code(
                module.module_location.path,
                function_name=CUSTOM_CODE_FUNCTION_NAME,
                custom_code_metadata=module.metadata,
                kwargs=kwargs,
            )
        logger.info(
            "Completed running the module and now will convert the results into list"
        )
        logger.info("About to convert and return the list.")
        return convert_custom_code_results_to_list(result)

    @staticmethod
    def get_file_info(file_path: str, last_modified_by: str = None) -> ModuleLocation:
        """Returns the file information needed for ModuleLocation."""
        size = str(os.path.getsize(file_path))
        file_extension = os.path.splitext(file_path)[1]
        if file_extension == ".zip":
            extension = ModuleExtenstion("ZIP")
        elif file_extension == ".py":
            extension = ModuleExtenstion("PY")
        last_modified_at = datetime.fromtimestamp(os.path.getmtime(file_path))
        return ModuleLocation(
            size=size,
            extension=extension,
            path=file_path,
            last_modified_by=last_modified_by,
            last_modified_at=last_modified_at,
        )

    async def create_module_clone(self, module_id: str, user_id: str) -> str:

        existing_module = await self.get_module_record_by_id_async(module_id=module_id)

        # note: for now cloning module comes as part of cpw itself. so below path segregation is possible
        # if in future of cloning of direct modules needs to be done. this needs to be corrected accordingly.
        module_path = Path(existing_module.module_location.path)
        updated_path = module_path.parent.parent/f"{uuid4().hex}/CLONED_{module_path.name}"
        FileUtils.createDeepCopyOfFile(
            source_file_path=module_path, dest_file_path=str(updated_path)
        )
        # del existing_module["_id"]

        module = Module(
            user_id=user_id,
            project_id=existing_module.project_id,
            site_id=existing_module.site_id,
            action_id=existing_module.action_id,
            run_id="",
            workflow_id="",
            name=f"CLONED_{existing_module.name}",
            description=existing_module.description,
            module_type=ModuleType.PYTHON,
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata=existing_module.metadata,
            created_at=datetime.now(timezone.utc),
            module_location=ModuleService.get_file_info(str(updated_path), user_id),
            access_mode=existing_module.access_mode,
            tags=existing_module.tags,
            created_by=existing_module.created_by,
        )
        logger.info("designed the module object to be inserted..")
        logger.info("inserting the module record to the db.")

        return await self.modules_dao.insert_module_record_async(module=module)
    async def get_module_records_by_ids_async(self, module_ids: List[str]) -> List[Module]:
        return await self.modules_dao.get_module_records_by_ids_async(module_ids=module_ids)
