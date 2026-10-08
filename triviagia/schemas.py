from pydantic import BaseModel, ConfigDict
from typing import List


class AviationChronicleSchema(BaseModel):
    id: str
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True)



class DeleteChronicleRequest(BaseModel):
    aviation_chronicle_id: str
    
    
    
class BulkDeleteChronicleRequest(BaseModel):
    aviation_chronicle_ids: List[str]
    
    
class BulkApproveChronicleRequest(BaseModel):
    aviation_chronicle_ids: List[str]