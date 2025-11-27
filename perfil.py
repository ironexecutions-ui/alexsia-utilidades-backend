from fastapi import APIRouter, HTTPException, Header
import jwt

from database import executar_select
from login import SECRET_KEY

router = APIRouter()


def validar_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


@router.get("/perfil")
def perfil(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    dados = validar_token(authorization)

    usuario = executar_select(
        "SELECT id, email, nome_completo, funcao, foto FROM usuarios WHERE id=%s",
        (dados["id"],)
    )

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return usuario[0]
