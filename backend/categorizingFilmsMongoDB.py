import os
import re
import time
import threading
import unicodedata
import concurrent.futures
from difflib import SequenceMatcher
import requests
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE CONEXIÓN ---
TMDB_API_KEY = os.getenv("passAPIMovieDB")
OMDB_API_KEY = os.getenv("passAPIOMDB") or os.getenv("OMDB_API_KEY")
MONGO_URI = "mongodb://localhost:27017"

client = MongoClient(MONGO_URI)
db = client["filmoteca_db"]
peliculas_col = db["peliculas"]

session = requests.Session()
if TMDB_API_KEY and len(TMDB_API_KEY) > 50:
    session.headers.update({"Authorization": f"Bearer {TMDB_API_KEY}"})

# Lista de estudios relevantes a preservar
ESTUDIOS_RELEVANTES = [
    "Studio Ghibli", "A24", "Pixar", "Marvel Studios",
    "Blumhouse", "Toei Animation", "Kyoto Animation",
    "Madhouse", "MAPPA", "DreamWorks", "Laika", "Bad Robot"
]
ESTUDIOS_PREPROCESADOS = [(est, est.lower()) for est in ESTUDIOS_RELEVANTES]

# Precompilación de expresiones regulares
RE_UNICODE_CLEAN = re.compile(r'[^a-z0-9\s]')
RE_TRAILING_ONE = re.compile(r'\s+1$')
RE_MULTIPLE_SPACES = re.compile(r'\s+')
RE_MODIFICADORES = re.compile(r'(?i)\b(original|animacion|animada|clasico|clasica|live action|remake|reboot|nueva)\b')

# Control de caché e hilos
cache_colecciones = {}
lock_cache = threading.Lock()

# Control de estado de OMDb API
omdb_limite_alcanzado = False
omdb_aviso_mostrado = False
lock_omdb = threading.Lock()

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()
    texto = RE_UNICODE_CLEAN.sub('', texto)
    texto = RE_TRAILING_ONE.sub('', texto)
    return RE_MULTIPLE_SPACES.sub(' ', texto).strip()

def extraer_modificadores_y_limpiar(texto):
    texto_lower = texto.lower()
    es_original = bool(re.search(r'\b(original|animacion|animada|clasico|clasica)\b', texto_lower))
    es_remake = bool(re.search(r'\b(live action|remake|reboot|nueva)\b', texto_lower))
    titulo_limpio = RE_MODIFICADORES.sub('', texto)
    return titulo_limpio, es_original, es_remake

def calcular_puntuacion_candidato(titulo_bd, ano_bd, candidato_tmdb):
    puntuacion = 0
    titulo_limpio, es_original, es_remake = extraer_modificadores_y_limpiar(titulo_bd)

    t_bd = normalizar_texto(titulo_limpio)
    t_tmdb = normalizar_texto(candidato_tmdb.get("title"))
    t_orig_tmdb = normalizar_texto(candidato_tmdb.get("original_title"))

    if t_bd == t_tmdb or t_bd == t_orig_tmdb:
        puntuacion += 80
    else:
        similitud = max(
            SequenceMatcher(None, t_bd, t_tmdb).ratio(),
            SequenceMatcher(None, t_bd, t_orig_tmdb).ratio()
        )
        puntuacion += similitud * 50

    release_date = candidato_tmdb.get("release_date", "")
    ano_tmdb = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

    # Ajuste por intención (Original vs. Remake)
    if ano_tmdb:
        if es_original:
            if ano_tmdb < 2010 or 16 in candidato_tmdb.get("genre_ids", []):
                puntuacion += 30
            else:
                puntuacion -= 30
        elif es_remake:
            if ano_tmdb >= 2010:
                puntuacion += 30
            else:
                puntuacion -= 30

    if ano_bd and ano_tmdb:
        diff = abs(int(ano_bd) - ano_tmdb)
        if diff == 0:
            puntuacion += 20
        elif diff <= 2:
            puntuacion += 10

    return puntuacion

def buscar_mejor_tmdb_match(titulo_bd, ano_bd=None):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"query": titulo_bd, "language": "es-ES"}
    if "Authorization" not in session.headers:
        params["api_key"] = TMDB_API_KEY

    res = session.get(url, params=params)
    if res.status_code != 200 or not res.json().get("results"):
        params.pop("language", None)
        res = session.get(url, params=params)
        if res.status_code != 200 or not res.json().get("results"):
            return None

    resultados = res.json()["results"][:10]
    mejor_candidato = None
    mejor_puntuacion = -1

    for candidato in resultados:
        score = calcular_puntuacion_candidato(titulo_bd, ano_bd, candidato)
        if score > mejor_puntuacion:
            mejor_puntuacion = score
            mejor_candidato = candidato

    if mejor_candidato and mejor_puntuacion >= 40:
        return mejor_candidato.get("id")

    return None

def obtener_orden_en_coleccion(collection_id, tmdb_id):
    with lock_cache:
        parts = cache_colecciones.get(collection_id)

    if parts is None:
        url = f"https://api.themoviedb.org/3/collection/{collection_id}"
        params = {"language": "es-ES"}
        if "Authorization" not in session.headers:
            params["api_key"] = TMDB_API_KEY
        
        res = session.get(url, params=params)
        if res.status_code == 200:
            parts = res.json().get("parts", [])
            parts = sorted(parts, key=lambda x: x.get("release_date") or "9999-12-31")
            with lock_cache:
                cache_colecciones[collection_id] = parts
        else:
            return None

    for index, part in enumerate(parts):
        if part.get("id") == tmdb_id:
            return index + 1
    return None

def extraer_premios(imdb_id, kw_text):
    """
    Intenta consultar los premios en OMDb API.
    Si se alcanza el límite diario (1.000 req) o falla, conmuta al fallback por Keywords de TMDB.
    """
    global omdb_limite_alcanzado, omdb_aviso_mostrado
    premios = set()

    # 1. Intentar OMDb si la API Key está presente y no hemos alcanzado el límite
    if OMDB_API_KEY and imdb_id and not omdb_limite_alcanzado:
        url_omdb = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
        try:
            res_omdb = session.get(url_omdb, timeout=5)
            if res_omdb.status_code == 200:
                data_omdb = res_omdb.json()
                
                # Comprobar si OMDb notifica límite de cuota
                if data_omdb.get("Response") == "False":
                    error_msg = data_omdb.get("Error", "").lower()
                    if "limit" in error_msg or "key" in error_msg:
                        with lock_omdb:
                            omdb_limite_alcanzado = True
                            if not omdb_aviso_mostrado:
                                print("\n⚠️  [ALERTA OMDB]: Se ha alcanzado el límite diario de la API de OMDb.")
                                print("🔄 Cambiando automáticamente al sistema de fallback con palabras clave de TMDB...\n")
                                omdb_aviso_mostrado = True
                else:
                    awards_str = data_omdb.get("Awards", "").lower()
                    if "oscar" in awards_str or "academy award" in awards_str:
                        premios.add("Óscar")
                    if "palme d'or" in awards_str or "cannes" in awards_str:
                        premios.add("Palma de Oro (Cannes)")
                    if "golden lion" in awards_str or "venice" in awards_str:
                        premios.add("Festival de Venecia")
                    if "golden bear" in awards_str or "berlin" in awards_str:
                        premios.add("Festival de Berlín")
                    if "golden globe" in awards_str:
                        premios.add("Globo de Oro")
                    if "bafta" in awards_str:
                        premios.add("BAFTA")
                    if "goya" in awards_str:
                        premios.add("Goya")
            elif res_omdb.status_code in (401, 402, 429):
                with lock_omdb:
                    omdb_limite_alcanzado = True
                    if not omdb_aviso_mostrado:
                        print("\n⚠️  [ALERTA OMDB]: Límite de peticiones alcanzado o API Key inválida (HTTP Status).")
                        print("🔄 Conmutando a fallback de TMDB...\n")
                        omdb_aviso_mostrado = True
        except Exception:
            pass

    # 2. Complemento / Fallback usando Keywords de TMDB
    if any(w in kw_text for w in ["oscar", "academy award"]):
        premios.add("Óscar")
    if any(w in kw_text for w in ["cannes", "palme d'or", "palma de oro"]):
        premios.add("Palma de Oro (Cannes)")
    if any(w in kw_text for w in ["venice", "venecia", "golden lion", "leon de oro"]):
        premios.add("Festival de Venecia")
    if any(w in kw_text for w in ["berlin", "berlinale", "golden bear", "oso de oro"]):
        premios.add("Festival de Berlín")
    if "sitges" in kw_text:
        premios.add("Festival de Sitges")
    if "goya" in kw_text:
        premios.add("Goya")
    if any(w in kw_text for w in ["san sebastian", "san sebastián", "concha de oro"]):
        premios.add("Festival de San Sebastián")

    return sorted(list(premios))

def obtener_metadatos_completos(tmdb_id):
    params = {
        "language": "es-ES",
        "append_to_response": "credits,keywords,external_ids"
    }
    if "Authorization" not in session.headers:
        params["api_key"] = TMDB_API_KEY

    res_peli = session.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}", params=params)
    if res_peli.status_code != 200:
        return None

    data_peli = res_peli.json()
    
    # 1. Datos básicos
    titulo_oficial = data_peli.get("title")
    titulo_original = data_peli.get("original_title")
    sinopsis = data_peli.get("overview")
    poster_path = data_peli.get("poster_path")
    cartel_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    
    release_date = data_peli.get("release_date", "")
    ano_oficial = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
    generos = [g["name"] for g in data_peli.get("genres", [])]

    # 2. Directores
    crew = data_peli.get("credits", {}).get("crew", [])
    directores = [p["name"] for p in crew if p.get("job") == "Director"]

    # 3. Estudio
    estudio_encontrado = None
    for comp in data_peli.get("production_companies", []):
        n_comp_lower = comp.get("name", "").lower()
        for est_orig, est_lower in ESTUDIOS_PREPROCESADOS:
            if est_lower in n_comp_lower:
                estudio_encontrado = est_orig
                break
        if estudio_encontrado:
            break

    # 4. Procesar Keywords de TMDB e ID de IMDb
    kw_obj = data_peli.get("keywords") or {}
    kw_raw = kw_obj.get("keywords") or kw_obj.get("results") or []
    kw_list = [k.get("name", "").lower() for k in kw_raw if isinstance(k, dict)]
    kw_text = " ".join(kw_list)

    imdb_id = data_peli.get("external_ids", {}).get("imdb_id")
    premios = extraer_premios(imdb_id, kw_text)

    # 5. Saga
    saga = None
    orden_saga = None
    coleccion = data_peli.get("belongs_to_collection")
    if coleccion:
        saga = coleccion.get("name", "").replace(" - Colección", "").replace(" Collection", "").strip()
        orden_saga = obtener_orden_en_coleccion(coleccion.get("id"), tmdb_id)

    return {
        "titulo_oficial": titulo_oficial,
        "titulo_original": titulo_original,
        "descripcion": sinopsis,
        "cartel": cartel_url,
        "año": ano_oficial,
        "generos": generos,
        "directores": directores,
        "estudio": estudio_encontrado,
        "premios": premios,
        "saga": saga,
        "orden_saga": orden_saga
    }

def procesar_pelicula(peli):
    peli_id = peli["_id"]
    titulo_bd = peli.get("titulo")
    ano_bd = peli.get("año") or peli.get("anio")
    tmdb_id = peli.get("tmdb_id")

    if not tmdb_id:
        tmdb_id = buscar_mejor_tmdb_match(titulo_bd, ano_bd)

    if not tmdb_id:
        return None, f"⚠️  No se encontró en TMDB: '{titulo_bd}'"

    meta = obtener_metadatos_completos(tmdb_id)
    if not meta:
        return None, f"❌ Error al obtener metadatos: '{titulo_bd}'"

    update_set = {
        "tmdb_id": int(tmdb_id),
        "titulo_original": meta["titulo_original"],
        "cartel": meta["cartel"] or peli.get("cartel"),
        "generos": meta["generos"],
        "directores": meta["directores"],
        "premios": meta["premios"]
    }

    if meta["año"]:
        update_set["año"] = meta["año"]
    if meta["estudio"]:
        update_set["estudio"] = meta["estudio"]
    if meta["saga"]:
        update_set["saga"] = meta["saga"]
        if meta["orden_saga"]:
            update_set["orden_saga"] = meta["orden_saga"]

    update_unset = {"anio": ""} if "anio" in peli else {}

    update_query = {"$set": update_set}
    if update_unset:
        update_query["$unset"] = update_unset

    op = UpdateOne({"_id": peli_id}, update_query)
    msg = f"✅ {titulo_bd} -> [{meta['titulo_oficial']}] | Director: {meta['directores']} | Premios: {meta['premios']} | Saga: {meta['saga']}"
    return op, msg

def migrar_base_de_datos():
    peliculas = list(peliculas_col.find({}))
    total = len(peliculas)
    print(f"🚀 Iniciando migración optimizada de {total} películas (15 hilos en paralelo)...\n")

    start_time = time.time()
    operaciones = []
    procesadas = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        resultados = executor.map(procesar_pelicula, peliculas)

        for op, msg in resultados:
            if op:
                operaciones.append(op)
                procesadas += 1
            if msg:
                print(msg)

    if operaciones:
        print(f"\n💾 Guardando {len(operaciones)} actualizaciones en MongoDB mediante Bulk Write...")
        peliculas_col.bulk_write(operaciones, ordered=False)

    tiempo_total = round(time.time() - start_time, 2)
    print(f"\n🎉 ¡Migración completada en {tiempo_total}s! Se actualizaron {procesadas}/{total} películas.")

if __name__ == "__main__":
    migrar_base_de_datos()