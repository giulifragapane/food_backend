# app/modules/pedido/model.py
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship

from app.core.base import Base
from app.modules.pedido.enums import EstadoPedido, FormaPago


# ──────────────────────────────────────────────
# Modelo principal Pedido
# ──────────────────────────────────────────────
class Pedido(Base, table=True):
    __tablename__ = "pedidos"

    usuario_id: int = Field(foreign_key="usuarios.id", nullable=False)
    direccion_entrega_id: int | None = Field(default=None, foreign_key="direcciones_entrega.id")

    estado: EstadoPedido = Field(default=EstadoPedido.PENDIENTE, nullable=False)
    forma_pago: FormaPago = Field(nullable=False)

    total: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        sa_column=Column(Numeric(10, 2), nullable=False),
    )

    detalles: list["DetallePedido"] = Relationship(
        back_populates="pedido",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# ──────────────────────────────────────────────
# Detalle de pedido con Snapshot Pattern
# ──────────────────────────────────────────────
class DetallePedido(Base, table=True):
    __tablename__ = "detalle_pedidos"

    pedido_id: int | None = Field(default=None, foreign_key="pedidos.id")
    producto_id: int = Field(foreign_key="productos.id", nullable=False)

    cantidad: int = Field(gt=0, nullable=False)

    # Snapshot del producto al momento de crear el pedido.
    producto_nombre: str = Field(max_length=150, nullable=False)
    precio_unitario: Decimal = Field(
        ge=0,
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    subtotal: Decimal = Field(
        ge=0,
        sa_column=Column(Numeric(10, 2), nullable=False),
    )

    pedido: Optional["Pedido"] = Relationship(back_populates="detalles")