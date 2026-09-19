from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple, Mapping, Any
from fastapi import status, HTTPException
from datetime import datetime, timezone
from yarl import URL
import json
from pathlib import Path

from app.services.apps.datasheet_gen.dsgen_controller.calculate_local_fit import calculate_local_fit
from .schemas import *
from app.services.apps.datasheet_gen.dao import DatasheetGeneratorDao
from app.services.apps.datasheet_gen.dsgen_controller.datasheet_workflow import *
from app.services.apps.datasheet_gen.dsgen_controller.export_datasheet import *
from app.services.apps.datasheet_gen.dsgen_controller.import_datasheet import *
# from .dao import ConnectorDao
import logging
import sys
logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

RESCALE_URL = URL('https://platform.rescale.com/api/v2')

class DatasheetGenService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        self.datasheets_dao = DatasheetGeneratorDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

    async def compute_datasheet_async(self,projectId:str, ds:int , nominal_age:int,reset:bool) -> str:
        datasheet_detail = run_workflow(projectId,ds,nominal_age,reset)      
        return datasheet_detail
 
    async def export_datasheet_async(self, metadata:dict, projectId:str, ds:str, nominal_age:str) -> str:

        # export_path = export_datasheet_workflow(metadata ,ds,nominal_age)         
        export_path = export_combined_datasheet_workflow(metadata,projectId,ds,nominal_age)         
        datasheet_path = export_path
        return datasheet_path
    
    async def export_new_fit_datasheet_async(self, metadata:dict, projectId:str ,ds:str , nominal_age:str) -> str:        
        export_path = export_new_datasheet_workflow(metadata,projectId,ds,nominal_age)         
        datasheet_path = export_path
        return datasheet_path

    async def save_metadata_async(self, metadata:dict, projectId:str ,ds:str) -> str:        
        metadata_path = save_metadata_async(metadata,projectId,ds)         
        return metadata_path

    async def read_csv_async(self, data:ReadCsv) -> str:
        
        file_name = os.path.basename(data.file_path)
        df = read_csv(data.project_id, data.datasheet,data.nominal_age, file_name)
        csv_data = json.loads(df.to_json(orient='records'))
                       
        return csv_data
    
    async def get_datasheets_async(self, projectId:str) -> str:
        # datasheets = get_datasheets(projectId,data.base_path)
        datasheets = await self.datasheets_dao.get_datasheets_by_project_id(projectId)
        return datasheets
    
    async def get_datasheets_details_async(self, projectId:str, data: BasePath) -> str:
        datasheets = get_datasheets_details(projectId,data.base_path)
        datasheets_details =[]
        if data.base_path == 'base':
            for datasheet in datasheets:
                datasheet = await self.datasheets_dao.get_datasheet_params(projectId, datasheet)
                datasheets_details.append(datasheet)
        else: 
            datasheets_details = datasheets
        return datasheets_details

    async def correct_tensile_async(self, data:CorrectTensile) -> str:
        try:
            
            df_ten_data = read_csv(data.project_id, data.datasheet, data.nominal_age , 'tensile_plot_data.csv')
            combined_results_list = read_csv(data.project_id, data.datasheet,  data.nominal_age , 'tensile_combined_results_list.csv')
            combined_results_list_initial = read_csv(data.project_id, data.datasheet,  data.nominal_age , 'pdf_tensile_combined_results_list.csv')
            recompute_Rp02 = data.recompute_Rp02
            corrected_params = data.corrected_tensile_results
            df_tensile_computed = correct_tensile(data.project_id,data.selected_sample,data.s_min,data.s_max,df_ten_data,combined_results_list,combined_results_list_initial,recompute_Rp02,corrected_params)
            
            correct_data = df_tensile_computed              
            return correct_data
        except Exception as e:
            logger.error(f"Failed with exception {e} : correct_tensile", exc_info=True)
            
    async def reset_tensile_async(self, data:CorrectTensile) -> str:
        try:
            
            df_ten_data = read_csv(data.project_id, data.datasheet, data.nominal_age , 'tensile_plot_data.csv')
            output_directory = os.path.join(EXPORT_PATH, str(data.project_id), str(data.datasheet), str(data.nominal_age))
            csv_file_path = os.path.join(output_directory, 'initial_tensile_combined_results_list.csv')
            corrected_params = {}
            if os.path.exists(csv_file_path):
                initial_fit_combined_results = read_csv(data.project_id, data.datasheet,  data.nominal_age , 'initial_tensile_combined_results_list.csv')
                df_all_sample_results = pd.DataFrame(initial_fit_combined_results)
                tensile_params = df_all_sample_results[df_all_sample_results['file_name'].astype(str).str.contains(data.selected_sample)].copy()
                corrected_params = tensile_params.to_dict(orient="records")  
                if corrected_params:
                    corrected_params = corrected_params[0]
                
            combined_results_list = read_csv(data.project_id, data.datasheet,  data.nominal_age , 'tensile_combined_results_list.csv')
            combined_results_list_initial = read_csv(data.project_id, data.datasheet,  data.nominal_age , 'pdf_tensile_combined_results_list.csv')

            recompute_Rp02 = False
            df_tensile_computed = correct_tensile(data.project_id,data.selected_sample,data.s_min,data.s_max,df_ten_data,combined_results_list,combined_results_list_initial,recompute_Rp02,corrected_params)
            correct_data = df_tensile_computed              
            return correct_data
        except Exception as e:
            logger.error(f"Failed with exception {e} : correct_tensile", exc_info=True)

    async def comparison_tensile_async(self, data:CompareTensile) -> str:
        try:
            
            output_directory = os.path.join(EXPORT_PATH, str(data.project_id), str(data.datasheet), str(data.nominal_age))
            csv_file_path = os.path.join(output_directory, 'initial_tensile_combined_results_list.csv')
            tensile_params = {}
            initial_fit_tensile = []
            if os.path.exists(csv_file_path):
                initial_fit_tensile_sample = read_csv(data.project_id, data.datasheet,  data.nominal_age , 'initial_tensile_combined_results_list.csv')
                initial_fit_tensile = initial_fit_tensile_sample.to_dict(orient="records")
            new_fit_tensile = read_csv(data.project_id, data.datasheet,  data.nominal_age , 'tensile_combined_results_list.csv')
            tensile_params = {
                'initial_fit_tensile': initial_fit_tensile,
                'new_fit_tensile': new_fit_tensile.to_dict(orient="records")
            }
                        
            return tensile_params
        except Exception as e:
            logger.error(f"Failed with exception {e} : compare_tensile_params", exc_info=True)

    async def preview_file_async(self, file_details:FileDetails) ->str:

        pdf_file_path = Path(file_details.file_path)
        if not pdf_file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file path provided."
            )

        # Your logic to generate file_name (extracting it from the path) and file_url
        file_name = pdf_file_path.name
        file_url = f"pdf_files/{file_details.project_id}/{file_name}"  # Update with the actual base URL
        return file_name,file_url

    async def local_fit_async(self, adjusted_params:AdjustedParams) -> str:
        local_fit = calculate_local_fit(adjusted_params)               
        return local_fit

    async def set_initial_fit_async(self, project_id:str, datasheet:str, nominal_age:str, new_fit_params) -> str:
        datasheet_detail = set_initial_fit(project_id, datasheet, nominal_age, new_fit_params)               
        return datasheet_detail
    
    async def save_flc_ascii_async(self, projectId, userId, flc_params:FlcParams) -> str:
        flc_ascii = save_flc_ascii(projectId, userId, flc_params)
        datasheet = await self.datasheets_dao.get_datasheet_for_converter(projectId, flc_ascii["datasheet"])
        if datasheet:
            datasheet_id = datasheet['id']
            substring_to_remove = f"/{flc_ascii['datasheet']}/FLC/{flc_ascii['datasheet']}_FLC_{flc_ascii['nominal_age']}"

            datasheet["flc_files"] = [file for file in datasheet["flc_files"] if substring_to_remove not in file]
            datasheet["flc_files"].extend(flc_ascii["flc_files"])

            update_data= {
                "flc_files":  datasheet["flc_files"],
            }
            updated_datasheet = await self.datasheets_dao.update_datasheet_record_async(datasheet_id, update_data)

        else:
            # Insert a new datasheet record if no datasheet exists
            datasheet= await self.insert_datasheet(flc_ascii)
        return flc_ascii
    
    async def save_tensile_ascii_async(self, projectId, userId, tensile_params:TensileParams) -> str:
        tensile_ascii = save_tensile_ascii(projectId, userId, tensile_params)
        datasheet = await self.datasheets_dao.get_datasheet_for_converter(projectId, tensile_ascii["datasheet"])
        if datasheet:
            datasheet_id = datasheet['id']
            if tensile_ascii["tensile_age"] not in datasheet.get("tensile_ages", []):
                datasheet["tensile_ages"].append(tensile_ascii["tensile_age"])
            substring_to_remove = f"{tensile_ascii['datasheet']}/Tensile/{tensile_ascii['tensile_age']} days/"
            datasheet["tensile_files"] = [file for file in datasheet["tensile_files"] if substring_to_remove not in file]
            
            datasheet["tensile_files"].extend(tensile_ascii["tensile_files"])

            update_data= {
                "tensile_files":  datasheet["tensile_files"],
                "tensile_ages": datasheet["tensile_ages"]
            }
            updated_datasheet = await self.datasheets_dao.update_datasheet_record_async(datasheet_id, update_data)

        else:
            # Insert a new datasheet record if no datasheet exists
            datasheet= await self.insert_datasheet( tensile_ascii)

        return tensile_ascii
    
    async def insert_datasheet(self, files_ascii):
        datasheet_object = Datasheets(
            project_id = files_ascii.get('project_id', None),
            user_id = files_ascii.get('user_id', None),
            datasheet = str(files_ascii.get('datasheet', None)),
            tensile_ages = [files_ascii.get('tensile_age', None)] if files_ascii.get('tensile_age') is not None else [],
            bulge_ages = [],  # Default as empty list
            datasheet_path = files_ascii.get('datasheet_path', None),
            tensile_files = files_ascii.get('tensile_files', []),
            bulge_files = [],  # Default as empty list
            flc_files = files_ascii.get('flc_files', []), # Default as empty list
            locked=False,  # Default lock status
            created_at = datetime.now(timezone.utc)
        )
        datasheet = await self.datasheets_dao.insert_datasheet_record_async(datasheet=datasheet_object)
        return datasheet
    
    async def tensile_file_convert_async(self, tensile_params:TensileParams) -> str:
        tensile_data = tensile_file_convert(tensile_params)  
        return tensile_data
    
    async def ingest_data_async(self, projectId:str, userId:str, files: list[UploadFile], filePaths: list[str]):
        ingestion_results = await save_datasheet(projectId, userId, files, filePaths )
        datasheet = Datasheets(**ingestion_results)
        datasheet = await self.datasheets_dao.upsert_datasheet_record_async(datasheet=datasheet)
        return datasheet

    async def upload_file_to_convert_async(self, projectId:str, fitFile: UploadFile, rawFile: UploadFile, metadataFile: str):
        convertor_results = convert_file(projectId, fitFile, rawFile, metadataFile )
        return convertor_results

    async def upload_tensile_file_to_convert_async(self, projectId:str, tensileFile: UploadFile):
        convertor_results = convert_tensile_file(projectId, tensileFile)
        return convertor_results

    async def download_results_async(self, projectId:str, datasheet: str):
        zip_path = Path(EXPORT_PATH, str(projectId), str(datasheet),'results.zip')
        folder_to_zip = Path(EXPORT_PATH, str(projectId), str(datasheet),'results')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_to_zip):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, folder_to_zip))

    async def download_ascii_async(self, projectId:str, datasheet: str, nominal_age:str, file_type:str):
        file_name = f"{datasheet}_{file_type}_{nominal_age}_ASCII_export.zip"
        nominal_age_days = f"{nominal_age} days"
        
        # folder_to_zip = Path(IMPORT_PATH, str(datasheet),str(file_type))
        zip_path = Path(IMPORT_PATH,str(projectId), str(datasheet),str(file_type),file_name)
        
        if file_type == 'Tensile':    
            folder_to_zip = Path(IMPORT_PATH, str(projectId), str(datasheet),str(file_type),str(nominal_age_days))
        else:
            # zip_path = Path(IMPORT_PATH, str(datasheet),str(file_type),file_name)
            folder_to_zip = Path(IMPORT_PATH, str(projectId), str(datasheet),str(file_type))
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_to_zip):
                for file in files:
                    if file.endswith('.tsv'):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, folder_to_zip))
        
    async def delete_file(self,file_path: str):
        os.remove(file_path)

    def delete_file_or_directory(self,path: str):
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            else:
                return {"error": "Path does not exist"}

            return {"success": True}
        except PermissionError as e:
            logger.error(f"PermissionError: {e}", exc_info=True)
            return {"error": "Permission denied"}
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return {"error": str(e)}
        
    async def download_file_async(self, projectId: str, path: str) -> Path:
            """
            Asynchronous helper method to prepare the file or zip based on the input path.
            """
            # Split the path into its parts
            path_parts = path.split('/')
            zip_file_name = f"{path_parts[-1]}.zip"  # The zip file name is the last part of the path

            # Target folder is the full path to the last part of the path
            folder_to_zip = Path(IMPORT_PATH, str(projectId), *path_parts)
            zip_path = Path(IMPORT_PATH, str(projectId), zip_file_name)  # Save zip outside the folder

            # Validate if the folder exists
            if not folder_to_zip.exists() or not folder_to_zip.is_dir():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Requested folder does not exist."
                )

            # Create the zip file if it doesn't exist
            if not zip_path.exists():
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(folder_to_zip):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, os.path.relpath(file_path, folder_to_zip))  # Only add files inside the folder

            return zip_path
    
    async def update_datasheet_async(self, datasheet_id: str, update_request: UpdateDatasheetRequest) -> dict:
        # Convert the Pydantic model to a dictionary, filtering out None values
        update_data = update_request.dict(exclude_unset=True)
        
        # Call the DAO method to update the datasheet
        updated_datasheet = await self.datasheets_dao.update_datasheet_record_async(datasheet_id, update_data)
        
        # Return the updated datasheet
        return updated_datasheet
    
        
    async def save_changes_async(
                self, 
                siteId: str, 
                projectId: str, 
                datasheetId: int, 
                nominalAge: int, 
                selectedDataSheetId: str, 
                data: SaveChangesRequest
            ) -> str:
            """
            Save changes into the datasheet_params collection.
            """
            try:
                # Prepare payload with metadata
                save_payload = {
                    "site_id": siteId,
                    "project_id": projectId,
                    "datasheet": datasheetId,
                    "nominal_age": nominalAge,
                    "datasheet_id": selectedDataSheetId,
                    "data": data,
                    "updated_at": datetime.utcnow()
                }

                # Perform upsert operation in DAO
                save_id = await self.datasheets_dao.upsert_datasheet_params(
                    projectId=projectId, 
                    datasheetId=datasheetId, 
                    nominalAge=nominalAge, 
                    selectedDataSheetId=selectedDataSheetId,
                    save_payload=save_payload
                )

                return save_id

            except Exception as e:
                raise Exception(f"Failed to save changes in service layer: {str(e)}")
        
    async def delete_datasheet_record(self, project_id: str, datasheet_name: str) -> bool:
        if '/' in datasheet_name:
            # path_parts = datasheet_name.split('/')
            
            base_datasheet = datasheet_name.split('/')[0]
            datasheet_result = await self.datasheets_dao.get_datasheet_for_converter(project_id, base_datasheet)
            datasheet_id = datasheet_result['id']
            if datasheet_result:
                # Determine key names based on subfolder
                path_parts = datasheet_name.split('/')
                subfolder = path_parts[1] if len(path_parts) > 1 else None

                if subfolder == "Tensile":
                    files_key = "tensile_files"
                    ages_key = "tensile_ages"
                elif subfolder == "Bulge":
                    files_key = "bulge_files"
                    ages_key = "bulge_ages"
                elif subfolder == "FLC":
                    files_key = "flc_files"
                    ages_key = ""
                else:
                    return False

                files = datasheet_result.get(files_key, [])
                ages = datasheet_result.get(ages_key, [])

                if len(path_parts) == 3:
                    # If a specific age is provided, update the files and ages
                    age = path_parts[2].split(' ')[0]

                    # Remove files matching the substring pattern
                    substring_to_remove = f"{base_datasheet}/{subfolder}/{age} days/"
                    files = [file for file in files if substring_to_remove not in file]

                    if int(age) in ages:
                        ages.remove(int(age))
                    filter = {"project_id": project_id, "datasheet": int(base_datasheet), "nominal_age":int(age)}
                    

                elif len(path_parts) == 2:
                    # If path is till subfolder, clear related keys
                    files = []
                    ages = []
                    filter = {"project_id": project_id, "datasheet": int(base_datasheet)}

                await self.datasheets_dao.delete_datasheet_params(filter)
                # Save the updated record back to the database
                if  subfolder == "FLC":
                    updated_record = {
                        files_key: files,
                    }
                else :
                    updated_record = {
                        files_key: files,
                        ages_key: ages
                    }
                await self.datasheets_dao.update_datasheet_record_async(datasheet_id, updated_record)

                return True
            else:
                return False
        else:
            
            filter = {"project_id": project_id, "datasheet": int(datasheet_name)}
            await self.datasheets_dao.delete_datasheet_params_many(filter)
            return await self.datasheets_dao.delete_datasheet(project_id, datasheet_name)
        
    def calculate_stats(self, group):
        stats = {}
        for column in group.columns:
            if column not in ['file_name', 'datasheet', 'nominal_age', 'load_direction']:
                stats[column] = {
                "count": int(group[column].count()), 
                "min": float(group[column].min()),      
                "max": float(group[column].max()),      
                "std": float(group[column].std()) if len(group) > 1 else 0.0,       
                "mean": float(group[column].mean())     
            }
            
        return stats   
     
    async def tensile_sample_data_async(self, data:List[dict]) -> str:
        try:
            
            selected_columns = ['nominal_age', 'load_direction', 'Rp02', 'Rm', 'Ag', 'A80', 'n4_6', 'n10_20', 'r8_12']
        
            com_df_data = pd.DataFrame(data)

            grouped = com_df_data.groupby('load_direction')  
            tensile_stats = {}
            for name, group in grouped:
                tensile_stats[str(name)] = self.calculate_stats(group)

            com_df_data = com_df_data[selected_columns]
            df_tensile_results = get_tensile_results(com_df_data)
            
            df_tensile_results = df_tensile_results.reset_index()
            df_tensile_results.columns = ['Aging (days)', 'Test direction','Rp02', 'Rm', 'Ag', 'A80', 'n4_6', 'n10_20', 'r8_12'] + list(df_tensile_results.columns[9:])
            
            tensile_results = json.loads(df_tensile_results.to_json(orient='records'))
            csv_data= {
                'tensile_results':tensile_results,
                'tensile_stats':tensile_stats
            }
            
            return csv_data
        
        except Exception as e:
            logging.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )





