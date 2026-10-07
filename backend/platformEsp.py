import time
import requests
from pymongo import MongoClient

import os
from dotenv import load_dotenv

import re
import concurrent.futures

# Carga las variables del archivo .env en el entorno de ejecución
load_dotenv()

# --- CONFIGURACIÓN ---
TMDB_API_KEY = os.getenv("passAPIMovieDB") 
MONGO_URI = "mongodb://localhost:27017"

# Conexión a MongoDB
client = MongoClient(MONGO_URI)
db = client["filmoteca_db"]
peliculas_col = db["peliculas"]

# Plataformas manuales/locales que NUNCA se borran ni modifican automáticamente
PLATAFORMAS_MANUALES = ["Piratería", "YouTube"]

# Mapeo de nombres oficiales de TMDB a vuestro formato habitual
MAPEO_PLATAFORMAS = {
    "Amazon Prime Video": "Prime Video",
    "Disney Plus": "Disney+",
    "Max": "HBO Max",
    "HBO Max": "HBO Max",
    "Movistar Plus+": "Movistar+",
    "Netflix": "Netflix",
    "Filmin": "Filmin",
    "Apple TV Plus": "Apple TV+"
}

session = requests.Session()

if TMDB_API_KEY and len(TMDB_API_KEY) > 50:
    session.headers.update({"Authorization": f"Bearer {TMDB_API_KEY}"})

def limpiar_titulo_y_extraer_ano(titulo):
    """
    Busca años en el título (ej. 1997, 2024), los extrae y limpia el texto
    de etiquetas basura como 'Remake' o 'Original'.
    """
    match_ano = re.search(r'\b(19\d{2}|20\d{2})\b', titulo)
    ano = match_ano.group(1) if match_ano else None

    titulo_limpio = re.sub(r'\b(19\d{2}|20\d{2})\b', '', titulo)
    titulo_limpio = re.sub(r'\(.*?\)', '', titulo_limpio)
    
    palabras_basura = r'(?i)\b(Remake|Original|Nueva|Animación|Live Action|Saga|Pelicula)\b'
    titulo_limpio = re.sub(palabras_basura, '', titulo_limpio)

    return titulo_limpio.strip(), ano

def buscar_datos_tmdb(titulo):
    if not TMDB_API_KEY:
        return None, None

    titulo_query, ano_query = limpiar_titulo_y_extraer_ano(titulo)
    url = "https://api.themoviedb.org/3/search/movie"
    
    params = {"query": titulo_query, "language": "es-ES"}
    
    if ano_query:
        params["primary_release_year"] = ano_query
        
    if "Authorization" not in session.headers:
        params["api_key"] = TMDB_API_KEY

    response = session.get(url, params=params)

    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            tmdb_id = results[0]["id"]
            fecha = results[0].get("release_date", "")
            ano_estreno = int(fecha[:4]) if fecha and len(fecha) >= 4 else None
            return tmdb_id, ano_estreno
            
    if titulo_query != titulo:
        params["query"] = titulo
        if "primary_release_year" in params:
            del params["primary_release_year"]
            
        res_retry = session.get(url, params=params)
        if res_retry.status_code == 200 and res_retry.json().get("results"):
            tmdb_id = res_retry.json()["results"][0]["id"]
            fecha = res_retry.json()["results"][0].get("release_date", "")
            ano_estreno = int(fecha[:4]) if fecha and len(fecha) >= 4 else None
            return tmdb_id, ano_estreno

    return None, None

def obtener_plataformas_suscripcion(tmdb_id):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
    params = {}
    if "Authorization" not in session.headers:
        params["api_key"] = TMDB_API_KEY
        
    response = session.get(url, params=params)
    
    if response.status_code != 200:
        return []

    data = response.json()
    es_data = data.get("results", {}).get("ES", {})
    flatrate_providers = es_data.get("flatrate", [])
    
    plataformas_detectadas = []
    for provider in flatrate_providers:
        nombre_oficial = provider.get("provider_name")
        nombre_limpio = MAPEO_PLATAFORMAS.get(nombre_oficial, nombre_oficial)
        plataformas_detectadas.append(nombre_limpio)
        
    return plataformas_detectadas

def procesar_pelicula(peli):
    titulo = peli.get("titulo")
    plataformas_actuales = peli.get("plataformas", [])
    plataformas_conservadas = [p for p in plataformas_actuales if p in PLATAFORMAS_MANUALES]

    tmdb_id, ano_estreno = buscar_datos_tmdb(titulo)
    
    sin_plataforma = False

    if tmdb_id:
        nuevas_plataformas_api = obtener_plataformas_suscripcion(tmdb_id)
        plataformas_finales = list(set(plataformas_conservadas + nuevas_plataformas_api))
        
        # <-- NUEVA LÓGICA: Si no hay plataformas oficiales ni manuales, añadir Piratería
        if not plataformas_finales:
            plataformas_finales = ["Piratería"]
            sin_plataforma = True

        datos_a_actualizar = {"plataformas": plataformas_finales}
        if ano_estreno:
            datos_a_actualizar["año"] = ano_estreno
        
        peliculas_col.update_one(
            {"_id": peli["_id"]},
            {"$set": datos_a_actualizar}
        )
        return {"estado": "ok", "titulo": titulo, "sin_plataforma": sin_plataforma}
    else:
        print(f"⚠️ No se encontró en TMDB: '{titulo}'")
        # Si no se encuentra en TMDB y tampoco tiene plataformas manuales, le añadimos Piratería
        if not plataformas_conservadas:
            peliculas_col.update_one(
                {"_id": peli["_id"]},
                {"$set": {"plataformas": ["Piratería"]}}
            )
            sin_plataforma = True

        return {"estado": "error", "titulo": titulo, "sin_plataforma": sin_plataforma}

def actualizar_catalogo():
    peliculas = list(peliculas_col.find({}))
    total_pelis = len(peliculas)
    print(f"🎬 Iniciando actualización acelerada para {total_pelis} películas...\n")

    actualizadas = 0
    titulos_no_encontrados = []
    titulos_sin_plataforma = []

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        resultados = executor.map(procesar_pelicula, peliculas)

        for resultado in resultados:
            if resultado["estado"] == "ok":
                actualizadas += 1
            else:
                titulos_no_encontrados.append(resultado["titulo"])
            
            # Recopilamos las que no tenían ninguna plataforma
            if resultado.get("sin_plataforma"):
                titulos_sin_plataforma.append(resultado["titulo"])

    tiempo_total = round(time.time() - start_time, 2)
    print(f"\n🎉 Proceso completado en {tiempo_total} segundos.")
    print(f"✅ {actualizadas} películas procesadas exitosamente.")
    print(f"🏴‍☠️ {len(titulos_sin_plataforma)} películas no tenían plataforma y se les asignó 'Piratería'.")

    # 1. Guardar lista de no encontradas en TMDB
    if titulos_no_encontrados:
        with open("peliculas_no_encontradas.txt", "w", encoding="utf-8") as file:
            file.write("PELÍCULAS NO ENCONTRADAS EN TMDB\n")
            file.write("-" * 60 + "\n")
            for t in titulos_no_encontrados:
                file.write(f"- {t}\n")

    # 2. Guardar lista de películas sin streaming/plataformas asignadas
    if titulos_sin_plataforma:
        with open("peliculas_sin_plataforma.txt", "w", encoding="utf-8") as file:
            file.write("PELÍCULAS SIN PLATAFORMA (SE LES AÑADIÓ PIRATERÍA)\n")
            file.write("-" * 60 + "\n")
            for t in titulos_sin_plataforma:
                file.write(f"- {t}\n")

if __name__ == "__main__":
    actualizar_catalogo()