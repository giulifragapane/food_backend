# app/modules/categoria/router.py
from fastapi import APIRouter, Depends, Query, status
from typing import Annotated
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_role
from app.modules.usuario.enums import RolCodigo
from app.modules.categoria.schema import CategoriaCreate, CategoriaRead, CategoriaUpdate, CategoriaList
from app.modules.categoria.service import CategoriaService

router = APIRouter(prefix="/categorias", tags=["categorias"])


def get_categoria_service(session: Session = Depends(get_session)) -> CategoriaService:
    return CategoriaService(session)


@router.post("/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED, summary="Crear una categoría nueva")
def create_categoria(
    data: CategoriaCreate,
    _admin=Depends(require_role([RolCodigo.ADMIN])),
    svc: CategoriaService = Depends(get_categoria_service),
) -> CategoriaRead:
    return svc.create(data)


@router.get("/", response_model=CategoriaList, status_code=status.HTTP_200_OK, summary="Listar categorías activas (paginado)")
def list_categorias(
    offset: Annotated[int, Query(ge=0, description="Cantidad de registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima de registros")] = 20,
    svc: CategoriaService = Depends(get_categoria_service),
) -> CategoriaList:
    return svc.get_all_active(offset=offset, limit=limit)


@router.get("/all/", response_model=CategoriaList, status_code=status.HTTP_200_OK, summary="Listar todas las categorias")
def list_categorias_all(
    offset: Annotated[int, Query(ge=0, description="Cantidad de registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima de registros")] = 20,
    _admin=Depends(require_role([RolCodigo.ADMIN])),
    svc: CategoriaService = Depends(get_categoria_service),
) -> CategoriaList:
    return svc.get_all(offset=offset, limit=limit)


@router.get("/buscar/", response_model=CategoriaRead, status_code=status.HTTP_200_OK, summary="Buscar categoría por nombre")
def search_categoria_by_nombre(
    nombre: str = Query(..., max_length=100, description="Nombre de la categoría a buscar"),
    svc: CategoriaService = Depends(get_categoria_service),
) -> CategoriaRead:
    return svc.get_by_nombre(nombre)


@router.get("/{categoria_id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK, summary="Obtener categoría por ID")
def get_categoria(categoria_id: int, svc: CategoriaService = Depends(get_categoria_service)) -> CategoriaRead:
    return svc.get_by_id(categoria_id)


@router.patch("/{categoria_id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK, summary="Actualización parcial de categoría")
def update_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    _admin=Depends(require_role([RolCodigo.ADMIN])),
    svc: CategoriaService = Depends(get_categoria_service),
) -> CategoriaRead:
    return svc.update(categoria_id, data)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar categoría (soft delete)")
def delete_categoria(
    categoria_id: int,
    _admin=Depends(require_role([RolCodigo.ADMIN])),
    svc: CategoriaService = Depends(get_categoria_service),
) -> None:
    svc.soft_delete(categoria_id)