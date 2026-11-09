"""Model de produtos: acesso a dados parametrizado e regras da entidade."""

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN_CHARS = 2
NOME_MAX_CHARS = 200


def _to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProdutoModel:
    def __init__(self, conn):
        self.conn = conn

    def listar(self):
        rows = self.conn.execute("SELECT * FROM produtos").fetchall()
        return [_to_dict(r) for r in rows]

    def buscar_por_id(self, produto_id):
        row = self.conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _to_dict(row) if row else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        cur = self.conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cur.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        self.conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )

    def deletar(self, produto_id):
        self.conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clauses, params = [], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clauses.append("preco <= ?")
            params.append(preco_max)
        where = " AND ".join(clauses) or "1=1"   # só fragmentos fixos são interpolados
        rows = self.conn.execute(f"SELECT * FROM produtos WHERE {where}", params).fetchall()
        return [_to_dict(r) for r in rows]
