import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

from fastmcp import Client
from fastmcp.client.client import CallToolResult
from fastmcp.client.tasks import ToolTask
from fastmcp.client.transports import StdioTransport
from mcp.types import TextContent


CAMINHO_RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_SERVIDOR = CAMINHO_RAIZ / "src" / "server.py"

STATUS_POR_COMANDO = {
    "aberto": "aberto",
    "abertos": "aberto",
    "em andamento": "em_andamento",
    "resolvido": "resolvido",
    "resolvidos": "resolvido",
    "fechado": "fechado",
    "fechados": "fechado",
}

ORIENTACAO_COMANDOS = (
    "Comandos disponíveis:\n"
    "- listar (todos os chamados) ou listar abertos, listar em andamento, "
    "listar resolvidos, listar fechados;\n"
    "- histórico do cliente 2;\n"
    "- alterar chamado 3 para fechado.\n"
    "Status aceitos: aberto, em andamento, resolvido e fechado."
)

STATUS_PARA_EXIBICAO = {
    "aberto": "Aberto",
    "em_andamento": "Em andamento",
    "resolvido": "Resolvido",
    "fechado": "Fechado",
}

FUSO_EXIBICAO = timezone(timedelta(hours=-3))


def _normalizar(texto: str) -> str:
    texto_sem_acentos = unicodedata.normalize("NFKD", texto.casefold())
    sem_marcas = "".join(
        caractere
        for caractere in texto_sem_acentos
        if not unicodedata.combining(caractere)
    )
    return " ".join(sem_marcas.replace("_", " ").replace("-", " ").split())


def interpretar_comando(texto: str) -> tuple[str, dict[str, int | str | None]]:
    comando = _normalizar(texto)

    correspondencia = re.fullmatch(
        r"listar(?: (todos|aberto|abertos|em andamento|resolvido|resolvidos|"
        r"fechado|fechados))?",
        comando,
    )
    if correspondencia:
        status = correspondencia.group(1)
        return "listar_chamados", {
            "status": STATUS_POR_COMANDO.get(status) if status else None
        }

    correspondencia = re.fullmatch(
        r"historico(?: do)? cliente (\d+)", comando
    )
    if correspondencia:
        return "buscar_historico_cliente", {
            "cliente_id": int(correspondencia.group(1))
        }

    correspondencia = re.fullmatch(
        r"(?:alterar|atualizar) chamado (\d+) para (.+)", comando
    )
    if correspondencia:
        status = STATUS_POR_COMANDO.get(correspondencia.group(2))
        if status is None:
            raise ValueError(
                "Status inválido. Use aberto, em andamento, resolvido ou "
                "fechado para atualizar o chamado."
            )
        return "atualizar_status", {
            "chamado_id": int(correspondencia.group(1)),
            "novo_status": status,
        }

    raise ValueError(ORIENTACAO_COMANDOS)


def _formatar_data(valor: object) -> str:
    if not isinstance(valor, str):
        return str(valor)
    try:
        data = datetime.fromisoformat(valor)
    except ValueError:
        return valor
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    data_local = data.astimezone(FUSO_EXIBICAO)
    return data_local.strftime("%d/%m/%Y às %H:%M UTC-3")


def _formatar_chamado(chamado: dict[str, object], incluir_historico: bool) -> str:
    id_chamado = chamado.get("id", "—")
    status = chamado.get("status", "desconhecido")
    status_exibido = STATUS_PARA_EXIBICAO.get(str(status), str(status))
    linhas = [
        f"**Chamado #{id_chamado} — {status_exibido}**",
        f"Descrição: {chamado.get('descricao', 'Sem descrição')}",
        f"Cliente: #{chamado.get('cliente_id', '—')}",
        f"Criado em: {_formatar_data(chamado.get('criado_em', '—'))}",
        f"Atualizado em: {_formatar_data(chamado.get('atualizado_em', '—'))}",
    ]

    if incluir_historico:
        historico = chamado.get("historico_status", [])
        if isinstance(historico, list) and historico:
            linhas.extend(["", "**Movimentações:**"])
            for evento in historico:
                if isinstance(evento, dict):
                    status_evento = evento.get("status", "desconhecido")
                    nome_status = STATUS_PARA_EXIBICAO.get(
                        str(status_evento), str(status_evento)
                    )
                    data_evento = _formatar_data(evento.get("alterado_em", "—"))
                    linhas.append(f"- {data_evento}: {nome_status}")
        else:
            linhas.extend(["", "Nenhuma movimentação registrada."])

    return "\n".join(linhas)


def _formatar_resultado(
    resultado: CallToolResult, nome_tool: str
) -> str:
    if resultado.structured_content is not None:
        conteudo = resultado.structured_content
        if isinstance(conteudo, dict) and "result" in conteudo:
            conteudo = conteudo["result"]
        if isinstance(conteudo, str):
            if conteudo == "Nenhum chamado encontrado.":
                return "Não encontrei chamados para esse filtro."
            return conteudo

        if nome_tool in ("listar_chamados", "buscar_historico_cliente"):
            if not isinstance(conteudo, list):
                return f"```json\n{json.dumps(conteudo, ensure_ascii=False, indent=2)}\n```"
            if not conteudo:
                if nome_tool == "buscar_historico_cliente":
                    return "Esse cliente ainda não possui chamados."
                return "Não encontrei chamados para esse filtro."

            titulo = (
                f"**Histórico do cliente #{conteudo[0].get('cliente_id', '—')}**"
                if nome_tool == "buscar_historico_cliente"
                and isinstance(conteudo[0], dict)
                else f"**Chamados encontrados: {len(conteudo)}**"
            )
            incluir_historico = nome_tool == "buscar_historico_cliente"
            detalhes = [
                _formatar_chamado(chamado, incluir_historico)
                for chamado in conteudo
                if isinstance(chamado, dict)
            ]
            return "\n\n".join([titulo, *detalhes])

        if nome_tool == "atualizar_status" and isinstance(conteudo, dict):
            id_chamado = conteudo.get("chamado_id", "—")
            status_atual = conteudo.get("status_atual", "desconhecido")
            nome_status_atual = STATUS_PARA_EXIBICAO.get(
                str(status_atual), str(status_atual)
            )
            if conteudo.get("alterado") is True:
                status_anterior = conteudo.get("status_anterior", "desconhecido")
                nome_status_anterior = STATUS_PARA_EXIBICAO.get(
                    str(status_anterior), str(status_anterior)
                )
                return (
                    f"**Chamado #{id_chamado} atualizado com sucesso.**\n\n"
                    f"Status anterior: {nome_status_anterior}\n\n"
                    f"Novo status: **{nome_status_atual}**"
                )
            return (
                f"O chamado #{id_chamado} já está com status "
                f"**{nome_status_atual}**. Nenhuma alteração foi necessária."
            )

        return f"```json\n{json.dumps(conteudo, ensure_ascii=False, indent=2)}\n```"

    textos = [
        bloco.text
        for bloco in resultado.content
        if isinstance(bloco, TextContent)
    ]
    return "\n".join(textos) or "A ferramenta não retornou conteúdo."


async def executar_tool(nome: str, argumentos: dict[str, int | str | None]) -> str:
    transporte = StdioTransport(
        command=sys.executable,
        args=[str(CAMINHO_SERVIDOR)],
        env=os.environ.copy(),
        cwd=str(CAMINHO_RAIZ),
    )
    async with Client(transporte) as cliente:
        resultado = await cliente.call_tool(nome, argumentos)
    if isinstance(resultado, ToolTask):
        raise RuntimeError("A ferramenta retornou uma tarefa em vez do resultado.")
    return _formatar_resultado(resultado, nome)
