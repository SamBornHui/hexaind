from typing import List, Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class SavedWorkflowsFromSession(BaseModel):

    workflow_id: str = Field(..., description="workflow id associated to session")

    workflow_version: str = Field(..., description="workflow version associated to session")

    name: str = Field(..., description="workflow name associated to session")

    description: str = Field(..., description="workflow description associated to session") 

    workflow_version: str = Field(..., description="workflow version tag")

    last_modified_by: Optional[str] = Field(default="", description="name of the user who modified the workflow")

    last_modified_at: Optional[datetime] = Field(default=None, description="wf last modified at time")

    created_at: Optional[datetime] = Field(default=None, description="wf created/published at time")

    created_by: Optional[str] = Field(default="",description="Name of user who published this workflow")

    last_run_status: Optional[str] = Field(default="N.A.", description="Workflow Last Run Status")

    last_run_at: Optional[datetime] = Field(default=None, description="Workflow Last Run At")

class WorkflowSessionDB(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the session object model")

    id: Optional[str] = Field(default=None, description="Workflow Id", alias="_id")

    name: str = Field(..., description="Session name")

    description: str = Field(..., description="Session description") 

    workflow_id: str = Field(..., description="Current workflow associated with session")

    saved_workflows: List[SavedWorkflowsFromSession] = Field(..., description="List of workflows associated to the current session")

    run_id: str = Field(..., description="Current workflow run_id associated with session") 

    owner_id: str = Field(default=None, description="ID of the user who created the session")
    
    owner_name: str = Field(default=None, description="Name of the user who created the session")

    created_at: datetime = Field(default=None, description="Created Date and Time UTC format")

    last_modified_by_id: str = Field(default=None, description="ID of the user who recently modified the session")

    last_modified_at: datetime = Field(default=None, description="Created Date and Time UTC format")

    project_id: str = Field(default=None, description="Project ID")

    site_id: str = Field(default=None, description="Site ID")

    last_run_status: Optional[str] = Field(default="N.A.", description="Workflow Last Run Status")

    last_run_at: Optional[datetime] = Field(default=None, description="Workflow Last Run At")

    is_template: Optional[bool] = Field(default=False, description="Indicates if the session is a template")

    template_screenshot: Optional[str] = Field(default=None, description="Indicates the session has template screenshot")
    
    favourited_by: Optional[List[str]] = Field(default=[], description="favouritee")


class CreateWorkflowSessionRequest(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the session object model")

    name: str = Field(..., description="Session name")

    description: str = Field(..., description="Session description") 

class CreateWorkflowSessionResponse(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the session object model")

    session_id: str = Field(..., description="Session id crested by server")


class GetAllSessionsResponse(BaseModel):

    sessions: List[WorkflowSessionDB]

    invalid_session_ids: Optional[List[str]] = Field(default=None,
                                                                description="Stores invalid wf/malformed session ids")

    sessions_count: int

    page_number: int

    page_limit: int


class FavouriteWorkflow(BaseModel):

    workflow_id: str = Field(..., description="id of session")

    user_id: str = Field(..., description="user_id")

    is_favourite: bool = Field(..., description="is_favouritee")

class FavouriteWorkflowResponse(BaseModel):

    message: str = Field(..., description="response message")

    workflow_id: str = Field(..., description="id of session")
