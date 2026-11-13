"""
Script de Verificação Automatizada dos Hooks PreToolUse e PostToolUse (TP4)
Testa o comportamento automatizado e verificável dos hooks configurados no Claude Code:
- Parsing do payload oficial do Claude Code (hook_event_name + tool_name + tool_input) e formato legado
- Bloqueio de violação de fronteira entre microsserviços com código oficial exit=2
- Bloqueio de segurança para arquivos sensíveis (.env) e comandos destrutivos (exit=2)
- Validação sintática automática pós-escrita (PostToolUse para .py e .json)
- Gravação de logs estruturados de auditoria
"""

import sys
import subprocess
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent


def testar_hook(comando: list, input_json: dict = None) -> tuple[int, str, str]:
    """Executa um script de hook passando payload opcional via stdin."""
    proc = subprocess.Popen(
        comando,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(root_dir),
    )
    stdin_data = json.dumps(input_json) if input_json else None
    stdout, stderr = proc.communicate(input=stdin_data)
    return proc.returncode, stdout.strip(), stderr.strip()


def executar_verificacao_completa_hooks():
    print("=" * 80)
    print("SUÍTE DE TESTES AUTOMATIZADOS: HOOKS PRE-TOOL-USE E POST-TOOL-USE")
    print("=" * 80)

    python_exe = sys.executable
    hook_pre1 = str(root_dir / "agent1" / ".claude" / "hooks" / "pre_tool_use.py")
    hook_post1 = str(root_dir / "agent1" / ".claude" / "hooks" / "post_tool_use.py")
    hook_pre2 = str(root_dir / "agent2" / ".claude" / "hooks" / "pre_tool_use.py")
    hook_post2 = str(root_dir / "agent2" / ".claude" / "hooks" / "post_tool_use.py")

    # 1. PreToolUse Agente 1 (Operação Válida com tool_input oficial)
    print("\n[TESTE 1] PreToolUse Agente 1: Operação legítima dentro do próprio módulo...")
    code, out, err = testar_hook(
        [python_exe, hook_pre1],
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "agent1/tools.py"},
        },
    )
    print(f" -> Saída: {out}")
    print(f" -> Código de Retorno: {code} (Esperado: 0 - APROVADO)")
    assert code == 0, "Deveria ter aprovado operação dentro do próprio módulo."

    # 2. PreToolUse Agente 1 (Violação de Fronteira com Agente 2)
    print("\n[TESTE 2] PreToolUse Agente 1: Violação de fronteira (tentando editar Agente 2)...")
    code, out, err = testar_hook(
        [python_exe, hook_pre1],
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "agent2/tools.py"},
        },
    )
    print(f" -> Saída de Erro: {err}")
    print(f" -> Código de Retorno: {code} (Esperado: 2 - BLOQUEADO OFICIAL)")
    assert code == 2, "Deveria ter bloqueado a violação de fronteira com exit code 2."

    # 3. PreToolUse Agente 1 (Violação de Segurança .env)
    print("\n[TESTE 3] PreToolUse Agente 1: Tentativa de modificação em arquivo de segredos (.env)...")
    code, out, err = testar_hook(
        [python_exe, hook_pre1],
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": ".env"},
        },
    )
    print(f" -> Saída de Erro: {err}")
    print(f" -> Código de Retorno: {code} (Esperado: 2 - BLOQUEADO OFICIAL)")
    assert code == 2, "Deveria ter bloqueado alteração em .env com exit code 2."

    # 4. PreToolUse Agente 1 (Comando Bash destrutivo)
    print("\n[TESTE 4] PreToolUse Agente 1: Comando destrutivo no Bash...")
    code, out, err = testar_hook(
        [python_exe, hook_pre1],
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf agent2/"},
        },
    )
    print(f" -> Saída de Erro: {err}")
    print(f" -> Código de Retorno: {code} (Esperado: 2 - BLOQUEADO OFICIAL)")
    assert code == 2, "Deveria ter bloqueado comando destrutivo com exit code 2."

    # 5. PostToolUse Agente 1 (Validação Sintática de Python + JSON)
    print("\n[TESTE 5] PostToolUse Agente 1: Validação sintática pós-escrita (.py e .json)...")
    code, out, err = testar_hook(
        [python_exe, hook_post1],
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "agent1/tools.py"},
        },
    )
    print(f" -> Saída (.py): {out}")
    assert code == 0 and "validado sintaticamente" in out.lower(), "Deveria ter compilado tools.py com sucesso."

    code_j, out_j, _ = testar_hook(
        [python_exe, hook_post1],
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "agent1/.claude/settings.json"},
        },
    )
    print(f" -> Saída (.json): {out_j}")
    assert code_j == 0 and "json" in out_j.lower(), "Deveria ter validado settings.json com sucesso."

    # 6. PreToolUse Agente 2 (Violação de Fronteira com Agente 1)
    print("\n[TESTE 6] PreToolUse Agente 2: Violação de fronteira (tentando alterar Agente 1)...")
    code, out, err = testar_hook(
        [python_exe, hook_pre2],
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "agent1/models.py"},
        },
    )
    print(f" -> Saída de Erro: {err}")
    print(f" -> Código de Retorno: {code} (Esperado: 2 - BLOQUEADO OFICIAL)")
    assert code == 2, "Deveria ter bloqueado tentativa de alterar Agente 1 com exit code 2."

    # 7. PostToolUse Agente 2 (Validação de Integridade)
    print("\n[TESTE 7] PostToolUse Agente 2: Validação sintática pós-escrita no Agente 2...")
    code, out, err = testar_hook(
        [python_exe, hook_post2],
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "agent2/tools.py"},
        },
    )
    print(f" -> Saída: {out}")
    print(f" -> Código de Retorno: {code} (Esperado: 0 - COMPILADO)")
    assert code == 0 and "validado sintaticamente" in out.lower(), "Deveria ter compilado o código do Agente 2 com sucesso."

    # 8. Verificação do Arquivo de Log de Auditoria
    print("\n[TESTE 8] Verificando logs gerados pelos hooks...")
    log_file1 = root_dir / "agent1" / ".claude" / "hooks" / "logs" / "hook_audit.log"
    log_file2 = root_dir / "agent2" / ".claude" / "hooks" / "logs" / "hook_audit.log"
    assert log_file1.exists(), "Log de auditoria do Agente 1 não foi criado."
    assert log_file2.exists(), "Log de auditoria do Agente 2 não foi criado."

    linhas1 = log_file1.read_text(encoding="utf-8").strip().splitlines()
    linhas2 = log_file2.read_text(encoding="utf-8").strip().splitlines()
    print(f" -> Log Agente 1: {len(linhas1)} eventos de auditoria gravados.")
    print(f" -> Log Agente 2: {len(linhas2)} eventos de auditoria gravados.")

    print("\n" + "=" * 80)
    print("TODOS OS TESTES DE HOOKS FORAM CONCLUÍDOS COM 100% DE SUCESSO!")
    print("=" * 80)


if __name__ == "__main__":
    executar_verificacao_completa_hooks()
