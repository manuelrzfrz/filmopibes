import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "filmoteca_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
peliculas_col = db["peliculas"]

def listar_duplicados():
    print(f"🔍 Buscando películas con 'tmdb_id' duplicado en la base de datos '{DB_NAME}'...\n")

    # Pipeline de agregación para encontrar tmdb_id compartidos
    pipeline = [
        {"$match": {"tmdb_id": {"$exists": True, "$ne": None}}},
        {
            "$group": {
                "_id": "$tmdb_id",
                "count": {"$sum": 1},
                "peliculas": {
                    "$push": {
                        "id": "$_id",
                        "titulo": "$titulo",
                        "titulo_original": "$titulo_original",
                        "año": "$año",
                        "directores": "$directores"
                    }
                }
            }
        },
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]

    duplicados = list(peliculas_col.aggregate(pipeline))

    if not duplicados:
        print("🎉 ¡Perfecto! No se encontraron películas compartiendo el mismo 'tmdb_id'.")
        return

    total_conflictos = len(duplicados)
    total_pelis_afectadas = sum(d["count"] for d in duplicados)

    print("=" * 80)
    print(f"⚠️  SE HAN ENCONTRADO {total_conflictos} GRUPOS DE DUPLICADOS ({total_pelis_afectadas} PELÍCULAS AFECTADAS)")
    print("=" * 80 + "\n")

    archivo_salida = "duplicados_tmdb.txt"
    with open(archivo_salida, "w", encoding="utf-8") as out_f:
        out_f.write(f"REPORTE DE DUPLICADOS DE TMDB_ID EN {DB_NAME.upper()}\n")
        out_f.write("=" * 70 + "\n\n")

        for idx, grupo in enumerate(duplicados, 1):
            tmdb_id = grupo["_id"]
            count = grupo["count"]

            header = f"Grupo #{idx} | TMDB ID: {tmdb_id} ({count} películas comparten este ID):"
            print(header)
            out_f.write(header + "\n")

            for peli in grupo["peliculas"]:
                id_str = str(peli["id"])
                tit = peli.get("titulo") or "Sin título"
                tit_orig = f" ({peli.get('titulo_original')})" if peli.get("titulo_original") else ""
                ano = f" - {peli.get('año')}" if peli.get("año") else ""
                dirs = f" | Dir: {', '.join(peli.get('directores', []))}" if peli.get("directores") else ""

                linea = f"   • [_id: {id_str}] {tit}{tit_orig}{ano}{dirs}"
                print(linea)
                out_f.write(linea + "\n")

            print("-" * 80)
            out_f.write("-" * 70 + "\n")

    print(f"\n📄 Se ha guardado el informe completo en: '{archivo_salida}'")

if __name__ == "__main__":
    listar_duplicados()