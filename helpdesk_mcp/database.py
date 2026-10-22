from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import TypedDict


STATUS_VALIDOS = ("aberto", "em_andamento", "resolvido", "fechado")
CAMINHO_BANCO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "helpdesk.sqlite3"


class Chamado(TypedDict):
    id: int
    cliente_id: int
    descricao: str
    status: str
    criado_em: str
    atualizado_em: str


@contextmanager
def conectar_banco(caminho_banco: str | Path) -> Iterator[sqlite3.Connection]:
    caminho = Path(caminho_banco)
    if str(caminho_banco) != ":memory:":
        caminho.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(str(caminho_banco))
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def inicializar_banco(caminho_banco: str | Path = CAMINHO_BANCO_PADRAO) -> None:
    with conectar_banco(caminho_banco) as conexao:
        conexao.execute("BEGIN")
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE
            )
            """
        )
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id),
                descricao TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('aberto', 'em_andamento', 'resolvido', 'fechado')
                ),
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
            """
        )
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_status_chamado (
                id INTEGER PRIMARY KEY,
                chamado_id INTEGER NOT NULL REFERENCES chamados(id),
                status TEXT NOT NULL CHECK (
                    status IN ('aberto', 'em_andamento', 'resolvido', 'fechado')
                ),
                alterado_em TEXT NOT NULL
            )
            """
        )
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_chamados_cliente_criado "
            "ON chamados(cliente_id, criado_em)"
        )
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status)"
        )
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_historico_chamado_alterado "
            "ON historico_status_chamado(chamado_id, alterado_em)"
        )

        quantidade = conexao.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
        if quantidade == 0:
            _inserir_dados_de_demonstracao(conexao)


def _inserir_dados_de_demonstracao(conexao: sqlite3.Connection) -> None:
    clientes = (
        ("Ana Lima", "ana.lima@example.test"),
        ("Bruno Costa", "bruno.costa@example.test"),
        ("Carla Souza", "carla.souza@example.test"),
    )
    for nome, email in clientes:
        conexao.execute(
            "INSERT INTO clientes (nome, email) VALUES (?, ?) "
            "ON CONFLICT(email) DO NOTHING",
            (nome, email),
        )

    ids_clientes = {
        email: conexao.execute(
            "SELECT id FROM clientes WHERE email = ?", (email,)
        ).fetchone()["id"]
        for _, email in clientes
    }
    chamados = (
        (
            1,
            ids_clientes["ana.lima@example.test"],
            "Não consigo acessar o portal de suporte.",
            "aberto",
            "2025-01-10T09:00:00+00:00",
        ),
        (
            2,
            ids_clientes["bruno.costa@example.test"],
            "Solicito ajuda para configurar as notificações.",
            "em_andamento",
            "2025-01-11T10:30:00+00:00",
        ),
        (
            3,
            ids_clientes["carla.souza@example.test"],
            "Erro ao exportar o relatório mensal.",
            "resolvido",
            "2025-01-12T14:15:00+00:00",
        ),
        (
            4,
            ids_clientes["ana.lima@example.test"],
            "Dúvida sobre a atualização da conta.",
            "fechado",
            "2025-01-13T16:45:00+00:00",
        ),
    )
    for chamado_id, cliente_id, descricao, status, criado_em in chamados:
        conexao.execute(
            """
            INSERT INTO chamados (
                id, cliente_id, descricao, status, criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chamado_id, cliente_id, descricao, status, criado_em, criado_em),
        )
        conexao.execute(
            """
            INSERT INTO historico_status_chamado (chamado_id, status, alterado_em)
            VALUES (?, ?, ?)
            """,
            (chamado_id, status, criado_em),
        )


def listar_chamados(
    caminho_banco: str | Path = CAMINHO_BANCO_PADRAO,
    status: str | None = None,
) -> list[Chamado] | str:
    if status is not None and status not in STATUS_VALIDOS:
        opcoes = ", ".join(STATUS_VALIDOS)
        raise ValueError(f"Status inválido: {status!r}. Valores aceitos: {opcoes}.")

    with conectar_banco(caminho_banco) as conexao:
        if status is None:
            linhas = conexao.execute(
                """
                SELECT id, cliente_id, descricao, status, criado_em, atualizado_em
                FROM chamados
                ORDER BY criado_em DESC, id ASC
                """
            ).fetchall()
        else:
            linhas = conexao.execute(
                """
                SELECT id, cliente_id, descricao, status, criado_em, atualizado_em
                FROM chamados
                WHERE status = ?
                ORDER BY criado_em DESC, id ASC
                """,
                (status,),
            ).fetchall()

    if not linhas:
        return "Nenhum chamado encontrado."
    return [dict(linha) for linha in linhas]
