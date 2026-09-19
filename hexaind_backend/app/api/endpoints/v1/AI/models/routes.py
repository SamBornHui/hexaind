import os
from pathlib import Path
import sys
import logging
import tempfile
import traceback
from typing import List, Union
from uuid import uuid4
import zipfile
from bson import ObjectId
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.services.data.assets.datasets.schemas import (
    MachineLearningModel,
    DeleteModelsResponse,
)
from app.services.AI.models.schemas import (
    CreateVisualizationsResponse,
    ModelsData,
    CompareModelsResponse,
    CompareModelsRequest,
    HighlightPointRequest,
    HighlightPointResponse,
)
from app.core.db.db_utils import get_db_async
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.services.AI.models.service import ModelService
from app.services.AI.prediction.dao import PredictionDao
from app.services.AI.prediction.schemas import DeployModel, CompatibleModel
from app.services.AI.prediction.service import PredictionService
from app.actions import Actions
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

models_router = APIRouter(tags=["Models"], route_class=CheckNameRoute)


class ModelsRouter:

    def __init__(self):
        pass

    @models_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/run/{run_id}/models/preview_models",
        response_model=List[MachineLearningModel],
        openapi_extra={"actions":Actions.Preview_Model_Result.value},

    )
    async def models_preview(
        site_id: str,
        project_id: str,
        run_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> List[MachineLearningModel]:
        try:
            obj = ModelService(db_async_client=client)
            results = await obj.modeldao.get_models_by_run_id(
                project_id=project_id, run_id=run_id
            )
            models = []
            for res in results:
                res["_id"] = str(res["_id"])
                models.append(MachineLearningModel(**res))

            return models

        except Exception as e:
            logger.error(f"Failed to fetch models due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/save_models",
        response_model=Union[List[MachineLearningModel], List],
    )
    async def save_models(
        site_id: str,
        project_id: str,
        models: List[MachineLearningModel],
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> Union[List[MachineLearningModel], List]:
        try:
            obj = ModelService(db_async_client=client)
            failed_models = []
            for model in models:
                model_json = model.model_dump()
                model_json["_id"] = ObjectId(model_json["id"])
                try:
                    data = {
                        "model.name": model_json["model"]["name"],
                        "access_mode": "EXTERNAL",
                    }
                    await obj.modeldao.update_model_async(
                        query={"_id": model_json["_id"]}, data=data, col_name="models"
                    )
                except:
                    logger.debug(
                        f"A model with the name '{model_json['model']['name']}' already exists."
                    )
                    failed_models.append(model)

            return failed_models

        except Exception as e:
            logger.error(f"Failed to save models due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/save_and_update_models",
        response_model=Union[List[MachineLearningModel], List],
    )
    async def save_and_update(
        site_id: str,
        project_id: str,
        models: List[MachineLearningModel],
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> Union[List[MachineLearningModel], List]:
        try:
            obj = ModelService(db_async_client=client)
            existing_doc = await obj.save_and_update_models(
                models, project_id=project_id
            )
            return existing_doc

        except Exception as e:
            logger.error(f"Failed to save models due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @models_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/models",
        response_model=List[MachineLearningModel],
    )
    async def get_models(
        site_id: str,
        project_id: str,
        search_term: str = Query(default=None),
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> List[MachineLearningModel]:
        try:
            logger.info("inside get models method.")
            obj = ModelService(db_async_client=client)
            results = await obj.modeldao.get_all_models(
                project_id=project_id,
                search_term=search_term,
                page_limit=page_limit,
                page_number=page_number,
            )
            models = []
            for res in results:
                res["_id"] = str(res["_id"])
                models.append(MachineLearningModel(**res))
            return models

        except Exception as e:
            logger.error(f"Failed to get models due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @models_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/model/{model_id}",
        response_model=MachineLearningModel,
    )
    async def get_model_by_id(
        site_id: str,
        project_id: str,
        model_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> MachineLearningModel:
        try:
            logger.info("inside get model method.")
            obj = ModelService(db_async_client=client)
            result = await obj.modeldao.get_model_by_id_async(
                model_id=ObjectId(model_id), project_id=project_id
            )
            result["_id"] = str(result["_id"])
            return MachineLearningModel(**result)

        except Exception as e:
            logger.error(f"Failed to get models due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @models_router.delete(
        "/v1/sites/{site_id}/projects/{project_id}/delete_models",
        response_model=DeleteModelsResponse,
    )
    async def delete_models(
        site_id: str,
        project_id: str,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> DeleteModelsResponse:
        """
        Deletes all models associated with a given project ID.
        """
        try:
            logger.info("Starting to delete models.")
            obj = ModelService(db_async_client=client)
            result = await obj.modeldao.delete_all_models(project_id=project_id)
            logger.info("Models deletion attempted.")

            if result.deleted_count > 0:
                return DeleteModelsResponse(
                    status="success", deleted_count=result.deleted_count
                )
            else:
                return DeleteModelsResponse(
                    status="no models found to delete", deleted_count=0
                )
        except Exception as e:
            logger.error(f"Failed to delete models due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete models due to: {str(e)}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/create_visualizations",
        response_model=CreateVisualizationsResponse,
        #openapi_extra={"actions":Actions.Preview_Model_Result.value}
    )
    async def create_visualizations(
        site_id: str,
        project_id: str,
        model_data: ModelsData,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CreateVisualizationsResponse:
        """
        Create parity and residual graphs.
        """
        try:
            logger.info("Starting to create models visualization.")
            model_handler = ModelService(db_async_client=client)
            visualization_data = await model_handler.create_visualization(
                model=model_data.model,
                summary_path=model_data.summary_path,
                data_path=model_data.data_path,
                chosen_column=model_data.chosen_column,
                output_col=model_data.output_col,
                split_ratio=model_data.split_ratio,
                data_type=model_data.data_type,
            )
            logger.info("Models visuaoization response .")

            return CreateVisualizationsResponse(visualization_data=visualization_data)

        except Exception as e:
            logger.error(
                f"Failed to create models visualization due to: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create models visualization due to: {str(e)}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/compare_models",
        response_model=CompareModelsResponse,
    )
    async def compare_models(
        site_id: str,
        project_id: str,
        models_config: CompareModelsRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CompareModelsResponse:
        """
        Create parity and residual graphs for comparison.
        """
        try:
            logger.info("Starting to create models visualization.")
            model_handler = ModelService(db_async_client=client)
            comapre_visualization_data = await model_handler.compare_models_visualization(
                project_id=project_id, models_config=models_config
            )
            logger.info("Models Comparison visualization response .")

            return CompareModelsResponse(
                comapre_visualization_data=comapre_visualization_data
            )
        except Exception as e:
            logger.error(
                f"Failed to create models comparison visualizations due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create models comparison visualizations due to: {str(e)}",
            )

    @models_router.delete(
        "/v1/sites/{site_id}/projects/{project_id}/model/{model_id}",
        response_model=DeleteModelsResponse,
    )
    async def delete_model(
        site_id: str,
        project_id: str,
        model_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> DeleteModelsResponse:
        """
        Deletes a specific model associated with a given project ID and model ID.
        """
        try:
            logger.info("Starting to delete a specific model.")
            obj = ModelService(db_async_client=client)
            result = await obj.modeldao.delete_model_by_id(
                project_id=project_id, model_id=model_id
            )
            logger.info("Model deletion attempted.")

            if result.deleted_count > 0:
                return DeleteModelsResponse(
                    status="success", deleted_count=result.deleted_count
                )
            else:
                return DeleteModelsResponse(
                    status="no model found to delete", deleted_count=0
                )
        except Exception as e:
            logger.error(f"Failed to delete model due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete model due to: {str(e)}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/interactiveGraphHover",
        response_model=HighlightPointResponse,
    )
    async def interactiveGraphHover(
        site_id: str,
        project_id: str,
        request_body: HighlightPointRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CompareModelsResponse:
        """
        Create summary for parity and residual graphs highlighted point.
        """
        try:
            logger.info("Starting to create highlighted point summary.")
            model_handler = ModelService(db_async_client=client)
            point_summary = model_handler.highlighted_point_summary(
                model=request_body.model,
                summary_path=request_body.summary_path,
                data_path=request_body.data_path,
                chosen_column=request_body.chosen_column,
                output_col=request_body.output_col,
                split_ratio=request_body.split_ratio,
                data_type=request_body.data_type,
                graph_name=request_body.graph_name,
                coordinates=request_body.coordinates,
            )
            logger.info("highlighted point summary response .")

            return HighlightPointResponse(point_summary=point_summary)

        except Exception as e:
            logger.error(
                f"Failed to create highlighted point summary due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create highlighted point summary due to: {str(e)}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/deployModel",
        response_model=MachineLearningModel,
    )
    async def deploy_model(
        site_id: str,
        project_id: str,
        deploy_model: DeployModel,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> MachineLearningModel:
        try:
            prediction_service_obj = PredictionService(db_async_client=client)
            response = await prediction_service_obj.deploy_model(
                deploy_model=deploy_model
            )
            return MachineLearningModel(**response)

        except Exception as e:
            logger.error(f"Failed to deploy model due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to deploy model: {str(e)}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/undeployModel",
        response_model=MachineLearningModel,
    )
    async def undeploy_model(
        site_id: str,
        project_id: str,
        deploy_model: DeployModel,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> MachineLearningModel:
        try:
            prediction_service_obj = PredictionService(db_async_client=client)
            response = await prediction_service_obj.undeploy_model(
                deploy_model=deploy_model
            )
            return MachineLearningModel(**response)
        except Exception as e:
            logger.error(f"Failed to undeploy model due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to deploy model: {str(e)}",
            )

    @models_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/models/compatibleModel",
        response_model=List[MachineLearningModel],
    )
    async def compatible_model(
        site_id: str,
        project_id: str,
        compatible_model: CompatibleModel,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> List[MachineLearningModel]:
        try:
            input_cols = compatible_model.input_cols
            document_filter = {
                "project_id": project_id,
                "ml_deployed_status.status": "deployed",
                "$expr": {"$setIsSubset": ["$model.configs.input_cols", input_cols]},
            }

            prediction_dao = PredictionDao(db_async_client=client)
            results = await prediction_dao.get_all_document(document_filter, "models")
            models = []
            for res in results:
                res["_id"] = str(res["_id"])
                models.append(MachineLearningModel(**res))
            return models

        except Exception as e:
            logger.error(f"Failed to undeploy model due to: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get compatible model: {str(e)}",
            )

    @staticmethod
    @models_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/models/download_models"
    )
    async def download_all_pkl_files(
        site_id: str,
        project_id: str,
        run_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ):
        """
        Create and download a zip file containing all .pkl files.
        """
        try:
            # Retrieve all the pickle files
            model_handler = ModelService(db_async_client=client)
            pickle_files, base_path = await model_handler.find_pickle_files(
                wf_run_id=run_id, project_id=project_id
            )
            logger.info(f"{len(pickle_files)} pickle files found.")

            if not pickle_files:
                raise HTTPException(status_code=400, detail="No .pkl files found")

            with tempfile.TemporaryDirectory() as temp_dir:
                zip_temp_path = Path(temp_dir) / f"model_files_{uuid4().hex}.zip"
                
                # Create the zip file in the temporary directory
                with zipfile.ZipFile(zip_temp_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for fileinfo in pickle_files:
                        file_path = Path(fileinfo["file_path"])

                        # Ensure file_path is within the base_path directory
                        try:
                            file_path.relative_to(base_path)
                        except ValueError:
                            raise HTTPException(status_code=400, detail="Invalid file path")

                        # Construct the archive name
                        file_ext = file_path.suffix
                        arcname = (
                            file_path.relative_to(base_path)
                            .with_name(fileinfo["model_name"])
                            .with_suffix(file_ext)
                        )
                        zipf.write(file_path, arcname=arcname)

                # Move the zip file to a temporary named file outside the context manager
                final_zip_path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
                final_zip_path.close()  # Close it so we can write to it

                # Copy the zip file content to the persistent temporary file
                with open(zip_temp_path, "rb") as src, open(final_zip_path.name, "wb") as dest:
                    dest.write(src.read())

            # Return the zip file as a response
            return FileResponse(
                final_zip_path.name,
                media_type="application/zip",
                filename=f"model_files_{run_id}.zip",
            )

        except Exception as e:
            logger.exception(f"Failed with exception - {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed with exception - {str(e)}"
            )
