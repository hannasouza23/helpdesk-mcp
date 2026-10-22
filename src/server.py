import os
from pathlib import Path

from fastmcp import FastMCP
from pydantic import StrictInt, StrictStr

from database import (
    CAMINHO_BANCO_PADRAO,
    Chamado,
    ChamadoComHistorico,
    ResultadoAtualizacaoStatus,
    atualizar_status_chamado as atualizar_status_no_banco,
    buscar_historico_cliente as consultar_historico_cliente,
    inicializar_banco,
    listar_chamados as consultar_chamados,
)


def criar_servidor(caminho_banco: str | Path = CAMINHO_BANCO_PADRAO) -> FastMCP:
    servidor = FastMCP("helpdesk")

    @servidor.tool(
        name="listar_chamados",
        description=(
            "Lista os chamados registrados, opcionalmente filtrados por status. "
            "Status aceitos: aberto, em_andamento, resolvido e fechado."
        ),
    )
    def listar_chamados(status: str | None = None) -> list[Chamado] | str:
        """Lista os chamados com os dados persistidos no SQLite."""
        return consultar_chamados(caminho_banco, status)

    @servidor.tool(
        name="buscar_historico_cliente",
        description=(
            "Busca os chamados e eventos de status persistidos de um cliente "
            "pelo seu identificador numérico."
        ),
    )
    def buscar_historico_cliente(cliente_id: StrictInt) -> list[ChamadoComHistorico]:
        """Retorna o histórico de chamados do cliente informado."""
        return consultar_historico_cliente(caminho_banco, cliente_id)

    @servidor.tool(
        name="atualizar_status",
        description=(
            "Atualiza o status de um chamado e registra a transição no histórico. "
            "Status aceitos: aberto, em_andamento, resolvido e fechado."
        ),
    )
    def atualizar_status(
        chamado_id: StrictInt, novo_status: StrictStr
    ) -> ResultadoAtualizacaoStatus:
        """Atualiza o status persistido e retorna os estados anterior e atual."""
        return atualizar_status_no_banco(caminho_banco, chamado_id, novo_status)

    return servidor


def main() -> None:
    caminho_banco = Path(os.environ.get("HELPDESK_DB_PATH", CAMINHO_BANCO_PADRAO))
    inicializar_banco(caminho_banco)
    criar_servidor(caminho_banco).run(transport="stdio")


if __name__ == "__main__":
    main()
