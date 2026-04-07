from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from database import get_async_session, engine, Base
from models import Profile
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

@app.get("/profiles")
async def get_all_profiles(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Profile).order_by(Profile.updated_at.desc()))
    profiles = result.scalars().all()
    return profiles

@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Profile).filter(Profile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/profiles/{profile_id}")
async def update_profile(profile_id: str, updates: dict, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Profile).filter(Profile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update allowed fields
    allowed_fields = ["firstname", "lastname", "account_type", "avatar_url"]
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(profile, field, value)
    
    await session.commit()
    return profile

@app.post("/api/webhooks/clerk")
async def clerk_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    # Get the Svix headers
    headers = request.headers
    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(status_code=400, detail="Missing Svix headers")

    payload = await request.body()
    secret = os.getenv("CLERK_WEBHOOK_SECRET")
    
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    webhook = Webhook(secret)
    try:
        event = webhook.verify(payload, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event["type"]
    if event_type == "user.created" or event_type == "user.updated":
        data = event["data"]
        user_id = data.get("id")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        avatar_url = data.get("image_url", "")
        
        # Check if profile already exists
        result = await session.execute(select(Profile).filter(Profile.id == user_id))
        existing_profile = result.scalars().first()
        
        if existing_profile:
            existing_profile.firstname = first_name
            existing_profile.lastname = last_name
            existing_profile.avatar_url = avatar_url
        else:
            new_profile = Profile(
                id=user_id,
                firstname=first_name,
                lastname=last_name,
                avatar_url=avatar_url,
                account_type="student"
            )
            session.add(new_profile)
            
        await session.commit()
        
    return {"message": "Webhook processed successfully"}
