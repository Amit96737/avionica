from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from dependencies import get_db
from triviagia import crud as triviagia_crud
from utils.pagination import PageNumberPagination
from triviagia.schemas import DeleteChronicleRequest, BulkDeleteChronicleRequest, BulkApproveChronicleRequest


router = APIRouter(
    prefix='/triviagia'
)   


@router.get("/aviation-chronicle-details/", tags=["Aviation Chronicle"])
async def get_aviation_chronicle(
    db: Session = Depends(get_db),
    pagination: PageNumberPagination = Depends(),
):
    return await triviagia_crud.get_aviation_chronicle(db, pagination=pagination)



@router.post("/upload-aviation-chronicle-file/", tags=["Aviation Chronicle"])
async def upload_aviation_chronicle_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await triviagia_crud.upload_aviation_chronicle_csv(file, db, background_tasks)



@router.delete("/delete-aviation-chronicle/", tags=["Aviation Chronicle"])
async def delete_aviation_chronicle(
    request: DeleteChronicleRequest,
    db: Session = Depends(get_db)
):
    return await triviagia_crud.delete_aviation_chronicle(
        db,
        request.aviation_chronicle_id
    )



@router.delete("/bulk-delete-aviation-chronicle/", tags=["Aviation Chronicle"])
async def bulk_delete_aviation_chronicle(
    request: BulkDeleteChronicleRequest,
    db: Session = Depends(get_db)
):
    return await triviagia_crud.bulk_delete_aviation_chronicle(
        db,
        request.aviation_chronicle_ids
    )
    
    
    
@router.patch("/bulk-approve-aviation-chronicle/", tags=["Aviation Chronicle"])
async def bulk_approve_aviation_chronicle(
    request: BulkApproveChronicleRequest,
    db: Session = Depends(get_db)
):
    return await triviagia_crud.bulk_approve_aviation_chronicle(
        db,
        request.aviation_chronicle_ids
    )
    
    
    
@router.patch("/bulk-disapprove-aviation-chronicle/", tags=["Aviation Chronicle"])
async def bulk_disapprove_aviation_chronicle(
    request: BulkApproveChronicleRequest,
    db: Session = Depends(get_db)
):
    return await triviagia_crud.bulk_disapprove_aviation_chronicle(
        db,
        request.aviation_chronicle_ids
    )
