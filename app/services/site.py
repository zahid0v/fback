from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4
import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException, status
from app.api.schemas.user import SiteCreate, SiteUser
from app.database.models import Session, Site, User, UserSiteLink
from passlib.context import CryptContext
from app.utils import generate_access_token, generate_url_safe_token

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

class SiteService:
    def __init__(self, session: AsyncSession, model=Site):
        self.model = model
        self.session = session

    async def _get(self, id: UUID):
        return await self.session.get(self.model, id)
    
    async def _get_user(self, id: str):
        return await self.session.get(User, id)

    async def _add(self, entity):
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def _get_site_url(self, id: UUID):
        sitee= await self._get(id)
        url=sitee.instance_url
        return url
    
    async def _get_token(self, id: UUID):
        sitee= await self._get(id)
        token=sitee.token
        return token
    
    async def _update(self, entity):
        return await self._add(entity)
    
    async def _delete(self, entity):
        await self.session.delete(entity)

    async def _add_Site(self, data: dict, router_prefix: str) -> Site:
        # Create a copy of the data and extract password
        # Create site instance
        site = self.model(
            id=uuid4(),  # explicit (optional; SQLModel can auto-gen, but explicit is safer)
            created_at=datetime.now(),
            name=data["name"],
            instance_url=data["instance_url"],
            ivion_id=data["ivion_id"],
        )
        site = await self._add(site)
        return site

    async def _generate_token(self, email, password) -> str:
        # Validate the credentials
        user = await self._get_by_email(email)

        if user is None or not password_context.verify(
            password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email or password is incorrect",
            )
        
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not verified",
            )

        return generate_access_token(
            data={
                "user": {
                    "name": user.name,
                    "id": str(user.id),
                },
            }
        )
    
    async def add(self, SiteCreate: SiteCreate) -> Site:
        return await self._add_Site(
            SiteCreate.model_dump(),
            "site"
        )

    async def token(self, email, password) -> str:
        return await self._generate_token(email, password)
    
    async def get(self, id: UUID) -> Site | None:
        return await self._get(id)
        
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
        print(f"🔧 [DEBUG] Payload: {payload}")

        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=site_user.instance_url + "/api/auth/generate_tokens",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                print(f"📤 POST {site_user.instance_url}/api/auth/generate_tokens → {response.status_code}")
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



    async def get_site_cred(self, site_id: UUID) -> Optional[SiteUser]:
        """
        Get site details with linked user credentials for a given site ID.
        
        Args:
            site_id: The UUID of the site
            
        Returns:
            SiteUser object containing site_id, instance_url, ivion_username, and ivion_password
            Returns None if site or linked user not found
        """
        print(f"🔧 [DEBUG] Getting site with user credentials for site_id: {site_id}")
        
        try:
            # Query to get site and linked user in one go
            stmt = (
                select(Site, User)
                .join(UserSiteLink, Site.id == UserSiteLink.site_id)
                .join(User, UserSiteLink.user_id == User.id)
                .where(Site.id == site_id)
            )
            
            result = await self.session.execute(stmt)
            row = result.first()
            
            if not row:
                print(f"❌ [DEBUG] No site found with ID: {site_id} or no linked user")
                return None
            
            site, user = row
            print(f"🔧 [DEBUG] Found site: {site.name}, user: {user.username}")
            
            # Create and return the SiteUser object
            site_user = SiteUser(
                site_id=site.id,
                user_id=user.id,
                ivion_id=site.ivion_id,
                instance_url=site.instance_url,
                ivion_username=user.ivion_username,
                ivion_password=user.ivion_password
            )
            
            print(f"🔧 [DEBUG] Successfully created SiteUser for site: {site.name}")

            print("Trying to login")
            response =await self._generate_session(site_user)
            print(response)
            return site_user
            

            
        except Exception as e:
            print(f"❌ [DEBUG] Error in get_site_with_user_credentials: {e}")
            return None
    






    async def get_user(self, id: uuid) -> User:
        return await self.session.get(User, id)

    async def _get_sites(self) -> dict:
        user = await self.get_user("95f32edf-35e3-4be9-b37c-ca33b6b2238e")

        site_user = SiteUser(
            site_id="1a2cfa81-9677-4b3f-9395-338ab0e9aef0",
            user_id=user.id,
            ivion_id="112233",
            instance_url="https://factory360core.iv.navvis.com",
            ivion_username=user.ivion_username,
            ivion_password=user.ivion_password
        )
        newsession = await self._generate_session(site_user)
        return newsession
    

