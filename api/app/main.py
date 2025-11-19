# api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.households import router as household_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Receipt scanning and food inventory management",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(household_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"message": "FreshReceipt API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get("/debug/routes")
async def list_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            routes.append(
                {"path": route.path, "methods": list(route.methods), "name": route.name}
            )
    return {"routes": routes}
