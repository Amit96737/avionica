from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session
from dependencies import get_db




router = APIRouter(
    prefix='/user'
)   



# @router.get("/manufacturer-details/", tags=["Manufacturer"])
# async def get_manufacturer(
#     db: Session = Depends(get_db)
# ):
#     return await manufacturer_crud.get_manufacture(db)


