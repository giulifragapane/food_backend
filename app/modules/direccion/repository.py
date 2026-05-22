# app/modules/direccion/repository.py
from sqlmodel import Session

from app.core.repository import BaseRepository
from app.modules.usuario.model import DireccionEntrega


class DireccionRepository(BaseRepository[DireccionEntrega]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, DireccionEntrega)