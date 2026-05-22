# app/modules/pedido/schema.py
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.pedido.enums import EstadoPedido, FormaPago


# ── Entrada ───────────────────────────────────────────────────────────────────
class DetallePedidoCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)


class PedidoCreate(BaseModel):
    direccion_entrega_id: Optional[int] = None
    forma_pago: FormaPago
    detalles: List[DetallePedidoCreate] = Field(..., min_length=1)


class PedidoEstadoUpdate(BaseModel):
    estado: EstadoPedido


# ── Salida ───────────────────────────────────────────────────────────────────
class DetallePedidoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    cantidad: int
    producto_nombre: str
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    direccion_entrega_id: Optional[int]
    estado: EstadoPedido
    forma_pago: FormaPago
    total: Decimal
    detalles: List[DetallePedidoRead] = Field(default_factory=list)


class PedidoList(BaseModel):
    data: List[PedidoRead]
    total: int