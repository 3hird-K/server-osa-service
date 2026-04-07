from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from database import get_async_session, engine, Base
from models import Users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from svix.webhooks import Webhook
from clerk_backend_api import Clerk

app = FastAPI(title="OSA Service Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/users")
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Users).order_by(Users.created_at.desc()))
    users = result.scalars().all()
    return users

@app.get("/users/{user_id}")
async def get_user(user_id: str, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Users).filter(Users.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}")
async def update_user(user_id: str, updates: dict, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Users).filter(Users.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    allowed_fields = ["firstname", "lastname", "account_type", "avatar_url"]
    
    # Validate account_type if being updated
    if "account_type" in updates:
        if updates["account_type"] not in ["student", "admin"]:
            raise HTTPException(status_code=400, detail="account_type must be 'student' or 'admin'")
    
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(user, field, value)
    
    await session.commit()
    return user


@app.post("/api/webhooks/clerk")
async def clerk_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):

    headers = request.headers
    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(status_code=400, detail="Missing Svix headers")

    payload = await request.body()
    secret = os.getenv("CLERK_WEBHOOK_SECRET")

    webhook = Webhook(secret)

    try:
        event = webhook.verify(payload, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]

    # Get Clerk user_id (e.g., user_3C17_Vez9Mfa5)
    user_id = data.get("id")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    avatar_url = data.get("image_url", "")
    username = data.get("username")  

    # Extract public_metadata for account_type/role
    public_metadata = data.get("public_metadata", {})
    account_type = public_metadata.get("role", "student")

    # Validate account_type
    if account_type not in ["student", "admin"]:
        account_type = "student"

    # Extract email
    email = None
    email_addresses = data.get("email_addresses", [])
    for email_obj in email_addresses:
        if email_obj.get("verification", {}).get("status") == "verified":
            email = email_obj.get("email_address")
            break

    if not email and email_addresses:
        email = email_addresses[0].get("email_address")

    # -------------------------
    # HANDLE EVENTS
    # -------------------------

    if event_type == "user.created":

        new_user = Users(
            id=user_id,
            firstname=first_name,
            lastname=last_name,
            email=email,
            avatar_url=avatar_url,
            username=username or email.split("@")[0],  # fallback
            account_type=account_type,  # From Clerk public_metadata or default "student"
        )

        session.add(new_user)
        await session.commit()

    elif event_type == "user.updated":

        result = await session.execute(
            select(Users).where(Users.id == user_id)
        )
        existing_user = result.scalars().first()

        if existing_user:
            existing_user.firstname = first_name
            existing_user.lastname = last_name
            existing_user.email = email
            existing_user.avatar_url = avatar_url
            existing_user.username = username or existing_user.username
            existing_user.account_type = account_type  # Update from Clerk public_metadata

            await session.commit()

    elif event_type == "user.deleted":

        result = await session.execute(
            select(Users).where(Users.id == user_id)
        )
        user = result.scalars().first()

        if user:
            await session.delete(user)
            await session.commit()

    return {"message": "Webhook processed"}

# @app.post("/api/webhooks/clerk")
# async def clerk_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
#     # Get the Svix headers
#     headers = request.headers
#     svix_id = headers.get("svix-id")
#     svix_timestamp = headers.get("svix-timestamp")
#     svix_signature = headers.get("svix-signature")

#     if not svix_id or not svix_timestamp or not svix_signature:
#         raise HTTPException(status_code=400, detail="Missing Svix headers")

#     payload = await request.body()
#     secret = os.getenv("CLERK_WEBHOOK_SECRET")
    
#     if not secret:
#         raise HTTPException(status_code=500, detail="Webhook secret not configured")

#     webhook = Webhook(secret)
#     try:
#         event = webhook.verify(payload, {
#             "svix-id": svix_id,
#             "svix-timestamp": svix_timestamp,
#             "svix-signature": svix_signature,
#         })
#     except Exception as e:
#         raise HTTPException(status_code=400, detail="Invalid signature")

#     # Handle the event
#     event_type = event["type"]
#     if event_type == "user.created" or event_type == "user.updated":
#         data = event["data"]
#         user_id = data.get("id")
#         first_name = data.get("first_name", "")
#         last_name = data.get("last_name", "")
#         avatar_url = data.get("image_url", "")
        
#         # Extract primary email from email_addresses array
#         email = None
#         email_addresses = data.get("email_addresses", [])
#         if email_addresses:
#             # Find primary email or use first email
#             for email_obj in email_addresses:
#                 if email_obj.get("verification") and email_obj["verification"].get("status") == "verified":
#                     email = email_obj.get("email_address")
#                     break
#             if not email and email_addresses:
#                 email = email_addresses[0].get("email_address")
        
#         # Sync to Users table with default account_type="student"
#         if email:
#             result = await session.execute(select(Users).filter(Users.id == user_id))
#             existing_user = result.scalars().first()
            
#             if existing_user:
#                 existing_user.firstname = first_name
#                 existing_user.lastname = last_name
#                 existing_user.email = email
#                 existing_user.avatar_url = avatar_url
#                 # Keep existing account_type unless explicitly changed
#             else:
#                 new_user = Users(
#                     id=user_id,
#                     firstname=first_name,
#                     lastname=last_name,
#                     email=email,
#                     avatar_url=avatar_url,
#                     username=email.split("@")[0],  # Generate username from email
#                     account_type="student"  # Default account type
#                 )
#                 session.add(new_user)
            
#         await session.commit()
        
#     return {"message": "Webhook processed successfully"}
