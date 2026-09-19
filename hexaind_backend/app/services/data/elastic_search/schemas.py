from pydantic import BaseModel, Field
from typing import List, Optional

class LogEntry(BaseModel):
    time: str = Field(..., description="The timestamp of the log entry.")

    log_level: str = Field(..., description="The level of the log entry (e.g., INFO, ERROR).")

    message: str = Field(..., description="The actual log message.")

    exc_info: Optional[str] = Field("N/A", description="Exception information if any; defaults to 'N/A' if not provided.")

class LogsResponse(BaseModel):
    logs: List[LogEntry] = Field(..., description="A list of log entries.")

    new_cursor_timestamp: Optional[str] = Field(None, description="The timestamp of the last log entry to use for pagination.")
    
    new_cursor_id: Optional[str] = Field(None, description="The ID of the last log entry to use for pagination.")
