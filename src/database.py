from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import TypedDict


STATUS_VALIDOS = ("aberto", "em_andamento", "resolvido", "fechado")
CAMINHO_BANCO_PADRAO = (
    Path(__file__).resolve().parents[1] / "data" / "helpdesk.sqlite3"
)


class Chamado(TypedDict):
    id: int
    cliente_id: int
    descricao: str
    status: str
    criado_em: str
    atualizado_em: str


class EventoStatus(TypedDict):
    status: str
    alterado_em: str


class ChamadoComHistorico(Chamado):
    historico_status: list[EventoStatus]


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
    return [
        Chamado(
            id=linha["id"],
            cliente_id=linha["cliente_id"],
            descricao=linha["descricao"],
            status=linha["status"],
            criado_em=linha["criado_em"],
            atualizado_em=linha["atualizado_em"],
        )
        for linha in linhas
    ]


def buscar_historico_cliente(
    caminho_banco: str | Path,
    cliente_id: int,
) -> list[ChamadoComHistorico]:
    if isinstance(cliente_id, bool) or not isinstance(cliente_id, int):
        raise ValueError("cliente_id deve ser um número inteiro.")

    with conectar_banco(caminho_banco) as conexao:
        cliente = conexao.execute(
            "SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
        if cliente is None:
            raise LookupError(f"Cliente não encontrado: {cliente_id}.")

        linhas = conexao.execute(
            """
            SELECT
                c.id,
                c.cliente_id,
                c.descricao,
                c.status,
                c.criado_em,
                c.atualizado_em,
                h.id AS evento_id,
                h.status AS evento_status,
                h.alterado_em AS evento_alterado_em
            FROM chamados AS c
            LEFT JOIN historico_status_chamado AS h
                ON h.chamado_id = c.id
            WHERE c.cliente_id = ?
            ORDER BY c.criado_em DESC, c.id ASC, h.alterado_em ASC, h.id ASC
            """,
            (cliente_id,),
        ).fetchall()

    chamados: list[ChamadoComHistorico] = []
    chamado_atual: ChamadoComHistorico | None = None
    for linha in linhas:
        if chamado_atual is None or chamado_atual["id"] != linha["id"]:
            chamado_atual = ChamadoComHistorico(
                id=linha["id"],
                cliente_id=linha["cliente_id"],
                descricao=linha["descricao"],
                status=linha["status"],
                criado_em=linha["criado_em"],
                atualizado_em=linha["atualizado_em"],
                historico_status=[],
            )
            chamados.append(chamado_atual)

        if linha["evento_id"] is not None:
            chamado_atual["historico_status"].append(
                EventoStatus(
                    status=linha["evento_status"],
                    alterado_em=linha["evento_alterado_em"],
                )
            )

    return chamados
