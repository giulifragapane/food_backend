# app/modules/producto/schema.py
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.categoria.schema import CategoriaRead
from app.modules.ingrediente.schema import IngredienteRead

class ProductoBase(BaseModel):
    nombre: str = Field(..., max_length=150)
    descripcion: str
    precio_base: Decimal = Field(..., ge=0)
    imagenes_url: List[str] = Field(default_factory=list)
    stock_cantidad: int = Field(default=0, ge=0)
    disponible: bool = True

    @field_validator("precio_base")
    @classmethod
    def redondear_precio(cls, v: Decimal) -> Decimal:
        return round(v, 2)


class ProductoCategoriaCreate(BaseModel):
    categoria_id: int
    es_principal: bool = False


class ProductoIngredienteCreate(BaseModel):
    ingrediente_id: int
    es_removible: bool = False


class ProductoCreate(ProductoBase):
    categorias: List[ProductoCategoriaCreate] = Field(default_factory=list)
    ingredientes: List[ProductoIngredienteCreate] = Field(default_factory=list)


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=150)
    descripcion: Optional[str] = None
    precio_base: Optional[Decimal] = Field(None, ge=0)
    imagenes_url: Optional[List[str]] = None
    stock_cantidad: Optional[int] = Field(None, ge=0)
    disponible: Optional[bool] = None
    categorias: Optional[List[ProductoCategoriaCreate]] = None
    ingredientes: Optional[List[ProductoIngredienteCreate]] = None


class ProductoDisponibilidadUpdate(BaseModel):
    stock_cantidad: Optional[int] = Field(None, ge=0)
    disponible: Optional[bool] = None


class ProductoCategoriaRead(BaseModel):
    categoria: CategoriaRead
    es_principal: bool
    model_config = ConfigDict(from_attributes=True)


class ProductoIngredienteRead(BaseModel):
    ingrediente: IngredienteRead
    es_removible: bool
    model_config = ConfigDict(from_attributes=True)


class ProductoRead(ProductoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categorias: List[ProductoCategoriaRead] = Field(default_factory=list)
    ingredientes: List[ProductoIngredienteRead] = Field(default_factory=list)


class ProductoList(BaseModel):
    data: List[ProductoRead]
    total: int