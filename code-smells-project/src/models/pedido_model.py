"""Model de pedidos: criação transacional, listagem sem N+1 e relatório agregado."""
from src.database import transaction
from src.errors import NotFoundError, ValidationError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))


def calcular_desconto(faturamento):
    return next((faturamento * taxa for minimo, taxa in FAIXAS_DESCONTO if faturamento > minimo), 0)


class PedidoModel:
    def __init__(self, conn):
        self.conn = conn

    def criar(self, usuario_id, itens):
        """Valida estoque e grava pedido + itens + baixa de estoque em uma única transação."""
        with transaction(self.conn):
            total = 0
            linhas = []
            for item in itens:
                produto = self.conn.execute(
                    "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],)
                ).fetchone()
                if produto is None:
                    raise ValidationError(f"Produto {item['produto_id']} não encontrado")
                if produto["estoque"] < item["quantidade"]:
                    raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
                total += produto["preco"] * item["quantidade"]
                linhas.append((produto["id"], item["quantidade"], produto["preco"]))

            pedido_id = self.conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            ).lastrowid
            self.conn.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido_id, pid, qtd, preco) for pid, qtd, preco in linhas],
            )
            self.conn.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                [(qtd, pid) for pid, qtd, _ in linhas],
            )
        return {"pedido_id": pedido_id, "total": total}

    def _listar(self, where="", params=()):
        rows = self.conn.execute(
            f"""
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido i ON i.pedido_id = p.id
            LEFT JOIN produtos pr ON pr.id = i.produto_id
            {where}
            ORDER BY p.id, i.id
            """,
            params,
        ).fetchall()
        pedidos = {}
        for r in rows:
            pedido = pedidos.setdefault(r["id"], {
                "id": r["id"],
                "usuario_id": r["usuario_id"],
                "status": r["status"],
                "total": r["total"],
                "criado_em": r["criado_em"],
                "itens": [],
            })
            if r["produto_id"] is not None:
                pedido["itens"].append({
                    "produto_id": r["produto_id"],
                    "produto_nome": r["produto_nome"] or "Desconhecido",
                    "quantidade": r["quantidade"],
                    "preco_unitario": r["preco_unitario"],
                })
        return list(pedidos.values())

    def listar_todos(self):
        return self._listar()

    def listar_por_usuario(self, usuario_id):
        return self._listar("WHERE p.usuario_id = ?", (usuario_id,))

    def atualizar_status(self, pedido_id, novo_status):
        """Atualiza o status; ao cancelar, devolve os itens ao estoque (na mesma transação)."""
        with transaction(self.conn):
            pedido = self.conn.execute("SELECT status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
            if pedido is None:
                raise NotFoundError("Pedido não encontrado")
            if novo_status == STATUS_CANCELADO and pedido["status"] != STATUS_CANCELADO:
                self.conn.execute(
                    """
                    UPDATE produtos SET estoque = estoque + (
                        SELECT COALESCE(SUM(i.quantidade), 0) FROM itens_pedido i
                        WHERE i.pedido_id = ? AND i.produto_id = produtos.id)
                    WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                    """,
                    (pedido_id, pedido_id),
                )
            self.conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))

    def relatorio_vendas(self):
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pendentes,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS aprovados,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        total_pedidos = row["total_pedidos"]
        faturamento = row["faturamento"]
        desconto = calcular_desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": row["pendentes"] or 0,
            "pedidos_aprovados": row["aprovados"] or 0,
            "pedidos_cancelados": row["cancelados"] or 0,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }

    def contagens(self):
        row = self.conn.execute(
            """
            SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
                   (SELECT COUNT(*) FROM usuarios) AS usuarios,
                   (SELECT COUNT(*) FROM pedidos) AS pedidos
            """
        ).fetchone()
        return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}
