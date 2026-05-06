import asyncio
from sqlalchemy import select
from database import async_session_maker
from models import Tasks, TimeLogs

async def check():
    async with async_session_maker() as s:
        r = await s.execute(select(Tasks).filter(Tasks.title == "Limpyo CR"))
        t = r.scalars().first()
        if t:
            print(f"Task: {t.title}")
            print(f"Status: {t.status}")
            print(f"Required Hours: {t.hours}")
            
            lr = await s.execute(select(TimeLogs).filter(TimeLogs.task_id == t.id))
            logs = lr.scalars().all()
            total = 0.0
            for l in logs:
                print(f"  Log {l.id}: {l.hours} hrs")
                if l.hours:
                    try:
                        total += float(str(l.hours).lower().replace('h', '').strip())
                    except: pass
            print(f"Total Logged: {total}")
        else:
            print("Task not found")

if __name__ == "__main__":
    asyncio.run(check())
