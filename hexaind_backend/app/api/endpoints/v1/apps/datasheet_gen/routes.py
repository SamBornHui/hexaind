import traceback
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File,BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import List
from app.services.admin.connectors.schemas import Connector
from app.core.db.db_utils import get_db_async
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.apps.datasheet_gen.service import DatasheetGenService
from app.services.apps.datasheet_gen.schemas import *
from app.env import *
import shutil
import os
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT

# from app.services.apps.datasheet_gen.schemas import ComputeDatasheetResponse, ExportDatasheetResponse,CsvDataResponse, ReadCsv
from app.api.rbac.end_points_v1_access_control import CheckNameRoute

datasheet_gen_router = APIRouter(tags = ["DatasheetGen"], route_class=CheckNameRoute)

logger = logging.getLogger(__package__)

class DatasheetGenRouter:
    
    def __init__(self):
        pass
    
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/{siteId}/projects/{projectId}/datasheet/{datasheet}/nominal_age/{nominal_age}/reset/{reset}/', response_model=ComputeDatasheetResponse)
    async def compute_datasheet( siteId: str, 
                                projectId: str, 
                                datasheet: int,
                                nominal_age:int,
                                reset:bool,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> ComputeDatasheetResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            datasheet_detail = await dsgen_handler.compute_datasheet_async(projectId= projectId,ds= datasheet, nominal_age=nominal_age, reset=reset)
            
            datasheet = Datasheet(**datasheet_detail)
            return ComputeDatasheetResponse(datasheet=[datasheet])

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : {siteId} , {datasheet}, {nominal_age}", exc_info=True)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e))
            

    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/{siteId}/projects/{projectId}/generate_datasheet/{datasheet}/nominal_age/{nominal_age}/', response_model=ExportDatasheetResponse)
    async def generate_datasheet( siteId: str,
                                projectId: str,  
                                datasheet: str,
                                nominal_age:str,
                                metadata: dict,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> ExportDatasheetResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            datasheet_path = await dsgen_handler.export_datasheet_async(metadata= metadata, projectId=projectId, ds= datasheet, nominal_age=nominal_age)

            return ExportDatasheetResponse(datasheet_path = datasheet_path)
        
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : {siteId} , {datasheet}, {nominal_age}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to generate datasheet")

    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/{siteId}/projects/{projectId}/generate_new_datasheet/{datasheet}/nominal_age/{nominal_age}/', response_model=ExportDatasheetResponse)
    async def generate_new_datasheet( siteId: str, 
                                projectId: str, 
                                datasheet: str,
                                nominal_age:str,
                                metadata: dict,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> ExportDatasheetResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            datasheet_path = await dsgen_handler.export_new_fit_datasheet_async(metadata= metadata, projectId=projectId, ds= datasheet, nominal_age=nominal_age)

            return ExportDatasheetResponse(datasheet_path = datasheet_path)
        
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : {siteId} , {datasheet}, {nominal_age}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to generate new datasheet")

    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/{siteId}/projects/{projectId}/datasheet/{datasheet}/save_metadata', response_model=ExportDatasheetResponse)
    async def save_metadata( siteId: str, 
                                projectId: str, 
                                datasheet: str,
                                metadata: dict,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> ExportDatasheetResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            datasheet_path = await dsgen_handler.save_metadata_async(metadata= metadata, projectId=projectId, ds= datasheet)

            return ExportDatasheetResponse(datasheet_path = datasheet_path)
        
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : {siteId} , {datasheet}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to save datasheet metadata")

    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/datasheet/read_csv', response_model=CSVDataResponse)
    async def read_csv( 
                                data: ReadCsv,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> CSVDataResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            csv_data = await dsgen_handler.read_csv_async(data =data)

            return CSVDataResponse(csv_data = csv_data)
        
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : read csv", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to read csv")

    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/get_datasheets', response_model=GetDatasheetsResponse)
    async def get_datasheets(   projectId:str,
                                # data: BasePath,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> GetDatasheetsResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            datasheets = await dsgen_handler.get_datasheets_async(projectId=projectId)

            return GetDatasheetsResponse(datasheets = datasheets)
        
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : get_datasheets", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to get datasheets")

    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/get_datasheets_details', response_model=GetDatasheetsDetailResponse)
    async def get_datasheets_details(   projectId:str,
                                data: BasePath,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> GetDatasheetsDetailResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            datasheets = await dsgen_handler.get_datasheets_details_async(projectId=projectId,data =data)

            return GetDatasheetsDetailResponse(datasheets = datasheets)
        
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : get_datasheets", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to get datasheets")
        
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/datasheet/correct_tensile', response_model= CorrectTensileResponse)
    async def correct_tensile( 
                                data: CorrectTensile,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> CorrectTensileResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            correct_data = await dsgen_handler.correct_tensile_async(data =data)

            return CorrectTensileResponse(correct_data = correct_data)
        
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : correct_tensile", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to get correct tensile file")
    
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/datasheet/reset_tensile_sample', response_model= CorrectTensileResponse)
    async def reset_tensile_sample( 
                                data: CorrectTensile,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> CorrectTensileResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            correct_data = await dsgen_handler.reset_tensile_async(data =data)

            return CorrectTensileResponse(correct_data = correct_data)
        
        except Exception as e:
            logger.error(f"Failed with exception {e} : correct_tensile", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to get correct tensile file")
    
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/datasheet/comparison_tensile_sample', response_model= CorrectTensileResponse)
    async def comparison_tensile_sample( 
                                data: CompareTensile,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> CorrectTensileResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            correct_data = await dsgen_handler.comparison_tensile_async(data =data)
            return CorrectTensileResponse(correct_data = correct_data)
        
        except Exception as e:
            logger.error(f"Failed with exception {e} : correct_tensile", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to get correct tensile file")
        
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/datasheet/preview', response_model=FilePreviewResponse)
    async def preview_file(file_details: FileDetails, 
                           client: AsyncIOMotorClient = Depends(get_db_async)) -> FilePreviewResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            file_name ,file_url = await dsgen_handler.preview_file_async(file_details = file_details)
            return FilePreviewResponse(file_name=file_name, file_url=file_url)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : preview pdf", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to preview datasheet pdf file")
        
    @staticmethod    
    @datasheet_gen_router.post('/v1/sites/datasheet/local_fit', response_model= LocalFitResponse)
    async def local_fit(adjusted_params: AdjustedParams, 
                           client: AsyncIOMotorClient = Depends(get_db_async)) -> LocalFitResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            local_fit = await dsgen_handler.local_fit_async(adjusted_params = adjusted_params)
            return LocalFitResponse(local_fit = local_fit)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : local_fit", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to compute local fit")

    @staticmethod    
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/save_flc_ascii', response_model= SaveASCIIResponse)
    async def save_flc_ascii(flc_params:FlcParams , projectId:str,
                           client: AsyncIOMotorClient = Depends(get_db_async), token: str= '') -> SaveASCIIResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            token = decodeJWT(token)
            flc_ascii = await dsgen_handler.save_flc_ascii_async(projectId = projectId, userId= token['user_id'], flc_params = flc_params)
            return SaveASCIIResponse(ascii = flc_ascii)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : save_flc_ascii", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to save flc ascii")

    @staticmethod    
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/save_tensile_ascii', response_model= SaveASCIIResponse)
    async def save_tensile_ascii(tensile_params:TensileParams , projectId:str,
                           client: AsyncIOMotorClient = Depends(get_db_async), token: str= '') -> SaveASCIIResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            token = decodeJWT(token)
            tensile_ascii = await dsgen_handler.save_tensile_ascii_async(projectId= projectId, userId= token['user_id'], tensile_params = tensile_params)
            return SaveASCIIResponse(ascii = tensile_ascii)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : save_tensile_ascii", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to save tensile ascii")
        
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/{siteId}/projects/{projectId}/datasheet/ingest_data', response_model= IngestDataResponse)
    async def upload_directory(siteId:str= '', projectId: str = '',
        files: list[UploadFile] = File(...),filePaths: list[str] =[],
        client: AsyncIOMotorClient = Depends(get_db_async),
        token: str = '') -> IngestDataResponse:
        try:
            token = decodeJWT(token)
            dsgen_handler = DatasheetGenService(db_async_client=client)
            ingestion_results = await dsgen_handler.ingest_data_async(projectId= projectId, userId= token['user_id'],files= files,filePaths =filePaths)
            return IngestDataResponse(ingestion_results=ingestion_results)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : ingest_data", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to ingest data")
    
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/upload_flc_file_to_convert', response_model= ConvertorUploadResponse)
    async def upload_flc_file_to_convert(projectId:str ,fitFile: UploadFile = File(...),
                                     rawFile: UploadFile = File(...),
                                     metadataFile:str = 'flc', 
                                     client: AsyncIOMotorClient = Depends(get_db_async)) -> ConvertorUploadResponse:
        try:
             
            # Save the uploaded directory to a temporary location
            dsgen_handler = DatasheetGenService(db_async_client=client)
            
            convertor_results = await dsgen_handler.upload_file_to_convert_async(projectId = projectId, fitFile = fitFile, rawFile = rawFile ,metadataFile=metadataFile)
            convertor_results_value = await convertor_results
            return ConvertorUploadResponse(convertor_results=convertor_results_value)
            # return IngestDataResponse(ingestion_results =await ingestion_results)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : upload_flc_file_to_convert", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to upload flc file to convert")
    
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/upload_tensile_file_to_convert', response_model= ConvertorUploadResponse)
    async def upload_tensile_file_to_convert(projectId:str, tensileFile: UploadFile = File(...),
                                     client: AsyncIOMotorClient = Depends(get_db_async)) -> ConvertorUploadResponse:
        try:
             
            # Save the uploaded directory to a temporary location
            dsgen_handler = DatasheetGenService(db_async_client=client)
            
            convertor_results = await dsgen_handler.upload_tensile_file_to_convert_async(projectId = projectId, tensileFile = tensileFile)
            convertor_results_value = await convertor_results
            return ConvertorUploadResponse(convertor_results=convertor_results_value)
            # return IngestDataResponse(ingestion_results =await ingestion_results)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : upload_tensile_file_to_convert", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to upload tensile file to convert")

    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/datasheet/tensile_file_convertor', response_model= TensileConvertorResponse)
    async def tensile_file_to_convert(tensile_params: TensileParams,
                                     client: AsyncIOMotorClient = Depends(get_db_async)) -> TensileConvertorResponse:
        try:
             
            # Save the uploaded directory to a temporary location
            dsgen_handler = DatasheetGenService(db_async_client=client)
            
            tensile_data = await dsgen_handler.tensile_file_convert_async(tensile_params = tensile_params)
            return TensileConvertorResponse(tensile_data=tensile_data)
            # return IngestDataResponse(ingestion_results =await ingestion_results)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : tensile_file_convertor", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to convert tensile file")
            
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/{datasheet}/download_results', response_model= None)
    async def download_results(datasheet: str,
                               projectId: str,
                           client: AsyncIOMotorClient = Depends(get_db_async)) :
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            download_result = await dsgen_handler.download_results_async(projectId = projectId, datasheet = datasheet)
            zip_path = Path(EXPORT_PATH,str(projectId), str(datasheet),'results.zip')
            return FileResponse(zip_path, filename="results.zip", media_type="application/zip")


        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : download_results", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to download results")
      
    @staticmethod 
    @datasheet_gen_router.post('/v1/sites/projects/{projectId}/datasheet/download_ascii', response_model= None)
    async def download_ascii(datasheet: str,
                             nominal_age:str,
                             file_type:str,
                             projectId:str,
                             background_tasks: BackgroundTasks,
                           client: AsyncIOMotorClient = Depends(get_db_async)) :
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            download_ascii = await dsgen_handler.download_ascii_async(projectId=projectId,datasheet = datasheet,nominal_age = nominal_age, file_type = file_type)
            file_name = f"{datasheet}_{file_type}_{nominal_age}_ASCII_export.zip"
            nominal_age_days = f"{nominal_age} days"
            zip_path = Path(IMPORT_PATH,str(projectId), str(datasheet),str(file_type),file_name)

            response = FileResponse(zip_path, filename= file_name, media_type="application/zip")
            background_tasks.add_task(dsgen_handler.delete_file, str(zip_path))
            return response


        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : download_ascii", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to download ASCII")
      
    @staticmethod 
    @datasheet_gen_router.delete('/v1/sites/projects/{projectId}/datasheet/{datasheet:path}/delete', response_model= None)
    async def delete_datasheet(datasheet: str,
                             projectId:str,
                             background_tasks: BackgroundTasks,
                           client: AsyncIOMotorClient = Depends(get_db_async)) :
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            imp_del_path = Path(IMPORT_PATH,str(projectId), str(datasheet))
            path_parts = datasheet.split('/')
            datasheet
            if len(path_parts) == 3:
                age = path_parts[2].split(' ')[0]
                datasheet_name = path_parts[0]
                exp_del_path = Path(EXPORT_PATH, str(projectId), str(datasheet_name), str(age))
            elif len(path_parts) == 2:  # Use 'elif' instead of 'else if'
                datasheet_name = path_parts[0]
                exp_del_path = Path(EXPORT_PATH, str(projectId), str(datasheet_name))
            else:
                exp_del_path = Path(EXPORT_PATH, str(projectId), str(datasheet))
            
            datasheet_deleted = await dsgen_handler.delete_datasheet_record(project_id=projectId, datasheet_name=datasheet)

            res = dsgen_handler.delete_file_or_directory(exp_del_path)
            res = dsgen_handler.delete_file_or_directory(imp_del_path)
            # background_tasks.add_task(delete_file_or_directory, str(imp_del_path))
            # background_tasks.add_task(delete_file_or_directory, str(exp_del_path))
            
            if not datasheet_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Datasheet record not found in the database."
                )

            return {"message": "Datasheet deleted successfully."}

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : delete datasheet", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to delete Datasheet")
      
    @staticmethod
    @datasheet_gen_router.post('/v1/sites/1/projects/{projectId}/datasheet/download_file', response_model=None)
    async def download_file(
        projectId: str,
        request: dict,
        background_tasks: BackgroundTasks,
        client: AsyncIOMotorClient = Depends(get_db_async)
    ):
        """
        API to download a file or zip based on project ID and file path.
        """
        try:
            # Extract 'path' from the JSON object
            path = request.get('path')
            if not path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The 'path' field is required in the request body."
                )

            dsgen_handler = DatasheetGenService(db_async_client=client)
            zip_path = await dsgen_handler.download_file_async(projectId=projectId, path=path)

            # Extract the file name from the zip path
            file_name = zip_path.name

            response = FileResponse(zip_path, filename=file_name, media_type="application/zip")
            background_tasks.add_task(dsgen_handler.delete_file, str(zip_path))

            return response

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : download_file", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to download the requested file.")
        
    @staticmethod
    @datasheet_gen_router.put("/v1/sites/datasheet/update_datasheet/{datasheet_id}")
    async def update_datasheet(
        datasheet_id: str, 
        update_request: UpdateDatasheetRequest, 
        client: AsyncIOMotorClient = Depends(get_db_async)
    ):
        try:
            # Initialize the service with the DB client
            dsgen_handler = DatasheetGenService(db_async_client=client)
            
            # Update the datasheet
            updated_datasheet = await dsgen_handler.update_datasheet_async(datasheet_id, update_request)
            
            # Return the updated datasheet
            return UpdateDatasheetResponse(datasheet = updated_datasheet)
        
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to update datasheet: {str(e)}")

    @staticmethod    
    @datasheet_gen_router.post('/v1/sites/{siteId}/projects/{projectId}/set_initial_fit/{datasheet}/nominal_age/{nominal_age}', response_model= ComputeDatasheetResponse)
    async def set_initial_fit(siteId: str,
                            projectId: str,  
                            datasheet: str,
                            nominal_age:str, 
                            new_fit_params:dict,
                            client: AsyncIOMotorClient = Depends(get_db_async)) -> ComputeDatasheetResponse:
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            datasheet_detail = await dsgen_handler.set_initial_fit_async(project_id = projectId, datasheet = datasheet, nominal_age = nominal_age, new_fit_params = new_fit_params)
            datasheet = Datasheet(**datasheet_detail)
            return ComputeDatasheetResponse(datasheet=[datasheet])
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : local_fit", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to compute local fit")
            
    @staticmethod
    @datasheet_gen_router.post(
            '/v1/sites/{siteId}/projects/{projectId}/datasheet/{datasheetId}/nominal_age/{nominalAge}/selected_datasheet/{selectedDataSheetId}/save_changes',
            response_model=SaveChangesResponse
        )
    async def save_changes(
                siteId: str,
                projectId: str,
                datasheetId: int,
                nominalAge: int,
                selectedDataSheetId: str,
                save_request: SaveChangesRequest,
                client: AsyncIOMotorClient = Depends(get_db_async)
        ) -> SaveChangesResponse:
            """
            API to save changes into the database, including nominalAge and selectedDataSheetId.
            """
            try:
                # Initialize the service handler
                dsgen_handler = DatasheetGenService(db_async_client=client)
                
                # Save the changes in DB
                save_id = await dsgen_handler.save_changes_async(
                    siteId=siteId,
                    projectId=projectId,
                    datasheetId=datasheetId,
                    nominalAge=nominalAge,
                    selectedDataSheetId=selectedDataSheetId,
                    data=save_request.data
                )

                # Return a successful response
                return SaveChangesResponse(
                    status_code=200,
                    message="Changes saved successfully",
                    save_id=save_id
                )

            except Exception as e:
                # Log and raise HTTP Exception
                logger.error(f"Error saving changes: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save changes in the database."
                )

    @staticmethod
    @datasheet_gen_router.post("/v1/sites/{siteId}/projects/{projectId}/datasheet/{datasheetId}/nominal_age/{nominalAge}/tensile_sample_data", response_model= TensileSampleDataResponse)
    async def tensile_sample_data(
        siteId: str,
        projectId: str,
        datasheetId: int,
        nominalAge: int,
        data: List[dict], 
        client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            dsgen_handler = DatasheetGenService(db_async_client=client)
            csv_data = await dsgen_handler.tensile_sample_data_async(data =data)

            return TensileSampleDataResponse(csv_data = csv_data)
        
        except Exception as e:
            logging.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    

datasheet_gen_router_obj = DatasheetGenRouter()
