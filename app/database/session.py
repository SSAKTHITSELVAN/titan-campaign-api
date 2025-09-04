from app.database.base import AsyncSessionLocal

# Dependency (e.g., for FastAPI)
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
