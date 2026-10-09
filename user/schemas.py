from pydantic import BaseModel
from typing import List


class Glossary(BaseModel):
    title: str
    description: str


class DeleteGlossaryRequest(BaseModel):
    glossary_id: str
    
    
class BulkDeleteGlossaryRequest(BaseModel):
    glossary_ids: List[str]
    
    
class BulkApproveGlossaryRequest(BaseModel):
    glossary_ids: List[str]