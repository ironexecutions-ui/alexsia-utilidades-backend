from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import string
from database import executar_select, executar_comando

router = APIRouter()


class FuncionarioCreate(BaseModel):
    nome_completo: str
    email: str
    senha: str
    funcao: str


class FuncionarioUpdate(BaseModel):
    nome_completo: str
    email: str
    senha: str | None = None
    funcao: str


def gerar_codigo_unico():
    while True:
        codigo = ''.join(random.choice(string.digits) for _ in range(20))
        existe = executar_select("SELECT id FROM usuarios WHERE codigo = %s", (codigo,))
        if not existe:
            return codigo


@router.get("/funcionarios")
def listar_funcionarios():
    sql = """
        SELECT id, email, nome_completo, senha, funcao, codigo
        FROM usuarios
    """
    dados = executar_select(sql)
    return dados


@router.post("/funcionarios")
def adicionar_funcionario(dados: FuncionarioCreate):
    email_existe = executar_select("SELECT id FROM usuarios WHERE email = %s", (dados.email,))
    if email_existe:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    codigo = gerar_codigo_unico()

    sql = """
        INSERT INTO usuarios (email, nome_completo, senha, funcao, codigo)
        VALUES (%s, %s, %s, %s, %s)
    """
    executar_comando(sql, (dados.email, dados.nome_completo, dados.senha, dados.funcao, codigo))

    return {"msg": "Funcionário adicionado com sucesso"}


@router.put("/funcionarios/{id}")
def editar_funcionario(id: int, dados: FuncionarioUpdate):

    sql_atualizar = """
        UPDATE usuarios SET nome_completo=%s, email=%s, funcao=%s
        WHERE id=%s
    """
    executar_comando(sql_atualizar, (dados.nome_completo, dados.email, dados.funcao, id))

    if dados.senha and dados.senha.strip() != "":
        executar_comando("UPDATE usuarios SET senha=%s WHERE id=%s", (dados.senha, id))

    return {"msg": "Funcionário atualizado com sucesso"}


@router.delete("/funcionarios/{id}")
def apagar_funcionario(id: int):
    executar_comando("DELETE FROM usuarios WHERE id=%s", (id,))
    return {"msg": "Funcionário removido"}
