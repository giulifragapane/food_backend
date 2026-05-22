# app/modules/usuario/schema.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.usuario.enums import RolCodigo


class UsuarioBase(BaseModel):
    nombre: str = Field(..., max_length=80)
    apellido: str = Field(..., max_length=80)
    email: EmailStr = Field(..., max_length=254)
    celular: str | None = Field(default=None, max_length=20)


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=80)
    apellido: str | None = Field(None, max_length=80)
    email: EmailStr | None = Field(None, max_length=254)
    celular: str | None = Field(None, max_length=20)


class UsuarioAdminUpdate(UsuarioUpdate):
    disabled: bool | None = None


class UsuarioRolesUpdate(BaseModel):
    roles: list[RolCodigo] = Field(..., min_length=1)


class UsuarioRolRead(BaseModel):
    rol_codigo: RolCodigo
    model_config = ConfigDict(from_attributes=True)


class UsuarioRead(UsuarioBase):
    id: int
    disabled: bool
    roles: list[UsuarioRolRead] = []
    model_config = ConfigDict(from_attributes=True)


class UsuarioList(BaseModel):
    data: list[UsuarioRead]
    total: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int