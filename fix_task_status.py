import asyncio
from sqlalchemy import select
from database import async_session_maker
from models import Tasks, TimeLogs

async def run_fix():
    print("Starting One-Time Task Status Fix...")
    async with async_session_maker() as s:
        # Fetch all tasks that are NOT completed
        r = await s.execute(select(Tasks).filter(Tasks.status != "Completed"))
        tasks = r.scalars().all()
        
        for task in tasks:
            print(f"Checking Task: {task.title} (ID: {task.id})")
            
            # Sum all logs for this task
            lr = await s.execute(select(TimeLogs).filter(TimeLogs.task_id == task.id))
            logs = lr.scalars().all()
            
            total_logged = 0.0
            for l in logs:
                if l.hours:
                    try:
                        h_str = "".join(c for c in str(l.hours) if c.isdigit() or c == '.')
                        total_logged += float(h_str)
                    except: pass
            
            # Parse required
            required = 0.0
            if task.hours:
                try:
                    req_str = "".join(c for c in str(task.hours) if c.isdigit() or c == '.')
                    required = float(req_str)
                except: pass
            
            print(f"  Logged: {total_logged}, Required: {required}")
            
            if required > 0 and total_logged >= (required - 0.01):
                print(f"  >>> UPDATING STATUS TO COMPLETED")
                task.status = "Completed"
        
        await s.commit()
    print("Fix Complete.")

if __name__ == "__main__":
    asyncio.run(run_fix())
