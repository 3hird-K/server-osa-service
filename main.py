from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from database import get_async_session, engine, Base
from models import Users, Tasks, TimeLogs, Notifications
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
import os
import uuid
from svix.webhooks import Webhook
from clerk_backend_api import Clerk
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel

    

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
 
 
 # --- TASK CRUD ENDPOINTS ---
 
@app.get("/tasks")
async def get_all_tasks(session: AsyncSession = Depends(get_async_session)):
     """Fetch all tasks from Neon DB with assignee details"""
     result = await session.execute(
         select(Tasks).options(selectinload(Tasks.assignee)).order_by(Tasks.created_at.desc())
     )
     tasks = result.scalars().all()
     return tasks
 
@app.get("/tasks/{task_id}")
async def get_task(task_id: str, session: AsyncSession = Depends(get_async_session)):
     """Fetch a single task by ID with assignee details"""
     result = await session.execute(
         select(Tasks).options(selectinload(Tasks.assignee)).filter(Tasks.id == task_id)
     )
     task = result.scalars().first()
     if not task:
         raise HTTPException(status_code=404, detail="Task not found")
     return task
 
@app.post("/tasks")
async def create_task(task_data: dict, session: AsyncSession = Depends(get_async_session)):
     """Create a new task in Neon DB"""
     try:
         task_id = f"TSK-{str(uuid.uuid4())[:8].upper()}"
         new_task = Tasks(
             id=task_id,
             title=task_data.get("title"),
             description=task_data.get("description"),
             status=task_data.get("status", "Pending"),
             assigned_to=task_data.get("assigned_to"),
             location=task_data.get("location"),
             hours=task_data.get("hours")
         )
         session.add(new_task)

         # Notification: Task Assigned (at creation)
         if task_data.get("assigned_to"):
             notif_id = f"NTF-{str(uuid.uuid4())[:8].upper()}"
             new_notif = Notifications(
                 id=notif_id,
                 user_id=task_data.get("assigned_to"),
                 title="New Task Assigned",
                 message=f"You have been assigned to: {new_task.title}",
                 type="task_assigned",
                 related_id=new_task.id
             )
             session.add(new_notif)

         await session.commit()
         return new_task
     except Exception as e:
         await session.rollback()
         raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
 
@app.put("/tasks/{task_id}")
async def update_task(task_id: str, updates: dict, session: AsyncSession = Depends(get_async_session)):
     """Update a task in Neon DB"""
     result = await session.execute(select(Tasks).filter(Tasks.id == task_id))
     task = result.scalars().first()
     if not task:
         raise HTTPException(status_code=404, detail="Task not found")
     
     old_assignee = task.assigned_to
     allowed_fields = ["title", "description", "status", "assigned_to", "location", "hours"]
     for field, value in updates.items():
         if field in allowed_fields:
             setattr(task, field, value)
     
     # Notification: Task Assigned
     if "assigned_to" in updates and updates["assigned_to"] != old_assignee and updates["assigned_to"]:
         notif_id = f"NTF-{str(uuid.uuid4())[:8].upper()}"
         new_notif = Notifications(
             id=notif_id,
             user_id=updates["assigned_to"],
             title="New Task Assigned",
             message=f"You have been assigned to: {task.title}",
             type="task_assigned",
             related_id=task.id
         )
         session.add(new_notif)

     await session.commit()
     return task
 
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, session: AsyncSession = Depends(get_async_session)):
     """Delete a task from Neon DB"""
     result = await session.execute(select(Tasks).filter(Tasks.id == task_id))
     task = result.scalars().first()
     if not task:
         raise HTTPException(status_code=404, detail="Task not found")
     
     await session.delete(task)
     await session.commit()
     return {"status": "success", "message": f"Task {task_id} deleted"}

# --- TIME LOGS ENDPOINTS ---

@app.get("/timelogs")
async def get_all_timelogs(session: AsyncSession = Depends(get_async_session)):
    """Fetch all time logs with task and user details"""
    result = await session.execute(
        select(TimeLogs)
        .options(selectinload(TimeLogs.task), selectinload(TimeLogs.user))
        .order_by(TimeLogs.date.desc())
    )
    return result.scalars().all()

@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str, session: AsyncSession = Depends(get_async_session)):
    """Fetch all logs for a specific task"""
    result = await session.execute(
        select(TimeLogs)
        .options(selectinload(TimeLogs.task), selectinload(TimeLogs.user))
        .filter(TimeLogs.task_id == task_id)
        .order_by(TimeLogs.date.desc())
    )
    return result.scalars().all()
 
@app.get("/users/{user_id}/logs")
async def get_user_logs(user_id: str, session: AsyncSession = Depends(get_async_session)):
    """Fetch all logs for a specific user"""
    result = await session.execute(
        select(TimeLogs)
        .options(selectinload(TimeLogs.task), selectinload(TimeLogs.user))
        .filter(TimeLogs.user_id == user_id)
        .order_by(TimeLogs.date.desc())
    )
    return result.scalars().all()

@app.post("/timelogs")
async def create_timelog(log_data: dict, session: AsyncSession = Depends(get_async_session)):
    """Create a new time log record"""
    try:
        log_id = f"LOG-{str(uuid.uuid4())[:8].upper()}"
        new_log = TimeLogs(
            id=log_id,
            task_id=log_data.get("task_id"),
            user_id=log_data.get("user_id"),
            start_time=log_data.get("start_time"),
            break_time=log_data.get("break_time"),
            back_time=log_data.get("back_time"),
            end_time=log_data.get("end_time"),
            hours=log_data.get("hours"),
            evidence_urls=log_data.get("evidence_urls") # Should be JSON string
        )
        session.add(new_log)
        
        # --- Auto-Completion Logic ---
        await check_task_completion(session, new_log.task_id)
        
        await session.commit()
        return new_log
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create time log: {str(e)}")

@app.put("/timelogs/{log_id}")
async def update_timelog(log_id: str, updates: dict, session: AsyncSession = Depends(get_async_session)):
    """Update an existing time log (for break, back, end_time, etc)"""
    result = await session.execute(select(TimeLogs).filter(TimeLogs.id == log_id))
    log = result.scalars().first()
    if not log:
        raise HTTPException(status_code=404, detail="Time log not found")
    
    allowed_fields = ["start_time", "break_time", "back_time", "end_time", "hours", "evidence_urls"]
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(log, field, value)
    
    # --- Auto-Completion Logic ---
    if "end_time" in updates or "hours" in updates:
        await check_task_completion(session, log.task_id)

    await session.commit()
    await session.refresh(log)
    return log


async def check_task_completion(session: AsyncSession, task_id: str):
    """
    Helper function to check if a task's logged hours meet or exceed its required hours.
    If they do, it marks the task as 'Completed' and sends a notification.
    """
    try:
        # 1. Fetch the task
        task_result = await session.execute(select(Tasks).filter(Tasks.id == task_id))
        task = task_result.scalars().first()
        
        if not task or task.status.lower() == "completed":
            return

        # 2. Sum all hours for this task across all logs
        logs_result = await session.execute(select(TimeLogs).filter(TimeLogs.task_id == task_id))
        all_logs = logs_result.scalars().all()
        
        total_logged_hours = 0.0
        for l in all_logs:
            if l.hours:
                try:
                    # Clean string (remove 'h', etc) and convert to float
                    h_str = "".join(c for c in str(l.hours) if c.isdigit() or c == '.')
                    if h_str:
                        total_logged_hours += float(h_str)
                except Exception as e:
                    print(f"[Auto-Complete] Error parsing log hours '{l.hours}': {e}")
        
        # 3. Parse required hours from task
        required_hours = 0.0
        if task.hours:
            try:
                req_str = "".join(c for c in str(task.hours) if c.isdigit() or c == '.')
                if req_str:
                    required_hours = float(req_str)
            except Exception as e:
                print(f"[Auto-Complete] Error parsing task required hours '{task.hours}': {e}")
        
        # 4. Compare and Update
        print(f"[Auto-Complete] Task {task_id}: Logged={total_logged_hours}, Required={required_hours}")
        
        if required_hours > 0 and total_logged_hours >= (required_hours - 0.01):
            task.status = "Completed"
            
            # Notification: Task Completed
            if task.assigned_to:
                notif_id = f"NTF-{str(uuid.uuid4())[:8].upper()}"
                new_notif = Notifications(
                    id=notif_id,
                    user_id=task.assigned_to,
                    title="Task Completed!",
                    message=f"Great job! Task '{task.title}' is now complete.",
                    type="task_completed",
                    related_id=task.id
                )
                session.add(new_notif)
            print(f"[Auto-Complete] Task {task.id} marked as Completed.")
            
    except Exception as e:
        print(f"[Auto-Complete] Critical Error: {str(e)}")

@app.delete("/timelogs/{log_id}")
async def delete_timelog(log_id: str, user_id: str, session: AsyncSession = Depends(get_async_session)):
    """Delete a time log if the task is not yet completed and it belongs to the user"""
    result = await session.execute(select(TimeLogs).filter(TimeLogs.id == log_id))
    log = result.scalars().first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Time log not found")
    
    # Ownership Check
    if log.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own logs")
        
    # Task Status Check: Lock logs if task is already completed
    task_result = await session.execute(select(Tasks).filter(Tasks.id == log.task_id))
    task = task_result.scalars().first()
    
    if task and task.status.lower() == "completed":
        raise HTTPException(status_code=400, detail="Cannot delete logs for a task that is already completed.")
        
    await session.delete(log)
    await session.commit()
    return {"message": "Log deleted successfully"}

# --- NOTIFICATIONS ENDPOINTS ---

@app.get("/users/{user_id}/notifications")
async def get_user_notifications(user_id: str, session: AsyncSession = Depends(get_async_session)):
    """Fetch all notifications for a specific user"""
    result = await session.execute(
        select(Notifications)
        .filter(Notifications.user_id == user_id)
        .order_by(Notifications.created_at.desc())
    )
    return result.scalars().all()

@app.patch("/notifications/{notif_id}/read")
async def mark_notification_as_read(notif_id: str, session: AsyncSession = Depends(get_async_session)):
    """Mark a notification as read"""
    result = await session.execute(select(Notifications).filter(Notifications.id == notif_id))
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    await session.commit()
    return notif

@app.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: str, session: AsyncSession = Depends(get_async_session)):
    """Delete a single notification"""
    result = await session.execute(select(Notifications).filter(Notifications.id == notif_id))
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    await session.delete(notif)
    await session.commit()
    return {"message": "Notification deleted successfully"}

@app.post("/users/{user_id}/welcome-notification")
async def create_welcome_notification(user_id: str, session: AsyncSession = Depends(get_async_session)):
    """Create a dummy welcome notification"""
    notif_id = f"NTF-{str(uuid.uuid4())[:8].upper()}"
    new_notif = Notifications(
        id=notif_id,
        user_id=user_id,
        title="Welcome back!",
        message="Glad to see you again. Check your tasks for updates.",
        type="system"
    )
    session.add(new_notif)
    await session.commit()
    return new_notif

# --- DASHBOARD STATS ENDPOINT ---

@app.get("/dashboard/stats")
async def get_dashboard_stats(session: AsyncSession = Depends(get_async_session)):
    """Fetch aggregated statistics for the dashboard"""
    from sqlalchemy import func
    
    try:
        # 1. Total Users
        total_users_result = await session.execute(select(func.count(Users.id)))
        total_users = total_users_result.scalar() or 0
        
        # 2. Total Tasks
        total_tasks_result = await session.execute(select(func.count(Tasks.id)))
        total_tasks = total_tasks_result.scalar() or 0
        
        # 3. Completed Tasks
        completed_tasks_result = await session.execute(
            select(func.count(Tasks.id)).filter(Tasks.status == "Completed")
        )
        completed_tasks = completed_tasks_result.scalar() or 0
        
        # 4. Pending/In Progress Tasks
        pending_tasks_result = await session.execute(
            select(func.count(Tasks.id)).filter(Tasks.status != "Completed")
        )
        pending_tasks = pending_tasks_result.scalar() or 0
        
        # 5. Total Hours Logged
        logs_result = await session.execute(select(TimeLogs.hours))
        all_hours = logs_result.scalars().all()
        total_hours = 0.0
        for h in all_hours:
            if h:
                try:
                    # Clean string (e.g. "2h" -> 2.0)
                    h_clean = "".join(c for c in str(h) if c.isdigit() or c == '.')
                    if h_clean:
                        total_hours += float(h_clean)
                except: pass
        
        # 6. Recent Activity (Latest 5 logs)
        recent_activity_result = await session.execute(
            select(TimeLogs)
            .options(selectinload(TimeLogs.task), selectinload(TimeLogs.user))
            .order_by(TimeLogs.date.desc())
            .limit(5)
        )
        recent_logs = recent_activity_result.scalars().all()
        
        # 7. Staff Count
        staff_count_result = await session.execute(
            select(func.count(Users.id)).filter(Users.account_type == "admin")
        )
        staff_count = staff_count_result.scalar() or 0

        # 8. Chart Data (Multi-Variable Trend - Last 30 Days)
        from datetime import timedelta
        import datetime
        thirty_days_ago = datetime.datetime.utcnow() - timedelta(days=30)
        
        # A. Users Daily counts
        users_daily_result = await session.execute(
            select(func.date(Users.created_at).label("date"), func.count(Users.id).label("count"))
            .filter(Users.created_at >= thirty_days_ago)
            .group_by(func.date(Users.created_at))
        )
        users_counts_map = {row.date.strftime("%b %d"): row.count for row in users_daily_result.all()}
        
        # B. Tasks Daily counts (Completed only)
        tasks_daily_result = await session.execute(
            select(func.date(Tasks.updated_at).label("date"), func.count(Tasks.id).label("count"))
            .filter(Tasks.updated_at >= thirty_days_ago, Tasks.status == "Completed")
            .group_by(func.date(Tasks.updated_at))
        )
        tasks_counts_map = {row.date.strftime("%b %d"): row.count for row in tasks_daily_result.all()}
        
        # C. Hours Daily counts
        hours_daily_result = await session.execute(
            select(func.date(TimeLogs.date).label("date"), TimeLogs.hours)
            .filter(TimeLogs.date >= thirty_days_ago)
        )
        hours_logs = hours_daily_result.all()
        hours_counts_map = {}
        for row in hours_logs:
            d_str = row.date.strftime("%b %d")
            try:
                h_val = float("".join(c for c in str(row.hours) if c.isdigit() or c == '.'))
                hours_counts_map[d_str] = hours_counts_map.get(d_str, 0.0) + h_val
            except: pass

        # Get base counts (before 30 days ago)
        base_users = (await session.execute(select(func.count(Users.id)).filter(Users.created_at < thirty_days_ago))).scalar() or 0
        base_tasks = (await session.execute(select(func.count(Tasks.id)).filter(Tasks.updated_at < thirty_days_ago, Tasks.status == "Completed"))).scalar() or 0
        
        base_hours_result = await session.execute(select(TimeLogs.hours).filter(TimeLogs.date < thirty_days_ago))
        base_hours = 0.0
        for h in base_hours_result.scalars().all():
            try: base_hours += float("".join(c for c in str(h) if c.isdigit() or c == '.'))
            except: pass
        
        chart_data = []
        cum_users = base_users
        cum_tasks = base_tasks
        cum_hours = base_hours
        
        for i in range(30, -1, -1):
            day_dt = datetime.datetime.utcnow() - timedelta(days=i)
            day_str = day_dt.strftime("%b %d")
            
            cum_users += users_counts_map.get(day_str, 0)
            cum_tasks += tasks_counts_map.get(day_str, 0)
            cum_hours += hours_counts_map.get(day_str, 0.0)
            
            chart_data.append({
                "name": day_str,
                "users": cum_users,
                "tasks": cum_tasks,
                "hours": round(cum_hours, 1)
            })

        return {
            "total_users": total_users,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "total_hours": round(total_hours, 1),
            "staff_count": staff_count,
            "recent_logs": recent_logs,
            "chart_data": chart_data
        }
    except Exception as e:
        print(f"Dashboard Stats Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")

class SupportMessage(BaseModel):
    user_id: str | None = None
    email: str | None = None
    message: str

@app.post("/support/message")
async def send_support_message(support: SupportMessage):
    """Send a support message to the admin email via SMTP"""
    admin_email = "dime.neil03@gmail.com"
    
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    if not smtp_user or not smtp_pass:
        # If credentials are not set, we just log it and return success for the demo
        # In production, this should be a properly configured SMTP service
        print(f"[Support] SMTP credentials not set. Message from {support.user_id or 'Guest'}: {support.message}")
        return {"status": "success", "message": "Support message received (Demo Mode)"}

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = admin_email
        msg['Subject'] = f"OSA Support Request - {support.user_id or 'Guest'}"
        
        body = f"User ID: {support.user_id or 'Not Logged In'}\n"
        body += f"User Email: {support.email or 'Not Provided'}\n\n"
        body += f"Message:\n{support.message}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        return {"status": "success", "message": "Message sent successfully"}
    except Exception as e:
        print(f"[Support] Email Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message via email")
