"""
==============================================================================
ARCHIVO: app/main.py
PROPÓSITO: Punto de entrada (Entrypoint) de la API con FastAPI.
DESCRIPCIÓN: Crea la instancia global de FastAPI, configura los permisos de CORS
            para permitir llamadas desde la app web (frontend) y conecta los
            routers creados en la carpeta 'routers/'.
==============================================================================
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import connect_db, close_db
from app.routers import peliculas, usuarios, valoraciones

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(
    title="Filmopibes API",
    description="API para la gestión y visualización de la Filmoteca",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios.router)
app.include_router(peliculas.router)
app.include_router(valoraciones.router)

@app.get("/")
async def root():
    return {"status": "online", "message": "API de Filmopibes funcionando correctamente"}