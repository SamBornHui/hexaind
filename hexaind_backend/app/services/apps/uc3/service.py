import json
import logging
import os
from typing import Dict, List

import aiofiles
import aiofiles.os
import dask.dataframe as dd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.api.endpoints.v1.workflows.runner.routes import WorkflowRunnerRouter
from app.api.endpoints.v1.workflows.sessions.routes import WorkflowSessionRouter
from app.services.workflows.runner.service import RunService

logger = logging.getLogger(__name__)
root_directory = (
    os.getenv("HEXAIND_DATA", "/hexaind-data")
    + "/datasets/r_{}/custom_code_results/UC3_Dashboard"
)


class UC3Service:

    async def get_workflow_names(
        self, site_id: str, project_id: str, client: AsyncIOMotorClient
    ) -> Dict[str, str]:
        """Fetch workflow names."""
        try:
            all_sessions = await WorkflowSessionRouter.get_all_workflow_sessions(
                siteId=site_id,
                projectId=project_id,
                page_limit=100,
                page_number=1,
                search_term=None,
                get_updated_details=True,
                client=client,
            )
            workflow_names = {
                wf.workflow_id: wf.name
                for wf_session in all_sessions.sessions
                for wf in [wf_session] + wf_session.saved_workflows
            }
            logger.info(
                f"Fetched workflow names for site {site_id} and project {project_id}"
            )
            return workflow_names
        except Exception as e:
            logger.exception("Failed to fetch workflow names.", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while fetching workflow names.",
            ) from e

    async def get_runs_for_workflow(
        self,
        site_id: str,
        project_id: str,
        workflow_id: str,
        client: AsyncIOMotorClient,
    ) -> Dict[str, str]:
        """Fetch runs of a workflow."""
        try:
            all_runs = await WorkflowRunnerRouter.get_all_runs_for_workflow(
                siteId=site_id,
                projectId=project_id,
                workflowId=workflow_id,
                page_limit=100,
                page_number=1,
                search_term=None,
                client=client,
            )
            if not all_runs or not all_runs.runs:
                logger.warning(f"No runs found for workflow {workflow_id}")
                return {}
            runs = {run.id: run.created_at for run in all_runs.runs}
            logger.info(
                f"Fetched runs for workflow {workflow_id} in site {site_id}, project {project_id}"
            )
            return runs
        except Exception as e:
            logger.exception(
                f"Failed to fetch runs for workflow {workflow_id}", exc_info=e
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while fetching runs for workflow.",
            ) from e

    async def get_dashboard_metadata(self, run_id: str) -> Dict:
        """Fetch dashboard metadata for a run."""

        try:
            metadata = None
            metadata_file_path = root_directory.format(run_id) + "/metadata.json"
            with open(metadata_file_path, "r") as f:
                metadata = json.load(f)
            logger.info(f"Fetched dashboard metadata for run {run_id}")
            return metadata
        except FileNotFoundError:
            logger.warning(f"Dashboard metadata not found for run {run_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metadata for dashboard not found for the run.",
            )
        except Exception as e:
            logger.exception(
                f"Failed to fetch dashboard metadata for run {run_id}", exc_info=e
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while fetching dashboard metadata.",
            ) from e

    async def get_tool_recipe_plots(
        self,
        run_id: str,
        feature_name: str,
        step_name: str,
        sync_client: MongoClient,
    ) -> List[str]:
        """Fetch tool recipe plots for a run."""

        tool_recipe_folder = os.path.join(root_directory.format(run_id), "TOOL_RECIPE")

        if not await aiofiles.os.path.exists(tool_recipe_folder):
            logger.warning(
                f"Tool recipe folder not found for run {run_id}, path: {tool_recipe_folder}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool recipe folder not found for the run.",
            )

        run_service = RunService(db_sync_client=sync_client)
        run = run_service.get_run_by_id(run_id)

        plots = []
        if run and not run.interactive_mode:
            for plot_name in ["_tool.html", "_recipe.html", "_start_date.html"]:
                plot_filename = f"{feature_name}_{step_name}{plot_name}"
                plot_path = os.path.join(tool_recipe_folder, plot_filename)
                if await aiofiles.os.path.exists(plot_path):
                    plots.append(plot_path)

        if len(plots) != 3:
            plots = await self._get_tool_recipe_plots_helper(
                tool_recipe_folder, feature_name, step_name
            )

        logger.info(f"Fetched tool recipe plots for run {run_id}")
        return plots

    async def _get_tool_recipe_plots_helper(
        self, tool_recipe_folder: str, feature_name: str, step_name: str
    ) -> list:
        """Helper function to fetch tool recipe plots for a run."""

        # Load data
        pivoted_data = dd.read_csv(
            f"{tool_recipe_folder}/pivoted_data.csv",
            dtype={"LOT_ID": "object", "parentlot": "object"},
            low_memory=False,
        )
        fd_context_data = dd.read_csv(
            f"{tool_recipe_folder}/fd_context_data.csv",
            dtype={"LOT_ID": "object", "parentlot": "object"},
            low_memory=False,
        )

        # Preprocess data
        fd_context_data["parentlot"] = fd_context_data["LOT_ID"].astype(str).str[:-4]
        fd_context_data["START_DATE"] = dd.to_datetime(fd_context_data["START_DATE"])

        fd_context_data_selected = fd_context_data[
            fd_context_data["TRAVELER_STEP"] == step_name
        ]
        selected_test_data = pivoted_data[["parentlot", "WAFER_ID", feature_name]]

        selected_test_data["parentlot"] = selected_test_data["parentlot"].astype(str)
        selected_test_data["WAFER_ID"] = selected_test_data["WAFER_ID"].astype(str)
        fd_context_data_selected["parentlot"] = fd_context_data_selected[
            "parentlot"
        ].astype(str)
        fd_context_data_selected["WAFER_ID"] = fd_context_data_selected[
            "WAFER_ID"
        ].astype(str)

        # Merge data
        merged_tool_recipe = dd.merge(
            selected_test_data,
            fd_context_data_selected,
            on=["parentlot", "WAFER_ID"],
            how="inner",
        )

        # Compute the Dask DataFrames to get the results
        merged_tool_recipe = merged_tool_recipe.compute()

        # Check if data is present for the step else raise exception
        if merged_tool_recipe.empty:
            logger.warning(f"Data not found for step {step_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data not found for the step.",
            )

        colors = px.colors.qualitative.Plotly

        # Generate plots
        plot_paths = []

        # Box plot for TOOL_NAME
        fig_tool = go.Figure()
        unique_tools = merged_tool_recipe["TOOL_NAME"].unique()
        for i, tool in enumerate(unique_tools):
            fig_tool.add_trace(
                go.Box(
                    y=merged_tool_recipe[merged_tool_recipe["TOOL_NAME"] == tool][
                        feature_name
                    ],
                    x=merged_tool_recipe[merged_tool_recipe["TOOL_NAME"] == tool][
                        "TOOL_NAME"
                    ],
                    name=tool,
                    marker=dict(color=colors[i % len(colors)]),
                )
            )
        fig_tool.update_layout(title="TOOL_NAME")
        tool_plot_path = f"{tool_recipe_folder}/{feature_name}_{step_name}_tool.html"
        fig_tool.write_html(tool_plot_path)
        plot_paths.append(tool_plot_path)
        plt.close("all")

        # Box plot for RECIPE_NAME
        fig_recipe = go.Figure()
        unique_recipes = merged_tool_recipe["RECIPE_NAME"].unique()
        for i, recipe in enumerate(unique_recipes):
            fig_recipe.add_trace(
                go.Box(
                    y=merged_tool_recipe[merged_tool_recipe["RECIPE_NAME"] == recipe][
                        feature_name
                    ],
                    x=merged_tool_recipe[merged_tool_recipe["RECIPE_NAME"] == recipe][
                        "RECIPE_NAME"
                    ],
                    name=recipe,
                    marker=dict(color=colors[i % len(colors)]),
                )
            )
        fig_recipe.update_layout(title="RECIPE_NAME")
        recipe_plot_path = (
            f"{tool_recipe_folder}/{feature_name}_{step_name}_recipe.html"
        )
        fig_recipe.write_html(recipe_plot_path)
        plot_paths.append(recipe_plot_path)
        plt.close("all")

        # Scatter plot for START_DATE
        fig_start_date = go.Figure()
        fig_start_date.add_trace(
            go.Scatter(
                x=merged_tool_recipe["START_DATE"],
                y=merged_tool_recipe[feature_name],
                mode="markers",
                name="START_DATE",
                marker=dict(color="blue"),
            )
        )

        scatter_fig = px.scatter(
            merged_tool_recipe,
            x="START_DATE",
            y=feature_name,
            trendline="lowess",
            trendline_options=dict(frac=0.2),
        )
        trendline = scatter_fig.data[1]  # Extract the trendline data

        fig_start_date.add_trace(
            go.Scatter(
                x=trendline["x"],
                y=trendline["y"],
                mode="lines",
                name="Trendline",
                line=dict(color="red"),
            )
        )
        fig_start_date.update_layout(title="START_DATE")
        start_date_plot_path = (
            f"{tool_recipe_folder}/{feature_name}_{step_name}_start_date.html"
        )
        fig_start_date.write_html(start_date_plot_path)
        plot_paths.append(start_date_plot_path)
        plt.close("all")

        return plot_paths
