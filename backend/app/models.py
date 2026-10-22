from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime

# --- MODELOS DE USUARIO ---
class UsuarioResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id")
    username: str
    role: str = "user"
    fecha_registro: Optional[datetime] = None

class LoginRequest(BaseModel):
    username: str

# --- MODELOS DE VALORACIÓN ---
class ValoracionData(BaseModel):
    nota: Optional[float] = Field(None, ge=0, le=10)
    rewatch: bool = False
    vista: bool = False
    enterado_novedad: bool = False
    quiero_ver: bool = False

class ValoracionUpsertRequest(BaseModel):
    pelicula_id: str
    usuario_id: str
    nota: Optional[float] = Field(None, ge=0, le=10)
    rewatch: Optional[bool] = None
    vista: Optional[bool] = None
    enterado_novedad: Optional[bool] = None
    quiero_ver: Optional[bool] = None

# --- MODELO PELÍCULA GRID ---
class PeliculaGridItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    titulo: str
    titulo_original: Optional[str] = None
    descripcion: Optional[str] = None
    año: Optional[int] = Field(None, alias="año")
    cartel: Optional[str] = None
    generos: List[str] = []
    directores: List[str] = []
    estudio: Optional[str] = None
    premios: List[str] = []
    saga: Optional[str] = None
    orden_saga: Optional[int] = None
    plataformas: List[str] = []
    
    # Mapa de valoraciones por usuario_id:
    # {"6ac59d1dcf8fefc204e1de50": {"nota": 8.5, "vista": true, ...}}
    valoraciones: Dict[str, ValoracionData] = {}