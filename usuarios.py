from fastapi import APIRouter
from database import executar_select

router = APIRouter()

@router.get("/usuarios")
def listar_usuarios():

    administradores = executar_select(
        "SELECT id, nome_completo, email, funcao, foto FROM usuarios WHERE funcao='admin'"
    )

    funcionarios = executar_select(
        "SELECT id, nome_completo, email, funcao, foto FROM usuarios WHERE funcao='func'"
    )

    return {
        "administradores": administradores,
        "funcionarios": funcionarios
    }
