#!/usr/bin/env python3
"""
Hook PreToolUse — Agente 1 (Extrator Enriquecido de Contratos)
Executado pelo Claude Code antes de operações de escrita (Write/Edit/MultiEdit) ou terminal (Bash).

Funções:
1. Validação estrita de fronteiras de microsserviço: bloqueia alterações no Agente 2.
2. Bloqueio de comandos destrutivos (drop de tabelas, remoção recursiva, alteração de segredos .env).
3. Retorno oficial de bloqueio do Claude Code (exit code 2) com registro estruturado em log.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone


def registrar_log(status: str, motivo: str, dados_tool: dict) -> None:
    """Grava o registro de auditoria do hook em arquivo de log."""
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "hook_audit.log"

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hook": "PreToolUse",
        "agente": "Agente 1 (Extrator)",
        "status": status,
        "motivo": motivo,
        "dados": dados_tool,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def extrair_alvo_operacao(dados: dict) -> str:
    """Extrai o caminho de arquivo ou comando a partir do payload oficial do Claude Code (tool_input) ou CLI."""
    tool_input = dados.get("tool_input")
    if isinstance(tool_input, dict):
        alvo = (
            tool_input.get("file_path")
            or tool_input.get("path")
            or tool_input.get("command")
            or tool_input.get("target")
            or ""
        )
        if alvo:
            return str(alvo)
    return str(dados.get("target", "") or dados.get("path", "") or dados.get("command", ""))


def validar_pre_tool() -> None:
    payload_bruto = sys.stdin.read().strip()
    if payload_bruto:
        try:
            dados = json.loads(payload_bruto)
        except Exception:
            dados = {"raw_input": payload_bruto}
    else:
        tool_name = os.getenv("CLAUDE_TOOL_NAME", sys.argv[1] if len(sys.argv) > 1 else "Edit")
        target = os.getenv("CLAUDE_TOOL_TARGET", sys.argv[2] if len(sys.argv) > 2 else "agent1/tools.py")
        dados = {"tool_name": tool_name, "tool_input": {"file_path": target}}

    tool_name = dados.get("tool_name", "")
    target = extrair_alvo_operacao(dados)
    target_lower = target.lower().replace("\\", "/")

    # 1. Verificação de Fronteira Estrita: Não pode tocar no Agente 2
    if "agent2" in target_lower:
        msg = (
            "[BLOQUEIO PRE-TOOL] Violação de fronteira arquitetural: "
            f"o Agente 1 não tem permissão para alterar arquivos do Agente 2 ('{target}')."
        )
        registrar_log("REJEITADO", msg, dados)
        print(msg, file=sys.stderr)
        sys.exit(2)

    # 2. Verificação de Segurança: Arquivo de Segredos .env
    if ".env" in target_lower:
        msg = (
            "[BLOQUEIO PRE-TOOL] Violação de segurança: "
            f"modificação direta em arquivos de ambiente/segredos ('{target}') é proibida."
        )
        registrar_log("REJEITADO", msg, dados)
        print(msg, file=sys.stderr)
        sys.exit(2)

    # 3. Verificação de Comandos Destrutivos no Bash
    comandos_proibidos = ["drop table", "rm -rf", "git push --force", "del /f /q"]
    for cmd in comandos_proibidos:
        if cmd in target_lower:
            msg = f"[BLOQUEIO PRE-TOOL] Comando proibido detectado: '{cmd}' em '{target}'."
            registrar_log("REJEITADO", msg, dados)
            print(msg, file=sys.stderr)
            sys.exit(2)

    # Aprovação
    msg = f"[PRE-TOOL APROVADO] Operação '{tool_name}' autorizada para '{target}'."
    registrar_log("APROVADO", msg, dados)
    print(msg)
    sys.exit(0)


if __name__ == "__main__":
    validar_pre_tool()
