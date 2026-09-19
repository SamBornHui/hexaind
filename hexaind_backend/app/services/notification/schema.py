from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from bson import ObjectId

class NotificationType(str, Enum):
    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'
    INFO = 'INFO'
    WARNING = 'WARNING'
    SYSTEM = 'SYSTEM'

class NotificationMessages(str, Enum):
    WORKFLOW_FAILURE = "Workflow has failed"
    WORKFLOW_COMPLETE = "Workflow has successfully completed"
    WORKFLOW_PUBLISH = "Workflow has published"
    JOB_FAILURE = "Job has failed"
    JOB_COMPLETE = "Job has successfully completed"
    DATASET_CREATED = "Dataset has been created"
    DATASET_UPDATED = "Dataset has been updated"
    MODEL_TRAINING_STARTED = "Model training has started"
    MODEL_TRAINING_ENDED = "Model has been trained"
    MODEL_EVALUATION = "Model is being evaluated"


class NotificationStatus(BaseModel):
    status: bool
    user_id: str

class NotificationImportance(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH  = "HIGH"


class NotificationCategory(str, Enum):
    WORKFLOWS = "WORKFLOWS"
    MODEL = "MODEL"
    DATA = "DATA"
    SCHEDULED_JOBS = "SCHEDULED_JOBS"
    COLLABORATION_TASK = "COLLABORATION_TASK"
    HEALTH_SECURITY = "HEALTH_SECURITY"
    PREDICTION = "PREDICTION"
    EDA_GENERATION = "EDA_GENERATION"

class NotificationModel(BaseModel):
    message: str = Field(..., description="notification message")
    category_id: str = Field(..., description="id of any dataset ,workflow,job ")
    project_id: str = Field(None, description="project ID this is associated with, if any")
    read: list[str] = Field( default_factory=list, description="user that read notification")
    deleted_by_users: list[str] = Field( default_factory=list, description="user that read notification")
    notification_type: NotificationType = Field(..., description="Notification type")
    created_at: datetime = Field(default = datetime.now(timezone.utc), description="Created Date and Time ")
    last_updated: datetime = Field(default = datetime.now(timezone.utc), description="Update Date and Time")
    importance: NotificationImportance = Field(..., description="Importance of notification")
    notification_category: NotificationCategory=Field(..., description="Notification message")

class ExampleModel(BaseModel):
    optional_field: Optional[str]

class slack_configuration(BaseModel):
    token:str=Field(None,description="slack app token")
    channel_name:str=Field(None,description="slack channel name")


class NotificationConfiguration(BaseModel):
    user_id:str = Field(...,description="user Id")
    in_app_notification:bool = Field(default = True, description="in app notfication configuration")
    slack:slack_configuration = Field(None, description="slack configuration values for notification delivery")
    teams_channel_url:str = Field(None, description="channel url for notification delivery")
    email:str = Field(None, description="email for notification delivery")
    sms_number:int = Field(None,description="number for notification delivery")

class NotificationReport(BaseModel):
    no_of_users:int = Field(None,description='no of user count')
    workflow_notification_count :int = Field(None,description='workflow_notification_count')
    notification_model :int = Field(None,description='model_notification_count')
    data_notification_count  :int = Field(None,description='data_notification_count')
    scheduled_job_notification_count  :int = Field(None,description='scheduled_job_notification_count')
    collaboration_notification_count  :int = Field(None,description='collaboration_notification_count')
    health_security_notification_count :int = Field(None,description='healt_security_notification_count')
