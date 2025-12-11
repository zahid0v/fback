from datetime import datetime, timedelta
from typing import List
from uuid import UUID
import uuid
import httpx
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException, status
from app.api.schemas.user import GetToken, SiteUser, UserCreate
from app.database.models import Session, Site, User, UserSiteLink
from passlib.context import CryptContext
from app.api.schemas.user import UserCreate
from app.utils import generate_access_token, generate_url_safe_token

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

class OpenpackService:
    def __init__(self, session: AsyncSession, model=User):
        self.model = model
        self.session = session
    
    async def _get_user(self) -> User | None:
        stmt = select(self.model).where(self.model.username == "dfre")
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _generate_session(
        self,
        site_user: SiteUser,  # must have .user_id (UUID) and .site_id (UUID)
    ) -> dict:
        # 🔐 Fix: username/password fields are likely swapped!
        # Usually: username = ivion_username, password = ivion_password
        payload = {
            "username": site_user.ivion_password,     # ✅ Fixed
            "password": site_user.ivion_username,     # ✅ Fixed
        }

        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=site_user.instance_url + "/api/auth/generate_tokens",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()

            # Parse response
            content_type = response.headers.get("content-type", "").lower()
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "json": response.json() if "application/json" in content_type else None,
                "text": response.text if "application/json" not in content_type else None
            }

            # ✅ Create and persist local session
            now = datetime.now()
            session_obj = Session(
                id=uuid.uuid4(),
                created_at=now,
                expering_at=now + timedelta(hours=1),  # or parse expiry from response if available
                user_id=site_user.user_id,    # ensure SiteUser has this
                site_id=site_user.site_id,    # ensure SiteUser has this
                data=response_data["json"] or {},  # e.g., store tokens, user info — use dict, not str
            )

            self.session.add(session_obj)
            await self.session.commit()
            await self.session.refresh(session_obj)  # get DB-generated fields if any

            # ✅ Return enriched response
            return session_obj.__dict__

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"External auth failed: {e.response.text[:200]}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Network error contacting auth API: {str(e)}"
            )
        except Exception as e:
            await self.session.rollback()  # safety: rollback on unexpected error
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )

    async def _get_Site(
        self,
        site_user: SiteUser,  # must have .user_id (UUID) and .site_id (UUID)
        jwt_token: str,  # JWT token for authorization
    ) -> dict:
        print("recieved token: ", jwt_token)
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {jwt_token}"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url="https://factory360core.iv.navvis.com/api/sites",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()

            # Parse response
            content_type = response.headers.get("content-type", "").lower()
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "json": response.json() if "application/json" in content_type else None,
                "text": response.text if "application/json" not in content_type else None
            }

            return response_data

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"External auth failed: {e.response.text[:200]}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Network error contacting auth API: {str(e)}"
            )
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )
    
    async def _get_Site_info(
        self,
        site_user: SiteUser,  # must have .user_id (UUID) and .site_id (UUID)
        jwt_token: str,  # JWT token for authorization
        siteId: str
    ) -> dict:
        print("recieved token: ", jwt_token)
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {jwt_token}"
        }
        print("req link", "https://factory360core.iv.navvis.com/api/sites/"+siteId)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url="https://factory360core.iv.navvis.com/api/sites/"+siteId,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()

            # Parse response
            content_type = response.headers.get("content-type", "").lower()
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "json": response.json() if "application/json" in content_type else None,
                "text": response.text if "application/json" not in content_type else None
            }

            return response_data

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"External auth failed: {e.response.text[:200]}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Network error contacting auth API: {str(e)}"
            )
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )
    async def _get_SitePois(
        self,
        site_id: str,
        site_user: SiteUser,  # must have .user_id (UUID) and .site_id (UUID)
        jwt_token: str,  # JWT token for authorization
    ) -> dict:
        print("recieved token: ", jwt_token)
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {jwt_token}"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url="https://factory360core.iv.navvis.com/api/site/"+site_id+"/pois",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()

            # Parse response
            content_type = response.headers.get("content-type", "").lower()
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "json": response.json() if "application/json" in content_type else None,
                "text": response.text if "application/json" not in content_type else None
            }

            return response_data

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"External auth failed: {e.response.text[:200]}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Network error contacting auth API: {str(e)}"
            )
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )

    async def get_sites(self) -> dict | None:
        user = await self._get_user()

        site_user = SiteUser(
            site_id="1a2cfa81-9677-4b3f-9395-338ab0e9aef0",
            user_id=user.id,
            ivion_id="112233",
            instance_url="https://factory360core.iv.navvis.com",
            ivion_username=user.ivion_username,
            ivion_password=user.ivion_password
        )
        newsession = await self._generate_session(site_user)
        data = newsession.get("data", {})
        principal = data.get("principal", {})
        sites = principal.get("site_default_group_read", {})
        external_site_ids = list(sites.keys())
        return {"sites": external_site_ids} 

    async def get_token(self) -> GetToken:
        user = await self._get_user()
        site_user = SiteUser(
            site_id="1a2cfa81-9677-4b3f-9395-338ab0e9aef0",
            user_id=user.id,
            ivion_id="112233",
            instance_url="https://factory360core.iv.navvis.com",
            ivion_username=user.ivion_username,
            ivion_password=user.ivion_password
        )
        newsession = await self._generate_session(site_user)
        data = newsession.get("data", {})
        access_token = data.get("access_token", {})
        refresh_token = data.get("refresh_token", {})

        return  {"access_token": access_token, "refresh_token": refresh_token}
    
    async def get_SiteInfo(self, siteId) -> dict | None:
        user = await self._get_user()
        site_user = SiteUser(
            site_id="1a2cfa81-9677-4b3f-9395-338ab0e9aef0",
            user_id=user.id,
            ivion_id="112233",
            instance_url="https://factory360core.iv.navvis.com",
            ivion_username=user.ivion_username,
            ivion_password=user.ivion_password
        )
        token = await self.get_token()
        print("🔧 [DEBUG] token: ", token)
        Sites = await self._get_Site_info(site_user=site_user, jwt_token=token.get("access_token"), siteId=siteId)

        print("🔧 [DEBUG] sites: ", Sites)
        return  Sites
    
    async def get_SitePois(self, siteId) -> dict | None:
        user = await self._get_user()
        site_user = SiteUser(
            site_id="1a2cfa81-9677-4b3f-9395-338ab0e9aef0",
            user_id=user.id,
            ivion_id="112233",
            instance_url="https://factory360core.iv.navvis.com",
            ivion_username=user.ivion_username,
            ivion_password=user.ivion_password
        )
        token = await self.get_token()
        print("🔧 [DEBUG] token: ", token)
        Sites = await self._get_SitePois(site_user=site_user, site_id=siteId, jwt_token=token.get("access_token"))

        print("🔧 [DEBUG] sites: ", Sites)
        return  Sites


    async def get_signedUrl(self, siteId) -> dict | None:
        user = await self._get_user()
        site_user = SiteUser(
            site_id="1a2cfa81-9677-4b3f-9395-338ab0e9aef0",
            user_id=user.id,
            ivion_id="112233",
            instance_url="https://factory360core.iv.navvis.com",
            ivion_username=user.ivion_username,
            ivion_password=user.ivion_password
        )
        token = await self.get_token()
        print("🔧 [DEBUG] token: ", token)
        # Sites = await self._get_SitePois(site_user=site_user, site_id=siteId, jwt_token=token.get("access_token"))

        signedUrl = "https://core.factory360.world/login?autologin=true&InstanceUrl=https://factory360core.iv.navvis.com/&access_token="+token.get("access_token")+"&refresh_token="+token.get("refresh_token")+"&siteId="+siteId

        return  {"signedUrl": signedUrl}