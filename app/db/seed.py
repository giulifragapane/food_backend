# app/db/seed.py
from sqlmodel import Session, select

from app.core.security import hash_password
from app.modules.usuario.enums import RolCodigo
from app.modules.usuario.model import Rol, Usuario, UsuarioRol


def seed_data(session: Session) -> None:
    seed_roles(session)
    seed_admin_user(session)
    session.commit()


def seed_roles(session: Session) -> None:
    roles = [
        (RolCodigo.ADMIN, "Administrador", "Acceso completo al sistema."),
        (RolCodigo.STOCK, "Stock", "Gestión de stock y disponibilidad de productos."),
        (RolCodigo.PEDIDOS, "Pedidos", "Gestión y cambio de estado de pedidos."),
        (RolCodigo.CLIENT, "Cliente", "Cliente de la tienda."),
    ]

    for codigo, nombre, descripcion in roles:
        existing = session.get(Rol, codigo)
        if not existing:
            session.add(
                Rol(
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                )
            )


def seed_admin_user(session: Session) -> None:
    admin_email = "admin@admin.com"

    existing_admin = session.exec(
        select(Usuario).where(Usuario.email == admin_email)
    ).first()

    if existing_admin:
        return

    admin = Usuario(
        nombre="Admin",
        apellido="Sistema",
        email=admin_email,
        celular=None,
        password_hash=hash_password("admin123"),
        disabled=False,
    )

    admin.roles.append(
        UsuarioRol(
            rol_codigo=RolCodigo.ADMIN,
        )
    )

    session.add(admin)