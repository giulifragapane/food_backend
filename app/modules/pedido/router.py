# app/modules/pedido/router.py
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import get_current_active_user, require_role
from app.modules.pedido.schema import PedidoCreate, PedidoEstadoUpdate, PedidoList, PedidoRead
from app.modules.pedido.service import PedidoService
from app.modules.usuario.enums import RolCodigo
from app.modules.usuario.schema import UsuarioRead

router = APIRouter(prefix="/api/v1/pedidos", tags=["pedidos"])


def get_pedido_service(session: Session = Depends(get_session)) -> PedidoService:
    return PedidoService(session)


def usuario_tiene_rol(usuario: UsuarioRead, roles_permitidos: list[RolCodigo]) -> bool:
    """
    Helper defensivo para saber si el usuario autenticado tiene alguno de los roles indicados.
    Se usa para decidir si lista todos los pedidos o solo los propios.
    """
    roles_usuario = getattr(usuario, "roles", []) or []
    valores_permitidos = [rol.value for rol in roles_permitidos]

    for rol in roles_usuario:
        if isinstance(rol, str) and rol in valores_permitidos:
            return True

        rol_codigo = getattr(rol, "rol_codigo", None)
        if rol_codigo is not None:
            rol_valor = getattr(rol_codigo, "value", rol_codigo)
            if rol_valor in valores_permitidos:
                return True

        codigo = getattr(rol, "codigo", None)
        if codigo is not None:
            codigo_valor = getattr(codigo, "value", codigo)
            if codigo_valor in valores_permitidos:
                return True

    return False


# ── Crear pedido ─────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un pedido desde el carrito",
)
def create_pedido(
    data: PedidoCreate,
    current_user: Annotated[UsuarioRead, Depends(get_current_active_user)],
    svc: PedidoService = Depends(get_pedido_service),
) -> PedidoRead:
    return svc.create(current_user.id, data)


# ── Listar pedidos ───────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=PedidoList,
    status_code=status.HTTP_200_OK,
    summary="Listar pedidos",
)
def list_pedidos(
    current_user: Annotated[UsuarioRead, Depends(get_current_active_user)],
    offset: Annotated[int, Query(ge=0, description="Cantidad de registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima de registros")] = 20,
    svc: PedidoService = Depends(get_pedido_service),
) -> PedidoList:
    es_staff_pedidos = usuario_tiene_rol(current_user, [RolCodigo.ADMIN, RolCodigo.PEDIDOS])
    return svc.get_all_for_user(
        usuario_id=current_user.id,
        es_staff_pedidos=es_staff_pedidos,
        offset=offset,
        limit=limit,
    )


# ── Obtener pedido por ID ─────────────────────────────────────────────────────
@router.get(
    "/{pedido_id}",
    response_model=PedidoRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener pedido por ID",
)
def get_pedido(
    pedido_id: int,
    current_user: Annotated[UsuarioRead, Depends(get_current_active_user)],
    svc: PedidoService = Depends(get_pedido_service),
) -> PedidoRead:
    es_staff_pedidos = usuario_tiene_rol(current_user, [RolCodigo.ADMIN, RolCodigo.PEDIDOS])
    return svc.get_by_id_for_user(
        pedido_id=pedido_id,
        usuario_id=current_user.id,
        es_staff_pedidos=es_staff_pedidos,
    )


# ── Cambiar estado de pedido ─────────────────────────────────────────────────
@router.patch(
    "/{pedido_id}/estado",
    response_model=PedidoRead,
    status_code=status.HTTP_200_OK,
    summary="Cambiar estado de pedido",
)
def update_estado_pedido(
    pedido_id: int,
    data: PedidoEstadoUpdate,
    _staff: Annotated[UsuarioRead, Depends(require_role([RolCodigo.ADMIN, RolCodigo.PEDIDOS]))],
    svc: PedidoService = Depends(get_pedido_service),
) -> PedidoRead:
    return svc.update_estado(pedido_id, data)


# ── Cancelar pedido propio ───────────────────────────────────────────────────
@router.patch(
    "/{pedido_id}/cancelar",
    response_model=PedidoRead,
    status_code=status.HTTP_200_OK,
    summary="Cancelar pedido propio",
)
def cancelar_mi_pedido(
    pedido_id: int,
    current_user: Annotated[UsuarioRead, Depends(get_current_active_user)],
    svc: PedidoService = Depends(get_pedido_service),
) -> PedidoRead:
    return svc.cancelar_mi_pedido(pedido_id, current_user.id)