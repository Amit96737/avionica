from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from avionica import crud as manufacturer_crud
from avionica.models import Manufacturer
from datetime import datetime
from avionica.schemas import BulkDeleteManufacturerRequest, BulkApproveManufacturerSchema
from avionica.crud import manufacturer_import_jobs



router = APIRouter(
    prefix='/manufacturer'
)   



@router.get(
    "/upload-manufacturer-status/{task_id}",
    tags=["Manufacturer"]
)
async def get_manufacturer_upload_status(task_id: str):

    job = manufacturer_import_jobs.get(task_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Import task not found"
        )

    return job



@router.post("/upload-manufacturer-file/", tags=["Manufacturer"])
async def upload_manufacturer_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await manufacturer_crud.upload_manufacturer_csv(file, db, background_tasks)



@router.get("/manufacturer-details/", tags=["Manufacturer"])
async def get_manufacturer(
    db: Session = Depends(get_db)
):
    return await manufacturer_crud.get_manufacture(db)


# @router.get("/manufacturer-details/", tags=["Manufacturer"])
# async def get_manufacturer(
#     db: Session = Depends(get_db),
#     pagination: PageNumberPagination = Depends(),
# ):
#     return await manufacturer_crud.get_manufacture(db,  pagination=pagination)



@router.patch("/update-manufacturer/", tags=["Manufacturer"])
async def update_manufacturer(
    manufacturer_id: str,
    db: Session = Depends(get_db)
):
    return await manufacturer_crud.update_manufacturer(
        db,
        manufacturer_id
    )
    
    

@router.delete("/delete-manufacturer/", tags=["Manufacturer"])
async def delete_manufacturer(
    manufacturer_id: str,
    db: Session = Depends(get_db)
):
    return await manufacturer_crud.delete_manufacturer(
        db,
        manufacturer_id
    )
    
    
    
@router.patch("/bulk-approve-manufacturer/", tags=["Manufacturer"])
async def bulk_approve_manufacturer(
    data: BulkApproveManufacturerSchema,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    manufacturer_ids = data.manufacturer_ids

    manufacturers = (
        db.query(Manufacturer)
        .filter(Manufacturer.id.in_(manufacturer_ids))
        .all()
    )

    if not manufacturers:
        raise HTTPException(
            status_code=404,
            detail="No manufacturers found"
        )

    for manufacturer in manufacturers:
        manufacturer.is_approved = True
        manufacturer.is_approved_time = datetime.utcnow()

    db.commit()

    background_tasks.add_task(
        manufacturer_crud.upload_manufacturer_logos_background,
        manufacturer_ids
    )

    return {
        "success": True,
        "message": "Manufacturers approved successfully.",
        "total": len(manufacturers)
    } 
    


@router.patch("/bulk-disapprove-manufacturer/", tags=["Manufacturer"])
async def bulk_disapprove_manufacturer(
    data: BulkApproveManufacturerSchema,
    db: Session = Depends(get_db)
):
    return await manufacturer_crud.bulk_disapprove_manufacturer(
        db,
        data.manufacturer_ids
    )
    
    

@router.delete("/bulk-delete-manufacturer/", tags=["Manufacturer"])
async def bulk_delete_manufacturer(
    request: BulkDeleteManufacturerRequest,
    db: Session = Depends(get_db)
):
    return await manufacturer_crud.bulk_delete_manufacturer(
        db,
        request.manufacturer_ids
    )
