from pydantic import BaseModel, UUID4
from typing import Optional

class UserBase(BaseModel):
    email: str

class User(UserBase):
    id: UUID4
    role: str
    agency_id: Optional[UUID4] = None

    class Config:
        from_attributes = True
