from typing import List
from uuid import UUID
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException, status
from app.api.schemas.user import UserCreate
from app.database.models import Site, User, UserSiteLink
from passlib.context import CryptContext
from app.api.schemas.user import UserCreate
from app.utils import generate_access_token, generate_url_safe_token

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

class UserService:
    def __init__(self, session: AsyncSession, model=User):
        self.model = model
        self.session = session

    async def _get(self, id: UUID):
        return await self.session.get(self.model, id)
    
    async def _add(self, entity):
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    
    async def _update(self, entity):
        return await self._add(entity)
    
    async def _delete(self, entity):
        await self.session.delete(entity)
    
    # async def _add_user(self, data: dict, router_prefix: str) -> User:
    #     user = self.model(
    #         **data,
    #         hashed_password=password_context.hash(data["password"][:72]),
    #     )
    #     # Add the user to database and get refreshed data
        
    #     # Generate the token with user id
    #     token = generate_url_safe_token({
    #         # Email can be skipped as not used in our case
    #         # "email": user.email,
    #         "id": str(user.id)
    #     })

    #     user.hashed_password = token
    #     user.password = token
    #     user = await self._add(user)
    #     return user
    async def _add_user(self, data: dict, router_prefix: str) -> User:
        # Create a copy of the data and extract password
        user_data = data.copy()
        plaintext_password = user_data.pop("password")
        
        # Hash the password
        password_hash = password_context.hash(plaintext_password[:72])
        
        # Create user with BOTH password fields set to the hash
        user = self.model(
            **user_data,
            password=password_hash,        # Set to hash (not recommended but works)
            hashed_password=password_hash, # Set to hash
        )
        
        # Add to database
        user = await self._add(user)
        
        # Generate token for response
        token = generate_url_safe_token({"id": str(user.id)})
        
        # If you need the token in the response, add it as a non-db attribute
        user.hashed_password = token
        return user 

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
    
    # async def add(self, UserCreate: UserCreate) -> User:
    #     return await self._add_user(
    #         UserCreate.model_dump(),
    #         "user"
    #     )
    # async def add(self, user_create: UserCreate) -> User:
    #     user_data = user_create.model_dump(exclude={"site_ids"})
        
    #     # Create user first
    #     user = await self._add_user(user_data, "user")
        
    #     # Add site relationships if provided
    #     if user_create.site_ids:
    #         # Fetch sites from database
    #         result = await self.session.execute(
    #             select(Site).where(Site.id.in_(user_create.site_ids))
    #         )
    #         sites = result.scalars().all()
    #         user.sites = list(sites)
            
    #         self.session.add(user)
    #         await self.session.commit()
    #         await self.session.refresh(user)
        
    #     return user
    # async def add(self, user_create: UserCreate) -> User:
    #     user_data = user_create.model_dump(exclude={"site_ids"})
        
    #     user = await self._add_user(user_data, "user")
        
    #     if user_create.site_ids:
    #         result = await self.session.execute(
    #             select(Site).where(Site.id.in_(user_create.site_ids))
    #         )
    #         sites = result.scalars().all()
            
    #         user.sites.extend(sites)  # This is the key fix
            
    #         await self.session.commit()
    #         await self.session.refresh(user, ["sites"])
    # async def add(self, user_create: UserCreate) -> User:
    #     user_data = user_create.model_dump(exclude={"site_ids"})
        
    #     # Create user first without sites
    #     user = await self._add_user(user_data, "user")
        
    #     # Handle sites in a separate method
    #     if user_create.site_ids:
    #         await self._add_user_sites(user.id, user_create.site_ids)
        
    #     # Get the complete user with sites
    #     complete_user = await self._get_user_with_sites(user.id)
        
    #     return complete_user

    # async def _add_user_sites(self, user_id: UUID, site_ids: List[int]):
    #     """Add site relationships without touching user object"""
    #     # Use raw SQL or direct table insertion
    #     # This depends on your association table structure
    #     pass

    # async def _get_user_with_sites(self, user_id: UUID) -> User:
    #     """Get user with sites eagerly loaded"""
    #     from sqlalchemy.orm import selectinload
        
    #     stmt = select(User).where(User.id == user_id).options(selectinload(User.sites))
    #     result = await self.session.execute(stmt)
    #     return result.scalar_one()


    async def add(self, user_create: UserCreate) -> User:
        user_data = user_create.model_dump(exclude={"site_ids"})
        
        print(f"🔧 [DEBUG] Starting user creation with username: {user_data.get('username')}")
        print(f"🔧 [DEBUG] Site IDs to associate: {user_create.site_ids}")
        
        # Create user first without sites
        user = await self._add_user(user_data, "user")
        print(f"🔧 [DEBUG] User created with ID: {user.id}")
        
        # Handle sites in a separate method
        if user_create.site_ids:
            print(f"🔧 [DEBUG] Adding {len(user_create.site_ids)} sites to user")
            success_count = await self._add_user_sites(user.id, user_create.site_ids)
            print(f"🔧 [DEBUG] Successfully added {success_count} site relationships")
        else:
            print(f"🔧 [DEBUG] No sites to associate")
        
        # Get the complete user with sites
        complete_user = await self._get_user_with_sites(user.id)
        print(f"🔧 [DEBUG] Final user sites count: {len(complete_user.sites)}")
        print(f"🔧 [DEBUG] Final user sites IDs: {[site.id for site in complete_user.sites]}")
        
        return complete_user

    async def _add_user_sites(self, user_id: UUID, site_ids: List[int]) -> int:
        """Add site relationships using the association table"""
        print(f"🔧 [DEBUG] _add_user_sites called with user_id: {user_id}, site_ids: {site_ids}")
        
        # First, verify that the sites exist
        result = await self.session.execute(
            select(Site).where(Site.id.in_(site_ids))
        )
        existing_sites = result.scalars().all()
        existing_site_ids = [site.id for site in existing_sites]
        
        print(f"🔧 [DEBUG] Found {len(existing_sites)} existing sites: {existing_site_ids}")
        
        # Check for missing sites
        missing_site_ids = set(site_ids) - set(existing_site_ids)
        if missing_site_ids:
            print(f"⚠️ [DEBUG] WARNING: Some sites not found: {missing_site_ids}")
        
        if not existing_sites:
            print(f"🔧 [DEBUG] No existing sites found, skipping relationship creation")
            return 0
        
        try:
            # Insert into the association table
            association_records = [
                {"user_id": user_id, "site_id": site.id} 
                for site in existing_sites
            ]
            
            print(f"🔧 [DEBUG] Inserting {len(association_records)} records into UserSiteLink: {association_records}")
            
            # Insert the relationships
            stmt = insert(UserSiteLink).values(association_records)
            result = await self.session.execute(stmt)
            
            await self.session.commit()
            print(f"🔧 [DEBUG] Successfully committed {len(association_records)} site relationships")
            
            return len(association_records)
            
        except Exception as e:
            print(f"❌ [DEBUG] Error in _add_user_sites: {e}")
            await self.session.rollback()
            raise

    async def _get_user_with_sites(self, user_id: UUID) -> User:
        """Get user with sites eagerly loaded"""
        from sqlalchemy.orm import selectinload
        
        print(f"🔧 [DEBUG] _get_user_with_sites called for user_id: {user_id}")
        
        stmt = select(User).where(User.id == user_id).options(selectinload(User.sites))
        result = await self.session.execute(stmt)
        user = result.scalar_one()
        
        print(f"🔧 [DEBUG] Retrieved user '{user.username}' with {len(user.sites)} sites")
        if user.sites:
            for i, site in enumerate(user.sites):
                print(f"🔧 [DEBUG]   Site {i+1}: {site.name} (ID: {site.id})")
        
        return user


    async def token(self, email, password) -> str:
        return await self._generate_token(email, password)
