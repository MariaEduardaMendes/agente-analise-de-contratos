#!/usr/bin/env python3
"""
Hook PostToolUse — Agente 1 (Extrator Enriquecido de Contratos)
Executado pelo Claude Code imediatamente após a conclusão de uma operação de escrita (FileWrite/FileEdit).

Funções:
1. Validação sintática automática imediata de arquivos Python modificados (`py_compile`).
2. Validação estrutural de arquivos JSON modificados.
3. Registro de rastreabilidade e integridade no log de auditoria.
"""

import sys
import os
import json
import py_compile
from pathlib import Path
from datetime import datetime, timezone

def registrar_log(status: str, mensagem: str, dados_tool: dict):
    """Grava o registro de auditoria do hook em arquivo de log."""
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "hook_audit.log"
    
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hook": "PostToolUse",
        "agente": "Agente 1 (Extrator)",
        "status": status,
        "mensagem": mensagem,
        "dados": dados_tool
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")

def executar_post_tool():
    payload_bruto = sys.stdin.read().strip()
    dados = {}
    if payload_bruto:
        try:
            dados = json.loads(payload_bruto)
        except Exception:
            dados = {"raw_input": payload_bruto}
    else:
        target = os.getenv("CLAUDE_TOOL_TARGET", sys.argv[1] if len(sys.argv) > 1 else "tools.py")
        dados = {"target": target}

    target = str(dados.get("target", "") or dados.get("path", "") or "")
    
    # Validação Sintática de Python
    if target.endswith(".py") and os.path.exists(target):
        try:
            py_compile.compile(target, doraise=True)
            msg = f"[POST-TOOL SUCESSO] Arquivo Python '{target}' validado sintaticamente sem erros de compilação."
            registrar_log("VALIDADO_SUCESSO", msg, dados)
            print(msg)
        except py_compile.PyCompileError as err:
            msg = f"[POST-TOOL ALERTA] Erro de sintaxe detectado no arquivo modificado '{target}': {err}"
            registrar_log("FALHA_SINTAXE", msg, dados)
            print(msg, file=sys.stderr)
            sys.exit(1)
            
    # Validação Estrutural de JSON
    elif target.endswith(".json") and os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as f:
                json.load(f)
            msg = f"[POST-TOOL SUCESSO] Arquivo JSON '{target}' validado com estrutura sintática correta."
            registrar_log("VALIDADO_SUCESSO", msg, dados)
            print(msg)
        except Exception as err:
            msg = f"[POST-TOOL ALERTA] Arquivo JSON '{target}' possui formatação corrompida: {err}"
            registrar_log("FALHA_JSON", msg, dados)
            print(msg, file=sys.stderr)
            sys.exit(1)
    else:
        msg = f"[POST-TOOL INFO] Operação concluída para '{target}'. Nenhuma compilação requerida."
        registrar_log("CONCLUIDO", msg, dados)
        print(msg)

    sys.exit(0)

if __name__ == "__main__":
    executar_post_tool()

