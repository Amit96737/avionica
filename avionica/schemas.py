from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from enum import Enum as PyEnum


class ProductSeries(str, PyEnum):
    airplane = "Airplane"
    helicopter = "Helicopter"

class ProductSchemaIn(BaseModel):
    series: Optional[ProductSeries] = ""
    data: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class ImageSchema(BaseModel):
    url: str
    license: Optional[str]
    author: Optional[str]
    wiki: Optional[str]

class ManufacturerIn(BaseModel):
    company_name: str
    headquarter: str
    founding_date: int
    company_description: str
    company_history: str
    logo: str
    cover_photo: ImageSchema
    product_series: List[ProductSchemaIn]
    interesting_facts: List[str]
    
    products_1: str
    products_2: str
    licence_type: str
    author_name: str
    wiki_link: str
    
    
class BulkDeleteManufacturerRequest(BaseModel):
    manufacturer_ids: List[str]
    
    
class BulkApproveManufacturerSchema(BaseModel):
    manufacturer_ids: List[str]
