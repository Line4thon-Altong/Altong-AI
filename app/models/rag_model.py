from pydantic import BaseModel
from typing import Any, Dict

class RagEmbedRequest(BaseModel):
    manual_id: int
    manual_json: Dict[str, Any]