# app/modules/usuario/router.py
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.enums import RolCodigo
from app.modules.usuario.model import Usuario
from app.modules.usuario.schema import Token, UsuarioCreate, UsuarioRead
from app.modules.usuario.service import UsuarioService
from app.modules.usuario.unit_of_work import UsuarioUnitOfWork

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_usuario_uow(
    session: Annotated[Session, Depends(get_session)],
) -> UsuarioUnitOfWork:
    return UsuarioUnitOfWork(session)


@router.post(
    "/register",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_in: UsuarioCreate,
    uow: Annotated[UsuarioUnitOfWork, Depends(get_usuario_uow)],
):
    with uow:
        service = UsuarioService(uow)
        return service.register(user_in)


@router.post("/token", response_model=Token)
def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    uow: Annotated[UsuarioUnitOfWork, Depends(get_usuario_uow)],
):
    with uow:
        service = UsuarioService(uow)
        token = service.authenticate(
            form_data.username,
            form_data.password,
        )

        response.set_cookie(
            key="access_token",
            value=token.access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.access_token_expire_minutes * 60,
        )

        return token


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return {"mensaje": "Sesión cerrada exitosamente"}


@router.get("/me", response_model=UsuarioRead)
def read_me(
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    return current_user


@router.get("/privado")
def ruta_privada(
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    roles = [
        usuario_rol.rol_codigo.value
        if hasattr(usuario_rol.rol_codigo, "value")
        else str(usuario_rol.rol_codigo)
        for usuario_rol in current_user.roles
    ]

    return {
        "mensaje": f"¡Hola, {current_user.nombre}! Accediste a una ruta privada.",
        "tus_roles": roles,
    }


@router.get("/admin/usuarios", response_model=list[UsuarioRead])
def list_users(
    _admin: Annotated[Usuario, Depends(require_role([RolCodigo.ADMIN]))],
    uow: Annotated[UsuarioUnitOfWork, Depends(get_usuario_uow)],
):
    with uow:
        service = UsuarioService(uow)
        return service.list_all()


@router.post("/admin/usuarios/{user_id}/desactivar", response_model=UsuarioRead)
def deactivate_user(
    user_id: int,
    _admin: Annotated[Usuario, Depends(require_role([RolCodigo.ADMIN]))],
    uow: Annotated[UsuarioUnitOfWork, Depends(get_usuario_uow)],
):
    with uow:
        service = UsuarioService(uow)
        return service.set_disabled(user_id, disabled=True)


@router.post("/admin/usuarios/{user_id}/activar", response_model=UsuarioRead)
def activate_user(
    user_id: int,
    _admin: Annotated[Usuario, Depends(require_role([RolCodigo.ADMIN]))],
    uow: Annotated[UsuarioUnitOfWork, Depends(get_usuario_uow)],
):
    with uow:
        service = UsuarioService(uow)
        return service.set_disabled(user_id, disabled=False)