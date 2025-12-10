# from typing import Annotated
# from uuid import UUID

# from fastapi import BackgroundTasks, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.core.security import oauth2_scheme_partner, oauth2_scheme_seller
# from app.database.models import DeliveryPartner, Seller
# from app.database.redis import is_jti_blacklisted
# from app.database.session import get_session
# from app.services.delivery_partner import DeliveryPartnerService
# from app.services.seller import SellerService
# from app.services.shipment import ShipmentService
# from app.services.shipment_event import ShipmentEventService
# from app.utils import decode_access_token

# # Asynchronous database session dep annotation
# SessionDep = Annotated[AsyncSession, Depends(get_session)]


# # Access token data dep
# async def _get_access_token(token: str) -> dict:
#     data = decode_access_token(token)

#     # Validate the token
#     if data is None or await is_jti_blacklisted(data["jti"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired access token",
#         )

#     return data


# # Seller access token data
# async def get_seller_access_token(
#     token: Annotated[str, Depends(oauth2_scheme_seller)],
# ) -> dict:
#     return await _get_access_token(token)


# # Delivery partner access token data
# async def get_partner_access_token(
#     token: Annotated[str, Depends(oauth2_scheme_partner)],
# ) -> dict:
#     return await _get_access_token(token)


# # Logged In Seller
# async def get_current_seller(
#     token_data: Annotated[dict, Depends(get_seller_access_token)],
#     session: SessionDep,
# ):
#     seller = await session.get(
#         Seller,
#         UUID(token_data["user"]["id"]),
#     )

#     if seller is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authorized",
#         )

#     return seller


# # Logged In Delivery partner
# async def get_current_partner(
#     token_data: Annotated[dict, Depends(get_partner_access_token)],
#     session: SessionDep,
# ):
#     partner = await session.get(
#         DeliveryPartner,
#         UUID(token_data["user"]["id"]),
#     )

#     if partner is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authorized",
#         )

#     return partner


# # Shipment service dep
# def get_shipment_service(
#     session: SessionDep,
#     tasks: BackgroundTasks,
# ):
#     return ShipmentService(
#         session,
#         DeliveryPartnerService(session, tasks),
#         ShipmentEventService(session, tasks),
#     )


# # Seller service dep
# def get_seller_service(session: SessionDep, tasks: BackgroundTasks):
#     return SellerService(session, tasks)


# # Delivery partner service dep
# def get_delivery_partner_service(session: SessionDep, tasks: BackgroundTasks):
#     return DeliveryPartnerService(session, tasks)


# # Seller dep annotation
# SellerDep = Annotated[
#     Seller,
#     Depends(get_current_seller),
# ]

# # Delivery partner dep annotation
# DeliveryPartnerDep = Annotated[
#     DeliveryPartner,
#     Depends(get_current_partner),
# ]

# # Shipment service dep annotation
# ShipmentServiceDep = Annotated[
#     ShipmentService,
#     Depends(get_shipment_service),
# ]

# # Seller service dep annotation
# SellerServiceDep = Annotated[
#     SellerService,
#     Depends(get_seller_service),
# ]

# # Delivery partner service dep annotaion
# DeliveryPartnerServiceDep = Annotated[
#     DeliveryPartnerService,
#     Depends(get_delivery_partner_service),
# ]


from typing import Annotated
from app.database.database import get_session
from fastapi import BackgroundTasks, Depends, HTTPException, status, FastAPI, Security
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.openpack import OpenpackService
from app.services.site import SiteService
from app.services.user import UserService
from fastapi.security import APIKeyHeader

import os
from dotenv import load_dotenv
from app.config import security_settings

# load_dotenv()
# API_TOKEN = os.getenv("API_TOKEN")

API_TOKEN = security_settings.API_TOKEN
ADMIN_TOKEN = security_settings.ADMIN_TOKEN
OPENPACK_TOKEN = security_settings.OPENPACK_TOKEN

SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_User_service(session: SessionDep):
    return UserService(session)

def get_Site_service(session: SessionDep):
    return SiteService(session)

def get_Openpack_service(session: SessionDep):
    return OpenpackService(session)

# User service dep annotation
UserServiceDep = Annotated[
    UserService,
    Depends(get_User_service),
]
OpenpackServiceDep = Annotated[
    OpenpackService,
    Depends(get_Openpack_service),
]
SiteServiceDep = Annotated[
    SiteService,
    Depends(get_Site_service),
]

app = FastAPI()

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def verify_token(api_key: str = Security(api_key_header)):
    print("reached ",api_key)
    print("required ",OPENPACK_TOKEN)
    if not api_key:
        raise HTTPException(status_code=403, detail="Authorization header missing")
    
    # Expect format: "Token <actual_token>"
    if not api_key.startswith("Token "):
        raise HTTPException(status_code=403, detail="Invalid token format. Use 'Token <value>'")
    
    token = api_key[len("Token "):]  # extract after 'Token '
    
    if token != OPENPACK_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    
    return token  # optional: return it or just `True`

async def verify_token_openpack(api_key: str = Security(api_key_header)):

    if not api_key:
        raise HTTPException(status_code=403, detail="Authorization header missing")
    
    # Expect format: "Token <actual_token>"
    if not api_key.startswith("Token "):
        raise HTTPException(status_code=403, detail="Invalid token format. Use 'Token <value>'")
    
    token = api_key[len("Token "):]  # extract after 'Token '
    
    if token != OPENPACK_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    
    return token  # optional: return it or just `True`


async def verify_admin(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="Authorization header missing")
    
    # Expect format: "Token <actual_token>"
    if not api_key.startswith("Token "):
        raise HTTPException(status_code=403, detail="Invalid token format. Use 'Token <value>'")
    
    token = api_key[len("Token "):]  # extract after 'Token '
    
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    
    return token  # optional: return it or just `True`