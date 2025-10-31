from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class RoleDelegationCreate(BaseModel):
    delegator_sid: str
    delegate_sid: str
    role_id: str
    effective_from: date
    effective_to: date
    is_active: bool = True

class RoleDelegationResponse(BaseModel):
    delegation_id: str
    delegator_sid: str
    delegate_sid: str
    role_id: str
    effective_from: date
    effective_to: date
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CardholderDataResponse(BaseModel):
    record_id: str
    upload_id: str
    quarter_id: str
    certifier_id: str
    area_owner_sid: Optional[str] = None
    area_owner_name: Optional[str] = None
    area_name: Optional[str] = None
    employee_sid: Optional[str] = None
    employee_name: Optional[str] = None
    team: Optional[str] = None
    access_to_area_allowed: Optional[bool] = None
    region: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    access_type: Optional[str] = None
    access_from_date: Optional[date] = None
    access_to_date: Optional[date] = None
    public_private_designation: Optional[str] = None
    cost_center_code_department_id: Optional[str] = None
    cost_center_name_department_name: Optional[str] = None
    csh_level_5_name: Optional[str] = None
    csh_level_6_name: Optional[str] = None
    csh_level_7_name: Optional[str] = None
    csh_level_8_name: Optional[str] = None
    csh_level_9_name: Optional[str] = None
    csh_level_10_name: Optional[str] = None
    process_owner_status: str
    area_owner_status: str
    certifier_status: str
    process_owner_comment: Optional[str] = None
    area_owner_comment: Optional[str] = None
    certifier_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    history: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class CardholderDataUpdate(BaseModel):
    record_id: str
    area_owner_sid: Optional[str] = None
    area_owner_name: Optional[str] = None
    area_name: Optional[str] = None
    employee_sid: Optional[str] = None
    employee_name: Optional[str] = None
    team: Optional[str] = None
    access_to_area_allowed: Optional[bool] = None
    region: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    access_type: Optional[str] = None
    access_from_date: Optional[date] = None
    access_to_date: Optional[date] = None
    public_private_designation: Optional[str] = None
    cost_center_code_department_id: Optional[str] = None
    cost_center_name_department_name: Optional[str] = None
    csh_level_5_name: Optional[str] = None
    csh_level_6_name: Optional[str] = None
    csh_level_7_name: Optional[str] = None
    csh_level_8_name: Optional[str] = None
    csh_level_9_name: Optional[str] = None
    csh_level_10_name: Optional[str] = None
    process_owner_status: Optional[str] = None
    area_owner_status: Optional[str] = None
    certifier_status: Optional[str] = None
    process_owner_comment: Optional[str] = None
    area_owner_comment: Optional[str] = None
    certifier_comment: Optional[str] = None

class StatusResponse(BaseModel):
    process_owner: Dict[str, int]
    area_owner: Dict[str, int]
    certifier: Dict[str, int]

class ReportRequest(BaseModel):
    start_date: date
    end_date: date
    quarter_id: Optional[str] = None
    status_filter: Optional[str] = None
    certifier_id: Optional[str] = None
