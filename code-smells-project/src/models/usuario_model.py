"""Model de usuários: senhas com hash forte e serialização sem dados sensíveis."""
from werkzeug.security import check_password_hash, generate_password_hash

TIPO_PADRAO = "cliente"


def _to_public_dict(row):
    # A senha (ou o hash) nunca sai deste model.
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def _is_hash(valor):
    # Formato do werkzeug: "<método>:<params>$<salt>$<hash>"
    return bool(valor) and ":" in valor and valor.count("$") >= 2


class UsuarioModel:
    def __init__(self, conn):
        self.conn = conn

    def listar(self):
        rows = self.conn.execute("SELECT * FROM usuarios").fetchall()
        return [_to_public_dict(r) for r in rows]

    def buscar_por_id(self, usuario_id):
        row = self.conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _to_public_dict(row) if row else None

    def criar(self, nome, email, senha, tipo=TIPO_PADRAO):
        cur = self.conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
        return cur.lastrowid

    def autenticar(self, email, senha):
        """Retorna o usuário (sem senha) se as credenciais conferem; None caso contrário."""
        row = self.conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        if row is None:
            return None
        armazenada = row["senha"] or ""
        if _is_hash(armazenada):
            if not check_password_hash(armazenada, senha):
                return None
        elif armazenada == senha:
            # Banco legado com senha em texto puro: migra para hash no primeiro login válido.
            self.conn.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(senha), row["id"])
            )
        else:
            return None
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
