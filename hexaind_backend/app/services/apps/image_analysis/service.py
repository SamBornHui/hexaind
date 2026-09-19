from pymongo import MongoClient
from skimage import io
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.apps.image_analysis.dao import ImageAnalysisDao
from app.services.apps.image_analysis.schema import *
from app.services.apps.image_analysis.controller.image_analysis_modules import *
import logging
import numpy as np
import os
from app.services.apps.image_analysis.image_analyisis_general_service import (
insertingDatainDB, 
deleteWf,
assignWf,
DissociateWfFromImage,
imageMasking,
getScaleBarValue,
updateOutputPathwf,
startBatchProcess,
updateWfandBatchStatus,
getWorkflowsFromDB,
cropImage,
rotateImage,
saveScalebar,
getResizeImages,
getfoldersImages,
generate_interactive_image,
update_segmentation_labels,
# generate_segmentation_tabular,
get_all_distinct_segmentation_labels_for_images
)
from app.services.apps.image_analysis.segmentation1 import cropAndSegmentationwWf


logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
class ImageAnalysisService:

    def __init__(self, db_sync_client: MongoClient = None, 
                 db_async_client: AsyncIOMotorClient = None) -> None:
        self.image_analysis_dao = ImageAnalysisDao(db_sync_client=db_sync_client,db_async_client=
                                                   db_async_client)
        
    async def do_segmentation(self, obj ):
        segmentation_data = await cropAndSegmentationwWf(obj, self.image_analysis_dao.db_sync)
        return segmentation_data
    
    async def image_categorization(self, dataset):
        image_cat_data= imageCategorization(dataset, self.image_analysis_dao.db_sync)
        return image_cat_data
    
    async def categorization_data(self, dataset_id):
        cat_data= get_categorization_data(dataset_id, self.image_analysis_dao.db_sync)
        return cat_data
    
    async def image_save_dataset(self, dataset):
        image_save_data= image_save_dataset(dataset, self.image_analysis_dao.db_sync)
        return image_save_data
        

    async def insertingDatainDB(self, obj):
        workflow_data = insertingDatainDB(obj,self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def delete_workflow(self, obj):
        workflow_data = deleteWf(obj,self.image_analysis_dao.db_sync)
        return workflow_data

    async def assign_workflow_to_image(self, obj):
        workflow_data = assignWf(obj,self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def deassociate_workflow_from_image(self, obj):
        workflow_data = DissociateWfFromImage(obj,self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def do_image_masking(self, obj):
        workflow_data = imageMasking(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    

    async def save_mask(self, mask_image_json_obj:Masks):
        logger.info("Inside save_mask function")
        mask_obj_dict = mask_image_json_obj.model_dump()
        categorized_data_id  = mask_image_json_obj.categorized_data_id
        category = mask_image_json_obj.category
        mask_objs  = mask_obj_dict["image_masking"]
        image_path = mask_image_json_obj.image
        print(mask_image_json_obj.categorized_data_id)

        results = []
        apply_all = mask_image_json_obj.apply_all
        
        filter1 = {"_id" : ObjectId(categorized_data_id)}
        categorized_data =  self.image_analysis_dao.get_document_sync(filter_document=filter1, collection="categorizeddata")
        print(categorized_data)
        list_of_images = categorized_data['data'][category]

        if apply_all == True:
            for image in list_of_images:
                image['image_masks'].extend(mask_objs)

        else:
            for image in list_of_images:
                if image_path == image['path']:
                    image['image_masks'].extend(mask_objs)
        
        categorized_data.pop('_id')
        result = self.image_analysis_dao.update_document_sync(filter_document=filter1, new_value=categorized_data, collection= 'categorizeddata')

        return {"message" : "obj save successfully"}


    async def get_masked_objs(self,obj:MaskedObjRequest):

        category = obj.category
        image_path = obj.image

        filer1 = {"_id" : ObjectId(obj.categorized_data_id)}
        print(obj.categorized_data_id)

        categorized_data =  await self.image_analysis_dao.get_document(filter_document=filer1, collection="categorizeddata")
        print(categorized_data)
        list_of_images = categorized_data['data'][category]

        for index, image in enumerate(list_of_images):
            if image_path == image['path']:    
                matched_index  = index

        all_masked_objects = categorized_data['data'][category][matched_index]['image_masks']

       
        get_masked_objs_response = {
            "data" : all_masked_objects
        }
        return get_masked_objs_response

    async def delete_masked_obj(self, obj:DeleteMaskObjects):
        category = obj.category
        image_path = obj.image
        coordinates = obj.coordinates

        filter1 = {"_id" : ObjectId(obj.categorized_data_id)}

        categorized_data =  await self.image_analysis_dao.get_document(filter_document=filter1, collection="categorizeddata")
        list_of_images = categorized_data['data'][category]

        for index, image in enumerate(list_of_images):
            if image_path == image['path']:    
                matched_index  = index
        all_masks = categorized_data['data'][category][matched_index]['image_masks']
        for index, mask in enumerate(all_masks):
            if mask["coordinates"] == coordinates:
                del all_masks[index]
                break
        logger.info(f"all masks     : {all_masks}")

        categorized_data.pop('_id')

        result = await self.image_analysis_dao.update_document(filter_document=filter1, new_value=categorized_data, collection= 'categorizeddata')
        return {"message" : "Mask is deleted successfully"}


    async def update_mask(self, obj:UpdateMaskConfig):
        category = obj.category
        image_path = obj.image
        old_coordinates = obj.old_coordinates
        new_coordinates = obj.new_coordinates
        apply_change = obj.apply_change
        mask_name  = obj.mask_name

        filter1 = {"_id" : ObjectId(obj.categorized_data_id)}

        categorized_data =  await self.image_analysis_dao.get_document(filter_document=filter1,collection="categorizeddata")
        list_of_images = categorized_data['data'][category]

        for index, image in enumerate(list_of_images):
            if image_path == image['path']:    
                matched_index  = index
        all_masks = categorized_data['data'][category][matched_index]['image_masks']
                       
        masked_image_obj = {
            "base_image":categorized_data['data'][category][matched_index]['manual_image'],
            "image":categorized_data['data'][category][matched_index]['manual_image'],
            "coordinates":new_coordinates,
            "ymax":0,
            "path":True,
            "user_id":""
        }
        masked_image = imageMasking(masked_image_obj, self.image_analysis_dao.db_sync)        
        if masked_image and 'cropimg' in masked_image:
            categorized_data['data'][category][matched_index]['masked_image'] = masked_image['cropimg']
        
        
        for index, mask in enumerate(all_masks):
            mask['apply'] = False
            if mask["coordinates"] == old_coordinates:
                mask['coordinates'] = new_coordinates
                mask['mask_name'] = mask_name
                mask['apply'] = apply_change

        logger.info(f"all masks     : {all_masks}")

        categorized_data.pop('_id')

        result = await self.image_analysis_dao.update_document(filter_document=filter1, new_value=categorized_data, collection= 'categorizeddata')

        return {"message" : "coordinates updated"}
    
    async def update_output_path(self, obj):
        workflow_data = updateOutputPathwf(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def start_batch_process(self, obj):
        workflow_data = await startBatchProcess(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def update_workflow_batch_status(self, obj):
        workflow_data = updateWfandBatchStatus(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def get_all_image_workflow(self,project_id):
        workflow_data = getWorkflowsFromDB(project_id, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def crop_image(self, obj):
        logger.info("inside crop_image function")

        workflow_data = cropImage(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def rotate_image(self, obj):
        workflow_data = rotateImage(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def extract_scalebar_value(self, obj):
        workflow_data = getScaleBarValue(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def save_scalebar_value(self, obj):
        workflow_data = saveScalebar(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def update_crop_image(self, obj):
        workflow_data = getResizeImages(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def get_folders_images(self, obj):
        workflow_data = getfoldersImages(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def generate_interactive_segmeneted_image(self, obj):
        workflow_data = await generate_interactive_image(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def update_image_annotations(self, obj):
        workflow_data = update_segmentation_labels(obj, self.image_analysis_dao.db_sync)
        return workflow_data
    
    async def get_all_unique_segmentation_labels(self, project_id:str):
        workflow_data = get_all_distinct_segmentation_labels_for_images(self.image_analysis_dao.db_sync,project_id=project_id)
        return workflow_data
    
    async def get_saved_annotations_by_dataset_id(self, dataset_id: str):
        masked_obj = await self.image_analysis_dao.find_annotations_by_dataset_id(dataset_id)
        get_saved_annotations_response = {"status": True, "data": masked_obj}
        if not masked_obj:
            get_saved_annotations_response.update({"status": False, "data": []})
        return get_saved_annotations_response
    
    async def save_annotations(self, annotations:Annotations) -> list:
        results = []
        annotations = annotations.model_dump()
        for annotation in annotations["annotations"]:
            report_status = {
                "error": True,
                "annotation": {},
                "error_msg": {}
            }
            if "_id" not in annotation:
                try:
                    inserted_id = await self.image_analysis_dao.insert_annotation(annotation)
                    
                    annotation['_id'] = inserted_id
                    report_status['annotation'] = annotation
                    report_status['error'] = False
                except Exception as e:
                    report_status['error_msg'] = str(e)
            else:
                report_status['annotation'] = annotation
                report_status['error'] = False
            results.append(report_status)
        
        if not results:
            err_str = f"error on saving annotations"
            logging.error(err_str)
            raise ValueError(err_str)
        
        return results

    
    async def get_saved_annotations_by_dataset_id(self, dataset_id: str):
        annotations = await self.image_analysis_dao.find_annotations_by_dataset_id(dataset_id)
        get_saved_annotations_response = {"status": True, "data": annotations}
        if not annotations:
            get_saved_annotations_response.update({"status": False, "data": []})
        return get_saved_annotations_response

    async def get_DM_dataset_by_id(self, dataset_id: str):
        annotations = await self.image_analysis_dao.find_DM_dataset_by_id(dataset_id)
        if not annotations:
            err_str = f"No annotations found for dataset_id {dataset_id}"
            logging.error(err_str)
            raise ValueError(err_str)
        
        return annotations
    
    async def delete_annotation_by_id(self, annotation_id: str) -> dict:
        result = await self.image_analysis_dao.find_and_delete_annotation_by_id(annotation_id)
        if result:
            return {"status": True, "msg": "Annotation Deleted successfully"}
        else:
            err_str = f"Annotation with id {annotation_id} not found or could not be deleted"
            logging.error(err_str)
            return {"status": False, "msg": err_str}
        
    async def change_annotation_name(self, annotation_id: str, annotation_name: str):
        result = await self.image_analysis_dao.update_annotation_name(annotation_id, annotation_name)
        if result.matched_count == 0:
            raise ValueError("Annotation(s) Not Found or no changes made")
        return {"status": True, "msg": "Annotation name updated successfully.", "data": {"modified_count": result.modified_count}}

    async def change_annotation_label(self, annotation_id: str, label: str, color: str):
        result = await self.image_analysis_dao.update_annotation_label(annotation_id, label, color)
        if result.matched_count == 0:
            raise ValueError("Annotation(s) Not Found or no changes made")
        return {"status": True, "msg": "Annotation label updated successfully.", "data": {"modified_count": result.modified_count}}

    async def update_coordinates_of_canvas(self, annotation_id: str, coordinates: dict[str, float]):
        result = await self.image_analysis_dao.update_coordinates(annotation_id, coordinates)
        if result.matched_count == 0:
            raise ValueError("Annotation(s) Not Found or no changes made")
        return {"status": True, "msg": "Annotation coordinates updated successfully.", "data": {"modified_count": result.modified_count}}
    
    async def reset_manual_image(self, obj: MaskedObjRequest):
        try:
            category = obj.category
            image_path = obj.image
            filer1 = {"_id" : ObjectId(obj.categorized_data_id)}

            categorized_data =  await self.image_analysis_dao.get_document(filter_document=filer1, collection="categorizeddata")
            list_of_images = categorized_data['data'][category]

            for index, image in enumerate(list_of_images):
                if image_path == image['path']:
                    
                    matched_index  = index
                    manual_thumb = False
                    clear_cordinates = False    
                    if obj.reset_from == 'rotate':
                        image['rotate_image'] = None
                        image['rotate_thumbnail'] = None
                        image['manual_image'] = image['default_manual_image']
                        image['rotate_options']['rotateval'] = 0
                        image['rotate_options']['auto_rotate'] = False
                        image['rotate_options']['manual_rotate'] = False
                        image['rotate_options']['manual_rotate'] = False
                        image['manual_shape'] = image['shape'][::-1]
                        manual_thumb = True
                        clear_cordinates = True
                        image['image_masks'] = []
                        
                    elif obj.reset_from == 'crop':
                        if image['rotate_image']:
                            image['manual_image'] = image['rotate_image']
                            image['manual_thumbnail'] = image['rotate_thumbnail']
                            img = io.imread(image['rotate_image'])
                            
                        elif image['default_manual_image']:
                            image['manual_image'] = image['default_manual_image']
                            img = io.imread(image['default_manual_image'])
                            manual_thumb = True
                        
                        else:
                            dir_path = os.path.split(image['image'])[0]

                            if dir_path.split('/')[-1] == 'processedimg':
                                image['manual_image'] = dir_path.replace('processedimg','modifiedimages')
                                image['manual_thumbnail'] = dir_path.replace('processedimg','modifiedimages')
                                image['manual_image'] = shutil.copy(image['image'], image['manual_image'])
                                image['manual_thumbnail'] = shutil.copy(image['thumpnail'], image['manual_thumbnail'])
                                img = io.imread(image['manual_image'])
                                
                            
                        image['manual_shape'] = img.shape[:2]    
                        clear_cordinates = True
                        image['image_masks'] = []
                            
                    
                    elif obj.reset_from == 'mask':
                        image['image_masks'] = []
                            
                    
                    if manual_thumb:
                        _ , image_extension =  os.path.splitext(image['manual_thumbnail'])
                        image['manual_thumbnail'] = image['thumpnail'].replace('processedimg/thumbnail','modifiedimages//thumb')
                        if not image['manual_thumbnail'].endswith(image_extension):
                            _ , extension_to_change = os.path.splitext(image['manual_thumbnail'])
                            image['manual_thumbnail'] = image['manual_thumbnail'].replace(extension_to_change , image_extension)
                            
                    if clear_cordinates:
                        image['manual_coordinates']['x2'] = image['shape'][1]
                        image['manual_coordinates']['w'] = image['shape'][1]
                        image['manual_coordinates']['y2'] = image['shape'][0]
                        image['manual_coordinates']['h'] = image['shape'][0]
                        image['manual_coordinates']['x1'] = 0
                        image['manual_coordinates']['y1'] = 0
                        image['manual_coordinates']['crop_cord'] = False
                        
                        

                    break

            result = await self.image_analysis_dao.update_document(filter_document=filer1, new_value=categorized_data, collection= 'categorizeddata')
            categorized_data['_id'] = str(categorized_data['_id'] ) 
            return_data = {"updated_data" : categorized_data['data'][category][matched_index]}   
            return_data['updated_data']['category'] = category
            return return_data
        except Exception as e:
            logger.error(f"unable to reset image due to {str(e)}")
            return {"message" : 'manual image not reset' , 'status' : False}


    async def delete_label(self, label_name:str) -> dict:
        try:
            logger.info(label_name)

            result  = await self.image_analysis_dao.update_label(label_name)
            return {"status": True}

           
        except Exception as e:
            raise Exception
        

    async def get_workflow_images_path(self, image_path:str):
        try:
            logger.info(image_path)

            result  = await self.image_analysis_dao.get_document(filter_document={"path":image_path}, collection="workflowimagespath")
            result["_id"] = str(result["_id"])
            return result

           
        except Exception as e:
            raise Exception

    
    