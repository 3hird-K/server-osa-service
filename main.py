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
from fastapi.openapi.docs import get_swagger_ui_html

    

# app = FastAPI(title="OSA Service Portal API")
app = FastAPI(
    title="OSA Service Portal API",
    docs_url=None, # This prevents FastAPI from trying to serve its own /docs
    swagger_ui_parameters={"defaultModelsExpandDepth": 1}
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://osa-service-portal-fastapi.vercel.app",
        "https://osaserviceportal.vercel.app",
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:8082"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    # 1. Get the standard UI HTML
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

    dark_styles = """
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-themes@3.0.1/themes/3.x/theme-dracula.css">
    <style>
        /* Base Backgrounds */
        body, .swagger-ui { background-color: #09090b !important; }
        .swagger-ui .topbar { display: none; }
        
        /* Headers & Branding */
        .swagger-ui .info .title { color: #f97316 !important; }
        .swagger-ui .opblock-tag { color: #eeeeee !important; border-bottom: 1px solid #18181b !important; }
        
        /* Fix the "Internal" Section Headers (Parameters, Responses, etc.) */
        .swagger-ui .opblock-section-header { 
            background: #18181b !important; 
            color: #ffffff !important; 
        }
        .swagger-ui .opblock-section-header h4 { color: #ffffff !important; }
        
        /* Table & Parameter Headers */
        .swagger-ui table thead tr td, 
        .swagger-ui table thead tr th { 
            color: #f97316 !important; 
            border-bottom: 1px solid #27272a !important; 
        }
        
        /* Text Contrast Fixes */
        .swagger-ui .opblock .opblock-summary-description,
        .swagger-ui .tabli button,
        .swagger-ui .response-col_status,
        .swagger-ui .response-col_links { 
            color: #d4d4d8 !important; 
        }
        
        /* Button Styling to match OSA */
        .swagger-ui .btn.execute { 
            background-color: #f97316 !important; 
            border-color: #f97316 !important; 
            color: white !important; 
        }
        
        /* Individual API Row Backgrounds */
        .swagger-ui .opblock { background: #121214 !important; border: 1px solid #1c1c21 !important; }
        .swagger-ui .opblock .opblock-summary { background: #121214 !important; }
    </style>
    """
    
    # 3. Inject the styles into the HTML head
    html_content = response.body.decode("utf-8")
    html_content = html_content.replace("</head>", f"{dark_styles}</head>")
    
    return HTMLResponse(content=html_content)

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
                    <span>© 2026 USTP APPDEV</span>
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
async def get_all_users(session: AsyncSession = Depends(get_async_session), account_type: str | None = None):
    if account_type:
        result = await session.execute(
            select(Users).filter(Users.account_type == account_type).order_by(Users.created_at.desc())
        )
    else:
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

@app.get("/students")
async def get_students(session: AsyncSession = Depends(get_async_session)):
    """Get all users with account_type 'student' (Clean up stale users first)"""
    import datetime
    from sqlalchemy import update
    
    # Silent background cleanup
    two_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
    await session.execute(
        update(Users)
        .where(Users.last_active < two_minutes_ago)
        .values(is_online=False)
    )
    await session.commit()

    result = await session.execute(
        select(Users).filter(Users.account_type == "student").order_by(Users.created_at.desc())
    )
    return result.scalars().all()

@app.get("/admins")
async def get_admins(session: AsyncSession = Depends(get_async_session)):
    """Get all users with account_type 'admin' (Clean up stale users first)"""
    import datetime
    from sqlalchemy import update
    
    # Silent background cleanup
    two_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
    await session.execute(
        update(Users)
        .where(Users.last_active < two_minutes_ago)
        .values(is_online=False)
    )
    await session.commit()

    result = await session.execute(
        select(Users).filter(Users.account_type == "admin").order_by(Users.created_at.desc())
    )
    return result.scalars().all()

@app.post("/users/{user_id}/logout")
async def user_logout(user_id: str, session: AsyncSession = Depends(get_async_session)):
    """Explicitly mark user as offline on logout"""
    result = await session.execute(select(Users).filter(Users.id == user_id))
    user = result.scalars().first()
    if user:
        user.is_online = False
        await session.commit()
    return {"status": "success"}

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

@app.post("/users/{user_id}/heartbeat")
async def user_heartbeat(user_id: str, session: AsyncSession = Depends(get_async_session)):
    """Update user's online status and last active timestamp"""
    result = await session.execute(select(Users).filter(Users.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    import datetime
    user.is_online = True
    user.last_active = datetime.datetime.utcnow()
    
    # Optional: Mark others as offline if they haven't pinged in 2 minutes
    # This keeps the "green dots" accurate across the whole system
    two_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
    from sqlalchemy import update
    await session.execute(
        update(Users)
        .where(Users.last_active < two_minutes_ago)
        .values(is_online=False)
    )
    
    await session.commit()
    return {"status": "active", "user_id": user_id}



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
            print(f"User created in Neon DB: {user_id}")

        except Exception as e:
            await session.rollback()
            print(f"Error creating user {user_id}: {str(e)}")
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
                print(f"User updated in Neon DB: {user_id}")
            else:
                print(f"User not found for update: {user_id}")

        except Exception as e:
            await session.rollback()
            print(f"Error updating user {user_id}: {str(e)}")
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
                print(f"User deleted from Neon DB: {user_id}")
            else:
                print(f"User not found for deletion: {user_id}")

        except Exception as e:
            await session.rollback()
            print(f"Error deleting user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

    return {"message": f"Webhook processed - event: {event_type}"}
