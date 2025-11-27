from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
import jwt
import datetime

from database import executar_select

router = APIRouter()

SECRET_KEY = "CHAVE_SUPER_SECRETA_QUE_DEVES_TROCAR"


def buscar_usuario_por_email(email):
    resultado = executar_select(
        "SELECT * FROM usuarios WHERE email=%s",
        (email,)
    )

    if not resultado:
        return None

    return resultado[0]


def buscar_usuario_por_codigo(codigo):
    resultado = executar_select(
        "SELECT * FROM usuarios WHERE codigo=%s",
        (codigo,)
    )

    if not resultado:
        return None

    return resultado[0]


def criar_token(usuario):
    payload = {
        "id": usuario["id"],
        "email": usuario["email"],
        "funcao": usuario["funcao"],
        "nome_completo": usuario["nome_completo"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")



@router.post("/login")
def login(dados: OAuth2PasswordRequestForm = Depends()):
    email = dados.username
    senha = dados.password

    usuario = buscar_usuario_por_email(email)

    if not usuario:
        raise HTTPException(status_code=400, detail="Email não encontrado")

    if senha != usuario["senha"]:
        raise HTTPException(status_code=400, detail="Senha incorreta")

    token = criar_token(usuario)

    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "email": usuario["email"],
            "funcao": usuario["funcao"],
            "foto": usuario["foto"]
        }
    }


@router.post("/login-codigo")
def login_codigo(payload: dict):
    if "codigo" not in payload or not payload["codigo"]:
        raise HTTPException(status_code=400, detail="Código não informado")

    codigo = payload["codigo"].strip()

    usuario = buscar_usuario_por_codigo(codigo)

    if not usuario:
        raise HTTPException(status_code=400, detail="Código não encontrado")

    token = criar_token(usuario)

    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "email": usuario["email"],
            "funcao": usuario["funcao"],
            "foto": usuario["foto"]
        }
    }
