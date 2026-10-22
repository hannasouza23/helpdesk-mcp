import os
from pathlib import Path

from fastmcp import FastMCP

from database import (
    CAMINHO_BANCO_PADRAO,
    Chamado,
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

    return servidor


def main() -> None:
    caminho_banco = Path(os.environ.get("HELPDESK_DB_PATH", CAMINHO_BANCO_PADRAO))
    inicializar_banco(caminho_banco)
    criar_servidor(caminho_banco).run(transport="stdio")


if __name__ == "__main__":
    main()
