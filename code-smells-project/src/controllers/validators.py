"""Validações de entrada reutilizadas pelos controllers (lançam ValidationError → 400)."""
from src.errors import ValidationError
from src.models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_MAX_CHARS, NOME_MIN_CHARS


def exigir_json(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def _numero(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(f"{campo} deve ser numérico")
    return valor


def validar_produto(dados):
    """Mesma validação para criação e atualização (antes divergiam)."""
    dados = exigir_json(dados)
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    preco = _numero(dados["preco"], "Preço")
    estoque = _numero(dados["estoque"], "Estoque")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN_CHARS:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_CHARS:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": int(estoque),
        "categoria": categoria,
    }


def validar_itens_pedido(itens):
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    normalizados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item do pedido inválido")
        produto_id, quantidade = item.get("produto_id"), item.get("quantidade")
        if not isinstance(produto_id, int) or isinstance(produto_id, bool):
            raise ValidationError("produto_id inválido")
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade < 1:
            raise ValidationError("Quantidade deve ser um inteiro maior que zero")
        normalizados.append({"produto_id": produto_id, "quantidade": quantidade})
    return normalizados


def float_opcional(valor, campo):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except ValueError as exc:
        raise ValidationError(f"{campo} inválido") from exc
