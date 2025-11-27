from fastapi import APIRouter, UploadFile, File, Form
from database import executar_select, executar_comando
from supabase import create_client, Client
import uuid

router = APIRouter()

SUPABASE_URL = "https://ivtvqtgqjtenhmsoavtb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2dHZxdGdxanRlbmhtc29hdnRiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDA4OTE4MCwiZXhwIjoyMDc5NjY1MTgwfQ.ywlsahdquSizD5KPf_Pqzi9fmT0fmQpDJfyqW8bnq7s"
BUCKET = "AlexsiaUtilidades"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@router.get("/produtos")
def listar_produtos():

    sql = """
        SELECT 
            p.id,
            p.nome,
            p.codigo_barras,
            p.categoria,
            p.preco_custo,
            p.preco_venda,
            p.unidade_medida,
            p.descricao,
            p.imagem_url,

            COALESCE(SUM(s.quantos), 0)
            - COALESCE((
                SELECT SUM(v.quantidade)
                FROM vendas_itens v
                WHERE v.produto_id = p.id
            ), 0) AS total_somas

        FROM produtos p
        LEFT JOIN soma_produtos s ON s.produto_id = p.id

        GROUP BY 
            p.id,
            p.nome,
            p.codigo_barras,
            p.categoria,
            p.preco_custo,
            p.preco_venda,
            p.unidade_medida,
            p.descricao,
            p.imagem_url

        ORDER BY p.nome
    """

    produtos = executar_select(sql)
    return produtos

# --------------------------------------------
# POST /produtos (criar produto)
# --------------------------------------------
@router.post("/produtos")
def criar_produto(
    codigo_barras: str = Form(...),
    nome: str = Form(...),
    categoria: str = Form(...),
    preco_custo: str = Form(...),
    preco_venda: str = Form(...),
    unidade_medida: str = Form(...),
    descricao: str = Form(""),
    imagem: UploadFile = File(None)
):

    # converter preços
    try:
        preco_custo = float(preco_custo)
        preco_venda = float(preco_venda)
    except:
        return {"erro": "Valores de preço inválidos"}


    # upload da imagem
    imagem_url = None

    if imagem:
        nome_arquivo = f"{uuid.uuid4()}.jpg"
        conteudo = imagem.file.read()

        try:
            supabase.storage.from_(BUCKET).upload(
                path=nome_arquivo,
                file=conteudo,
                file_options={"content-type": imagem.content_type}
            )
            imagem_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{nome_arquivo}"

        except Exception as e:
            print("Erro Supabase:", e)
            return {"erro": "Não foi possível enviar a imagem"}


    # salvar no banco
    sql = """
        INSERT INTO produtos
        (codigo_barras, nome, categoria, preco_custo, preco_venda, unidade_medida, imagem_url, descricao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    ok = executar_comando(sql, (
        codigo_barras,
        nome,
        categoria,
        preco_custo,
        preco_venda,
        unidade_medida,
        imagem_url,
        descricao
    ))

    if not ok:
        return {"erro": "Erro ao salvar produto"}

    return {"mensagem": "Produto registrado com sucesso"}



# --------------------------------------------
# POST /soma_produtos/add
# --------------------------------------------
@router.post("/soma_produtos/add")
def adicionar_quantidade(produto_id: int = Form(...), quantos: int = Form(...)):

    sql = """
        INSERT INTO soma_produtos (produto_id, quantos)
        VALUES (%s, %s)
    """

    ok = executar_comando(sql, (produto_id, quantos))

    if not ok:
        return {"erro": "Erro ao adicionar quantidade"}

    return {"mensagem": "Quantidade adicionada"}



# --------------------------------------------
# POST /soma_produtos/remove
# --------------------------------------------
@router.post("/soma_produtos/remove")
def remover_quantidade(produto_id: int = Form(...), quantos: int = Form(...)):

    sql = """
        INSERT INTO soma_produtos (produto_id, quantos)
        VALUES (%s, %s)
    """

    ok = executar_comando(sql, (produto_id, -abs(quantos)))

    if not ok:
        return {"erro": "Erro ao remover quantidade"}

    return {"mensagem": "Quantidade removida"}



# --------------------------------------------
# PUT /produtos/{produto_id}
# --------------------------------------------
@router.put("/produtos/{produto_id}")
def atualizar_produto(
    produto_id: int,
    codigo_barras: str = Form(...),
    nome: str = Form(...),
    categoria: str = Form(...),
    preco_custo: str = Form(...),
    preco_venda: str = Form(...),
    unidade_medida: str = Form(...),
    descricao: str = Form(""),
    imagem: UploadFile = File(None)
):

    # converter preços
    try:
        preco_custo = float(preco_custo)
        preco_venda = float(preco_venda)
    except:
        return {"erro": "Valores de preço inválidos"}


    # upload da imagem nova (se tiver)
    imagem_url = None

    if imagem:
        nome_arquivo = f"{uuid.uuid4()}.jpg"
        conteudo = imagem.file.read()

        supabase.storage.from_(BUCKET).upload(
            path=nome_arquivo,
            file=conteudo,
            file_options={"content-type": imagem.content_type}
        )

        imagem_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{nome_arquivo}"


    sql_base = """
        UPDATE produtos SET 
        codigo_barras=%s,
        nome=%s,
        categoria=%s,
        preco_custo=%s,
        preco_venda=%s,
        unidade_medida=%s,
        descricao=%s
    """

    valores = [
        codigo_barras,
        nome,
        categoria,
        preco_custo,
        preco_venda,
        unidade_medida,
        descricao
    ]


    if imagem:
        sql_base += ", imagem_url=%s"
        valores.append(imagem_url)

    sql_base += " WHERE id=%s"
    valores.append(produto_id)


    ok = executar_comando(sql_base, tuple(valores))

    if not ok:
        return {"erro": "Erro ao atualizar"}

    return {"mensagem": "Produto atualizado com sucesso"}
