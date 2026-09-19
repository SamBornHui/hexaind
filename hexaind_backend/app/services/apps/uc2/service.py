import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from pandas import read_csv
from datetime import datetime
import aiofiles 
import asyncio
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
import numpy as np


FILE_LOCK = asyncio.Lock()

from app.config.env_vars import environment
from app.services.apps.uc2.schemas import *

logger = logging.getLogger(__package__)

UC2_ROOT_FOLDER_NAME = "UC2_LR_FORECAST"
UC2_ROOT_FOLDER = Path(environment.base_path / UC2_ROOT_FOLDER_NAME)

# model fanout file paths
TABLE1_FANOUT_FILE_NAME = "Model_Information.csv"

TABLE1_FANOUT_TITLE = "Model Information"

TABLE2_FANOUT_FILE_NAME = "Avg Cpk Performance.csv"

TABLE2_FANOUT_TITLE = "VPM Model Performance"

PIE_CHART_FANOUT_FILE_NAME = "Chamber-specific CpK Performance.html"

PIE_CHART_FANOUT_TITLE = "Chamber-specific Cpk Performance"

TABLE3_FANOUT_FILE_NAME = "chamberwise_simulation_fanout_report.csv"

TABLE3_FANOUT_TITLE = "Conventional vs VPM Model Performance: Chamber-wise"


# LINE_CHART_FANOUT_FILE_PREFIX = "chamberwise_comparison_fanout"

# LINE_CHART_FANOUT_TITLE = "Chamberwise Comparison"

# BAR_PLOT_FANOUT_FILE_PREFIX = "conv_vpm_comparison"

# BAR_PLOT_FANOUT_TITLE = "Conv VPM Comparison"

# Model Refresh file paths
TABLE1_REFRESH_FILE_NAME = "comparison_report.csv"

TABLE1_REFRESH_TITLE = "Latest Model vs Active Cpk Comparison"

TABLE2_REFRESH_FILE_NAME = "chamberwise_simulation_report.csv"

TABLE2_REFRESH_TITLE = "Cpk Comparison by Chambers"

BAR_CHART_REFRESH_FILE_PREFIX = "cpk_model_comparison.html"

BAR_CHART_REFRESH_TITLE = "Cpk Model Comparision"

LINE_CHART_REFRESH_FILE_PREFIX = "chamberwise_comparison_"

LINE_CHART_REFRESH_TITLE = "Chamberwise Comparision"


class UC2Service:

    def __init__(self) -> None:
        pass

    async def get_project_names(self) -> List[str]:
        """
        Fetches a list of project folder names within the UC2 directory.
        """

        try:
            return [item.name for item in UC2_ROOT_FOLDER.iterdir() if item.is_dir()]
        except Exception as e:
            logger.error(f"Error fetching project names: {e}")
            raise e

    async def get_project_metadata(self, project_name: str) -> List[Metadata]:
        """
        Fetches metadata for a given project name from its work week folders.
        """

        project_folder = UC2_ROOT_FOLDER / project_name
        project_metadata = []

        for work_week_folder in project_folder.iterdir():
            if work_week_folder.is_dir():
                metadata_file = work_week_folder / "metadata.json"
                try:
                    metadata = json.loads(metadata_file.read_text())
                    
                    # lowercase all keys
                    metadata = {k.lower(): v for k, v in metadata.items()}

                    feedforward_params = metadata.get("feedforward_params", {})
                    ucl = metadata.get("ucl", None)
                    lcl = metadata.get("lcl", None)
                    target = metadata.get("target", None)
                    
                    # get folder names inside current work week folder
                    output_column_names = [item.name for item in work_week_folder.iterdir() if item.is_dir()]
                    logger.info(f"output_column_names: {output_column_names}")

                    optimization_folders = {}
                    for output_name in output_column_names:
                        output_column_folder = work_week_folder / output_name
                        subfolders = [
                            sub.name
                            for sub in output_column_folder.iterdir()
                            if sub.is_dir()
                        ]
                        optimization_folders[output_name] = subfolders
                    
                    project_metadata.append(
                        Metadata(
                            step_name=metadata["step name"],
                            tech_node=metadata["tech node"],
                            start_date=metadata["start date"],
                            end_date=metadata["end date"],
                            interval = metadata["interval"],
                            output_column_names = output_column_names,
                            work_week_folder_name=work_week_folder.name,
                            feedforward_params=feedforward_params,
                            ucl=ucl,
                            lcl=lcl,
                            target=target,
                            optimization_folders=optimization_folders
                        )
                    )
                except FileNotFoundError:
                    logger.warning(f"Metadata file not found for {work_week_folder.name}")
                    continue
                except Exception as e:
                    logger.error(f"Error reading metadata file: {e}")
                    raise e
        
        project_metadata.sort(key=lambda x: datetime.strptime(x.start_date, "%Y-%m-%d"), reverse=True)

        return project_metadata

    async def get_project_data( 
        self, project_name: str, work_week_folder_name: str, output_column_name: str, optimization_folder: Optional[str] = None 
    ) -> UC2ProjectData:
        """
        Fetches project data from specific work week folder for a given project.
        """

        base_folder = UC2_ROOT_FOLDER / project_name / work_week_folder_name / output_column_name
        if optimization_folder:
            output_column_folder = base_folder / optimization_folder
        else:
            output_column_folder = base_folder

        project_data = UC2ProjectData(
            
            model_refresh = ModelRefreshData(table1=TableData(data={}, title=TABLE1_REFRESH_TITLE, file_path=""),
                                            table2=TableData(data={}, title=TABLE2_REFRESH_TITLE, file_path=""),
                                            bar_plot=PlotData(type=PlotType.BOX_PLOT, title=BAR_CHART_REFRESH_TITLE, file_paths=[]),
                                            line_plot=PlotData(type=PlotType.LINE_PLOT, title=LINE_CHART_REFRESH_TITLE, file_paths=[])
                                            ),
            
            model_fanout = ModelFanOutData(table1=TableData(data={}, title=TABLE1_FANOUT_TITLE, file_path=""),
                                           table2=TableData(data={}, title=TABLE2_FANOUT_TITLE, file_path=""),
                                           table3=TableData(data={}, title=TABLE3_FANOUT_TITLE, file_path=""),
                                           pie_chart=PlotData(type=PlotType.PIE_CHART, title=PIE_CHART_FANOUT_TITLE, file_paths=[]),
                                           bar_plot=None,
                                           line_plot=None
                                           ),
            chamber_plot_paths={}
        )

        try:
            for item in output_column_folder.iterdir():
                if not item.is_file():
                    continue
                
                file_path = str(item.resolve())

                '''
                file_path = str(
                    UC2_ROOT_FOLDER / project_name / work_week_folder_name / output_column_name / item.name
                )
                '''
                file_name = item.stem
                file_extension = item.suffix

                if file_extension == ".html":

                    # 1) Detect Active_{chamber_id}.html
                    if file_name.startswith("Active_"):
                        chamber_id = file_name.replace("Active_", "", 1)
                        # If we haven't seen this chamber_id yet, initialize a dict
                        if chamber_id not in project_data.chamber_plot_paths:
                            project_data.chamber_plot_paths[chamber_id] = {}
                        project_data.chamber_plot_paths[chamber_id]["Active"] = file_path

                    # 2) Detect InActive_{chamber_id}.html
                    elif file_name.startswith("InActive_"):
                        chamber_id = file_name.replace("InActive_", "", 1)
                        if chamber_id not in project_data.chamber_plot_paths:
                            project_data.chamber_plot_paths[chamber_id] = {}
                        project_data.chamber_plot_paths[chamber_id]["InActive"] = file_path


                    elif BAR_CHART_REFRESH_FILE_PREFIX in item.name:
                        project_data.model_refresh.bar_plot.file_paths.append(file_path)

                    elif LINE_CHART_REFRESH_FILE_PREFIX in item.name and "fanout" not in item.name:
                        project_data.model_refresh.line_plot.file_paths.append(file_path)
                    
                    elif PIE_CHART_FANOUT_FILE_NAME in item.name:
                        project_data.model_fanout.pie_chart.file_paths.append(file_path)

                elif file_extension == ".csv":

                    if TABLE1_FANOUT_FILE_NAME in item.name:
                        project_data.model_fanout.table1.file_path = file_path
                        project_data.model_fanout.table1.data = self.__getTablePreview(file_path)
                    
                    elif TABLE2_FANOUT_FILE_NAME in item.name:
                        project_data.model_fanout.table2.file_path = file_path
                        project_data.model_fanout.table2.data = self.__getTablePreview(file_path)
                    
                    elif TABLE3_FANOUT_FILE_NAME in item.name:
                        project_data.model_fanout.table3.file_path = file_path
                        project_data.model_fanout.table3.data = self.__getTablePreview(file_path)
                    
                    elif TABLE1_REFRESH_FILE_NAME in item.name:
                        project_data.model_refresh.table1.file_path = file_path
                        project_data.model_refresh.table1.data = self.__getTablePreview(file_path)
                    
                    elif TABLE2_REFRESH_FILE_NAME in item.name:
                        project_data.model_refresh.table2.file_path = file_path
                        project_data.model_refresh.table2.data = self.__getTablePreview(file_path)

        except Exception as e:
            logger.error(f"Error fetching project data: {e}")
            raise e

        return project_data
    
    async def get_unique_chamber_count(self, project_name: str, work_week_folder_name: str, output_column_name: str, file_name: str, column_name: str, optimization_folder: Optional[str] = None) -> int:
        """
        Fetches the unique chamber count from a specified file and column.
        """
        output_column_folder = UC2_ROOT_FOLDER / project_name / work_week_folder_name / output_column_name
        if optimization_folder:
            output_column_folder = output_column_folder / optimization_folder
        file_path = output_column_folder / file_name

        try:
            logger.info(f"Looking for file at: {file_path}")
            table = pd.read_csv(file_path)

            logger.info(f"Columns in CSV: {table.columns.tolist()}")

            if table.empty:
                logger.warning("The DataFrame is empty.")
                return 0

            if column_name not in table.columns:
                logger.warning(f"Column {column_name} not found in DataFrame.")
                return 0

            unique_chamber_count = table[column_name].nunique()

            logger.info(f"Unique chamber count: {unique_chamber_count}")
            return unique_chamber_count

        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return 0  
        except Exception as e:
            logger.error(f"Error fetching unique chamber count: {e}")
            raise e


    async def fetch_project_data_with_chamber_count(self, project_name: str, work_week_folder_name: str, output_column_name: str, optimization_folder: Optional[str] = None) -> UC2ProjectData:
        project_data = await self.get_project_data(project_name, work_week_folder_name, output_column_name,optimization_folder)


        project_data.unique_chamber_count_Fanout = await self.get_unique_chamber_count(
            project_name, work_week_folder_name, output_column_name, TABLE3_FANOUT_FILE_NAME, "Chamber Id", optimization_folder
        )
        
        project_data.unique_chamber_count_Refresh = await self.get_unique_chamber_count(
            project_name, work_week_folder_name, output_column_name, TABLE2_REFRESH_FILE_NAME, "Chamber Id", optimization_folder
        )

        return project_data
    

    async def update_status(self, project_name: str, work_week_folder_name: str, output_column_name: str, interval: int, status: str, chamber_id: str,optimization_folder: Optional[str] = None) -> None:
        # Determine output column folder path
        output_column_folder = UC2_ROOT_FOLDER / project_name / work_week_folder_name / output_column_name
        if optimization_folder:
            output_column_folder = output_column_folder / optimization_folder
        # Define the path for the table file
        table_file_path = output_column_folder / TABLE3_FANOUT_FILE_NAME
        
        # Check if table file exists
        if not table_file_path.exists():
            raise FileNotFoundError(f"Table file not found: {table_file_path}")
        
        # Read the table from the CSV file
        table = pd.read_csv(table_file_path)
        
        # If the table is empty, log a warning and return
        if table.empty:
            logger.warning(f"The table in {TABLE3_FANOUT_FILE_NAME} is empty.")
            return

        # Check for required columns in the table
        required_columns = ["Status", "Chamber Id", "CONV Model"]
        missing_columns = [col for col in required_columns if col not in table.columns]
        if missing_columns:
            raise KeyError(f"Missing columns in {TABLE3_FANOUT_FILE_NAME}: {missing_columns}")
        
        '''
        # Filter the table for the provided chamber_id
        table = table[table["Chamber Id"] == chamber_id]
        if table.empty:
            logger.warning(f"No entries found for Chamber Id: {chamber_id}")
            return
        '''

         # Filter the table for the provided chamber_id
        table_filtered = table[table["Chamber Id"] == chamber_id]
        if table_filtered.empty:
            logger.warning(f"No entries found for Chamber Id: {chamber_id}")
            return

        # Update the status based on the input
        for idx, row in table_filtered.iterrows():
            current_status = row["Status"]
            if current_status != status:
                # Update the status
                table.loc[table["Chamber Id"] == chamber_id, "Status"] = status

                # Optionally log the change
                logger.info(f"Status for Chamber Id {chamber_id} updated from '{current_status}' to '{status}' in TABLE3_FANOUT_FILE_NAME.")

        # Save the updated table back to the file
        table.to_csv(table_file_path, index=False)

        # Print completion message
        print(f"Status updated for {status} in {TABLE3_FANOUT_FILE_NAME} for Chamber Id: {chamber_id}.")


        # Extract work week information from work_week_folder_name
        year_prefix = work_week_folder_name[1:5]  
        week_number_str = work_week_folder_name[5:]  

        # Validate the format of work_week_folder_name
        if not year_prefix.isdigit() or not week_number_str.startswith("WW") or not week_number_str[2:].isdigit():
            raise HTTPException(status_code=400, detail="Invalid work_week_folder_name format. Expected format: Y<YYYY>WW<WW>")

        # Calculate the current and next work week
        week_number = int(week_number_str[2:])
        year = int(year_prefix)
        total_weeks = week_number + interval
        next_year = year + (total_weeks - 1) // 52
        next_week_number = (total_weeks - 1) % 52 + 1

        # Create the folder paths for current and next work week
        current_folder = UC2_ROOT_FOLDER / project_name / f"Y{year}WW{week_number:02d}"
        next_folder = UC2_ROOT_FOLDER / project_name / f"Y{next_year}WW{next_week_number:02d}"

        # Create the output column folder and next work week folder if they do not exist
        current_folder.mkdir(parents=True, exist_ok=True)
        next_folder.mkdir(parents=True, exist_ok=True)

        # Define status tracking CSV file names for current and next work week
        status_tracking_file_name = f"WW{week_number:02d}_status_tracking.csv"
        
        # Save the status tracking CSV files inside the same output column folder   
        status_tracking_file_path_current = output_column_folder / status_tracking_file_name
        if optimization_folder:
            status_tracking_file_path_next = (UC2_ROOT_FOLDER / project_name / f"Y{next_year}WW{next_week_number:02d}" / output_column_name / optimization_folder / status_tracking_file_name)
        else:
            status_tracking_file_path_next = (UC2_ROOT_FOLDER / project_name / f"Y{next_year}WW{next_week_number:02d}" / output_column_name / status_tracking_file_name)

        #status_tracking_file_path_next = (UC2_ROOT_FOLDER / project_name / f"Y{next_year}WW{next_week_number:02d}" / output_column_name / optimization_folder / status_tracking_file_name)


        # Function to create files if they do not exist
        async def create_file_if_not_exists(file_path: Path):
            if not file_path.exists():
                async with aiofiles.open(file_path, mode='w') as f:
                    df = pd.DataFrame(columns=["Chamber Id", "Status", "CONV Model", "Date"])
                    await f.write(df.to_csv(index=False))

        # Create the status tracking files if they don't exist
        await asyncio.gather(
            create_file_if_not_exists(status_tracking_file_path_current),
            create_file_if_not_exists(status_tracking_file_path_next)
        )

        # Read the status tracking files (current and next)
        status_tracking_current = pd.read_csv(status_tracking_file_path_current)
        status_tracking_next = pd.read_csv(status_tracking_file_path_next)

        # Update the status tracking files based on the provided status
        for _, row in table_filtered.iterrows():
            chamber_id = str(row["Chamber Id"])
            conv_model = row["CONV Model"]
            
            condition_current = (
                (status_tracking_current["Chamber Id"] == chamber_id) &
                (status_tracking_current["CONV Model"] == conv_model)
            )
            condition_next = (
                (status_tracking_next["Chamber Id"] == chamber_id) &
                (status_tracking_next["CONV Model"] == conv_model)
            )
            
            # If the status is "Active", add the entry if not present
            if status == "Active":
                if not condition_current.any():
                    new_row = {
                        "Chamber Id": chamber_id,
                        "Status": "Active",
                        "CONV Model": conv_model,
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    status_tracking_current = pd.concat([status_tracking_current, pd.DataFrame([new_row])], ignore_index=True)

                if not condition_next.any():
                    new_row = {
                        "Chamber Id": chamber_id,
                        "Status": "Active",
                        "CONV Model": conv_model,
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    status_tracking_next = pd.concat([status_tracking_next, pd.DataFrame([new_row])], ignore_index=True)

            # If the status is "InActive", remove the entry
            elif status == "InActive":
                status_tracking_current = status_tracking_current[~condition_current]
                status_tracking_next = status_tracking_next[~condition_next]

        # Save the updated status tracking files
        async def save_file(file_path: Path, df: pd.DataFrame):
            async with FILE_LOCK:  # Ensure only one task writes to the file at a time
                try:
                    async with aiofiles.open(file_path, mode='w') as f:
                        await f.write(df.to_csv(index=False))
                except Exception as e:
                    logger.error(f"Error while saving file {file_path}: {e}")
                    raise HTTPException(status_code=500, detail="Error saving file")

        await asyncio.gather(
            save_file(status_tracking_file_path_current, status_tracking_current),
            save_file(status_tracking_file_path_next, status_tracking_next)
        )

        # Print completion message
        print(f"Status updated for {status} in work week folders {work_week_folder_name} and {next_folder}.")
    
    '''
    async def fetch_chamber_plot(self,project_name: str,work_week_folder_name: str,output_column_name: str,status: str,
        chamber_id: str) -> HTMLResponse:

        output_column_folder = (UC2_ROOT_FOLDER/ project_name/ work_week_folder_name/ output_column_name)

        plot_file_name = f"{status}_{chamber_id}.html"
        plot_file_path = output_column_folder / plot_file_name

        if not plot_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No {status} plot file found for Chamber Id '{chamber_id}' "
                    f"in project '{project_name}', work week '{work_week_folder_name}'. "
                    f"Expected path: {plot_file_path}"
                )
            )
        async with aiofiles.open(plot_file_path, mode="r", encoding="utf-8") as f:
            html_content = await f.read()
        return HTMLResponse(content=html_content, status_code=200)
    '''

    def __getTablePreview(self, file_path: str) -> TablePreview:
        """
        Fetches a preview of the data in a CSV file.
        """

        table = read_csv(file_path)
        table.fillna("N/A", inplace=True)
        table_columns = table.columns.tolist()
        table_data = table.values.tolist()

        return TablePreview(
            column_names=table_columns,
            data=table_data,
            total_rows=len(table),
        ).model_dump()

    async def get_spc_data_csv(self,project_name: str,work_week_folder_name: str,output_column_name: str,
        feedforward_params: Dict[str, Any],ucl: Optional[int],lcl: Optional[int],target: Optional[int],
        chamber_ids: Optional[List[str]] = None,filter_by_feedforward: bool = False,optimization_folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reads data_spc_charts.csv from the specified folder, filters by chamber_ids,
        optionally filters by feedforward columns, and returns data grouped by chamber.
        """
        
        base_folder = UC2_ROOT_FOLDER / project_name / work_week_folder_name / output_column_name
        if optimization_folder:
            base_folder = base_folder / optimization_folder 
        csv_path = base_folder / "data_spc_charts.csv"

        if not csv_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"data_spc_charts.csv not found at {csv_path}"
            )

        # Read the CSV
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading data_spc_charts.csv: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Cannot read data_spc_charts.csv: {str(e)}"
            )

        df.columns = [col.lower() for col in df.columns]

        out_col = output_column_name.lower()

        if "run_complete_datetime".lower() not in df.columns:
            raise HTTPException(
                status_code=422,
                detail="Column 'RUN_COMPLETE_DATETIME' not found (expected as lowercase 'run_complete_datetime')."
            )
        if "chamber" not in df.columns:
            raise HTTPException(
                status_code=422,
                detail="Column 'CHAMBER' not found (expected as lowercase 'chamber')."
            )
        if out_col not in df.columns:
            raise HTTPException(
                status_code=422,
                detail=f"Column '{output_column_name}' not found in data (checked as lowercase '{out_col}')."
            )
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        # Filter by chamber if chamber_ids provided
        if chamber_ids:
            df = df[df["chamber"].astype(str).isin(chamber_ids)]

        # If filter_by_feedforward, drop rows with NaN in any feedforward param
        if filter_by_feedforward and feedforward_params:
            ff_cols = [k.lower() for k in feedforward_params.keys() if k.lower() in df.columns]
            if ff_cols:
                df.dropna(subset=ff_cols, how="any", inplace=True)
        
        df.dropna(subset=[out_col], how="any", inplace=True)

        # If there's no data left, return an empty chambers object
        if df.empty:
            return {
                "ucl": ucl,
                "lcl": lcl,
                "target": target,
                "chambers": {}
            }

        # Group by "chamber" and build the response
        chambers_data = {}
        for chamber_id, group_df in df.groupby("chamber"):
            # Convert columns to lists
            runcomplete_list = group_df["run_complete_datetime"].tolist()
            output_list = group_df[out_col].tolist()

            chambers_data[chamber_id] = {
                "runcomplete_datetime": runcomplete_list,
                "output_values": output_list
            }

        return {
            "ucl": ucl,
            "lcl": lcl,
            "target": target,
            "chambers": chambers_data
        }

    
    async def get_siso_plots(self,project_name:str,work_week_folder_name:str,output_column_name:str,optimization_folder:str,subfolder:str)->List[str]:
        """
        Returns a list of .html file paths:
        """

        folder_path = (
            UC2_ROOT_FOLDER /
            project_name /
            work_week_folder_name /
            output_column_name /
            optimization_folder /
            subfolder
        )

        if not folder_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Folder not found: {folder_path}"
            )

        # Collect all .html files from that folder
        html_files = []
        for item in folder_path.iterdir():
            if item.is_file() and item.suffix.lower() == ".html":
                html_files.append(str(item))

        return html_files

