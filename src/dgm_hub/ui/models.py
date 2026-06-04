from pydantic import BaseModel
from typing import Dict, Any


class ApprovalRequest(BaseModel):

    action_id:str

    action_type:str

    description:str

    payload:Dict[str,Any]


class ApprovalResponse(BaseModel):

    approved:bool
