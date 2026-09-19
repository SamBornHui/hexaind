from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
# from app.services.apps.image_analysis.schema import *
from pymongo import MongoClient
from app.core.db.db_utils import get_db_async, get_db_sync
import logging
from app.services.apps.image_analysis.service import ImageAnalysisService
from app.services.apps.image_analysis.workflow_widgets.service import ImageAnalysisWidgetsService
from app.services.apps.image_analysis.schema import *
from app.api.rbac.end_points_v1_access_control import CheckNameRoute

from app.services.data.assets.image_datasets.schemas import RegionPropertiesConfig
# from app.services.apps.image_analysis.segmentation import ImageAnalysisSegmenatationService
from bson import ObjectId
from typing import List
import websocket
from app.config.env_vars import environment
import os
from PIL import Image

image_analysis_router = APIRouter(prefix="/v1/image_analysis", tags = ["ImageAnalysis"], route_class=CheckNameRoute)
# image_analysis_router = APIRouter(tags=["Image Analysis"])
logger = logging.getLogger(__package__)


active_image_progress_connections = []
active_image_batch_processing_connections = []

class ImageAnalysisRouter:
    def __init__(self) -> None:
        pass
    
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/segmentation")
    async def segmentation(
        siteId: str,
        projectId: str,
        segmentation_properties: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside segmentation")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            segmenation_response = await image_analysis_service_obj.do_segmentation(segmentation_properties)
            return segmenation_response
        except Exception as e:
            logger.error(
                f"Failed to segment the image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @staticmethod
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/categorization_data/dataset/{datasetId}")
    async def image_categorization(
        siteId: str,
        projectId: str,
        datasetId:str,
        client: MongoClient= Depends(get_db_sync)) -> CategorizationResponse:
    
        
        try:
            logger.info("Inside ")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            cat_data= await image_analysis_service_obj.categorization_data(datasetId)
            return CategorizationResponse(categorization_data=cat_data)
        except Exception as e:
            logger.error(
                f"Failed to get categorization data of images dataset due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/create_image_workflow")
    async def create_workflow(
        siteId: str,
        projectId: str,
        create_image_worflow_json:dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        try:
            logger.info("Inside create_image_analysis_workflow")
            logger.info(create_image_worflow_json)
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            workflow_data= await image_analysis_service_obj.insertingDatainDB(create_image_worflow_json)
            
            return workflow_data   
        except Exception as e:
            logger.error(
                f"Failed to segment the image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.delete("/sites/{siteId}/projects/{projectId}/delete_image_workflow")
    async def delete_image_workflow(
        siteId: str,
        projectId: str,
        delete_worlflow_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside segmentation")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            delete_workflow_response = await image_analysis_service_obj.delete_workflow(delete_worlflow_json_obj)
            return delete_workflow_response
        except Exception as e:
            logger.error(
                f"Failed to segment the image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/assign_workflow_to_image")
    async def assign_workflow_to_image(
        siteId: str,
        projectId: str,
        assign_workflow_to_image_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside segmentation")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            assign_workflow_response = await image_analysis_service_obj.assign_workflow_to_image(assign_workflow_to_image_json_obj)
            return assign_workflow_response
        except Exception as e:
            logger.error(
                f"Failed assign_workflow_to_image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/deassociate_workflow_from_image")
    async def deassociate_workflow_from_image(
        siteId: str,
        projectId: str,
        deassociate_workflow_from_image_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside deassociate_workflow_from_image")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            deassociate_workflow_response = await image_analysis_service_obj.deassociate_workflow_from_image(deassociate_workflow_from_image_json_obj)
            return deassociate_workflow_response
        except Exception as e:
            logger.error(
                f"Failed to deassociate_workflow_from_image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/Update_favorite_workflow")
    async def Update_favorite_workflow(
        siteId: str,
        projectId: str,
        Update_favorite_workflow_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Updating favorite workflow")
            db = client
            obj = Update_favorite_workflow_json_obj
            workflow_id = ObjectId(obj['workflow_id'])
            user_id = obj['userId']
            favorite_status = obj['favorite']
            db = client[environment.hexaind3_database_name]
            # Find the workflow document
            workflow = db['sampleworkflows'].find_one({'_id': workflow_id})

            if not workflow:
                logger.error("Workflow not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workflow not found"
                )

            favorited_by = workflow.get('favorited_by', [])
            user_found = False

            # Update existing user's favorite status or add new entry
            for i in favorited_by:
                if i['user_id'] == user_id:
                    i['favorite'] = favorite_status
                    user_found = True
                    break

            if not user_found:
                favorited_by.append({'user_id': user_id, 'favorite': favorite_status})

            # Remove duplicates and update the workflow document
            favorited_by = list({v['user_id']: v for v in favorited_by}.values())
            db['sampleworkflows'].update_one(
                {"_id": workflow_id},
                {'$set': {'favorited_by': favorited_by}}
            )

            return {"message": "Favorite workflow updated successfully"}

        except Exception as e:
            logger.error(f"Failed to update favorite workflow: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/mask_image")
    async def mask_image(
        siteId: str,
        projectId: str,
        mask_image_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside mask_image")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            mask_image_response = await image_analysis_service_obj.do_image_masking(mask_image_json_obj)
            return mask_image_response
        except Exception as e:
            logger.error(
                f"Failed to mask the image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )    
        

        
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/save_mask")
    async def save_mask(
        siteId: str,
        projectId: str,
        mask_image_json_obj: Masks,
        client: MongoClient= Depends(get_db_sync),
    ):
        try:
            logger.info("Inside save mask api")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            mask_image_response = await image_analysis_service_obj.save_mask(mask_image_json_obj)
            return mask_image_response
        except Exception as e:
            logger.error(
                f"Failed to mask the image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )  
        

    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/get_masked_objs')
    async def get_masked_object(siteId: str,
                                projectId: str, 
                                get_masked_obj_config:MaskedObjRequest,
                                client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info("Inside get_saved_annotations of image_analysis_router")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            response = await image_analysis_service.get_masked_objs(obj=get_masked_obj_config)
            return response
        except Exception as e:
            logger.error(f"unable to  get_saved_annotations   due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.delete('/sites/{siteId}/projects/{projectId}/delete_masked_objs')
    async def delete_masked_object(siteId: str,
                                projectId: str, 
                                get_masked_obj_config:DeleteMaskObjects,
                                client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info("Inside get_saved_annotations of image_analysis_router")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            response = await image_analysis_service.delete_masked_obj(obj=get_masked_obj_config)
            return response
        except Exception as e:
            logger.error(f"unable to  get_saved_annotations   due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.put('/sites/{siteId}/projects/{projectId}/update_mask')
    async def update_mask(siteId: str,
                                projectId: str, 
                                update_label_mask_objects_config: UpdateMaskConfig,
                                client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info("Inside update_mask_coordinates")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            response = await image_analysis_service.update_mask(obj=update_label_mask_objects_config)
            return response
        except Exception as e:
            logger.error(f"unable to  get_saved_annotations   due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    
    
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/update_output_path")
    async def update_output_path(
        siteId: str,
        projectId: str,
        update_output_path_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside update_output_path")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            update_output_path_response = await image_analysis_service_obj.update_output_path(update_output_path_json_obj)
            return update_output_path_response
        except Exception as e:
            logger.error(
                f"Failed to update_output_path due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/check_output_directory")
    async def check_output_directory(
        siteId: str,
        projectId: str,
        check_output_directory_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        try:
            logger.info("Inside check_output_directory")
            output_directory = check_output_directory_json_obj['outputDirectory']
    
            if not os.path.exists(output_directory):
                check_output_directory_response = {"directory_exist": False,
                                                   "dir_path":output_directory}
            else:
                check_output_directory_response = {"directory_exist": True,
                                                   "dir_path":output_directory}
            return check_output_directory_response
        except Exception as e:
            logger.error(
                f"Failed to check_output_directory due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

     
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/start_batch_processing")
    async def start_batch_processing(
        siteId: str,
        projectId: str,
        start_batch_processing_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside update_output_path")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            start_batch_process_response = await image_analysis_service_obj.start_batch_process(start_batch_processing_json_obj)
            return start_batch_process_response
        except Exception as e:
            logger.error(
                f"Failed to update_output_path due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/workflow_and_batch_status")
    async def workflow_and_batch_status(
        siteId: str,
        projectId: str,
        workflow_and_batch_status_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside workflow_and_batch_status")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            workflow_and_batch_status_response = await image_analysis_service_obj.update_workflow_batch_status(workflow_and_batch_status_json_obj)
            return workflow_and_batch_status_response
        except Exception as e:
            logger.error(
                f"Failed to update_workflow_and_batch_status due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @image_analysis_router.get("/sites/{siteId}/projects/{projectId}/get_image_workflows")
    async def get_image_workflows(
        siteId: str,
        projectId: str,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside workflow_and_batch_status")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            all_image_workflow = await image_analysis_service_obj.get_all_image_workflow(projectId)
            return all_image_workflow
        except Exception as e:
            logger.error(
                f"Failed to get_image_workflows due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
    

    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/crop_image")
    async def crop_image(
        siteId: str,
        projectId: str,
        crop_image_json_obj:dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside crop_image")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            crop_image_response = await image_analysis_service_obj.crop_image(crop_image_json_obj)
            return crop_image_response
        except Exception as e:
            logger.error(
                f"Failed to crop_image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
    

    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/update_crop_image")
    async def update_crop_image(
        siteId: str,
        projectId: str,
        update_crop_image_json_obj:dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside crop_image")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            crop_image_response = await image_analysis_service_obj.update_crop_image(update_crop_image_json_obj)
            return crop_image_response
        except Exception as e:
            logger.error(
                f"Failed to crop_image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/get_folders_images")
    async def get_folders_images(
        siteId: str,
        projectId: str,
        folders_images_obj:dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside crop_image")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            crop_image_response = await image_analysis_service_obj.get_folders_images(folders_images_obj)
            return crop_image_response
        except Exception as e:
            logger.error(
                f"Failed to crop_image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )


    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/rotate_image")
    async def rotate_image(
        siteId: str,
        projectId: str,
        rotate_image_json_obj:dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside rotate_image API")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            rotate_image_response = await image_analysis_service_obj.rotate_image(rotate_image_json_obj)
            return rotate_image_response
        except Exception as e:
            logger.error(
                f"Failed to rotate_image due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
    
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/extract_scalebar_value")
    async def extract_scalebar_value(
        siteId: str,
        projectId: str,
        extract_scalebar_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside deassociate_workflow_from_image")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            scalebar_value_response = await image_analysis_service_obj.extract_scalebar_value(extract_scalebar_json_obj)
            return scalebar_value_response
        except Exception as e:
            logger.error(
                f"Failed to extract scalebar_value due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
    
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/save_scalebar_value")
    async def save_scalebar_value(
        siteId: str,
        projectId: str,
        save_scalebar_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside deassociate_workflow_from_image")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            scalebar_value_response = await image_analysis_service_obj.save_scalebar_value(save_scalebar_json_obj)
            return scalebar_value_response
        except Exception as e:
            logger.error(
                f"Failed to extract scalebar_value due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
    
    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/update_image_annotations")
    async def update_image_annotations(
        siteId: str,
        projectId: str,
        update_image_annotations_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside save_annotation")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            save_annotation_response = await image_analysis_service_obj.update_image_annotations(update_image_annotations_json_obj)
            return save_annotation_response
        except Exception as e:
            logger.error(
                f"Failed to save_annotation due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )


    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/generate_interactive_segmeneted_image")
    async def generate_interactive_segmeneted_image(
        siteId: str,
        projectId: str,
        get_annotation_data_json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside get_annotation_data")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            save_annotation_response = await image_analysis_service_obj.generate_interactive_segmeneted_image(get_annotation_data_json_obj)
            return save_annotation_response
        except Exception as e:
            logger.error(
                f"Failed to get_annotation_data due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )


    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/generate_segmenation_tabular_dataset")
    async def generate_segmenation_tabular_dataset(
        siteId: str,
        projectId: str,
        json_obj: dict,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside get_annotation_data")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            save_annotation_response = await image_analysis_service_obj.generate_segmenation_tabular_dataset(json_obj)
            return save_annotation_response
        except Exception as e:
            logger.error(
                f"Failed to get_annotation_data due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )



    @image_analysis_router.post("/sites/{siteId}/projects/{projectId}/get_all_unique_segmentation_labels")
    async def get_all_unique_segmentation_labels(
        siteId: str,
        projectId: str,
        client: MongoClient= Depends(get_db_sync),
    ):
        
        try:
            logger.info("Inside get_annotation_data")
            image_analysis_service_obj = ImageAnalysisService(db_sync_client=client)
            save_annotation_response = await image_analysis_service_obj.get_all_unique_segmentation_labels(projectId)
            return save_annotation_response
        except Exception as e:
            logger.error(
                f"Failed to get_annotation_data due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )



    @image_analysis_router.websocket("/image_progress_socket")
    async def image_progress_socket_endpoint(websocket1: WebSocket):
        await websocket1.accept()
        active_image_progress_connections.append(websocket1)
        try:
            while True:
                data = await websocket1.receive_text()
                # Broadcast the message to all connected clients
                for connection in active_image_progress_connections:
                    if connection != websocket1:
                        await connection.send_text(data)
        except WebSocketDisconnect:
            active_image_progress_connections.remove(websocket1)


    @image_analysis_router.websocket("/image_batch_processing_socket")
    async def image_batch_processing_socket_endpoint(websocket2: WebSocket):
        await websocket2.accept()
        active_image_batch_processing_connections.append(websocket2)
        try:
            while True:
                data = await websocket2.receive_text()
                # Broadcast the message to all connected clients
                for connection in active_image_batch_processing_connections:
                    if connection != websocket2:
                        await connection.send_text(data)
        except WebSocketDisconnect:
            active_image_batch_processing_connections.remove(websocket2)

# image_batch_processing_socket
    @staticmethod 
    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/save_annotations')
    async def save_annotations(projectId: str, 
                               annotations: Annotations, 
                               client: AsyncIOMotorClient = Depends(get_db_async) ):

        logger.info("Inside save_annotations of image_analysis_router")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            annotation_result  = await image_analysis_service.save_annotations(annotations=annotations)
            return annotation_result 
        except Exception as e:
            logger.error(f"unable to  save annotations for project id {projectId}  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/dataset/{datasetId}/get_saved_annotations')
    async def get_saved_annotations(projectId: str, 
                                    datasetId: str, 
                                    client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info("Inside get_saved_annotations of image_analysis_router")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            response = await image_analysis_service.get_saved_annotations_by_dataset_id(datasetId)
            return response
        except Exception as e:
            logger.error(f"unable to  get_saved_annotations for dataset id {datasetId}  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
    @staticmethod
    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/dataset/{datasetId}/get_DM_dataset_by_id')
    async def get_DM_dataset_by_id(projectId: str, 
                                   datasetId: str, 
                                   client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info("Inside get_DM_dataset_by_id of image_analysis_router")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            annotations = await image_analysis_service.get_DM_dataset_by_id(datasetId)
            return {"status": True, "data": annotations}
        
        except Exception as e:
            logger.error(f"unable to get_DM_dataset_by_id for dataset id {datasetId}  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
    
    @staticmethod
    @image_analysis_router.delete('/sites/{siteId}/projects/{projectId}/delete_annotation/{id}')
    async def delete_annotation(projectId: str, 
                                id: str, 
                                client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info(f"Inside delete_annotation of image_analysis_router with id: {id}")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            result = await image_analysis_service.delete_annotation_by_id(id)
            return result
        except Exception as e:
            logger.error(f"unable to delete_annotation with id {id}  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @staticmethod
    @image_analysis_router.put('/sites/{siteId}/projects/{projectId}/change_annotation_name')
    async def change_annotation_name(projectId: str, 
                                     data: ChangeAnnotationNameRequest, 
                                     client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            result = await image_analysis_service.change_annotation_name(data.annotation_id, data.annotation_name)
            return result
        except Exception as e:
            logger.error(f"unable to change_annotation_name  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @image_analysis_router.put('/sites/{siteId}/projects/{projectId}/change_annotation_label')
    async def change_annotation_label(projectId: str, 
                                      data: ChangeAnnotationLabelRequest, 
                                      client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            result = await image_analysis_service.change_annotation_label(data.annotation_id, data.label, data.color)
            return result
        except Exception as e:
            logger.error(f"unable to change_annotation_label due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @image_analysis_router.put('/sites/{siteId}/projects/{projectId}/update_coordinates')
    async def update_coordinates_of_canvas(projectId: str, 
                                           data: UpdateCoordinatesRequest, 
                                           client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            result = await image_analysis_service.update_coordinates_of_canvas(data.annotation_id, data.coordinates)
            return result
        except Exception as e:
            logger.error(f"unable to update_coordinates_of_canvas  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @image_analysis_router.put('/sites/{siteId}/projects/{projectId}/reset_manual_image')
    async def reset_manual_image(projectId: str, 
                                           data: MaskedObjRequest, 
                                           client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            result = await image_analysis_service.reset_manual_image(data)
            return result
        except Exception as e:
            logger.error(f"unable to update_coordinates_of_canvas  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @image_analysis_router.get('/sites/{siteId}/projects/{projectId}/dataset/{datasetId}/retrieve_fe_data')
    async def retrieve_fe_data(projectId: str, datasetId: str, client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            image_analysis_ww_service = ImageAnalysisWidgetsService(db_async_client=client)
            result = image_analysis_ww_service.retrieve_fe_data(datasetId)
            return result
        except Exception as e:
            logger.error(f"unable to update_coordinates_of_canvas  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
   
    @staticmethod
    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/dataset/{datasetId}/quantification_techniques')
    async def quantification_techniques(projectId: str, datasetId: str, data: QuantTechRequest, client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            image_analysis_ww_service = ImageAnalysisWidgetsService(db_async_client=client)
            result = await image_analysis_ww_service.quantification_techniques(data)
            return result
        except Exception as e:
            logger.error(f"unable to update_coordinates_of_canvas  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/dataset/{datasetId}/batch_processing')
    async def batch_processing(projectId: str, datasetId: str, data: BatchProcessingRequest, client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            image_analysis_ww_service = ImageAnalysisWidgetsService(db_async_client=client)
            
            result = image_analysis_ww_service.batchProcessing(data, projectId)
            return result
        except Exception as e:
            logger.error(f"unable to update_coordinates_of_canvas  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/get_image_size')
    async def get_image_size(projectId: str, data: dict ,client: AsyncIOMotorClient = Depends(get_db_async)):
        # Trim the path
        image_path = data['path']
        path = image_path.strip()
        if not path:
            return {"status": False, "message": "Path is empty"}
        file_path = Path(path)
        if not file_path.exists():
            return {"status": False, "message": "File does not exist"}
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                return {"status": True, "data": {"width": width, "height": height}}
        except Exception as e:
            logger.error(f"unable to get image size  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    
    
    @staticmethod
    @image_analysis_router.delete('/sites/{siteId}/projects/{projectId}/delete_label/{label_name}')
    async def delete_labels(
                                siteId:str,
                                projectId: str, 
                                label_name : str , 
                                client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info(f"Inside delete_annotation of image_analysis_router with id: {id}")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            result = await image_analysis_service.delete_label(label_name)
            return result
        except Exception as e:
            logger.error(f"unable to delete__segmented_annotation  due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @staticmethod
    @image_analysis_router.post('/sites/{siteId}/projects/{projectId}/workflow_images_path')
    async def workflow_images_path(
                                siteId:str,
                                projectId: str, 
                                workflow_images_path_body : WorkflowImagesPathRequest , 
                                client: AsyncIOMotorClient = Depends(get_db_async)):
        logger.info(f"Inside delete_annotation of image_analysis_router with id: {id}")
        try:
            image_analysis_service = ImageAnalysisService(db_async_client=client)
            result = await image_analysis_service.get_workflow_images_path(image_path = workflow_images_path_body.path)
            return result
        except Exception as e:
            logger.error(f"unable to get workflow_images_path due to {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
