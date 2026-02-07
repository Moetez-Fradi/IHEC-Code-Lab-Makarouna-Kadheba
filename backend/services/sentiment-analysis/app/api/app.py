from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logger
from app.api.endpoints import router as api_router

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    Plus besoin de charger des modèles lourds ici (PyTorch) car on utilise OpenRouter.
    """
    logger.info("======================================================================")
    logger.info(f"🚀 Démarrage de {settings.PROJECT_NAME} v1.0.0 (Mode API LLM)")
    logger.info("======================================================================")
    
    yield  # L'application tourne ici
    
    logger.info("🛑 Arrêt du service Sentiment Analysis")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configuration CORS (Important pour que ton Frontend React/Angular puisse appeler l'API)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Inclusion des routes
app.include_router(api_router, prefix="/api/v1")