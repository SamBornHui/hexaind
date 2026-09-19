from datetime import datetime
from pathlib import Path
import logging
import shutil
import os
import toml
from typing import List
import requests

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient

from app.config.env_vars import environment, jupyterhub_environment
from app.api.endpoints.v1.jupyter.hub.schemas import JupyterNBPathType, JupyterNBTypeObj

logger = logging.getLogger(__package__)


class JupyterHubService:

    def __init__(
        self, db_sync_client: MongoClient, db_async_client: AsyncIOMotorClient
    ):
        self.db_sync_client = db_sync_client
        self.db_async_client = db_async_client
        logger.info("Initialized the init method")

    async def fetch_paths_and_types(
        self, project_id, user_id: str = None
    ) -> List[JupyterNBTypeObj]:  # , user_id
        # base_dir = environment.jupyter_hub_folder
        # root_dir = Path(f"{base_dir}/{project_id}")

        base_dir = environment.jupyter_hub_folder
        master_notebooks_dir = base_dir / f"p_{project_id}/master_notebooks"
        paths_to_check = [master_notebooks_dir]
        if user_id:
            root_dir = base_dir / f"p_{project_id}/u_{user_id}"
            if root_dir.exists():
                paths_to_check.append(root_dir)

        result = []
        try:
            base_url = (
                f"{jupyterhub_environment.api_url}/user/{project_id}/api/sessions"
            )
            response = requests.get(
                base_url, params={"token": jupyterhub_environment.api_token}
            )
            sessions_response = response.json()

            for path in paths_to_check:
                if path.exists():
                    file_paths_all = list(path.rglob("main.ipynb"))
                    for file_path in file_paths_all:
                        session = {
                            "kernel": {
                                "execution_state": "no session",
                                "last_activity": None,
                            }
                        }

                        logger.info(f"filepath: {file_path} - Session: {session}")
                        folder_name = file_path.parent.name
                        path_type = (
                            JupyterNBPathType.MASTER
                            if "master_notebooks" in str(file_path)
                            else JupyterNBPathType.CLONE
                        )
                        remaining_path = (
                            str(file_path.parent)
                            .replace(str(base_dir), "", 1)
                            .lstrip("/")
                        )
                        for ses in sessions_response:
                            if (
                                ses["name"] == "main.ipynb"
                                and remaining_path in ses["path"]
                            ):
                                session = ses
                                break

                        description = ""
                        # pick up description from toml file if exists
                        pkg_toml_file = file_path.parent / "pyproject.toml"
                        try:
                            if pkg_toml_file.exists():
                                with open(str(pkg_toml_file), "r") as f:
                                    config = toml.load(f)
                                    description = config["project"]["description"]
                        except Exception as e:
                            logger.error(
                                f"error when reading toml file from {pkg_toml_file} , {str(e)}"
                            )
                            pass
                        last_act = session["kernel"]["last_activity"]
                        obj = JupyterNBTypeObj(
                            name=folder_name,
                            nb_type=path_type,
                            launch_url=f"{jupyterhub_environment.redirect_url}user/{project_id}/notebooks/{remaining_path}/main.ipynb?token={jupyterhub_environment.api_token}",
                            relative_path=remaining_path,
                            description=description,
                            last_activity=last_act if last_act else None,
                            status=session["kernel"]["execution_state"],
                        )
                        result.append(obj)

        except Exception as e:
            logger.exception(f"Failed with Exception: {str(e)}")

        return result

    async def clone_or_promote(self, src: str, dest: str):
        """
        Copy a folder with its entire contents to a different destination.

        :param src: Source directory path to copy.
        :param dest: Destination directory path where the folder should be copied.
        """
        # Ensure the source exists
        if not os.path.exists(src):
            logger.exception(f"The source directory '{src}' does not exist.")
            raise FileNotFoundError(f"The source directory '{src}' does not exist.")

        # Ensure the destination directory exists, if not, create it
        if not os.path.exists(dest):
            logger.info(f"Created destination path - {dest}")
            os.makedirs(dest)

        try:
            # Copy the entire directory tree from src to dest
            shutil.copytree(src, dest, dirs_exist_ok=True)
            logger.info(f"Successfully copied '{src}' to '{dest}'.")

            return True

        except Exception as e:
            logger.exception(f"Failed to copy directory: {e}")
            raise e
