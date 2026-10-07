from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, BackgroundTasks
from sqlalchemy.orm import Session
from dependencies import get_db
from typing import List
from aircraft import crud as aircraft_crud
from aircraft.schemas import BulkDeleteAircraftRequest, DeleteAircraftRequest, BulkApproveAircraftRequest, UpdateAircraftRequest
from aircraft.models import Aircraft
from datetime import datetime
import uuid
from aircraft.crud import process_aircraft_upload, aircraft_import_jobs


router = APIRouter(
    prefix="/aircraft"
)


        
@router.get(
    "/upload-json-status/{task_id}",
    tags=["Aircraft"]
)
async def get_aircraft_upload_status(task_id: str):

    job = aircraft_import_jobs.get(task_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Aircraft upload task not found"
        )

    return job



@router.post("/upload-json", tags=["Aircraft"])
async def upload_aircraft_json(
    background_tasks: BackgroundTasks,
    manufacturer_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    files_data = []

    for file in files:
        content = await file.read()

        files_data.append({
            "file_name": file.filename,
            "content": content,
        })

    task_id = str(uuid.uuid4())

    aircraft_import_jobs[task_id] = {
        "status": "processing",
        "message": "Aircraft upload started in background."
    }

    background_tasks.add_task(
        process_aircraft_upload,
        task_id,
        manufacturer_id,
        files_data
    )

    return {
        "success": True,
        "task_id": task_id,
        "manufacturer_id": manufacturer_id,
        "total_files": len(files),
        "message": "Aircraft upload started in background.",
    }


    
@router.get("/aircraft-details/", tags=["Aircraft"])
async def get_aircraft(
    db: Session = Depends(get_db)
):
    return aircraft_crud.get_aircraft(db)



@router.delete("/delete-aircraft/", tags=["Aircraft"])
async def delete_aircraft(
    request: DeleteAircraftRequest,
    db: Session = Depends(get_db)
):
    return await aircraft_crud.delete_aircraft(
        db,
        request.aircraft_id
    )
    


@router.delete("/bulk-delete-aircraft/", tags=["Aircraft"])
async def bulk_delete_aircraft(
    request: BulkDeleteAircraftRequest,
    db: Session = Depends(get_db)
):
    return await aircraft_crud.bulk_delete_aircraft(
        db,
        request.aircraft_ids
    )
    
    

@router.patch("/update-aircraft/", tags=["Aircraft"])
async def update_aircraft(
    request: UpdateAircraftRequest,
    db: Session = Depends(get_db)
):
    return await aircraft_crud.update_aircraft(
        db,
        request.aircraft_id
    )



@router.patch("/bulk-approve-aircraft/", tags=["Aircraft"])
async def bulk_approve_aircraft(
    request: BulkApproveAircraftRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    aircraft_data = (
        db.query(Aircraft)
        .filter(Aircraft.id.in_(request.aircraft_ids))
        .all()
    )

    if not aircraft_data:
        raise HTTPException(
            status_code=404,
            detail="No aircraft found."
        )

    for aircraft in aircraft_data:
        aircraft.is_approved = True
        aircraft.is_approved_time = datetime.utcnow()

    db.commit()

    background_tasks.add_task(
        aircraft_crud.upload_aircraft_images_background,
        request.aircraft_ids
    )

    return {
        "success": True,
        "message": "Aircraft approved successfully.",
        "total": len(aircraft_data)
    }
    


@router.patch("/bulk-disapprove-aircraft/", tags=["Aircraft"])
async def bulk_disapprove_aircraft(
    request: BulkApproveAircraftRequest,
    db: Session = Depends(get_db)
):
    return await aircraft_crud.bulk_disapprove_aircraft(
        db,
        request.aircraft_ids
    )
    
