from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class NotificationType(str, Enum):    
    
    SUCCESS = 'SUCCESS'

    ERROR = 'ERROR'

    INFO = 'INFO'

    WARNING = 'WARNING'

    SYSTEM = 'SYSTEM'


class Notification(BaseModel):
    
    message: Optional[str] = Field(..., description="Notification message")

    workflow_id: Optional[str] = Field(..., description="Workflow ID this is associated with, if any")

    read: Optional[bool] = Field(default=False, description="Marked as read or not")
    
    notification_type: Optional[NotificationType]= Field(..., description="Notification type")

    created_at: Optional[datetime] = Field(default=None, description="Created Date and Time UTC format")

    user_id: Optional[str] = Field(default=None, description="User Id")

    id: Optional[str] = Field(default=None, description="User Id", alias="_id")

