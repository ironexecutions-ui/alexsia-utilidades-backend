from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from login import router as login_router
from perfil import router as perfil_router
from inventario import router as inventario_router
from funcionarios import router as funcionarios_router
from usuarios import router as usuarios_router
from desempenho import router as desempenho_router
from rotas_painel_comercial import router as painel_router

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login_router)
app.include_router(perfil_router)
app.include_router(inventario_router)
app.include_router(funcionarios_router)
app.include_router(usuarios_router)
app.include_router(desempenho_router)
app.include_router(painel_router)

@app.get("/perfil")
def teste_perfil():
    return {"email": "teste@loja.com", "funcao": "admin"}
