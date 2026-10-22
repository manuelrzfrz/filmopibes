"""
==============================================================================
ARCHIVO: app/database.py
PROPÓSITO: Conexión asíncrona con MongoDB.
DESCRIPCIÓN: Inicializa el cliente oficial asíncrono (Motor) utilizando los
            parámetros del archivo de configuración (core/config.py) y expone
            el objeto 'db' para interactuar con las colecciones.
==============================================================================
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "filmoteca_db")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_db():
    db_instance.client = AsyncIOMotorClient(MONGO_URI)
    db_instance.db = db_instance.client[DB_NAME]
    print(f"✅ Conectado a MongoDB asíncrono: '{DB_NAME}'")

async def close_db():
    if db_instance.client:
        db_instance.client.close()
        print("🔌 Conexión a MongoDB cerrada.")

def get_db():
    return db_instance.db