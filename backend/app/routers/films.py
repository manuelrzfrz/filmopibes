"""
==============================================================================
ARCHIVO: app/routers/films.py
PROPÓSITO: Endpoints REST para la gestión de películas.
DESCRIPCIÓN: Define las rutas HTTP para consultar (con filtros por género o
            búsqueda por nombre), crear, modificar campos específicos y
            eliminar películas en la base de datos de MongoDB.
==============================================================================
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from app.database import get_db
from app.models import PeliculaGridItem

router = APIRouter(prefix="/api/films", tags=["Films"])

@router.get("/grid", response_model=List[PeliculaGridItem])
async def obtener_peliculas_grid(
    buscar: Optional[str] = Query(None, description="Búsqueda por título o director"),
    genero: Optional[str] = Query(None),
    saga: Optional[str] = Query(None),
    plataforma: Optional[str] = Query(None),
    db = Depends(get_db)
):
    """
    Devuelve la lista completa de películas con las valoraciones unificadas de todos los usuarios
    para renderizar en formato tabla / Excel.
    """
    pipeline = []

    match_stage = {}
    if buscar:
        match_stage["$or"] = [
            {"titulo": {"$regex": buscar, "$options": "i"}},
            {"titulo_original": {"$regex": buscar, "$options": "i"}},
            {"directores": {"$regex": buscar, "$options": "i"}}
        ]
    if genero:
        match_stage["generos"] = genero
    if saga:
        match_stage["saga"] = saga
    if plataforma:
        match_stage["plataformas"] = plataforma

    if match_stage:
        pipeline.append({"$match": match_stage})

    # Unir con la colección 'valoraciones'
    pipeline.extend([
        {
            "$lookup": {
                "from": "valoraciones",
                "localField": "_id",
                "foreignField": "pelicula_id",
                "as": "lista_valoraciones"
            }
        },
        {
            "$sort": {"titulo": 1}
        }
    ])

    cursor = db["peliculas"].aggregate(pipeline)
    resultado = []

    async for peli in cursor:
        peli["_id"] = str(peli["_id"])
        
        # Formatear lista_valoraciones en un diccionario {usuario_id_str: {...}}
        valoraciones_map = {}
        for val in peli.get("lista_valoraciones", []):
            u_id = str(val["usuario_id"])
            valoraciones_map[u_id] = {
                "nota": val.get("nota"),
                "rewatch": val.get("rewatch", False),
                "vista": val.get("vista", False),
                "enterado_novedad": val.get("enterado_novedad", False),
                "quiero_ver": val.get("quiero_ver", False)
            }
            
        peli["valoraciones"] = valoraciones_map
        peli.pop("lista_valoraciones", None)
        resultado.append(peli)

    return resultado


@router.get("/filtros")
async def obtener_filtros_disponibles(db = Depends(get_db)):
    """Obtiene valores únicos para rellenar los desplegables de filtro en la tabla."""
    generos = await db["peliculas"].distinct("generos")
    sagas = await db["peliculas"].distinct("saga")
    plataformas = await db["peliculas"].distinct("plataformas")
    directores = await db["peliculas"].distinct("directores")
    estudios = await db["peliculas"].distinct("estudio")

    return {
        "generos": sorted([g for g in generos if g]),
        "sagas": sorted([s for s in sagas if s]),
        "plataformas": sorted([p for p in plataformas if p]),
        "directores": sorted([d for d in directores if d]),
        "estudios": sorted([e for e in estudios if e])
    }