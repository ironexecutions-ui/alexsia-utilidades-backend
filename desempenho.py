from fastapi import APIRouter, HTTPException, Query
from database import executar_select
from datetime import datetime

router = APIRouter()


# --------------------------------------------------------------
# ROTAS DE DESEMPENHO
# --------------------------------------------------------------

# --------------------------------------------------------------
# ROTA 1: MAIORES E MENORES VENDIDOS
# --------------------------------------------------------------
@router.get("/desempenho/maiores-menores")
def maiores_menores(
    data: str = Query(..., description="Data no formato YYYY-MM-DD"),
    limite: int = Query(5, description="Quantidade de produtos desejados")
):
    try:
        data_inicio = datetime.strptime(data, "%Y-%m-%d")
        data_fim = datetime.now()
    except:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    vendas = executar_select(
        """
        SELECT 
            vi.produto_id,
            p.nome AS nome_produto,
            SUM(vi.quantidade) AS total_vendido
        FROM vendas_itens vi
        JOIN produtos p ON p.id = vi.produto_id
        WHERE vi.data_hora BETWEEN %s AND %s
        GROUP BY vi.produto_id, p.nome
        ORDER BY total_vendido DESC
        """,
        (data_inicio, data_fim)
    )

    if not vendas:
        return {"maiores": [], "menores": []}

    maiores = sorted(vendas, key=lambda x: x["total_vendido"], reverse=True)[:limite]
    menores = sorted(vendas, key=lambda x: x["total_vendido"])[:limite]

    return {
        "maiores": maiores,
        "menores": menores
    }
@router.get("/desempenho/historico")
def historico(
    pagina: int = Query(1),
    limite: int = Query(10)
):
    offset = (pagina - 1) * limite

    sql = """
        SELECT
            vi.venda_numero,
            vi.produto_id,
            p.nome AS nome_produto,
            vi.quantidade,
            vi.preco_pago,
            vi.data_hora,
            vi.usuario_nome,
            (
                SELECT SUM(preco_pago)
                FROM vendas_itens
                WHERE venda_numero = vi.venda_numero
            ) AS total_venda
        FROM vendas_itens vi
        JOIN produtos p ON p.id = vi.produto_id
        ORDER BY vi.data_hora ASC
        LIMIT %s OFFSET %s
    """

    resultado = executar_select(sql, (limite, offset))

    return {"historico": resultado}
@router.get("/desempenho/graficos")
def graficos():

    # últimos 7 dias
    dias = executar_select(
        """
        SELECT 
            DATE(vi.data_hora) AS label,
            SUM(vi.preco_pago) AS total
        FROM vendas_itens vi
        WHERE vi.data_hora >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(vi.data_hora)
        ORDER BY DATE(vi.data_hora)
        """
    )

    # últimas 7 semanas (formato Ano-Semana)
    semanas = executar_select(
        """
        SELECT 
            DATE_FORMAT(vi.data_hora, '%x-%v') AS label,
            SUM(vi.preco_pago) AS total
        FROM vendas_itens vi
        GROUP BY DATE_FORMAT(vi.data_hora, '%x-%v')
        ORDER BY DATE_FORMAT(vi.data_hora, '%x-%v') DESC
        LIMIT 7
        """
    )

    # últimos 7 meses
    meses = executar_select(
        """
        SELECT 
            DATE_FORMAT(vi.data_hora, '%Y-%m') AS label,
            SUM(vi.preco_pago) AS total
        FROM vendas_itens vi
        GROUP BY DATE_FORMAT(vi.data_hora, '%Y-%m')
        ORDER BY DATE_FORMAT(vi.data_hora, '%Y-%m') DESC
        LIMIT 7
        """
    )

    return {
        "dias": dias,
        "semanas": semanas[::-1],  # mais antigo -> mais novo
        "meses": meses[::-1]
    }
