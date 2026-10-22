from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.models import UsuarioResponse, LoginRequest

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios & Autenticación"])

@router.get("", response_model=list[UsuarioResponse])
async def obtener_usuarios(db = Depends(get_db)):
    """Obtiene la lista de los 2 usuarios para permitir la selección de usuario en el frontend."""
    usuarios_cursor = db["usuarios"].find({})
    usuarios = []
    async for u in usuarios_cursor:
        u["_id"] = str(u["_id"])
        usuarios.append(u)
    return usuarios

@router.post("/login", response_model=UsuarioResponse)
async def login_usuario(payload: LoginRequest, db = Depends(get_db)):
    """Inicia sesión / selecciona usuario activo por nombre de usuario."""
    usuario = await db["usuarios"].find_one({"username": payload.username})
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario '{payload.username}' no encontrado")
    usuario["_id"] = str(usuario["_id"])
    return usuario