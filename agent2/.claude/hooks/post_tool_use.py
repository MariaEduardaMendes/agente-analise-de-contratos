#!/usr/bin/env python3
"""
Hook PostToolUse — Agente 2 (Avaliador de Conformidade e Risco)
Executado pelo Claude Code imediatamente após a conclusão de uma operação de escrita (Write/Edit/MultiEdit).

Funções:
1. Validação sintática automática de arquivos Python modificados (`py_compile`).
2. Validação da integridade estrutural de arquivos JSON.
3. Retorno exit code 2 em caso de falha sintática ou JSON corrompido.
"""

import sys
import os
import json
import py_compile
from pathlib import Path
from datetime import datetime, timezone


def registrar_log(status: str, mensagem: str, dados_tool: dict) -> None:
    """Grava o registro de auditoria do hook em arquivo de log."""
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "hook_audit.log"

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hook": "PostToolUse",
        "agente": "Agente 2 (Auditor de Risco)",
        "status": status,
        "mensagem": mensagem,
        "dados": dados_tool,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def extrair_caminho_arquivo(dados: dict) -> str:
    """Extrai file_path/path a partir do payload oficial do Claude Code (tool_input) ou legado."""
    tool_input = dados.get("tool_input")
    if isinstance(tool_input, dict):
        caminho = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("target") or ""
        if caminho:
            return str(caminho)
    return str(dados.get("target", "") or dados.get("path", "") or "")


def resolver_caminho_existente(target: str) -> Path | None:
    """Resolve caminhos relativos tanto a partir do cwd quanto da raiz do agente."""
    if not target:
        return None
    candidato = Path(target)
    if candidato.exists():
        return candidato
    agent_dir = Path(__file__).resolve().parent.parent.parent
    candidato_agente = agent_dir / target
    if candidato_agente.exists():
        return candidato_agente
    return None


def executar_post_tool() -> None:
    payload_bruto = sys.stdin.read().strip()
    if payload_bruto:
        try:
            dados = json.loads(payload_bruto)
        except Exception:
            dados = {"raw_input": payload_bruto}
    else:
        target = os.getenv("CLAUDE_TOOL_TARGET", sys.argv[1] if len(sys.argv) > 1 else "tools.py")
        dados = {"tool_input": {"file_path": target}}

    target = extrair_caminho_arquivo(dados)
    arquivo = resolver_caminho_existente(target)

    # Validação Sintática de Python
    if target.lower().endswith(".py") and arquivo is not None:
        try:
            py_compile.compile(str(arquivo), doraise=True)
            msg = f"[POST-TOOL SUCESSO AGENTE 2] Código Python '{target}' validado sintaticamente sem erros."
            registrar_log("VALIDADO_SUCESSO", msg, dados)
            print(msg)
        except py_compile.PyCompileError as err:
            msg = f"[POST-TOOL ALERTA AGENTE 2] Erro de sintaxe detectado no arquivo modificado '{target}': {err}"
            registrar_log("FALHA_SINTAXE", msg, dados)
            print(msg, file=sys.stderr)
            sys.exit(2)

    # Validação Estrutural de JSON
    elif target.lower().endswith(".json") and arquivo is not None:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                json.load(f)
            msg = f"[POST-TOOL SUCESSO AGENTE 2] Arquivo JSON '{target}' validado estruturalmente com sucesso."
            registrar_log("VALIDADO_SUCESSO", msg, dados)
            print(msg)
        except Exception as err:
            msg = f"[POST-TOOL ALERTA AGENTE 2] Arquivo JSON '{target}' possui formatação corrompida: {err}"
            registrar_log("FALHA_JSON", msg, dados)
            print(msg, file=sys.stderr)
            sys.exit(2)
    else:
        msg = f"[POST-TOOL INFO AGENTE 2] Operação finalizada para '{target}'."
        registrar_log("CONCLUIDO", msg, dados)
        print(msg)

    sys.exit(0)


if __name__ == "__main__":
    executar_post_tool()
