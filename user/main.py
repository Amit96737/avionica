from fastapi import APIRouter, Depends , BackgroundTasks, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from user import crud as user_crud
from utils.pagination import PageNumberPagination
from user.schemas import DeleteGlossaryRequest, BulkDeleteGlossaryRequest, BulkApproveGlossaryRequest



router = APIRouter(
    prefix='/user'
)   




@router.get(
    "/upload-glossary-status/{task_id}",
    tags=["User"]
)
async def get_glossary_upload_status(task_id: str):

    job = user_crud.glossary_import_jobs.get(task_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Import task not found"
        )

    return job 




@router.post("/upload-glossary-file/", tags=["User"])
async def upload_glossary_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await user_crud.upload_glossary_csv(file, db, background_tasks)




@router.get("/all-glossary-details/", tags=["User"])
async def get_glossary_details(
    db: Session = Depends(get_db),
    pagination: PageNumberPagination = Depends(),
):
    return await user_crud.get_glossary_details(db, pagination=pagination)




@router.delete("/delete-glossary/", tags=["User"])
async def delete_glossary(
    request: DeleteGlossaryRequest,
    db: Session = Depends(get_db)
):
    return await user_crud.delete_glossary(
        db,
        request.glossary_id
    )




@router.delete("/bulk-delete-glossary/", tags=["User"])
async def bulk_delete_glossary(
    request: BulkDeleteGlossaryRequest,
    db: Session = Depends(get_db)
):
    return await user_crud.bulk_delete_glossary(
        db,
        request.glossary_ids
    )
    
    
    
    
@router.patch("/bulk-approve-glossary/", tags=["User"])
async def bulk_approve_glossary(
    request: BulkApproveGlossaryRequest,
    db: Session = Depends(get_db)
):
    return await user_crud.bulk_approve_glossary(
        db,
        request.glossary_ids
    )
    
    
    
    
@router.patch("/bulk-disapprove-glossary/", tags=["User"])
async def bulk_disapprove_glossary(
    request: BulkApproveGlossaryRequest,
    db: Session = Depends(get_db)
):
    return await user_crud.bulk_disapprove_glossary(
        db,
        request.glossary_ids
    )

