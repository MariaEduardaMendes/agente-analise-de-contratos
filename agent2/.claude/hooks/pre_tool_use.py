#!/usr/bin/env python3
"""
Hook PreToolUse — Agente 2 (Avaliador de Conformidade e Risco)
Executado pelo Claude Code antes de qualquer operação de escrita (FileWrite/FileEdit) ou comando de terminal (Bash).

Funções:
1. Validação estrita de fronteiras de microsserviço: bloqueia alterações no Agente 1.
2. Bloqueio de comandos destrutivos e modificações em arquivos de segredos (.env).
3. Registro de auditoria em log estruturado.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

def registrar_log(status: str, motivo: str, dados_tool: dict):
    """Grava o registro de auditoria do hook em arquivo de log."""
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "hook_audit.log"
    
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hook": "PreToolUse",
        "agente": "Agente 2 (Auditor de Risco)",
        "status": status,
        "motivo": motivo,
        "dados": dados_tool
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")

def validar_pre_tool():
    payload_bruto = sys.stdin.read().strip()
    dados = {}
    if payload_bruto:
        try:
            dados = json.loads(payload_bruto)
        except Exception:
            dados = {"raw_input": payload_bruto}
    else:
        tool_name = os.getenv("CLAUDE_TOOL_NAME", sys.argv[1] if len(sys.argv) > 1 else "FileEdit")
        target = os.getenv("CLAUDE_TOOL_TARGET", sys.argv[2] if len(sys.argv) > 2 else "agent2/tools.py")
        dados = {"tool_name": tool_name, "target": target}

    tool_name = dados.get("tool_name", "")
    target = str(dados.get("target", "") or dados.get("path", "") or dados.get("command", ""))

    # 1. Verificação de Fronteira Estrita: Bloqueia tentativa de alterar arquivos do Agente 1
    if "agent1" in target.lower():
        msg = f"[BLOQUEIO PRE-TOOL AGENTE 2] Violação de fronteira arquitetural: o Agente 2 não tem permissão para alterar arquivos do Agente 1 ('{target}')."
        registrar_log("REJEITADO", msg, dados)
        print(msg, file=sys.stderr)
        sys.exit(1)

    # 2. Verificação de Segurança: Arquivo de Segredos .env
    if ".env" in target.lower():
        msg = f"[BLOQUEIO PRE-TOOL AGENTE 2] Violação de segurança: modificação direta em arquivos de ambiente/segredos ('{target}') é proibida."
        registrar_log("REJEITADO", msg, dados)
        print(msg, file=sys.stderr)
        sys.exit(1)

    # 3. Verificação de Comandos Destrutivos no Bash
    comandos_proibidos = ["drop table", "rm -rf", "git push --force", "del /f /q"]
    for cmd in comandos_proibidos:
        if cmd in target.lower():
            msg = f"[BLOQUEIO PRE-TOOL AGENTE 2] Comando destrutivo proibido: '{cmd}' em '{target}'."
            registrar_log("REJEITADO", msg, dados)
            print(msg, file=sys.stderr)
            sys.exit(1)

    # Aprovação
    msg = f"[PRE-TOOL APROVADO AGENTE 2] Operação '{tool_name}' autorizada para '{target}'."
    registrar_log("APROVADO", msg, dados)
    print(msg)
    sys.exit(0)

if __name__ == "__main__":
    validar_pre_tool()
