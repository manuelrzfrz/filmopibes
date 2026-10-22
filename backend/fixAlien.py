import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "filmoteca_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
peliculas_col = db["peliculas"]

def fix_alien_3():
    # Buscamos Alien 3 y le ponemos su TMDB ID correcto (8078)
    res = peliculas_col.update_many(
        {"titulo": {"$regex": "alien 3", "$options": "i"}},
        {"$set": {"tmdb_id": 8078}}
    )
    
    if res.modified_count > 0:
        print(f"✅ ¡Corregido! Se ha actualizado 'Alien 3' con el tmdb_id: 8078 en {res.modified_count} documento(s).")
    else:
        print("⚠️ No se ha modificado nada. Comprueba que el título sea exactamente 'Alien 3'.")

if __name__ == "__main__":
    fix_alien_3()