# app/modules/pedido/service.py
from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session

from app.modules.pedido.enums import EstadoPedido
from app.modules.pedido.model import DetallePedido, Pedido
from app.modules.pedido.schema import PedidoCreate, PedidoEstadoUpdate, PedidoList, PedidoRead
from app.modules.pedido.unit_of_work import PedidoUnitOfWork


class PedidoService:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Helpers privados ──────────────────────────────────────────────────────
    def _get_or_404(self, uow: PedidoUnitOfWork, pedido_id: int) -> Pedido:
        pedido = uow.pedidos.get_active_by_id(pedido_id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado.",
            )
        return pedido

    def _get_my_or_404(self, uow: PedidoUnitOfWork, pedido_id: int, usuario_id: int) -> Pedido:
        pedido = uow.pedidos.get_active_by_id_and_usuario(pedido_id, usuario_id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado.",
            )
        return pedido

    def _validar_transicion_estado(self, estado_actual: EstadoPedido, estado_nuevo: EstadoPedido) -> None:
        transiciones_validas = {
            EstadoPedido.PENDIENTE: [EstadoPedido.CONFIRMADO, EstadoPedido.CANCELADO],
            EstadoPedido.CONFIRMADO: [EstadoPedido.EN_PREP, EstadoPedido.CANCELADO],
            EstadoPedido.EN_PREP: [EstadoPedido.EN_CAMINO],
            EstadoPedido.EN_CAMINO: [EstadoPedido.ENTREGADO],
            EstadoPedido.ENTREGADO: [],
            EstadoPedido.CANCELADO: [],
        }

        if estado_nuevo not in transiciones_validas[estado_actual]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede cambiar el estado de {estado_actual.value} a {estado_nuevo.value}.",
            )

    def _devolver_stock_del_pedido(self, uow: PedidoUnitOfWork, pedido: Pedido) -> None:
        """
        Devuelve al stock las cantidades reservadas/descontadas al crear el pedido.
        Se usa cuando un pedido pasa a CANCELADO desde PENDIENTE o CONFIRMADO.
        """
        for detalle in pedido.detalles:
            producto = uow.productos.get_by_id(detalle.producto_id)

            if producto and producto.deleted_at is None:
                producto.stock_cantidad += detalle.cantidad

                # Si vuelve a tener stock, lo dejamos disponible.
                if producto.stock_cantidad > 0:
                    producto.disponible = True

                producto.updated_at = uow.now
                uow.productos.add(producto)

    # ── Casos de uso ─────────────────────────────────────────────────────────
    def create(self, usuario_id: int, data: PedidoCreate) -> PedidoRead:
        with PedidoUnitOfWork(self._session) as uow:
            if data.direccion_entrega_id is not None:
                direccion = uow.direcciones.get_active_by_id_and_usuario(
                    data.direccion_entrega_id,
                    usuario_id,
                )
                if not direccion:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="La dirección de entrega no existe o no pertenece al usuario.",
                    )

            pedido = Pedido(
                usuario_id=usuario_id,
                direccion_entrega_id=data.direccion_entrega_id,
                forma_pago=data.forma_pago,
                estado=EstadoPedido.PENDIENTE,
                total=Decimal("0.00"),
            )

            uow.pedidos.add(pedido)

            total = Decimal("0.00")

            for item in data.detalles:
                producto = uow.productos.get_by_id(item.producto_id)

                if not producto or producto.deleted_at is not None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Producto con id={item.producto_id} no encontrado.",
                    )

                if not producto.disponible:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El producto '{producto.nombre}' no está disponible.",
                    )

                if producto.stock_cantidad < item.cantidad:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Stock insuficiente para '{producto.nombre}'. Stock actual: {producto.stock_cantidad}.",
                    )

                precio_unitario = producto.precio_base
                subtotal = precio_unitario * item.cantidad
                total += subtotal

                detalle = DetallePedido(
                    pedido=pedido,
                    producto_id=producto.id,
                    cantidad=item.cantidad,
                    producto_nombre=producto.nombre,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                )

                pedido.detalles.append(detalle)

                # Descontamos stock dentro de la misma transacción.
                producto.stock_cantidad -= item.cantidad
                if producto.stock_cantidad == 0:
                    producto.disponible = False

                producto.updated_at = uow.now
                uow.productos.add(producto)

            pedido.total = total
            pedido.updated_at = uow.now
            uow.pedidos.add(pedido)

            result = PedidoRead.model_validate(pedido)

        return result

    def get_all_for_user(self, usuario_id: int, es_staff_pedidos: bool, offset: int = 0, limit: int = 20) -> PedidoList:
        with PedidoUnitOfWork(self._session) as uow:
            if es_staff_pedidos:
                pedidos = uow.pedidos.get_active_all(offset, limit)
                total = uow.pedidos.count_active_all()
            else:
                pedidos = uow.pedidos.get_active_by_usuario(usuario_id, offset, limit)
                total = uow.pedidos.count_active_by_usuario(usuario_id)

            result = PedidoList(
                data=[PedidoRead.model_validate(pedido) for pedido in pedidos],
                total=total,
            )

        return result

    def get_by_id_for_user(self, pedido_id: int, usuario_id: int, es_staff_pedidos: bool) -> PedidoRead:
        with PedidoUnitOfWork(self._session) as uow:
            if es_staff_pedidos:
                pedido = self._get_or_404(uow, pedido_id)
            else:
                pedido = self._get_my_or_404(uow, pedido_id, usuario_id)

            result = PedidoRead.model_validate(pedido)

        return result

    def update_estado(self, pedido_id: int, data: PedidoEstadoUpdate) -> PedidoRead:
        with PedidoUnitOfWork(self._session) as uow:
            pedido = self._get_or_404(uow, pedido_id)

            self._validar_transicion_estado(pedido.estado, data.estado)

            if data.estado == EstadoPedido.CANCELADO:
                self._devolver_stock_del_pedido(uow, pedido)

            pedido.estado = data.estado
            pedido.updated_at = uow.now
            uow.pedidos.add(pedido)

            result = PedidoRead.model_validate(pedido)

        return result

    def cancelar_mi_pedido(self, pedido_id: int, usuario_id: int) -> PedidoRead:
        with PedidoUnitOfWork(self._session) as uow:
            pedido = self._get_my_or_404(uow, pedido_id, usuario_id)

            if pedido.estado not in [EstadoPedido.PENDIENTE, EstadoPedido.CONFIRMADO]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Solo se pueden cancelar pedidos en estado PENDIENTE o CONFIRMADO.",
                )

            self._devolver_stock_del_pedido(uow, pedido)

            pedido.estado = EstadoPedido.CANCELADO
            pedido.updated_at = uow.now
            uow.pedidos.add(pedido)

            result = PedidoRead.model_validate(pedido)

        return result