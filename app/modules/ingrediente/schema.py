# app/modules/ingrediente/schema.py
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

# ── Base schema para el ingrediente, con campos comunes a creación y actualización
class IngredienteBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: str
    es_alergeno: bool = False

# ── Entrada ───────────────────────────────────────────────────────────────────
class IngredienteCreate(IngredienteBase):
    pass


class IngredienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    es_alergeno: Optional[bool] = None

# ── Salida ───────────────────────────────────────────────────────────────────
class IngredienteRead(IngredienteBase): #Recibe model
    model_config = ConfigDict(from_attributes=True)
    id: int

class IngredienteList(BaseModel):
    data: List[IngredienteRead]
    total: int