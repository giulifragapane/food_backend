# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from app.core.database import create_db_and_tables, engine
from app.db.seed import seed_data
from app.modules.categoria.router import router as categoria_router
from app.modules.ingrediente.router import router as ingrediente_router
from app.modules.producto.router import router as producto_router
from app.modules.usuario.router import router as auth_router
from app.modules.direccion.router import router as direccion_router
from app.modules.pedido.router import router as pedido_router
from app.modules.admin.router import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)
    yield


app = FastAPI(
    title="API Parcial",
    description="API para el parcial de programación - Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categoria_router)
app.include_router(ingrediente_router)
app.include_router(producto_router)
app.include_router(auth_router)
app.include_router(direccion_router)
app.include_router(pedido_router)
app.include_router(admin_router)