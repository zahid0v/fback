# from sqlmodel import SQLModel, Field
# from datetime import datetime
# from typing import Optional
# from uuid import UUID, uuid4
# from sqlmodel import Column, Field, Relationship, SQLModel, select
# from sqlalchemy.dialects import postgresql
# from typing import List, Optional

# class Instance(SQLModel, table=True):
#     id: UUID = Field(
#         sa_column=Column(
#             postgresql.UUID,
#             default=uuid4,
#             primary_key=True,
#         )
#     )
#     url: str = Field(unique=True, index=True)
#     sites: List["Site"] = Relationship(back_populates="instance")

# class Site(SQLModel, table=True):
#     __tablename__ = "site"  # Changed to lowercase for consistency

#     id: UUID = Field(
#         sa_column=Column(
#             postgresql.UUID,
#             default=uuid4,
#             primary_key=True,
#         )
#     )
#     created_at: datetime = Field( 
#         sa_column=Column(
#             postgresql.TIMESTAMP,
#             default=datetime.now,
#         )
#     )
#     name: str = Field(index=True)

#     instance_id: UUID = Field(foreign_key="instance.id")  # Fixed type from str to UUID
    
#     instance: Instance = Relationship(back_populates="sites",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )

#     users: List["User"] = Relationship(back_populates="site",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )
    
#     pois: List["Poi"] = Relationship(
#         back_populates="site",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )

# class User(SQLModel, table=True):
#     __tablename__ = "user"  # Changed to lowercase for consistency

#     id: UUID = Field(
#         sa_column=Column(
#             postgresql.UUID,
#             default=uuid4,
#             primary_key=True,
#         )
#     )
#     created_at: datetime = Field( 
#         sa_column=Column(
#             postgresql.TIMESTAMP,
#             default=datetime.now,
#         )
#     )
#     username: str = Field(unique=True, index=True)
#     password: str  # plaintext (not recommended for production)
#     hashed_password: str  # actual stored password

#     site_id: Optional[UUID] = None  # Added missing foreign keyUUID = Field(foreign_key="site.id")  # Added missing foreign key
#     site: Optional[Site] = Relationship(back_populates="users",  # Fixed relationship nameSite = Relationship(back_populates="users",  # Fixed relationship name
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )

# class Poi(SQLModel, table=True):
#     id: UUID = Field(
#         sa_column=Column(
#             postgresql.UUID,
#             default=uuid4,
#             primary_key=True,
#         )
#     )
#     poi_url: str

#     # Foreign key to Site - now matches the actual table name
#     site_id: UUID = Field(foreign_key="site.id")
#     site: Site = Relationship(back_populates="pois",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )

import json
from sqlalchemy import ForeignKey
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Column, Field, Relationship, SQLModel, select
from sqlalchemy.dialects import postgresql
from typing import List, Optional

class Instance(SQLModel, table=True):
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    url: str = Field(unique=True, index=True)
    # sites: List["Site"] = Relationship(back_populates="instance")


# class User(SQLModel, table=True):
#     __tablename__ = "user"

#     id: UUID = Field(
#         sa_column=Column(
#             postgresql.UUID,
#             default=uuid4,
#             primary_key=True,
#         )
#     )
#     created_at: datetime = Field( 
#         sa_column=Column(
#             postgresql.TIMESTAMP,
#             default=datetime.now,
#         )
#     )
#     username: str = Field(unique=True, index=True)
#     password: str
#     hashed_password: str

#     # # CORRECTED: Proper optional foreign key
#     # site_id: Optional[UUID] = Field(default=None, foreign_key="site.id")
    
#     # # CORRECTED: Proper relationship
#     site: Optional["Site"] = Relationship(back_populates="users",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )

# class Site(SQLModel, table=True):
#     __tablename__ = "site"

#     id: UUID = Field(
#         sa_column=Column(
#             postgresql.UUID,
#             default=uuid4,
#             primary_key=True,
#         )
#     )
#     created_at: datetime = Field( 
#         sa_column=Column(
#             postgresql.TIMESTAMP,
#             default=datetime.now,
#         )
#     )
#     name: str = Field(index=True)
#     instance_url: str
#     ivion_id: str
#     # instance_id: UUID = Field(foreign_key="instance.id")
    
#     # instance: Instance = Relationship(back_populates="sites",
#     #     sa_relationship_kwargs={"lazy": "selectin"},
#     # )
#     # users: List["User"] = Relationship(back_populates="site",
#     #     sa_relationship_kwargs={"lazy": "selectin"},
#     # )
#     # pois: List["Poi"] = Relationship(back_populates="site",
#     #     sa_relationship_kwargs={"lazy": "selectin"},
#     # )





class UserSiteLink(SQLModel, table=True):
    __tablename__ = "user_site_link"
    user_id: UUID = Field(
        foreign_key="user.id",
        primary_key=True,
    )
    site_id: UUID = Field(
        foreign_key="site.id",
        primary_key=True,
    )

class Site(SQLModel, table=True):
    __tablename__ = "site"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field( 
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    name: str = Field(index=True)
    instance_url: str
    ivion_id: str
    
    users: list["User"] = Relationship(
        back_populates="sites",
        link_model=UserSiteLink
    )

class User(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field( 
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    username: str = Field(unique=True, index=True)
    ivion_password: str
    ivion_username: str
    hashed_password: str
    
    sites: list["Site"] = Relationship(
        back_populates="users",
        link_model=UserSiteLink
    )



class Poi(SQLModel, table=True):
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    poi_url: str
    site_id: str
#     site_id: UUID = Field(foreign_key="site.id")
#     site: Site = Relationship(back_populates="pois",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )


class Session(SQLModel, table=True):
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field( 
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    expering_at: datetime

    # Fixed foreign keys
    user_id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            ForeignKey("user.id"),
            nullable=False,
        )
    )
    site_id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            ForeignKey("site.id"),
            nullable=False,
        )
    )
    
    data: Optional[dict] = Field(
        sa_column=Column(postgresql.JSONB, nullable=True),
        default=None,
    )
    
    user: Optional["User"] = Relationship()
    site: Optional["Site"] = Relationship()

