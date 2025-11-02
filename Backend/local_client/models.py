"""
Pydantic models for API communication
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from pydantic import BaseModel, Field
from uuid import UUID


class CameraSchema(BaseModel):
    """Camera information"""
    id: str
    name: str
    ip_address: str
    rtsp_url: str
    rtsp_url_sub: Optional[str] = None
    camera_type: str = "rtsp"
    location: Optional[str] = None
    record_quality: str = "medium"
    
    class Config:
        from_attributes = True


class ScheduleSchema(BaseModel):
    """Recording schedule"""
    id: str
    name: str
    schedule_type: str  # once, daily, weekly, continuous
    start_time: str  # HH:MM:SS format
    end_time: str  # HH:MM:SS format
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None  # YYYY-MM-DD format
    days_of_week: List[str] = []  # ['monday', 'tuesday', ...]
    is_active: bool = True
    camera: CameraSchema
    
    class Config:
        from_attributes = True


class RecordingRegistrationRequest(BaseModel):
    """Request to register a new recording"""
    camera_id: str
    schedule_id: Optional[str] = None
    recording_name: Optional[str] = None


class RecordingRegistrationResponse(BaseModel):
    """Response from recording registration"""
    recording_id: str
    message: str


class RecordingStatusUpdate(BaseModel):
    """Recording status update"""
    recording_id: str
    status: str  # scheduled, recording, completed, failed, stopped
    progress: Optional[float] = Field(None, ge=0, le=100)
    frames_recorded: Optional[int] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    gcp_path: Optional[str] = None


class HeartbeatData(BaseModel):
    """Heartbeat data"""
    client_id: str
    active_recordings: int
    available_space_gb: float
    last_upload: Optional[datetime] = None
    system_info: Optional[Dict[str, Any]] = None


class HeartbeatResponse(BaseModel):
    """Heartbeat response"""
    message: str
    client_id: str
    status: str


class StatusUpdateResponse(BaseModel):
    """Response to status update"""
    message: str

