from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from database import get_async_session, engine, Base
from models import Users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from svix.webhooks import Webhook
from clerk_backend_api import Clerk
from fastapi.responses import HTMLResponse

app = FastAPI(title="OSA Service Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OSA Service Server | USTP</title>
        <link rel="icon" type="image/png" href="https://raw.githubusercontent.com/3hird-K/osa-service-portal/with-fastapi/assets/osa.png">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            body { font-family: 'Inter', sans-serif; background-color: #09090b; }
            .orange-glow { box-shadow: 0 0 20px rgba(249, 115, 22, 0.1); }
            .accent-orange { color: #f97316; }
            .bg-orange-main { background-color: #f97316; }
            .border-card { border-color: #18181b; }
        </style>
    </head>
    <body class="text-zinc-400 min-h-screen flex items-center justify-center p-6">
        <div class="max-w-xl w-full">
            <div class="mb-10">
                <div class="flex items-center justify-between mb-6">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 rounded bg-orange-main flex items-center justify-center text-white font-bold orange-glow">
                            O
                        </div>
                        <div>
                            <h2 class="text-zinc-100 font-semibold tracking-tight uppercase text-xs">Osa Service Portal</h2>
                            <p class="text-[10px] text-zinc-500 font-bold tracking-[0.2em] uppercase">System Backend</p>
                        </div>
                    </div>
                    <img src="https://raw.githubusercontent.com/3hird-K/osa-service-portal/with-fastapi/assets/ustp.png" 
                         alt="USTP Logo" class="h-12 w-auto opacity-80 hover:opacity-100 transition-opacity">
                </div>
                
                <h1 class="text-3xl font-bold text-zinc-100 tracking-tight">
                    Backend <span class="accent-orange">Service Engine</span>
                </h1>
                <p class="text-zinc-500 text-sm mt-1 font-medium">University of Science and Technology of Southern Philippines</p>
            </div>

            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="bg-[#121214] border border-card p-5 rounded-2xl">
                    <div class="flex items-center space-x-2 mb-3">
                        <div class="w-2 h-2 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse"></div>
                        <span class="text-[10px] uppercase font-bold tracking-widest text-zinc-500">API Status</span>
                    </div>
                    <p class="text-xl font-bold text-zinc-100 tracking-tight text-white">Operational</p>
                    <p class="text-[10px] text-green-500 font-medium mt-1">Ready for Requests</p>
                </div>
                <div class="bg-[#121214] border border-card p-5 rounded-2xl">
                    <div class="flex items-center space-x-2 mb-3 text-zinc-500">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        <span class="text-[10px] uppercase font-bold tracking-widest text-zinc-500">Environment</span>
                    </div>
                    <p class="text-xl font-bold text-zinc-100 tracking-tight text-white">Production</p>
                    <p class="text-[10px] text-orange-500 font-medium mt-1">Neon + Render</p>
                </div>
            </div>

            <div class="bg-[#121214] border border-card rounded-2xl overflow-hidden">
                <a href="/docs" class="flex items-center justify-between p-4 hover:bg-zinc-800/50 transition-all border-b border-card group">
                    <div class="flex items-center space-x-4">
                        <div class="p-2 bg-zinc-900 rounded-lg text-orange-500 group-hover:bg-orange-500 group-hover:text-white transition-all">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        </div>
                        <div>
                            <p class="text-sm font-semibold text-zinc-100">Swagger UI</p>
                            <p class="text-xs text-zinc-500 uppercase tracking-tighter">Interactive API Docs</p>
                        </div>
                    </div>
                    <svg class="w-4 h-4 text-zinc-600 group-hover:text-orange-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </a>
                
                <a href="/redoc" class="flex items-center justify-between p-4 hover:bg-zinc-800/50 transition-all group">
                    <div class="flex items-center space-x-4">
                        <div class="p-2 bg-zinc-900 rounded-lg text-zinc-500 group-hover:bg-zinc-100 group-hover:text-black transition-all">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                        </div>
                        <div>
                            <p class="text-sm font-semibold text-zinc-100">Redoc Schema</p>
                            <p class="text-xs text-zinc-500 uppercase tracking-tighter">Static Documentation</p>
                        </div>
                    </div>
                    <svg class="w-4 h-4 text-zinc-600 group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </a>
            </div>

            <div class="mt-12 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-600">
                <div class="flex items-center space-x-2">
                    <span class="w-1.5 h-1.5 bg-zinc-700 rounded-full"></span>
                    <span>© 2026 USTP CAPSTONE</span>
                </div>
                <span class="flex items-center">
                    Engineered by: <span class="text-orange-500 ml-2">IT3R1</span> 
                </span>
            </div>
        </div>
    </body>
    </html>
    """
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


# -------------------------
# /profiles endpoints (alias to /users for frontend compatibility)
# -------------------------

@app.get("/profiles")
async def get_all_profiles(session: AsyncSession = Depends(get_async_session)):
    """Fetch all user profiles from Neon DB"""
    result = await session.execute(select(Users).order_by(Users.created_at.desc()))
    users = result.scalars().all()
    return users


@app.get("/profiles/{user_id}")
async def get_profile(user_id: str, session: AsyncSession = Depends(get_async_session)):
    """Fetch a single user profile from Neon DB"""
    result = await session.execute(select(Users).filter(Users.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/profiles/{user_id}")
async def update_profile(user_id: str, updates: dict, session: AsyncSession = Depends(get_async_session)):
    """Update user profile in Neon DB"""
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


# -------------------------
# Manual sync endpoint - useful if webhook doesn't fire
# -------------------------

@app.post("/sync-user/{user_id}")
async def sync_user_from_clerk(user_id: str, session: AsyncSession = Depends(get_async_session)):
    """
    Manually sync a Clerk user to Neon DB if webhook hasn't fired yet.
    This endpoint fetches the user from Clerk and creates/updates in Neon.
    """
    try:
        # Fetch user from Clerk
        clerk_user = clerk.users.get(user_id)
        
        # Extract user data
        first_name = clerk_user.first_name or ""
        last_name = clerk_user.last_name or ""
        avatar_url = clerk_user.image_url or ""
        username = clerk_user.username
        
        # Get primary email
        email = None
        if clerk_user.email_addresses:
            for email_obj in clerk_user.email_addresses:
                if email_obj.verification and email_obj.verification.status == "verified":
                    email = email_obj.email_address
                    break
            if not email:
                email = clerk_user.email_addresses[0].email_address
        
        # Get account type from public_metadata
        public_metadata = clerk_user.public_metadata or {}
        account_type = public_metadata.get("role", "student")
        if account_type not in ["student", "admin"]:
            account_type = "student"
        
        # Check if user exists
        result = await session.execute(select(Users).where(Users.id == user_id))
        existing_user = result.scalars().first()
        
        if existing_user:
            # Update existing user
            existing_user.firstname = first_name
            existing_user.lastname = last_name
            existing_user.email = email
            existing_user.avatar_url = avatar_url
            if username:
                existing_user.username = username
            existing_user.account_type = account_type
            await session.commit()
            print(f"✅ User synced (updated) in Neon DB: {user_id}")
            return {"message": "User synced (updated)", "user_id": user_id, "status": "updated"}
        else:
            # Create new user
            username_value = username
            if not username_value and email:
                username_value = email.split("@")[0]
            if not username_value:
                username_value = f"user_{user_id[-8:]}"
            
            new_user = Users(
                id=user_id,
                firstname=first_name,
                lastname=last_name,
                email=email,
                avatar_url=avatar_url,
                username=username_value,
                account_type=account_type,
            )
            session.add(new_user)
            await session.commit()
            print(f"✅ User synced (created) in Neon DB: {user_id}")
            return {"message": "User synced (created)", "user_id": user_id, "status": "created"}
            
    except Exception as e:
        await session.rollback()
        print(f"❌ Error syncing user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync user: {str(e)}")


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
        try:
            # Generate username fallback if not provided
            username_value = username
            if not username_value and email:
                username_value = email.split("@")[0]
            if not username_value:
                username_value = f"user_{user_id[-8:]}"

            new_user = Users(
                id=user_id,
                firstname=first_name,
                lastname=last_name,
                email=email,
                avatar_url=avatar_url,
                username=username_value,
                account_type=account_type,  # From Clerk public_metadata or default "student"
            )

            session.add(new_user)
            await session.commit()
            print(f"✅ User created in Neon DB: {user_id}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    elif event_type == "user.updated":
        try:
            result = await session.execute(
                select(Users).where(Users.id == user_id)
            )
            existing_user = result.scalars().first()

            if existing_user:
                existing_user.firstname = first_name
                existing_user.lastname = last_name
                existing_user.email = email
                existing_user.avatar_url = avatar_url
                if username:
                    existing_user.username = username
                existing_user.account_type = account_type  # Update from Clerk public_metadata

                await session.commit()
                print(f"✅ User updated in Neon DB: {user_id}")
            else:
                print(f"⚠️  User not found for update: {user_id}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error updating user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

    elif event_type == "user.deleted":
        try:
            result = await session.execute(
                select(Users).where(Users.id == user_id)
            )
            user = result.scalars().first()

            if user:
                await session.delete(user)
                await session.commit()
                print(f"✅ User deleted from Neon DB: {user_id}")
            else:
                print(f"⚠️  User not found for deletion: {user_id}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error deleting user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

    return {"message": f"Webhook processed - event: {event_type}"}

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
