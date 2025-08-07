from pydantic import BaseModel, UUID4
from typing import Optional

class Account(BaseModel):
    id: UUID4
    user_id: str # Ou UUID4, dependendo da sua tabela
    store_id: int
    store_name: str
    agency_id: Optional[UUID4] = None

    class Config:
        from_attributes = True
