# app/modules/usuario/service.py
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.core.unit_of_work import UnitOfWork
from app.modules.usuario.enums import RolCodigo
from app.modules.usuario.model import Usuario, UsuarioRol
from app.modules.usuario.schema import (
    Token,
    UsuarioAdminUpdate,
    UsuarioCreate,
    UsuarioList,
    UsuarioRead,
    UsuarioRolesUpdate,
)


class UsuarioService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _get_or_404(self, user_id: int) -> Usuario:
        user = self.uow.usuarios.get_by_id(user_id)

        if not user or user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        return user

    def register(self, user_in: UsuarioCreate) -> Usuario:
        if self.uow.usuarios.get_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está en uso.",
            )

        rol_client = self.uow.roles.get_by_codigo(RolCodigo.CLIENT)
        if not rol_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No existe el rol CLIENT. Ejecutá el seed inicial.",
            )

        usuario = Usuario(
            nombre=user_in.nombre,
            apellido=user_in.apellido,
            email=user_in.email,
            celular=user_in.celular,
            password_hash=hash_password(user_in.password),
        )

        usuario.roles.append(
            UsuarioRol(
                rol_codigo=RolCodigo.CLIENT,
            )
        )

        return self.uow.usuarios.add(usuario)

    def authenticate(self, email: str, password: str) -> Token:
        user = self.uow.usuarios.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cuenta de usuario eliminada.",
            )

        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario deshabilitado.",
            )

        role_values = [
            usuario_rol.rol_codigo.value
            if hasattr(usuario_rol.rol_codigo, "value")
            else str(usuario_rol.rol_codigo)
            for usuario_rol in user.roles
        ]

        access_token = create_access_token(
            data={
                "sub": user.email,
                "roles": role_values,
            }
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def list_all(self) -> list[Usuario]:
        return self.uow.usuarios.get_all()

    def list_admin(self, offset: int = 0, limit: int = 20, rol: RolCodigo | None = None) -> UsuarioList:
        if rol is not None:
            usuarios = self.uow.usuarios.get_by_role(rol, offset, limit)
            total = self.uow.usuarios.count_by_role(rol)
        else:
            usuarios = self.uow.usuarios.get_all_paginated(offset, limit)
            total = self.uow.usuarios.count_active()

        return UsuarioList(
            data=[UsuarioRead.model_validate(usuario) for usuario in usuarios],
            total=total,
        )

    def update_admin(self, user_id: int, data: UsuarioAdminUpdate) -> Usuario:
        user = self._get_or_404(user_id)
        patch = data.model_dump(exclude_unset=True)

        if "email" in patch and patch["email"] != user.email:
            existing = self.uow.usuarios.get_by_email(patch["email"])
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El email ya está en uso.",
                )

        for field, value in patch.items():
            setattr(user, field, value)

        user.updated_at = self.uow.now
        return self.uow.usuarios.update(user)

    def soft_delete_admin(self, user_id: int) -> None:
        user = self._get_or_404(user_id)

        user.deleted_at = self.uow.now
        user.updated_at = self.uow.now
        user.disabled = True

        self.uow.usuarios.update(user)

    def update_roles(self, user_id: int, data: UsuarioRolesUpdate) -> Usuario:
        user = self._get_or_404(user_id)

        roles_unicos = list(dict.fromkeys(data.roles))

        for rol_codigo in roles_unicos:
            if not self.uow.roles.get_by_codigo(rol_codigo):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Rol {rol_codigo.value} no encontrado.",
                )

        self.uow.usuarios.clear_roles(user.id)

        user.roles.clear()

        for rol_codigo in roles_unicos:
            user.roles.append(
                UsuarioRol(
                    usuario_id=user.id,
                    rol_codigo=rol_codigo,
                )
            )

        user.updated_at = self.uow.now
        return self.uow.usuarios.update(user)

    def set_disabled(self, user_id: int, disabled: bool) -> Usuario:
        user = self._get_or_404(user_id)

        user.disabled = disabled
        user.updated_at = self.uow.now

        return self.uow.usuarios.update(user)