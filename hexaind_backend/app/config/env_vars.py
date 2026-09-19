from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Optional
import os
import logging

from pydantic import AmqpDsn, AnyHttpUrl, DirectoryPath, RedisDsn, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__package__)


def get_secret(key):
    """Get a secret from the configured secret manager"""
    from app.core.services.cloud_utils.utils import get_secret_manager

    secret_manager = get_secret_manager()
    return secret_manager.get_secret(key)


class ClientId(str, Enum):
    UC = "UC"
    P = "P"
    TSL = "TSL"
    VM1 = "VM1"
    VM2 = "VM2"
    TEST1 = "TEST1"
    TEST2 = "TEST2"
    NVLS05 = "NVLS05"
    SPOCK05 = "SPOCK05"


class ThermocalcEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("thermocalc.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: name.upper(),
    )
    thermocalc_home: Optional[Path] = None
    thermo_calc_service_url: Optional[str] = None
    max_polling_count_for_tc_status: int = 100
    seconds_to_sleep_for_tc_status: int = 10
    thermocalc_batch_limit: int = 1
    thermocalc_host: str = "KSWNNAWPLICAP01.novelis.biz"
    thermocalc_path: str


class ElasticEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="elastic_",
        env_file=("monitoring.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: f"elastic_{name}".upper(),
    )

    username: str
    password: str
    url: AnyHttpUrl


class CeleryEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("celery.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: name.upper(),
    )

    celery_result_backend_url: RedisDsn
    celery_broker_url: AmqpDsn
    broker_connection_retry: bool = True
    broker_connection_max_retries: Optional[int] = None
    broker_connection_retry_delay: int = 5
    broker_connection_retry_on_startup: bool = True
    task_ignore_result: bool = True
    task_acks_late: bool = True
    celery_worker_autoscale: str
    worker_prefetch_multiplier: int = 1
    worker_cancel_log_running_tasks_on_connection_loss: bool = False
    worker_max_tasks_per_child: int = 1


class AirflowEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="airflow_",
        env_file=("backend.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: f"airflow_{name}".upper(),
    )

    proj_dir: Path
    uid: int = 1000
    username: str
    password: str
    url: AnyHttpUrl


class AppHubEnvironment(BaseSettings):
    """Environment settings for AppHub service."""
    model_config = SettingsConfigDict(
        env_prefix="apphub_",
        env_file=("backend.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: f"apphub_{name}".upper(),
    )
    
    host: str = "https://hexaind-op-sage1-apphub.corp.databrick.tech"
    username: str = "admin"
    password: str = "changeme"


class JupyterHubEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="jupyterhub_",
        env_file=("jupyterhub.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: f"jupyterhub_{name}".upper(),
    )
    api_url: AnyHttpUrl
    api_token: str
    redirect_url: AnyHttpUrl

    @property
    def data_dir(self) -> Path:
        dir = environment.hexaind_data / "jupyterhub_data"
        dir.mkdir(exist_ok=True, parents=True)
        return dir
    
    def project_dir(self, project_id: str) -> Path:
        dir = self.data_dir / f"p_{project_id}"
        dir.mkdir(exist_ok=True, parents=True)
        dir.chmod(0o777)
        return dir

    def project_data(self, project_id: str) -> Path:
        dir = self.project_dir(project_id) / "data"
        dir.mkdir(exist_ok=True, parents=True)
        dir.chmod(0o777)
        return dir

    def project_modules(self, project_id: str) -> Path:
        dir = self.project_dir(project_id) / "modules"
        dir.mkdir(exist_ok=True, parents=True)
        dir.chmod(0o777)
        return dir

    def workflow_dir(self, project_id: str, workflow_id: str) -> Path:
        dir = self.project_dir(project_id) / f"w_{workflow_id}"
        dirs = [
            dir / "published", # published dir
            dir / "master", # master working dir
            dir / "data", # workflow data dir
        ]
        for dir_ in dirs:
            dir_.mkdir(exist_ok=True, parents=True)
            dir_.chmod(0o777)
        return dir

class RescaleEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="rescale_",
        env_file=("backend.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: f"rescale_{name}".upper(),
    )

    uri: str
    socket_url: str
    status_interval: int

class GatewayEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="gateway_",
        env_file=("backend.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: f"gateway_{name}".upper(),
    )

    uri: AnyHttpUrl
    superset_url: AnyHttpUrl
    username: str = "admin"
    password: str = "admin"


class Environment(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        alias_generator=lambda name: name.upper(),
    )

    # deployment type
    is_standalone_deployment: bool = False

    # Directory Paths
    hexaind_data: DirectoryPath
    hexaind_home: DirectoryPath
    hexaind_drive: DirectoryPath
    hexaind_destination: Path

    # client_id: ClientId

    hexaind_2_api_url: Optional[AnyHttpUrl] = None
    max_workers_for_assets_router: int = 10

    server_admin_email_to_create_if_no_server_admin: str = ""
    server_admin_is_sso_user: bool = False
    server_admin_password: str = ""
    first_name: str = ""
    last_name: str = ""

    # MLFlow
    mlflow_tracking_uri: str = ""

    ## External App Ports used by Jupyter containers
    external_app_port_start: int = 0
    external_app_port_end: int = 0

    # Scrap Analysis
    scrap_default_config: str = "app/services/apps/scrap_analysis/sam2024/config.ini"

    # image analytics socket
    image_progress_socket: str = ""
    image_batch_processing_socket: str = ""

    user_inactive_after_secs: int = 300
    user_logout_after_secs: int = 60*60*24*15

    container_socket: str = "/var/run/docker.sock"

    # gcp credentials
    external_google_creds_path: str = ""
    google_application_credentials: str = ""

    @property
    def mongo_details(self) -> str:
        # if self.is_standalone_deployment:
        #     return os.getenv("MONGO_DETAILS")
        # mongodb_url = get_secret("mongo-details-with-credentials")
        # if self.is_standalone_deployment:
        #     auth_info = mongodb_url.split("@")[0]
        #     mongo_details_env = os.getenv("MONGO_DETAILS")
        #     if mongo_details_env != "NONE":
        #         return mongo_details_env
        #     ip_address = os.environ.get(
        #         "VM_INTERNAL_IP", "default_ip"
        #     )  # Provide a default IP if not found
        #     port = os.environ.get(
        #         "MONGO_EXPOSED_PORT", "default_port"
        #     )  # Provide a default port if not found
        #     return f"{auth_info}@{ip_address}:{port}/"
        # return mongodb_url
        return "mongodb://localhost:27017/"
       
    
    @property
    def thermocalc_mongo_detail(self)->str:
        return os.getenv("THERMOCALC_MONGO_DETAILS")

    hexaind3_database_name: str = "Hexaind"

    # micron specific
    dev_mode: bool = False
    tdam_shared_path: Path = Field(
        validation_alias=AliasChoices("tdam_shared_path", "hexaind_data")
    )

    @property
    def tdam_datacatalog_path(self) -> DirectoryPath:
        folder = self.tdam_shared_path / "DATABRICK" / "DATA_CATALOG"
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    def tdam_datacatalog_sessions_path(self, job_id: str) -> Path:
        folder = (
            self.tdam_shared_path
            / "DATABRICK"
            / "DATA_CATALOG_SESSIONS"
            / f"data_pull_job_{job_id}"
        )
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    def override_tdam_datacatalog_sessions_path_for_cpw(
        self, job_id: str, stage: str
    ) -> Path:
        folder = (
            self.hexaind_data
            / "DATABRICK"
            / "DATA_CATALOG_SESSIONS"
            / f"data_pull_job_{job_id}"
            / f"{stage}"
        )
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    @property
    def tdam_datacatalog_databrick_session_path_format(self) -> str:
        folder = self.tdam_shared_path / "DATABRICK" / "DATA_CATALOG_SESSIONS"
        folder.mkdir(exist_ok=True, parents=True)
        return str(folder) + "/data_pull_job_{}"

    @property
    def tdam_cache_path(self) -> DirectoryPath:
        folder = self.tdam_datacatalog_path / "CACHE"
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    @property
    def tdam_pre_cache_path(self) -> DirectoryPath:
        folder = self.tdam_datacatalog_path / "PRE_CACHE"
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    @property
    def tdam_upload_path(self) -> DirectoryPath:
        folder = self.tdam_datacatalog_path / "UPLOAD"
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    @property
    def gcp_client_id(self) -> str:
        return get_secret("gcp-client-id")

    hexaind_front_end_url: str = "http://localhost:4200"
    form_login_allowed: bool = True
    sso_login_allowed: bool = True
    show_all_ad_users: bool = False

    @property
    def invite_from_email(self) -> str:
        return get_secret("invite-from-email")

    @property
    def send_email_using(self):
        # sendgrid or smtp, if smtp, please have a secret 'smtp-server-port-email-password-as-csv' and enable ir
        return get_secret("send-email-using")

    @property
    def smtp_server_port_email_password_csv(self):
        return get_secret(
            "smtp-server-port-email-password-as-csv"
        )  # For gmail account 'smtp.gmail.com,587,<gmail_id>,<gmail_pwd>'

    @property
    def sendgrid_api_key(self) -> str:
        return get_secret("sendgrid-api-key")

    @cached_property
    def data_folder(self) -> Path:
        folder = self.hexaind_data
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def home_folder(self) -> Path:
        folder = self.hexaind_home
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def data_folder_format_string(self) -> str:
        folder = self.hexaind_data
        folder_prefix = folder / "datasets"
        folder_prefix.mkdir(parents=True, exist_ok=True)
        return (
            str(folder_prefix) + "/p_{}/Workflow_Results/wf_{}/r_{}"
        )  # project_id , wf_id, run_id

    @cached_property
    def data_folder_format_string_for_published_wf(self) -> str:
        folder = self.hexaind_data
        folder_prefix = folder / "datasets"
        folder_prefix.mkdir(parents=True, exist_ok=True)
        return (
            str(folder_prefix) + "/p_{}/Workflow_Results/wf_{}/wf_{}/r_{}"
        )  # project_id , master wf id, wf_id, run_id

    @cached_property
    def wf_inputs_folder(self) -> str:
        folder = self.hexaind_data
        folder_prefix = folder / "datasets"
        folder_prefix.mkdir(parents=True, exist_ok=True)
        return str(folder_prefix) + "/p_{}/Workflow_Inputs/wf_{}/"  # project_id , wf_id

    @property
    def base_path(self) -> Path:
        return self.data_folder

    @cached_property
    def logs_folder(self) -> Path:
        folder = self.home_folder / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def validation_logs_folder(self) -> Path:
        folder = self.logs_folder / "validation_logs"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def datasets_folder(self) -> Path:
        folder = self.data_folder / "datasets"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def datasets_cache_folder(self) -> Path:
        folder = self.datasets_folder / "cache"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def modules_folder(self) -> Path:
        folder = self.data_folder / "modules"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def wf_configs_folder(self) -> str:
        folder = self.hexaind_data
        folder_prefix = folder / "configs"
        folder_prefix.mkdir(parents=True, exist_ok=True)
        return folder_prefix

    @cached_property
    def cpw_results_folder(self) -> str:
        folder = self.datasets_folder
        folder_prefix = folder
        folder_prefix.mkdir(parents=True, exist_ok=True)
        return str(folder_prefix) + "/r_{}/custom_code_results"

    @cached_property
    def wf_action_results_folder(self) -> Path:
        folder = self.hexaind_data
        folder_prefix = folder / "action_results"
        folder_prefix.mkdir(parents=True, exist_ok=True)
        return folder_prefix

    @cached_property
    def custom_python_code_datasets_location(self) -> str:
        """path used to create a dataset when default values are converted to datasets"""
        folder = self.datasets_folder / "custom_python_code_datasets"
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)

    @cached_property
    def redis_data_folder(self) -> Path:
        folder = self.hexaind_data / "redis_data"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def jupyter_hub_folder(self) -> Path:
        folder = self.hexaind_data / "jupyterhub"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @cached_property
    def feature_configs_folder(self) -> Path:
        folder = self.hexaind_data / "features"
        folder.mkdir(parents=True, exist_ok=True)
        # if not folder.exists():
        #     raise FileNotFoundError("The feature config doesn't exist. Please check")
        return folder

    @property
    def get_features_file(self) -> Path:

        # TODO: As part of enhancement, we can move all the common features to one file and read, then remaining required features -> Dictionary

        id = os.getenv("CLIENT_FLAG")
        logger.info(f"CLIENT_ID: {id}")
        # id = self.cliend_id
        base_path = Path(Path(__file__).parent)
        if id:
            feature_file = base_path / f"feature_flags_{str(id)}.json"
            logger.info(f"ID: {id} | Feature file: {feature_file}")
        else:
            feature_file = ""
            logger.info(f"ID: {id} Feature file: {feature_file}")

        return feature_file


class CPWConstants(BaseSettings):
    data_source_path: str = Field(
        default="DATA_SOURCE_PATH",
        description="The path of data in pd.Dataframe return type, used as key in pd.Dataframe.attr's."
    )
    class Config:
        allow_mutation = False

environment = Environment()  # type: ignore
celery_environment = CeleryEnvironment()  # type: ignore
airflow_environment = AirflowEnvironment()  # type: ignore
jupyterhub_environment = JupyterHubEnvironment()  # type: ignore
rescale_environment = RescaleEnvironment()  # type: ignore
thermocalc_environment = ThermocalcEnvironment()  # type: ignore
cpw_constants = CPWConstants()
gateway_environment = GatewayEnvironment() # type: ignore
apphub_environment = AppHubEnvironment() # type: ignore