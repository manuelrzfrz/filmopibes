from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Filmopibes API",
    description="API REST para la gestión del catálogo de cine de Filmopibes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"mensaje": "API de Filmopibes lista y funcionando 🎬"}

@app.get("/ping")
async def ping_db():
    from app.database import client
    try:
        await client.admin.command('ping')
        return {"estado": "ok", "db": "Conexión con MongoDB correcta 🟢"}
    except Exception as e:
        return {"estado": "error", "detalle": str(e)}
