from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr

class BaseUser(BaseModel):
    username: str


class UserRead(BaseUser):
    pass

class UserCreate(BaseUser):
    password: str
    ivion_password: str
    ivion_username: str
    site_ids: list[UUID] = []

    
class SiteRead(BaseModel):
    name: str


class SiteCreate(BaseModel):
    name: str
    instance_url: str
    ivion_id: str

class SiteUser(BaseModel):
    site_id: UUID
    user_id: UUID
    ivion_id: str
    instance_url: str
    ivion_username: str
    ivion_password: str

class SessionRead(BaseModel):
    id: UUID
    created_at: datetime
    expering_at: datetime
    site_id: UUID
    data: dict

class SitesRead(BaseModel):
    sites: list[str]

class GetToken(BaseModel):
    access_token: str
    refresh_token: str

class SignedUrl(BaseModel):
    signedUrl: str