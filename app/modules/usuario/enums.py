# app/modules/usuario/enums.py
from enum import Enum


class RolCodigo(str, Enum):
    ADMIN = "ADMIN"
    STOCK = "STOCK"
    PEDIDOS = "PEDIDOS"
    CLIENT = "CLIENT"