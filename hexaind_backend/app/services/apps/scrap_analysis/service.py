import os
import io
import sys
import json
import shutil
import aiofiles
import asyncio
import logging
import pandas as pd
from bson import ObjectId
from datetime import datetime, timezone
from pymongo import MongoClient
from typing import List, Tuple, Dict, Union
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict
from openpyxl import load_workbook

from .dao import SAMDao
from .schemas import (
    SAMUseCase,
    SAMViz,
    SAMVisualization,
    SAMCustomInformation,
    Scenarios_INFO,
    ScenarioDetail,
    GetLimitsResponse,
)
from .sam2024.optimization import solve, alloy_bars_interactive, prime_bars_interactive
from .sam2024 import read_input as read
from .sam2024.utility import read_config

from app.config.env_vars import environment as env
from app.services.data.assets.datasets.schemas import (
    Dataset,
    AccessMode,
)
from app.services.admin.authentication.service import ServerBasedRoleNames
from app.services.data.assets.datasets.service import (
    User,
    DatasetsService,
)

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class SAMService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:  # type: ignore
        logger.debug("Initializing ScrapAnalysisService")
        self.sam_dao = SAMDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.UNIT = ""
        self.MG_BURNOFF = 0.0
        self.EXTERNAL_SCRAP_SOURCES = ""
        self.OPTIMIZE_COST = False
        self.OPTIMIZE_CASTING = False
        self.MOLTEN_MINIMUM = 0.0

    async def get_baseline_files(
        self, site_id, project_id, search_term, page_number, page_limit
    ) -> Tuple[List[Dataset], int]:
        """
        fetch baseline files including uploaded and generated result files by users
        Args:
            site_id (str): Site ID.
            project_id (str): Project ID.
            search_term (str): Search term.
            page_number (int): Page number.
            page_limit (int): Page limit.
        Returns:
            Tuple[List[Dataset], int]: List of datasets and count.
        """

        try:
            logger.info("inside get_baseline_files method.")
            baselines_datasets, doc_count = await self.sam_dao.get_baselines_async(
                site_id=site_id,
                project_id=project_id,
                search_term=search_term,
            )
            return (baselines_datasets, doc_count)

        except Exception as e:
            logger.error(f"Error fetching baseline files: {e}")
            raise e

    # async def list_limit_data(
    #     self, project_id: str, file_path: str
    # ) -> GetLimitsResponse:
    #     """
    #     format Limits sheet data from baseline file to display in the frontend
    #     Args:
    #         project_id (str): Project ID.
    #         file_path (str): File path.
    #     Returns:
    #         GetLimitsResponse: Limits data.
    #     """
    #     try:
    #         logger.info("inside list_limit_data method.")
    #         df = pd.read_excel(file_path, sheet_name="Limits")
    #         limits = df.iloc[:, :2].to_dict("records") # Plant, Alloy data from Limits sheet in the baseline file
    #         demands = df.columns[2:].tolist()

    #         return GetLimitsResponse(limits=limits, demands=demands, ,message="success")
    #     except Exception as e:
    #         logger.error(f"Error formatting Limits sheet data: {e}", exc_info=True)
    #         return GetLimitsResponse(limits=[], demands=[], message=str(e))

    async def list_limit_data(
        self, project_id: str, file_path: str
    ) -> GetLimitsResponse:
        """
        Formats the 'Limits' sheet data from the baseline file for frontend display.

        Args:
            project_id (str): Project ID.
            file_path (str): File path.

        Returns:
            GetLimitsResponse: Limits data.
        """
        try:
            logger.info("Inside list_limit_data method.")

            # Run the blocking read_excel() in an async-friendly way
            df = await asyncio.to_thread(pd.read_excel, file_path, sheet_name="Limits")

            # Convert the DataFrame to a list of dictionaries
            limits = df.fillna(1).to_dict("records")

            # Extract demand column names
            demands = df.columns[2:].tolist()

            logger.info("Limits data formatted successfully.")
            return GetLimitsResponse(limits=limits, demands=demands, message="success")

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}", exc_info=True)
            return GetLimitsResponse(limits=[], demands=[], message="File not found")

        except pd.errors.ParserError:
            logger.error(f"Error parsing Excel file: {file_path}", exc_info=True)
            return GetLimitsResponse(
                limits=[], demands=[], message="Error parsing file"
            )

        except Exception as e:
            logger.error(
                f"Unexpected error formatting Limits sheet data: {e}", exc_info=True
            )
            return GetLimitsResponse(limits=[], demands=[], message=str(e))

    async def format_data(
        self, df: pd.DataFrame, baseline_cols: List[str]
    ) -> Tuple[List, List, dict]:
        """
        format baseline data
        Args:
            df (pd.DataFrame): Dataframe.
            baseline_cols (List): List of baseline columns.
        Returns:
            Tuple[List, List, dict]: List of scraps, sources and formatted data.
        """

        logger.info("inside format_baseline_data method.")
        df["Alloy"] = df["Alloy"].astype(str)
        # Initialize a defaultdict for storing the scrap data
        formatted_data = defaultdict(dict)
        scraps = list()
        sources = list()
        # Process scrap sheet data
        for _, row in df.iterrows():

            # Extract the values from the row
            row_data = row[baseline_cols].to_dict()
            plant = row_data.pop("Plant")
            alloy = row_data.pop("Alloy")

            # Skip rows where 'Plant' value is 'None' or NaN
            if plant == "None" or pd.isna(plant):
                continue

            # Prepare the dictionary structure
            current_dict = {plant: row_data}

            if alloy not in scraps:
                scraps.append(alloy)
            if plant not in sources:
                sources.append(plant)
            # Update the scrap_data dictionary
            formatted_data[alloy].update(current_dict)

        return scraps, sources, formatted_data

    async def format_baseline_data(self, project_id, file_path: str) -> Dict:
        """
        fetch scrap data
        Args:
            project_id (str): Project ID.
            file_path (str): File path.
        Returns:
            Dict: Formatted data.
        """

        try:
            logger.info("inside fetch_scrap_data method.")
            path = os.path.splitext(file_path)[0]

            df = pd.read_excel(file_path, sheet_name="Scrap")
            scrap_cols = [
                "Plant",
                "Alloy",
                "Available Weight",
                "Recovery",
                "Si",
                "Mg",
                "Cu",
                "Fe",
                "Mn",
                "Cr",
                "Zn",
                "Ti",
            ]
            scraps, sources, scrap_data = await self.format_data(df, scrap_cols)
            # Now scrap_data contains the data organized by 'Alloy' and 'Plant'
            scrap_output_fname = os.path.join(path + f"_scrap_proj_{project_id}.json")
            demand_output_fname = os.path.join(path + f"_demand_proj_{project_id}.json")
            with open(scrap_output_fname, "w") as fp:
                json.dump(scrap_data, fp)

            scrap_cols.remove("Available Weight")
            logger.info(f"after removing scrap cols:   {scrap_cols}")
            demands_cols = ["Supply", "RAS scrap rate"]
            df = pd.read_excel(file_path, sheet_name="Demand")
            demands, furnaces, demand_data = await self.format_data(
                df, demands_cols + scrap_cols
            )
            with open(demand_output_fname, "w") as fp:
                json.dump(demand_data, fp)

            return dict(
                scrap_alloys=scraps,
                sources=sources,
                scrap_file_path=scrap_output_fname,
                demand_alloys=demands,
                furnaces=furnaces,
                demand_file_path=demand_output_fname,
            )

        except Exception as e:
            logger.error(f"Error formatting baseline data: {e}", exc_info=True)
            raise e

    async def extract_data(
        self,
        project_id,
        alloys: List,
        file_path: str,
        baseline_file: str,
    ) -> Dict:
        """
        extract data
        Args:
            project_id (str): Project ID.
            alloys (List): List of alloys.
            file_path (str): File path.
            baseline_file (str): Baseline file path.
        Returns:
            Dict: Extracted data.
        """

        try:
            logger.info("inside extract_data method.")
            if os.path.exists(file_path):
                data = json.load(open(file_path))
                extracted_data = dict()
                for i in alloys:
                    if i not in data:
                        logger.error(f"Alloy {i} not found in data.")
                        continue
                    else:
                        logger.info(f"extracted data: {data[i]}")
                        extracted_data[i] = data[i]

                return extracted_data
            else:
                formatted_data = await self.format_baseline_data(
                    project_id=project_id, file_path=baseline_file
                )
                #### Extract data from the formatted data functionality will be implemented in the next PR
                return formatted_data

        except Exception as e:
            logger.error(f"Error formatting baseline data: {e}", exc_info=True)
            raise e

    async def remove_data(self, path: str, is_directory: bool = False) -> None:
        """
        Remove a file or directory.

        Args:
            path (str): Path to the file or directory.
            is_directory (bool): If True, removes a directory. Default is False.

        Returns:
            None
        """
        try:
            logger.info("Inside remove_data method.")
            if os.path.exists(path):
                if is_directory:
                    shutil.rmtree(path)
                    logger.info(f"Directory removed: {path}")
                else:
                    os.remove(path)
                    logger.info(f"File removed: {path}")
            else:
                logger.warning(f"Path does not exist: {path}")
        except Exception as e:
            logger.error(
                f"Error removing {'directory' if is_directory else 'file'}: {e}",
                exc_info=True,
            )
            raise e

    async def clean_alloy_directories(
        self, sam_visualizations: List[SAMVisualization]
    ) -> None:
        """
        Cleans up extra images in the parent directories of the plot files,
        keeping only the files specified in the 'plots' list.
        Args:
            sam_visualizations (List[SAMVisualization]): SAM Visualizations data.

        Returns: None
        """
        logger.info("inside clean_alloy_directories method.")
        for sam in sam_visualizations:
            if not sam.plots:
                logger.info(f"Skipping {sam.alloy}: No plots defined.")
                continue

            # Extract the directory from the first plot path
            first_plot_path = sam.plots[0]
            alloy_dir = os.path.dirname(first_plot_path)
            all_plots = (
                sam.plots
                + [plot.replace(".html", ".json") for plot in sam.plots]
                + [plot.replace(".html", ".png") for plot in sam.plots]
            )

            all_plots = sam.plots[:]  # Create a copy
            all_plots.extend(
                [
                    plot.replace(".html", ext)
                    for plot in sam.plots
                    for ext in [".json", ".png"]
                ]
            )

            # Get a set of all plot filenames for O(1) lookups
            plot_filenames = {os.path.basename(plot) for plot in all_plots}

            # List all files in the alloy directory
            try:
                for filename in os.listdir(alloy_dir):
                    file_path = os.path.join(alloy_dir, filename)
                    # Check if it's a file and not in the plots list
                    if os.path.isfile(file_path) and filename not in plot_filenames:
                        await self.remove_data(file_path)
            except FileNotFoundError:
                logger.warning(f"Directory not found: {alloy_dir}")
            except Exception as e:
                logger.error(f"Error processing {alloy_dir}: {e}")

        logger.info("clean_alloy_directories method completed.")

    async def save_scenarios(self, project_id: str, scenarios_data: SAMUseCase) -> Dict:
        """
        Save or update scenarios based on usecase_id.
        Args:
            project_id (str): Project ID.
            scenarios_data (SAMUseCase): SAM UseCase data.
        Returns:
            Dict: Success/Failed message.
        """
        try:
            logger.info("inside save_scenarios method.")

            # Check if `usecase_id` exists
            if scenarios_data.usecase_id:
                # Update the existing entry in the database
                existing_entry = await self.sam_dao.get_scenario_by_usecase_id(
                    project_id=project_id, usecase_id=scenarios_data.usecase_id
                )
                if not existing_entry:
                    return dict(
                        usecase_id=scenarios_data.usecase_id,
                        message=f"Usecase with ID {scenarios_data.usecase_id} not found.",
                        usecase_data="",
                    )

                # Update the entry
                scenarios_data.modified_date = datetime.now(timezone.utc)
                await self.sam_dao.update_scenario(
                    project_id=project_id,
                    usecase_id=scenarios_data.usecase_id,
                    scenarios_data=scenarios_data.model_dump(),
                )
                if scenarios_data.visualizations:
                    logger.info("going to clean_alloy_directories in background")
                    # Run clean_alloy_directories in the background
                    asyncio.create_task(
                        self.clean_alloy_directories(scenarios_data.visualizations)
                    )
                return dict(
                    message="Scenarios updated successfully.",
                    usecase_id=scenarios_data.usecase_id,
                    usecase_data=scenarios_data,
                )

            # For new entry
            # Check if `usecase_name` already exists
            existing_usecase = await self.sam_dao.get_scenario_by_usecase_name(
                project_id=project_id, usecase_name=scenarios_data.usecase_name
            )
            if existing_usecase:
                return dict(
                    usecase_id="",
                    message=f"Usecase with name '{scenarios_data.usecase_name}' already exists.",
                    usecase_data="",
                )

            # Create new entry
            new_usecase_id = await self.sam_dao.create_new_scenario(
                project_id=project_id, scenarios_data=scenarios_data.model_dump()
            )
            scenarios_data.usecase_id = new_usecase_id
            return dict(
                message="New scenario created successfully.",
                usecase_id=new_usecase_id,
                usecase_data=scenarios_data,
            )
        except Exception as e:
            logger.error(f"Unexpected error in save_scenarios: {e}", exc_info=True)

    async def get_scenarios(self, project_id: str) -> List:
        """
        Get scenarios based on project_id.
        Args:
            project_id (str): Project ID.
        Returns:
            List: List of scenarios.
        """
        try:
            logger.info("inside get_scenarios method.")
            scenarios = await self.sam_dao.get_scenarios_by_project_id(
                project_id=project_id
            )
            if not scenarios:
                logger.info(f"No scenarios for project {project_id} found.")
                return []
            return scenarios
        except Exception as e:
            logger.error(f"Unexpected error in get_scenarios: {e}", exc_info=True)
            raise e

    def save_baseline_custom_info_sync(
        self, user: User, baseline_path: str, name: str, tags: List[str]
    ) -> Union[SAMCustomInformation, None]:
        """
        Save baseline custom information synchronously.

        Args:
            user (User): The user initiating the upload.
            baseline_path (str): Path to the baseline file.
            name (str): Furnace name for the analysis.
            tags (List[str]): List of tags to associate with the upload.

        Returns:
            Union[SAMCustomInformation, None]: Custom SAM information if successful, otherwise None.
        """
        if (
            user.server_role == ServerBasedRoleNames.SERVER_ADMIN
            or user.server_role == ServerBasedRoleNames.PROJECT_ADMIN
        ):
            logger.info(
                "User is a Admin and has access to upload baseline file and this will be available for all the project."
            )
            tags.append("admin_upload")

            try:
                outfiles = self.run_scrap_analysis_model_sync(
                    input_file_list=[baseline_path],
                    config_path="",
                    furnace_list=[name],
                )
                if outfiles:
                    logger.info(
                        f"SAM output generated successfully: {baseline_path} \n {outfiles}"
                    )
                    return SAMCustomInformation(
                        sam_result=outfiles[0],
                        furnace_name=name,
                        config_path="",
                    )
                raise Exception("Error running SAM model: No output files generated.")
            except:
                logger.error(
                    "Error in getting Scrap Analysis Model output for baseline file",
                    exc_info=True,
                )
                return None

    async def load_configs(self, config_path: str, baseline_file: str) -> None:
        """
        Load configuration settings from either a baseline file or a config file.

        Args:
            config_path (str): Path to the configuration file.
            baseline_file (str): Path to the baseline Excel file.
        """

        logger.info(f"inside load_configs method.")
        config_df = await self.read_config_sheet(baseline_file)
        if not config_df.empty:
            logger.info(f"Config data: config_df case")
            self.UNIT = config_df.get("Units", pd.Series([""])).iloc[0]
            self.MG_BURNOFF = config_df.get("Mg Burnoff", pd.Series([0.0])).iloc[0]
            self.EXTERNAL_SCRAP_SOURCES = config_df.get(
                "External Scrap Sources", pd.Series([""])
            ).str.cat(sep=", ")
            self.OPTIMIZE_COST = config_df.get(
                "Optimize Cost", pd.Series([False])
            ).iloc[0]
            self.OPTIMIZE_CASTING = config_df.get(
                "Optimize Casting Schedule", pd.Series([False])
            ).iloc[0]
            self.MOLTEN_MINIMUM = config_df.get(
                "Molten Minimum", pd.Series([0.0])
            ).iloc[0]

            logger.info(f"unit: {self.UNIT}")
            logger.info(f"MG_BURNOFF: {self.MG_BURNOFF}")
            logger.info(f"EXTERNAL_SCRAP_SOURCES: {self.EXTERNAL_SCRAP_SOURCES}")
            logger.info(f"OPTIMIZE_COST: {self.OPTIMIZE_COST}")
            logger.info(f"OPTIMIZE_CASTING: {self.OPTIMIZE_CASTING}")
            logger.info(f"MOLTEN_MINIMUM: {self.MOLTEN_MINIMUM}")

        elif config_path:
            logger.info(f"Config data: config_path case")
            config = read_config(config_path)
            self.UNIT = config.get("SAM", "units", fallback="lbs")
            self.MG_BURNOFF = config.getfloat("SAM", "mg_burnoff")
            self.EXTERNAL_SCRAP_SOURCES = config.get(
                "SAM", "external_scrap_sources"
            ).split(", ")
            self.OPTIMIZE_COST = config.getboolean(
                "SAM", "optimize_cost", fallback=False
            )
            self.OPTIMIZE_CASTING = config.getboolean(
                "SAM", "optimize_casting_schedule", fallback=False
            )
            self.MOLTEN_MINIMUM = config.getfloat("SAM", "molten_minimum", fallback=0.0)

    async def read_config_sheet(
        self, file_path: str, sheet_name: str = "Config"
    ) -> pd.DataFrame:
        """
        Read a specific sheet from an Excel file asynchronously.

        Args:
            file_path (str): Path to the Excel file.
            sheet_name (str, optional): Name of the sheet to read. Defaults to "Config".

        Returns:
            pd.DataFrame: The content of the sheet as a DataFrame, or an empty DataFrame if the sheet is not found.
        """

        try:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            excel_bytes = io.BytesIO(content)
            logger.info(f"Reading Excel file: {file_path}")
            with pd.ExcelFile(excel_bytes) as xls:
                if sheet_name in xls.sheet_names:
                    return pd.read_excel(xls, sheet_name=sheet_name)
                else:
                    logger.info(f"Sheet '{sheet_name}' not found.")
                    return pd.DataFrame()  # Return empty DataFrame if not found
            logger.info(f"Excel file read successfully: {file_path}")
        except Exception as e:
            logger.info(f"Error reading Excel file: {e}")
            return pd.DataFrame()

    def run_scrap_analysis_model_sync(
        self, input_file_list: List, config_path: str, furnace_list: List
    ) -> List:
        """
        Run the scrap analysis model synchronously.

        Args:
            input_file_list (List): List of input file paths.
            config_path (str): Path to the configuration file.
            furnace_list (List): List of furnace names.

        Returns:
            List: A list of output file paths generated from the analysis.
        """

        asyncio.run(self.load_configs(config_path, input_file_list[0]))

        output_file_list = []
        for input_filename, furnace in zip(input_file_list, furnace_list):
            logger.info(f"input_filename:     {input_filename}")
            scrap_flow_dict, plant_dict, transportation_dict, limits_df = (
                read.read_input(input_filename)
            )
            output_file_list.append(
                solve(
                    scrap_flow_dict,
                    plant_dict,
                    transportation_dict,
                    limits_df,
                    furnace,
                    logger,
                    optimize_cost=self.OPTIMIZE_COST,
                    OPTIMIZE_CASTING=self.OPTIMIZE_CASTING,
                    MG_BURNOFF=self.MG_BURNOFF,
                    MOLTEN_MINIMUM=self.MOLTEN_MINIMUM,
                    EXTERNAL_SCRAP_SOURCES=self.EXTERNAL_SCRAP_SOURCES,
                    input_filename=input_filename,
                )
            )

        return output_file_list

    async def run_scrap_analysis_model(
        self,
        input_file_list: List,
        config_path: str,
        furnace_list: List,
        baseline_path: str = None,
    ) -> List:
        """
        Run the scrap analysis model Asynchronously.

        Args:
            input_file_list (List): List of input file paths.
            config_path (str): Path to the configuration file.
            furnace_list (List): List of furnace names.
            baseline_path (str, optional): Path to the baseline file. Defaults to None.

        Returns:
            List: A list of output file paths generated from the analysis.
        """

        await self.load_configs(config_path, baseline_path)
        output_file_list = []
        for input_filename, furnace in zip(input_file_list, furnace_list):
            logger.info(f"input_filename:     {input_filename}")
            scrap_flow_dict, plant_dict, transportation_dict, limits_df = (
                read.read_input(input_filename)
            )
            output_file_list.append(
                solve(
                    scrap_flow_dict,
                    plant_dict,
                    transportation_dict,
                    limits_df,
                    furnace,
                    logger,
                    optimize_cost=self.OPTIMIZE_COST,
                    OPTIMIZE_CASTING=self.OPTIMIZE_CASTING,
                    MG_BURNOFF=self.MG_BURNOFF,
                    MOLTEN_MINIMUM=self.MOLTEN_MINIMUM,
                    EXTERNAL_SCRAP_SOURCES=self.EXTERNAL_SCRAP_SOURCES,
                    input_filename=input_filename,
                )
            )

        return output_file_list

    async def transform_data(self, data: Dict) -> Dict:
        # Extract keys and values for scraps
        scraps_headers = list(data["scraps"].keys())
        scraps_data = list(zip(*data["scraps"].values()))

        # Extract keys and values for demands
        demands_headers = list(data["demands"].keys())
        demands_data = list(zip(*data["demands"].values()))

        # Extract keys and values for limits
        limits_headers = list(data["limits"].keys())
        limits_data = list(zip(*data["limits"].values()))

        # Combine everything into the final structure
        result = {
            "scraps": [scraps_headers] + [list(row) for row in scraps_data],
            "demands": [demands_headers] + [list(row) for row in demands_data],
            "limits": [limits_headers] + [list(row) for row in limits_data],
        }
        return result

    async def remove_blank_rows(self, sheet):
        last_non_blank_row = sheet.max_row
        while last_non_blank_row > 0:
            if any(cell.value is not None for cell in sheet[last_non_blank_row]):
                break
            last_non_blank_row -= 1

        # Remove rows after the last non-blank row
        if last_non_blank_row < sheet.max_row:
            sheet.delete_rows(
                last_non_blank_row + 1, sheet.max_row - last_non_blank_row
            )
        return sheet

    async def sam_input_data_processing(
        self,
        scenario: ScenarioDetail,
        usecase_name: str,
        result_dir: str,
        baseline_path: str,
        dataset_obj,
        user_id: str,
        project_id: str,
    ) -> str:

        # Transform the data into the required format
        data = await self.transform_data(scenario.model_dump())
        scrap_rows = data["scraps"]
        demand_rows = data["demands"]
        limit_rows = data["limits"]

        logger.info(f"scrap_rows: {scrap_rows}")
        logger.info(f"demand_rows: {demand_rows}")
        logger.info(f"limit_rows: {limit_rows}")

        intermediate_fname = f"{usecase_name}_{scenario.scenario_name}.xlsx"
        intermediate_fpath = os.path.join(result_dir, intermediate_fname)

        wbook = load_workbook(baseline_path)

        scrap_counter = dict()
        demand_counter = dict()
        # for an (alloy, plant) pair, there might be multiple demand alloys for which the limit is set
        limit_counter = defaultdict(list)

        # ------------- keep track of the index of the alloys in the header in the Limits sheet ----------------------
        #### old code
        # limit_sheet = wbook["Limits"]
        limit_sheet = await self.remove_blank_rows(wbook["Limits"])

        # keep track of the demand alloy headers that already exist in the sheet
        # if a new alloy is entered in the demand section, this alloy will be added to the limits sheet
        limit_alloys_header_index = dict()
        existing_limit_alloy_headers = limit_sheet[1][2:]
        for idx, demand_header in enumerate(existing_limit_alloy_headers, start=3):
            limit_alloys_header_index[demand_header.value] = idx

        # keep track of the scrap alloy headers that already exist in the sheet
        # if a new alloy is entered in the scrap section, this alloy will be added to the limits sheet
        # UNTESTED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        limit_alloys_row_index = dict()
        # B2 through BX
        #### old code
        # existing_limit_alloy_rows = [
        #     row[0] for row in limit_sheet[2 : limit_sheet.max_row]
        # ]
        existing_limit_alloy_rows = [
            row[1] for row in limit_sheet[2 : limit_sheet.max_row]
        ]

        # A2 through AX
        ## old code
        # existing_limit_source_rows = [
        #     row[1] for row in limit_sheet[2 : limit_sheet.max_row]
        # ]
        existing_limit_source_rows = [
            row[0] for row in limit_sheet[2 : limit_sheet.max_row]
        ]

        for idx, (scrap_row, source_row) in enumerate(
            zip(existing_limit_alloy_rows, existing_limit_source_rows), start=2
        ):
            limit_alloys_row_index[str(scrap_row.value) + str(source_row.value)] = idx

        # -------------------------------------------------------------------------------------------------------------

        for row in scrap_rows[1:]:
            alloy, plant, cost, available, *chem = row
            available = 0 if not available else int(available)
            cost = 0 if not cost else float(cost)
            chem = map(float, chem)
            scrap_counter[(alloy, plant)] = [cost, available, *chem]
        logger.info(f"scrap_counter: {scrap_counter}")

        for row in demand_rows[1:]:
            alloy, plant, supply, *chem = row
            supply = 0 if not supply else int(supply)
            minimum_supply = supply
            maximum_supply = supply
            chem = map(float, chem)
            demand_counter[(alloy, plant)] = [
                supply,
                minimum_supply,
                maximum_supply,
                *chem,
            ]
        logger.info(f"demand_counter: {demand_counter}")

        for row in limit_rows[1:]:
            plant, scrap, demand, val = row
            limit_counter[(plant, scrap)].append((demand, val))
        logger.info(f"limit_counter: {limit_counter}")
        # ---------------------------------- SCRAP -------------------------------------------------------------------------
        #   0       1     2       3               4               5         6          7     8     9     10    11    12    13   14
        # Plant, Alloy, Form, Cost,     Minimum Weight, Available Weight, Recovery,   Si,   Mg,   Cu,   Fe,   Mn,   Cr,   Zn,   Ti
        ### old code
        # scrap_sheet = wbook["Scrap"]
        scrap_sheet = await self.remove_blank_rows(wbook["Scrap"])
        for row in scrap_sheet[2 : scrap_sheet.max_row]:
            plant, alloy = str(row[0].value).strip(), str(row[1].value).strip()
            if (alloy, plant) not in scrap_counter:
                continue
            cost, avail, *chem = scrap_counter[(alloy, plant)]
            row[3].value = cost
            row[5].value = avail
            for cell, element in zip(row[7:], chem):
                cell.value = element
            # row[7].value  = si
            # row[8].value  = mg
            # row[9].value  = cu
            # row[10].value = fe
            # row[11].value = mn
            # row[12].value = cr
            # row[13].value = zn
            # row[14].value = ti

            scrap_counter.pop((alloy, plant))
        logger.info(f"scrap_counter after pop: {scrap_counter}")
        # for the entries that were not already in the sheet, add a new row at the end
        # ----------- these are the new alloy entries --------------------
        ### old code
        # for [(alloy, plant), (available, *chem)] in scrap_counter.items():

        for [(alloy, plant), (cost, available, *chem)] in scrap_counter.items():
            row = [plant, alloy, "Scrap", cost, 0, available, 0.98, *chem]
            scrap_sheet.append(row)
            # add the new alloy to the limits sheet
            ## old code
            # limit_alloys_row_index[alloy] = max(limit_alloys_row_index.values()) + 1
            limit_alloys_row_index[str(alloy) + str(plant)] = (
                max(limit_alloys_row_index.values()) + 1
            )
            # workbook last entered
            #### old code
            # limit_sheet.cell(row=limit_alloys_row_index[alloy], column=1).value = plant
            # limit_sheet.cell(row=limit_alloys_row_index[alloy], column=2).value = alloy
            limit_sheet.cell(
                row=limit_alloys_row_index[str(alloy) + str(plant)], column=1
            ).value = plant
            limit_sheet.cell(
                row=limit_alloys_row_index[str(alloy) + str(plant)], column=2
            ).value = alloy

        # ----------------------------- DEMAND --------------------------------------------------------------------------------
        #   0       1     2          3      4       5                6          7     8    9     10    11    12    13   14
        # Plant, Alloy, Supply, Minimum, Maximum , RAS Scrap Rate, Recovery,  Si,   Mg,   Cu,   Fe,   Mn,   Cr,   Zn,   Ti
        # demand_sheet = wbook["Demand"]
        demand_sheet = await self.remove_blank_rows(wbook["Demand"])
        for row in demand_sheet[2 : demand_sheet.max_row]:
            plant, alloy = str(row[0].value).strip(), str(row[1].value).strip()
            if (alloy, plant) not in demand_counter:
                continue
            supply, minimum_supply, maximum_supply, *chem = demand_counter[
                (alloy, plant)
            ]
            row[2].value = supply
            row[3].value = minimum_supply
            row[4].value = maximum_supply
            for cell, element in zip(row[7:], chem):
                cell.value = element
            # row[5].value  = si
            # row[6].value  = mg
            # row[7].value  = cu
            # row[8].value  = fe
            # row[9].value  = mn
            # row[10].value = cr
            # row[11].value = zn
            # row[12].value = ti

            demand_counter.pop((alloy, plant))
        logger.info(f"demand_counter after pop: {demand_counter}")

        # the new demand into limits
        for [
            (alloy, plant),
            (supply, minimum_supply, maximum_supply, *chem),
        ] in demand_counter.items():
            row = [
                plant,
                alloy,
                supply,
                minimum_supply,
                maximum_supply,
                0,
                1,
                *chem,
            ]
            demand_sheet.append(row)
            # add to limits top row
            limit_alloys_header_index[alloy] = (
                max(limit_alloys_header_index.values()) + 1
            )
            limit_sheet.cell(row=1, column=limit_alloys_header_index[alloy]).value = (
                alloy
            )

        # ------------------------------ LIMIT --------------------------------------------------------------------------------
        #   0      1         2              3
        # Plant, Alloy, Demand alloy 1, Demand alloy 2, ......
        # this is a matrix such that for the given plant and supply pair, there exists an entry for the demand alloy

        # for each of the demand alloys in the received limit data, add a new header to the sheet if it doesn't already exist

        ### comment out in latest code
        # for alloys in limit_counter.values():
        #     print(alloys)
        #     for alloy in alloys:
        #         if alloy not in limit_alloys_header_index:
        #             limit_alloys_header_index[alloy] = (
        #                 max(limit_alloys_header_index.values()) + 1
        #             )
        #             # add this to the sheet
        #             print("-" * 20)
        #             print(alloy, limit_alloys_header_index[alloy])
        #             print("-" * 20)

        #             limit_sheet.cell(
        #                 row=1, column=limit_alloys_header_index[alloy]
        #             ).value = alloy

        for [(plant, alloy), demand_alloys] in limit_counter.items():
            for demand_alloy, val in demand_alloys:
                limit_sheet.cell(
                    row=limit_alloys_row_index[str(alloy) + str(plant)],
                    column=limit_alloys_header_index[demand_alloy],
                ).value = val

        logger.info(f"limit_alloys_header_index: {limit_alloys_header_index}")

        ### comment out in latest code
        # for row in limit_sheet[2 : limit_sheet.max_row]:
        #     plant, alloy = str(row[0].value).strip(), str(row[1].value).strip()
        #     if (alloy, plant) not in limit_counter:
        #         continue
        #     for demand_alloy in limit_counter[(alloy, plant)]:
        #         row[limit_alloys_header_index[demand_alloy]].value = 0
        #     limit_counter.pop((alloy, plant))

        # if only the alloys that are already in the Limits sheet are allowed to be entered in the frontend, this for loop is not needed
        # for plant, scrap in limit_counter.keys():
        #     print(plant, scrap)
        #     for demand_alloy in limit_counter[(plant, scrap)]:
        #         row = [plant, scrap]
        #         for _ in range(2, limit_alloys_header_index[demand_alloy]):
        #             row.append("")
        #         row.append(0)
        #         limit_sheet.append(row)

        wbook.save(intermediate_fpath)
        await self.save_sam_intermediate_file_as_dataset(
            scenario=scenario,
            project_id=project_id,
            intermediate_fpath=intermediate_fpath,
            usecase_name=usecase_name,
            user_id=user_id,
            dataset_obj=dataset_obj,
        )
        logger.info(f"Intermediate file saved at {intermediate_fpath}")
        return intermediate_fpath

    async def save_sam_intermediate_file_as_dataset(
        self,
        scenario,
        project_id,
        intermediate_fpath,
        usecase_name,
        user_id,
        dataset_obj,
    ) -> None:
        logger.info(
            f"Processing intermediate file for {scenario.scenario_name}: {intermediate_fpath}"
        )

        # Check if `intermediate_processing` key exists
        intermediate_processing = scenario.results.get("intermediate_processing")
        outfile_name = f"{usecase_name}_{scenario.scenario_name}"
        if not intermediate_processing:
            # First attempt: Save dataset
            logger.info(
                f"Saving intermediate file as dataset for {scenario.scenario_name}"
            )
            tags = [
                "sam",
                "scenario_run",
                "scrap_analysis",
                scenario.scenario_name,
                usecase_name,
            ]
            dataset_id = dataset_obj.save_tabular_dataset_helper_sync(
                input_data=intermediate_fpath,
                project_id=project_id,
                site_id="1",
                user_id=user_id,
                action_id="",
                run_id="",
                workflow_id="",
                name=outfile_name,
                description=outfile_name,
                access_mode=AccessMode.INTERNAL,
                tags=tags,
            )
            scenario.results.update(
                {
                    "intermediate_processing": {
                        "dataset_id": dataset_id,
                        "scenario_name": scenario.scenario_name,
                        "file_path": intermediate_fpath,
                    }
                }
            )
            logger.info(f"Intermediate file saved as dataset: {intermediate_fpath}")

        else:

            prev_file_path = intermediate_processing.get("file_path")
            prev_file_name = os.path.basename(prev_file_path)
            current_dataset_id = intermediate_processing.get("dataset_id")

            if outfile_name != prev_file_name:

                logger.info(
                    f"Scenario file  name updated from {prev_file_name} to {outfile_name}. Updating dataset."
                )
                new_tags = [
                    "sam",
                    "scenario_run",
                    "scrap_analysis",
                    scenario.scenario_name,
                    usecase_name,
                ]
                await self.sam_dao.custom_update_dataset(
                    dataset_id=current_dataset_id,
                    new_tags=new_tags,
                    new_path=intermediate_fpath,
                    name=outfile_name,
                )
                scenario.results["intermediate_processing"].update(
                    {
                        "scenario_name": scenario.scenario_name,
                        "file_path": intermediate_fpath,
                    }
                )
                logger.info(
                    f"Dataset and scenario name updated: {scenario.scenario_name}, file path: {intermediate_fpath}"
                )

    async def run_scenarios(
        self, project_id: str, usecase_id: str, user_id: str
    ) -> Dict:
        """
        Run scenarios based on usecase_id.
        Args:
            project_id (str): Project ID.
            usecase_id (str): Usecase ID.
            user_id (str): User ID.
        Returns:
            Dict: Scenario data.
        """
        try:
            logger.info("inside run_scenarios method.")
            # Fetch the scenario based on `usecase_id`
            scenario = await self.sam_dao.get_scenario_by_usecase_id(
                project_id=project_id, usecase_id=usecase_id
            )
            if not scenario:
                return dict(
                    usecase_id=usecase_id,
                    message=f"Usecase with ID {usecase_id} not found.",
                )

            scenario["_id"] = str(scenario["_id"])
            logger.info(f"Scenario data: {scenario}")
            sam_scenarios = SAMUseCase(**scenario)
            logger.info(f"Scenario data: {sam_scenarios}")
            dataset_obj = DatasetsService(db_async_client=self.sam_dao.db_async_client)
            baseline_detail = await dataset_obj.get_dataset_by_id(
                dataset_id=sam_scenarios.baseline_file
            )
            logger.info(f"Baseline detail: {baseline_detail}")
            baseline_path = baseline_detail.dataset_location[0].path
            logger.info(f"Baseline path: {baseline_path}")
            # Run the scenarios
            result_dir = os.path.join(
                env.base_path,
                "scrap_analysis",
                str(project_id),
                f"{sam_scenarios.usecase_name}_{user_id}",
            )
            os.makedirs(result_dir, exist_ok=True)
            logger.info(f"Result directory created at {result_dir}")
            config_path = ""
            logger.info(f"default config_path ==== {config_path}")
            if sam_scenarios.config_content and os.path.exists(
                sam_scenarios.config_content
            ):
                config_path = sam_scenarios.config_content
                logger.info(f"override config_path ==== {config_path}")

            intermediate_files = []
            furnace_list = []
            for scenario in sam_scenarios.scenarios:
                # data processing for sam core service
                intermediate_fpath = await self.sam_input_data_processing(
                    scenario=scenario,
                    usecase_name=sam_scenarios.usecase_name,
                    result_dir=result_dir,
                    baseline_path=baseline_path,
                    dataset_obj=dataset_obj,
                    user_id=user_id,
                    project_id=project_id,
                )

                intermediate_files.append(intermediate_fpath)
                furnace_list.append(scenario.scenario_name)

            # run the sam script
            try:
                output_files = await self.run_scrap_analysis_model(
                    intermediate_files,
                    config_path=config_path,
                    furnace_list=furnace_list,
                    baseline_path=baseline_path,
                )
                if not output_files:
                    raise Exception(
                        "Error running SAM model: No output files generated."
                    )

            except Exception as e:
                logger.error(f"Error running SAM model: {e}", exc_info=True)
                return {}

            for scenario, output_file in zip(sam_scenarios.scenarios, output_files):
                scenario.results.update(
                    {
                        "excel_result": output_file,
                        "alloys": await self.get_demand_alloys(output_file),
                    }
                )

            if sam_scenarios.visualizations:
                logger.info("visualizations found and clearing it now")
                sam_scenarios.visualizations = None

            sam_scenarios.unit = self.UNIT

            await self.sam_dao.update_scenario(
                project_id=project_id,
                usecase_id=usecase_id,
                scenarios_data=sam_scenarios.model_dump(),
            )

            return sam_scenarios

        except Exception as e:
            logger.error(f"Unexpected error in run_scenarios: {e}", exc_info=True)
            return {}

    async def get_demand_alloys(self, output_file: str) -> List:
        """
        Get demand alloys from the output file.

        Args:
            output_file (str): Path to the output file.

        Returns:
            List: List of demand alloys.
        """
        try:
            logger.info("inside get_demand_alloys method.")
            # Read the output file
            output_df = pd.read_excel(output_file, sheet_name=0)
            demand_alloys = output_df.columns.to_list()
            demand_alloys.remove("Metal") if "Metal" in demand_alloys else demand_alloys
            logger.info(f"Demand alloys: {demand_alloys}")
            return demand_alloys
        except Exception as e:
            logger.error(f"Error getting demand alloys: {e}", exc_info=True)
            return []

    async def extract_scenario_details(self, scenarios: List) -> tuple[List, List]:
        """
        Extracts scenario data from the scenarios object.
        Args:
            scenarios (List): List of scenarios.
        Returns:
            tuple[List, List]: List of scenario names and file paths.
        """

        names = [scenario.name for scenario in scenarios]
        file_paths = [scenario.file_path for scenario in scenarios]
        return names, file_paths

    async def get_unique_furnaces(self, baseline_path: str) -> List:
        """
        Get unique furnace names from the baseline file.

        Args:
            baseline_path (str): Path to the baseline file.

        Returns:
            List: List of unique furnace names.
        """
        try:
            logger.info("inside get_unique_furnaces method.")
            # Read the baseline file
            baseline_df = pd.read_excel(baseline_path, sheet_name="Demand")
            furnace_names = baseline_df["Plant"].unique().tolist()
            logger.info(f"Unique furnace names: {furnace_names}")
            return furnace_names
        except Exception as e:
            logger.error(f"Error getting unique furnace names: {e}", exc_info=True)
            return []

    async def plot_viz(self, viz_data: SAMViz) -> List:
        """
        Generate and save alloy bar visualizations based on scenario data.

        Args:
            viz_data (SAMViz): SAM usecase data to plot viz.

        Returns:
            List[str]: A list of file paths where the plots are saved.
        """
        try:
            logger.info("inside plot_viz method.")
            logger.info(f"Scenario viz_data : {viz_data}")

            if not viz_data.scenarios:
                logger.error("scenarios data from visualization not found")

            if viz_data.baseline:
                logger.info(
                    "Baseline data found in visualization data, going to create sam output for baseline"
                )
                dataset_obj = DatasetsService(
                    db_async_client=self.sam_dao.db_async_client
                )
                baseline_detail = await dataset_obj.get_dataset_by_id(
                    dataset_id=viz_data.baseline
                )
                logger.info(f"Baseline detail: {baseline_detail}")
                baseline_path = baseline_detail.dataset_location[0].path
                furnaces = await self.get_unique_furnaces(baseline_path)
                logger.info(f"Baseline path: {baseline_path}")
                # Run the SAM output for baseline
                # # run the sam script
                try:
                    output_files = await self.run_scrap_analysis_model(
                        [baseline_path],
                        config_path=None,
                        furnace_list=baseline_detail.name,
                    )
                    if not output_files:
                        raise Exception(
                            "Error running SAM model: No output files generated."
                        )
                    baseline_detail.custom_information = SAMCustomInformation(
                        sam_result=output_files[0],
                        furnace_name=baseline_detail.name,
                        config_path="",
                    )
                    logger.info(
                        f"baseline_detail.custom_information: {baseline_detail.custom_information} \n\n {baseline_detail}"
                    )

                    logger.info("going to update baseline data with custom information")
                    dataset_obj.update_dataset_record_data_sync(
                        dataset_id=baseline_detail.id,
                        key_to_update="custom_information",
                        data=baseline_detail.custom_information.model_dump(),
                    )
                    logger.info("baseline data updated with custom information")
                    logger.info(f"viz data: {viz_data}")
                    for scenario in viz_data.scenarios:
                        if scenario.name == "Baseline":
                            scenario.file_path = output_files[0]
                    logger.info(f"viz data after updating scenarios: {viz_data}")

                except Exception as e:
                    logger.error(f"Error running SAM model: {e}", exc_info=True)
                    return {}

            dir_path = os.path.dirname(viz_data.scenarios[0].file_path)
            alloy_name = viz_data.alloy_name.replace("/", "_")
            alloy_dir = os.path.join(dir_path, alloy_name)
            os.makedirs(alloy_dir, exist_ok=True)
            logger.info(f"Result viz directory created at {alloy_dir}")
            time_stamp = str(datetime.now(timezone.utc))
            plot_filenames = [
                f"{alloy_name}_Fractional_BOM_{time_stamp}.html",
                f"{alloy_name}_BOM_Weight_{time_stamp}.html",
                f"{alloy_name}_Prime_Fractional_BOM_{time_stamp}.html",
                f"{alloy_name}_Prime_BOM_Weight_{time_stamp}.html",
            ]
            plot_paths = [
                os.path.join(alloy_dir, filename) for filename in plot_filenames
            ]

            scenario_names, filenames = await self.extract_scenario_details(
                viz_data.scenarios
            )
            alloy_bars_interactive(
                filenames=filenames,
                scenario_names=scenario_names,
                alloy_name=viz_data.alloy_name,
                plot1_path=plot_paths[0],
                plot2_path=plot_paths[1],
                units=viz_data.unit,
            )
            logger.info(f"Plots generated: {plot_paths}")
            logger.info("going to plot prime viz")
            try:
                prime_bars_interactive(
                    filenames=filenames,
                    scenario_names=scenario_names,
                    furnace_names=furnaces,
                    plot1_path=plot_paths[2],
                    plot2_path=plot_paths[3],
                    units=viz_data.unit,
                )
                logger.info(f"Prime Plots generated: {plot_paths}")
            except Exception as e:
                logger.error(f"Error plotting prime viz: {e}", exc_info=True)
                pass

            existing_plots = [plot for plot in plot_paths if os.path.isfile(plot)]
            missing_plots = set(plot_paths) - set(existing_plots)
            for plot in missing_plots:
                logger.error(f"Plot not generated: {plot}")
                raise Exception(f"Plot not generated: {plot}")

            return existing_plots

        except Exception as e:
            logger.error(f"Unexpected error in plot viz: {e}", exc_info=True)
            return []

    async def remove_sam_data(
        self, project_id: str, sam_case: str, sam_id: str
    ) -> Dict:
        """
        Remove SAM data based on sam_id.

        Args:
            project_id (str): Project ID.
            sam_case (str): SAM case ('baseline' or 'usecase').
            sam_id (str): Mongo document ID.

        Returns:
            Dict: Success or Failure message.
        """
        try:
            logger.info("Inside remove_sam_data method.")
            if sam_case not in {"baseline", "usecase"}:
                logger.warning(f"Invalid sam_case provided: {sam_case}")
                return {"error": "Invalid SAM case. Must be 'baseline' or 'usecase'."}

            delete_kwargs = {"project_id": project_id, "_id": ObjectId(sam_id)}
            collection_name = "datasets" if sam_case == "baseline" else "scrap_analysis"
            deleted_doc = await self.sam_dao.delete_document(
                delete_kwargs, collection_name
            )
            logger.info(f"Deleted document: {deleted_doc}")
            if not deleted_doc:
                logger.error(f"No document found for {sam_case} with ID {sam_id}")
                return {}

            deleted_doc["_id"] = str(deleted_doc["_id"])

            if sam_case == "baseline":
                data = Dataset(**deleted_doc)
                if data.dataset_location:
                    await self.remove_data(data.dataset_location[0].path)
                    logger.info(
                        f"Baseline data removed: {data.dataset_location[0].path}"
                    )
                return {"sam_id": sam_id, "message": "Baseline deleted successfully."}

            elif sam_case == "usecase":
                data = SAMUseCase(**deleted_doc)

                intermediate_files = []
                parent_dir = None
                for scenario in data.scenarios:
                    if (
                        scenario.results
                        and "intermediate_processing" in scenario.results
                    ):
                        intermediate_file_path = scenario.results[
                            "intermediate_processing"
                        ]["file_path"]
                        intermediate_files.append(intermediate_file_path)
                        logger.info(f"Kept intermediate file: {intermediate_file_path}")
                        if not parent_dir:
                            parent_dir = os.path.dirname(intermediate_file_path)

                if parent_dir and os.path.exists(parent_dir):
                    for item in os.listdir(parent_dir):
                        item_path = os.path.join(parent_dir, item)
                        if os.path.isdir(item_path):
                            await self.remove_data(item_path, is_directory=True)
                            logger.info(f"Deleted folder: {item_path}")
                        elif item_path not in intermediate_files:
                            await self.remove_data(item_path)
                            logger.info(f"Deleted file: {item_path}")

                logger.info(
                    f"Extracted parent directory from intermediate processing: {parent_dir}"
                )

                return {
                    "sam_id": sam_id,
                    "message": "Usecase data deleted successfully.",
                }

        except Exception as e:
            logger.error(f"Unexpected error in remove_sam_data: {e}", exc_info=True)
            return {}

    # async def prime_plot(self, project_id: str, baseline_id: str) -> Dict:
    #     """
    #     Prime the SAM plot for the given baseline and usecase.
    #     Args:
    #         project_id (str): Project ID.
    #         baseline_id (str): Baseline ID.
    #     Returns:
    #         Dict: Plot data.
    #     """
    #     try:
    #         logger.info("Inside prime_plot method.")
    #         # Fetch the baseline data
    #         baseline_data = await self.sam_dao.get_dataset_by_id(dataset_id=baseline_id)
    #         if not baseline_data:
    #             return {"error": "Baseline data not found."}

    #         # Extract the baseline and usecase file paths
    #         baseline_file = baseline_data.dataset_location[0].path
    #         scenario_names = ['Baseline']
    #         furnace_names = []
    #         if baseline_data.custom_information:
    #             baseline_output = baseline_data.custom_information.sam_result

    #         # Plot the visualizations
    #         plot_paths = await self.plot_viz(
    #             SAMViz(
    #                 baseline=baseline_id,
    #                 scenarios=[SAMScenario(name="Baseline", file_path=baseline_file)],
    #                 alloy_name=alloy_name,
    #                 unit=usecase_data.unit,
    #             )
    #         )
    #         logger.info(f"Plot paths: {plot_paths}")

    #         return {"plot_paths": plot_paths}

    #     except Exception as e:
    #         logger.error(f"Unexpected error in prime_plot: {e}", exc_info=True)
    #         return {}
