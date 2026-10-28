from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from app.database import get_db
from app.models import ValoracionUpsertRequest

router = APIRouter(prefix="/api/ratings", tags=["Ratings"])

@router.post("")
async def guardar_o_actualizar_valoracion(payload: ValoracionUpsertRequest, db = Depends(get_db)):
    """
    Crea o actualiza parcialmente la valoración de una película para un usuario específico.
    """
    try:
        user_oid = ObjectId(payload.usuario_id)
        peli_oid = ObjectId(payload.pelicula_id)
    except Exception:
        raise HTTPException(status_code=400, detail="IDs de MongoDB con formato inválido")

    filtro = {"usuario_id": user_oid, "pelicula_id": peli_oid}
    
    # Construir mapa de campos recibidos
    update_data = {}
    if payload.nota is not None:
        update_data["nota"] = payload.nota
    if payload.rewatch is not None:
        update_data["rewatch"] = payload.rewatch
    if payload.vista is not None:
        update_data["vista"] = payload.vista
    if payload.enterado_novedad is not None:
        update_data["enterado_novedad"] = payload.enterado_novedad
    if payload.quiero_ver is not None:
        update_data["quiero_ver"] = payload.quiero_ver

    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    # Realizar Upsert
    await db["valoraciones"].update_one(
        filtro,
        {"$set": update_data},
        upsert=True
    )

    # Recuperar el estado final del documento
    val_actualizada = await db["valoraciones"].find_one(filtro)
    val_actualizada["_id"] = str(val_actualizada["_id"])
    val_actualizada["usuario_id"] = str(val_actualizada["usuario_id"])
    val_actualizada["pelicula_id"] = str(val_actualizada["pelicula_id"])

    return {
        "status": "ok",
        "mensaje": "Valoración actualizada correctamente",
        "data": val_actualizada
    }