from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from airport import crud as airport_crud
from typing import List
from airport.crud import process_airport_upload, airport_import_jobs
from airport.schemas import DeleteAirportRequest, BulkDeleteAirportRequest, BulkApproveAirportRequest, AirportNestedRequest
import json
import uuid
from airport.helper import REQUIRED_AIRPORT_FIELDS
from utils.pagination import PageNumberPagination
from pydantic import ValidationError

router = APIRouter(
    prefix="/airport"
)


@router.get(
    "/upload-airport-json-status/{task_id}",
    tags=["Airport"]
)
async def get_airport_upload_status(task_id: str):
    
    print("TOTAL JOBS:", len(airport_import_jobs))

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
    invalid_files = []

    task_id = str(uuid.uuid4())

    for file in files:

        file_name = file.filename

        if not file_name.lower().endswith(".json"):
            invalid_files.append({
                "file_name": file_name,
                "error": "Only JSON files are allowed."
            })
            continue

        content = await file.read()

        try:
            data = json.loads(content.decode("utf-8"))

        except UnicodeDecodeError:
            invalid_files.append({
                "file_name": file_name,
                "error": "File must be UTF-8 encoded JSON."
            })
            continue

        except json.JSONDecodeError as e:
            invalid_files.append({
                "file_name": file_name,
                "error": (
                    f"Invalid JSON format: "
                    f"line {e.lineno}, column {e.colno}: "
                    f"{e.msg}"
                )
            })
            continue

        if not isinstance(data, dict):
            invalid_files.append({
                "file_name": file_name,
                "error": "JSON root must be an object."
            })
            continue
        
        try:
            AirportNestedRequest.model_validate(data)

        except ValidationError as e:

            validation_errors = []

            for error in e.errors():

                field_path = ".".join(
                    str(item)
                    for item in error["loc"]
                )

                validation_errors.append(
                    f"{field_path}: {error['msg']}"
                )

            invalid_files.append({
                "file_name": file_name,
                "error": " | ".join(validation_errors)
            })

            continue


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
            invalid_files.append({
                "file_name": file_name,
                "error": (
                    "Required field(s) missing: "
                    + ", ".join(missing_fields)
                )
            })
            continue

        files_data.append({
            "file_name": file_name,
            "content": content,
        })

    if not files_data:

        return {
            "success": False,
            "task_id": None,
            "total_files": len(files),
            "valid_files": 0,
            "invalid_files": len(invalid_files),
            "invalid_file_details": invalid_files,
            "message": "No valid airport files found."
        }

    airport_import_jobs[task_id] = {
        "status": "processing",
        "total_files": len(files),
        "valid_files": len(files_data),
        "invalid_files": len(invalid_files),
        "inserted_count": 0,
        "updated_count": 0,
        "failed_count": 0,
        "invalid_file_details": invalid_files,
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
        "valid_files": len(files_data),
        "invalid_files": len(invalid_files),
        "invalid_file_details": invalid_files,
        "message": "Airport upload started in background."
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
    db: Session = Depends(get_db)
):
    return await airport_crud.bulk_approve_airport(
        db,
        request.airport_ids
    )
    
    
    
@router.patch("/bulk-disapprove-airport/", tags=["Airport"])
async def bulk_disapprove_airport(
    request: BulkApproveAirportRequest,
    db: Session = Depends(get_db)
):
    return await airport_crud.bulk_disapprove_airport(
        db,
        request.airport_ids
    )
    
    