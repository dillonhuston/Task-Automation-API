
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
from app.routers.auth import router as auth_router
from app.routers.tasks import router as task_router
#from app.routers.admin import router as admin_router
from app.routers.file_upload import router as file_router
from app.routers.files import router as file_data
from app.models.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

sys.path.append(str(Path(__file__).parent))

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





app.include_router(auth_router)
app.include_router(file_router)
app.include_router(task_router)
#pp.include_router(admin_router)
app.include_router(file_data)


@app.get("/health")
async def get_health():
    return {"success": 200}