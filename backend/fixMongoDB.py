import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "filmoteca_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
peliculas_col = db["peliculas"]

def crear_indices():
    print(f"⚙️ Creando índices en la colección 'peliculas' de '{DB_NAME}'...\n")

    # Índices simples para ordenación y filtrado rápido en el frontend
    peliculas_col.create_index([("titulo", ASCENDING)])
    peliculas_col.create_index([("generos", ASCENDING)])
    peliculas_col.create_index([("saga", ASCENDING)])
    peliculas_col.create_index([("plataformas", ASCENDING)])
    
    # Índice único para evitar duplicados por ID de TMDB (ignora los que no lo tengan con 'sparse=True')
    peliculas_col.create_index([("tmdb_id", ASCENDING)], unique=True, sparse=True)

    print("✅ Índices de películas creados correctamente.")
    print("🚀 La base de datos ya está al 100% para el frontend.")

if __name__ == "__main__":
    crear_indices()