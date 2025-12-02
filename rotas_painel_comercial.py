from fastapi import APIRouter, HTTPException, Header
from database import executar_select, executar_insert
from login import SECRET_KEY
from datetime import datetime
import pytz
import jwt
from fpdf import FPDF
import base64

router = APIRouter()


def validar_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


# ------------------------------------------------------------
# ROTA 1: BUSCAR PRODUTO POR CÓDIGO
# ------------------------------------------------------------

@router.get("/painel/produto")
def buscar_produto(codigo: str, authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    if authorization.startswith("Bearer "):
        authorization = authorization.replace("Bearer ", "").strip()

    validar_token(authorization)

    produto = executar_select(
        "SELECT id, nome, categoria, preco_venda, imagem_url, unidade_medida FROM produtos WHERE codigo_barras = %s",
        (codigo,)
    )

    if not produto:
        return {"status": "erro", "mensagem": "Produto não cadastrado"}

    return {"status": "ok", "produto": produto[0]}


# ------------------------------------------------------------
# ROTA 2: REGISTRAR VENDA
# ------------------------------------------------------------

@router.post("/painel/registrar-venda")
def registrar_venda(body: dict, authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    if authorization.startswith("Bearer "):
        authorization = authorization.replace("Bearer ", "").strip()

    user = validar_token(authorization)
    print("DEBUG TOKEN USER:", user)

    usuario_nome = user["nome_completo"]

    itens = body.get("itens")
    total = body.get("total")

    if not itens or len(itens) == 0:
        raise HTTPException(status_code=400, detail="Nenhum item para registrar")

    ultimo = executar_select("SELECT venda_numero FROM vendas_itens ORDER BY id DESC LIMIT 1")

    if ultimo:
        venda_numero = ultimo[0]["venda_numero"] + 1
    else:
        venda_numero = 1

    fuso = pytz.timezone("America/Sao_Paulo")
    data_hora = datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

    for item in itens:
        executar_insert(
            """
            INSERT INTO vendas_itens 
            (produto_id, quantidade, preco_pago, venda_numero, data_hora, usuario_nome)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                item["id"],
                item["quantidade"],
                item["subtotal"],
                venda_numero,
                data_hora,
                usuario_nome
            )
        )

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, "Alexsia Utilidades", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Data e hora: {data_hora}", ln=True)
    pdf.cell(0, 8, f"Operador: {usuario_nome}", ln=True)
    pdf.cell(0, 8, f"Venda numero: {venda_numero}", ln=True)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Itens da venda:", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(90, 8, "Produto", border=1)
    pdf.cell(20, 8, "Qtd", border=1, align="C")
    pdf.cell(35, 8, "Unitario", border=1, align="R")
    pdf.cell(35, 8, "Subtotal", border=1, align="R")
    pdf.ln(8)

    pdf.set_font("Arial", "", 11)
    for item in itens:
        pdf.cell(90, 8, item["nome"], border=1)
        pdf.cell(20, 8, str(item["quantidade"]), border=1, align="C")
        pdf.cell(35, 8, f"R$ {item['preco']:.2f}", border=1, align="R")
        pdf.cell(35, 8, f"R$ {item['subtotal']:.2f}", border=1, align="R")
        pdf.ln(8)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, f"Total pago: R$ {total:.2f}", ln=True, align="R")

    pdf_output = bytes(pdf.output(dest="S"))
    pdf_b64 = base64.b64encode(pdf_output).decode("utf-8")

    return {
        "status": "ok",
        "pdf_base64": pdf_b64
    }
@router.get("/painel/buscar-nome")
def buscar_por_nome(q: str, authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    if authorization.startswith("Bearer "):
        authorization = authorization.replace("Bearer ", "").strip()

    validar_token(authorization)

    produtos = executar_select(
        """
        SELECT id, nome, preco_venda, imagem_url, unidade_medida, categoria
        FROM produtos
        WHERE nome LIKE %s
        ORDER BY nome ASC
        LIMIT 10
        """,
        (f"%{q}%",)
    )

    return {"status": "ok", "produtos": produtos}
# ------------------------------------------------------------
# ROTA 3: ATUALIZAR PREÇO DO PRODUTO
# ------------------------------------------------------------
@router.put("/painel/atualizar-preco")
def atualizar_preco(body: dict, authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    if authorization.startswith("Bearer "):
        authorization = authorization.replace("Bearer ", "").strip()

    validar_token(authorization)

    produto_id = body.get("id")
    novo_preco = body.get("preco")

    if not produto_id or novo_preco is None:
        raise HTTPException(status_code=400, detail="Dados incompletos")

    try:
        executar_insert(
            "UPDATE produtos SET preco_venda = %s WHERE id = %s",
            (float(novo_preco), produto_id)
        )
    except:
        raise HTTPException(status_code=500, detail="Erro ao atualizar o preço")

    return {"status": "ok", "mensagem": "Preço atualizado com sucesso"}
@router.get("/fechamento/20dias")
def fechamento_20dias(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    if authorization.startswith("Bearer "):
        authorization = authorization.replace("Bearer ", "").strip()

    validar_token(authorization)

    query = """
        SELECT 
            CASE
                WHEN TIME(data_hora) >= '04:00:00' THEN DATE(data_hora)
                ELSE DATE(DATE_SUB(data_hora, INTERVAL 1 DAY))
            END AS dia_comercial,
            SUM(preco_pago) AS total_dia
        FROM vendas_itens
        GROUP BY dia_comercial
        ORDER BY dia_comercial DESC
        LIMIT 20
    """

    dias = executar_select(query)

    if not dias:
        return {
            "diaAtual": {
                "data": None,
                "total": 0
            },
            "ultimos20dias": []
        }

    ultimo = dias[0]["dia_comercial"]

    ultimo_str = ultimo.strftime("%Y-%m-%d")

    soma_atual = executar_select(
        """
        SELECT 
            SUM(preco_pago) AS total_dia
        FROM vendas_itens
        WHERE 
            CASE
                WHEN TIME(data_hora) >= '04:00:00' THEN DATE(data_hora)
                ELSE DATE(DATE_SUB(data_hora, INTERVAL 1 DAY))
            END = %s
        """,
        (ultimo_str,)
    )

    total_atual = soma_atual[0]["total_dia"] if soma_atual[0]["total_dia"] else 0

    ultimos = []
    for d in dias:
        ultimos.append({
            "data": d["dia_comercial"].strftime("%Y-%m-%d"),
            "total": float(d["total_dia"])
        })

    return {
        "diaAtual": {
            "data": ultimo_str,
            "total": float(total_atual)
        },
        "ultimos20dias": ultimos
    }
