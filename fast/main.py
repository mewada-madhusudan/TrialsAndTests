from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
from datetime import datetime, date
import pandas as pd
import json
import os
import uuid
from io import BytesIO

from database import DatabaseManager
from schemas import (
    RoleDelegationCreate, RoleDelegationResponse, CardholderDataResponse,
    CardholderDataUpdate, StatusResponse, ReportRequest
)

app = FastAPI(title="Cardholder Management API", version="1.0.0")

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("reports", exist_ok=True)

@app.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    quarter_id: str = Query(...),
    uploaded_by: str = Query(...),
):
    """Upload Excel file with cardholder data and save to database"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are allowed")
        
        # Save uploaded file
        file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Create data upload record
        upload_data = {
            'quarter_id': quarter_id,
            'uploaded_by': uploaded_by,
            'file_name': file.filename,
            'file_path': file_path,
            'file_size': len(content),
            'upload_status': 'processing',
            'records_count': len(df)
        }
        upload_id = DatabaseManager.create_data_upload(upload_data)
        
        # Process each row and create cardholder data records
        records_created = 0
        for _, row in df.iterrows():
            try:
                record_data = {
                    'upload_id': upload_id,
                    'quarter_id': quarter_id,
                    'certifier_id': str(row.get('certifier_id', '')),
                    'area_owner_sid': str(row.get('Area_Owner_SID', '')) if pd.notna(row.get('Area_Owner_SID')) else None,
                    'area_owner_name': str(row.get('Area_Owner_Name', '')) if pd.notna(row.get('Area_Owner_Name')) else None,
                    'area_name': str(row.get('Area_Name', '')) if pd.notna(row.get('Area_Name')) else None,
                    'employee_sid': str(row.get('Employee_SID', '')) if pd.notna(row.get('Employee_SID')) else None,
                    'employee_name': str(row.get('Employee_Name', '')) if pd.notna(row.get('Employee_Name')) else None,
                    'team': str(row.get('Team', '')) if pd.notna(row.get('Team')) else None,
                    'access_to_area_allowed': bool(row.get('Access_to_Area_allowed_(Y-N)', False)) if pd.notna(row.get('Access_to_Area_allowed_(Y-N)')) else None,
                    'region': str(row.get('Region', '')) if pd.notna(row.get('Region')) else None,
                    'country_name': str(row.get('Country_Name', '')) if pd.notna(row.get('Country_Name')) else None,
                    'city': str(row.get('City', '')) if pd.notna(row.get('City')) else None,
                    'access_type': str(row.get('Access_Type', '')) if pd.notna(row.get('Access_Type')) else None,
                    'access_from_date': pd.to_datetime(row.get('Access_FROM_Date')).date() if pd.notna(row.get('Access_FROM_Date')) else None,
                    'access_to_date': pd.to_datetime(row.get('Access_TO_Date')).date() if pd.notna(row.get('Access_TO_Date')) else None,
                    'public_private_designation': str(row.get('Public-Private_Designation', '')) if pd.notna(row.get('Public-Private_Designation')) else None,
                    'cost_center_code_department_id': str(row.get('Cost_Center_Code-Department_Id', '')) if pd.notna(row.get('Cost_Center_Code-Department_Id')) else None,
                    'cost_center_name_department_name': str(row.get('Cost_Center_Name-Department_Name', '')) if pd.notna(row.get('Cost_Center_Name-Department_Name')) else None,
                    'csh_level_5_name': str(row.get('CSH_Level_5_Name', '')) if pd.notna(row.get('CSH_Level_5_Name')) else None,
                    'csh_level_6_name': str(row.get('CSH_Level_6_Name', '')) if pd.notna(row.get('CSH_Level_6_Name')) else None,
                    'csh_level_7_name': str(row.get('CSH_Level_7_Name', '')) if pd.notna(row.get('CSH_Level_7_Name')) else None,
                    'csh_level_8_name': str(row.get('CSH_Level_8_Name', '')) if pd.notna(row.get('CSH_Level_8_Name')) else None,
                    'csh_level_9_name': str(row.get('CSH_Level_9_Name', '')) if pd.notna(row.get('CSH_Level_9_Name')) else None,
                    'csh_level_10_name': str(row.get('CSH_Level_10_Name', '')) if pd.notna(row.get('CSH_Level_10_Name')) else None,
                    'history': json.dumps([{
                        "action": "created",
                        "timestamp": datetime.now().isoformat(),
                        "user": uploaded_by
                    }])
                }
                DatabaseManager.create_cardholder_record(record_data)
                records_created += 1
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        # Update upload status
        DatabaseManager.update_upload_status(upload_id, "completed", records_created)
        
        return {
            "message": "File uploaded successfully",
            "upload_id": upload_id,
            "records_processed": records_created,
            "total_rows": len(df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/records")
async def fetch_records(
    quarter_id: Optional[str] = Query(None),
    certifier_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
):
    """Fetch records from cardholder_data table"""
    try:
        records = DatabaseManager.get_cardholder_records(
            quarter_id=quarter_id,
            certifier_id=certifier_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {str(e)}")

@app.post("/save-records")
async def save_records(
    records: List[CardholderDataUpdate],
    updated_by: str = Query(...),
):
    """Save modified records back to database"""
    try:
        updated_count = 0
        for record_update in records:
            update_data = record_update.dict(exclude_unset=True)
            record_id = update_data.pop('record_id')
            
            if DatabaseManager.update_cardholder_record(record_id, update_data, updated_by):
                updated_count += 1
        
        return {"message": f"Successfully updated {updated_count} records"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving records: {str(e)}")

@app.get("/delegates")
async def fetch_delegates(
    is_active: Optional[bool] = Query(None),
    role_id: Optional[str] = Query(None),
):
    """Fetch records from role_delegations table"""
    try:
        delegations = DatabaseManager.get_role_delegations(
            is_active=is_active,
            role_id=role_id
        )
        return delegations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching delegates: {str(e)}")

@app.post("/make-delegate")
async def make_delegate(delegation: RoleDelegationCreate):
    """Create a new role delegation record"""
    try:
        delegation_data = delegation.dict()
        delegation_id = DatabaseManager.create_role_delegation(delegation_data)
        
        # Return the created delegation
        delegations = DatabaseManager.get_role_delegations()
        created_delegation = next((d for d in delegations if d['delegation_id'] == delegation_id), None)
        
        return created_delegation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating delegation: {str(e)}")

@app.get("/report")
async def generate_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    quarter_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    certifier_id: Optional[str] = Query(None),
):
    """Generate Excel report with date range and filters"""
    try:
        records = DatabaseManager.get_records_for_report(
            start_date=start_date,
            end_date=end_date,
            quarter_id=quarter_id,
            status_filter=status_filter,
            certifier_id=certifier_id
        )
        
        # Convert to DataFrame
        data = []
        for record in records:
            data.append({
                'Record ID': record['record_id'],
                'Upload ID': record['upload_id'],
                'Quarter ID': record['quarter_id'],
                'Certifier ID': record['certifier_id'],
                'Area Owner SID': record['area_owner_sid'],
                'Area Owner Name': record['area_owner_name'],
                'Area Name': record['area_name'],
                'Employee SID': record['employee_sid'],
                'Employee Name': record['employee_name'],
                'Team': record['team'],
                'Access to Area Allowed': record['access_to_area_allowed'],
                'Region': record['region'],
                'Country Name': record['country_name'],
                'City': record['city'],
                'Access Type': record['access_type'],
                'Access From Date': record['access_from_date'],
                'Access To Date': record['access_to_date'],
                'Public Private Designation': record['public_private_designation'],
                'Cost Center Code Department ID': record['cost_center_code_department_id'],
                'Cost Center Name Department Name': record['cost_center_name_department_name'],
                'CSH Level 5 Name': record['csh_level_5_name'],
                'CSH Level 6 Name': record['csh_level_6_name'],
                'CSH Level 7 Name': record['csh_level_7_name'],
                'CSH Level 8 Name': record['csh_level_8_name'],
                'CSH Level 9 Name': record['csh_level_9_name'],
                'CSH Level 10 Name': record['csh_level_10_name'],
                'Process Owner Status': record['process_owner_status'],
                'Area Owner Status': record['area_owner_status'],
                'Certifier Status': record['certifier_status'],
                'Process Owner Comment': record['process_owner_comment'],
                'Area Owner Comment': record['area_owner_comment'],
                'Certifier Comment': record['certifier_comment'],
                'Created At': record['created_at'],
                'Updated At': record['updated_at']
            })
        
        df = pd.DataFrame(data)
        
        # Generate report file
        report_filename = f"cardholder_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        report_path = f"reports/{report_filename}"
        
        df.to_excel(report_path, index=False)
        
        return FileResponse(
            path=report_path,
            filename=report_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/status")
async def get_status_counts(quarter_id: Optional[str] = Query(None)):
    """Get count of different statuses"""
    try:
        status_counts = DatabaseManager.get_status_counts(quarter_id=quarter_id)
        return status_counts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status counts: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Cardholder Management API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
