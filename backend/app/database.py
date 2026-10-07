import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_URI)
db = client.filmoteca_db

peliculas_col = db.peliculas
usuarios_col = db.usuarios
valoraciones_col = db.valoraciones
