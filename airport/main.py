from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from airport import crud as airport_crud
from typing import List
from airport.crud import process_airport_upload, airport_import_jobs
from airport.schemas import DeleteAirportRequest, BulkDeleteAirportRequest, BulkApproveAirportRequest
from airport.models import AirportData
from datetime import datetime
import json
import uuid
from airport.helper import REQUIRED_AIRPORT_FIELDS
from utils.pagination import PageNumberPagination


router = APIRouter(
    prefix="/airport"
)


@router.get(
    "/upload-airport-json-status/{task_id}",
    tags=["Airport"]
)
async def get_airport_upload_status(task_id: str):

    job = airport_import_jobs.get(task_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Airport upload task not found"
        )

    return job



@router.get("/airport-details/", tags=["Airport"])
async def get_airport(
    db: Session = Depends(get_db),
    pagination: PageNumberPagination = Depends(),
):
    return airport_crud.get_airport(db, pagination=pagination)



@router.post("/upload-airport-json", tags=["Airport"])
async def upload_airport_json(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
):
    files_data = []
    
    task_id = str(uuid.uuid4())

    for file in files:

        if not file.filename.lower().endswith(".json"):
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: Only JSON files are allowed."
            )

        content = await file.read()

        try:
            data = json.loads(content.decode("utf-8"))

        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: File must be UTF-8 encoded JSON."
            )

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid JSON format "
                    f"at line {e.lineno}, column {e.colno}."
                )
            )

        if not isinstance(data, dict):
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: JSON root must be an object."
            )

        missing_fields = []

        for section, fields in REQUIRED_AIRPORT_FIELDS.items():

            section_data = data.get(section)

            if not isinstance(section_data, dict):
                missing_fields.append(section)
                continue

            for field in fields:

                if field not in section_data:
                    missing_fields.append(
                        f"{section}.{field}"
                    )
                    continue

                value = section_data.get(field)

                if value is None:
                    missing_fields.append(
                        f"{section}.{field}"
                    )
                    continue

                if isinstance(value, str) and not value.strip():
                    missing_fields.append(
                        f"{section}.{field}"
                    )

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Required field(s) "
                    f"missing: "
                    + ", ".join(missing_fields)
                )
            )

        files_data.append({
            "file_name": file.filename,
            "content": content,
        })

    airport_import_jobs[task_id] = {
    "status": "processing",
    "total_files": len(files),
    "inserted_count": 0,
    "updated_count": 0,
    "failed_count": 0,
    "message": "Airport upload started in background."
    }


    background_tasks.add_task(
        process_airport_upload,
        files_data,
        task_id
    )

    return {
        "success": True,
        "task_id": task_id,
        "total_files": len(files),
        "message": "Airport upload started in background.",
    }
    
    
    
@router.delete("/delete-airport/", tags=["Airport"])
async def delete_airport(
    request: DeleteAirportRequest,
    db: Session = Depends(get_db)
):
    return await airport_crud.delete_airport(
        db,
        request.airport_id
    )



@router.delete("/bulk-delete-airport/", tags=["Airport"])
async def bulk_delete_airport(
    request: BulkDeleteAirportRequest,
    db: Session = Depends(get_db)
):
    return await airport_crud.bulk_delete_airport(
        db,
        request.airport_ids
    )
    
    

@router.patch("/bulk-approve-airport/", tags=["Airport"])
async def bulk_approve_airport(
    request: BulkApproveAirportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    airport_data = (
        db.query(AirportData)
        .filter(AirportData.id.in_(request.airport_ids))
        .all()
    )

    if not airport_data:
        raise HTTPException(
            status_code=404,
            detail="Airport not found."
        )

    for airport in airport_data:
        airport.is_approved = True
        airport.is_approved_time = datetime.utcnow()

    db.commit()
    
    return {
        "success": True,
        "message": "Airport approved successfully.",
        "total": len(airport_data)
    }
    
    
    
@router.patch("/bulk-disapprove-airport/", tags=["Airport"])
async def bulk_disapprove_airport(
    request: BulkApproveAirportRequest,
    db: Session = Depends(get_db)
):
    return await airport_crud.bulk_disapprove_airport(
        db,
        request.airport_ids
    )
    
    