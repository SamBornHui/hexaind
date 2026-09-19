import hashlib
import hmac
import logging
import shutil
import tempfile
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config.env_vars import environment
from app.core.db.db_utils import close_db_sync, get_db_sync
from app.services.data.assets.custom_python_widget_recipes.service import (
    CustomPythonWidgetRecipeService,
)
from app.services.data.assets.custom_python_widgets.service import (
    CustomPythonWidgetService,
)
from app.services.data.assets.modules.service import ModuleService
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.sessions.service import WorkflowSessionService
from app.services.workflows.workflow_designer.service import (
    InteractiveWorkflowDesginerService,
)

logger = logging.getLogger(__name__)


class ImpExService:
    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,  # type: ignore
    ):
        self.session_service = WorkflowSessionService(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.workflow_designer_service = WorkflowDesignerService(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.interactive_workflow_designer_service = InteractiveWorkflowDesginerService(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.custom_python_widget_recipe_service = CustomPythonWidgetRecipeService(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.module_service = ModuleService(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

        self.db_sync_client = get_db_sync()
        self.custom_python_widget_service = CustomPythonWidgetService(
            db_sync_client=self.db_sync_client, db_async_client=db_async_client
        )
        self.base_path = environment.modules_folder
        self.temp_dir = tempfile.mkdtemp()
        self.module_files: List[str] = []
        self.zip_file_path: Optional[str] = None

        self.secret_key = "This_Is_Not_Secure_Secret_Key"  # this is experimental. TODO: use Azure Key Vault

    def compute_hmac(self, file_path: str) -> str:
        """
        Computes HMAC of the given file using the secret key.

        Args:
            file_path (str): Path to the file for which HMAC is computed.

        Returns:
            str: Hexadecimal representation of the HMAC.
        """
        logger.debug(f"Computing HMAC for file: {file_path}")
        secret_key = self.secret_key.encode()
        hmac_hash = hmac.new(secret_key, digestmod=hashlib.sha256)
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hmac_hash.update(chunk)
        hmac_value = hmac_hash.hexdigest()
        logger.debug(f"Computed HMAC: {hmac_value}")
        return hmac_value

    def compare_hmac(self, stored_hmac: str, generated_hmac: str) -> bool:
        """
        Compares two HMAC (Hash-based Message Authentication Code) values for equality.

        Args:
            stored_hmac (str): The HMAC value that was previously stored.
            generated_hmac (str): The newly computed HMAC value to compare against the stored HMAC.

        Returns:
            bool: True if the HMAC values are equal, False otherwise.
        """
        return hmac.compare_digest(stored_hmac, generated_hmac)

    def cleanup(self):
        """
        Cleans up temporary files and directories used during the workflow import/export process.
        """
        try:
            shutil.rmtree(self.temp_dir)
            logger.debug(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error removing temporary directory {self.temp_dir}: {e}")
        self.temp_dir = None
        self.zip_file_path = None
        self.module_files = []
        close_db_sync(self.db_sync_client)
        logger.info("Cleanup completed")
