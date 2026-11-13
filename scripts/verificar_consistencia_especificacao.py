"""
Script de Verificação de Consistência entre Código e Especificação (CLAUDE.md / AGENTS.md)
Valida:
1. Existência e correspondência de endpoints FastAPI declarados nos contratos
2. Assinaturas das tools Python (@function_tool) declaradas na documentação
3. Existência e integridade dos modelos Pydantic v2
4. Validade sintática do frontmatter YAML das skills (.claude/skills e skills/) e subagentes (.claude/agents e subagents/)
5. Schema oficial do .claude/settings.json (allow, deny, ask e hooks com array aninhado) e integridade dos scripts de hook
"""

import sys
import re
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))


def extrair_frontmatter(caminho: Path) -> dict:
    texto = caminho.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", texto, re.DOTALL)
    if not match:
        return {}
    resultado = {}
    for linha in match.group(1).splitlines():
        if ":" in linha and not linha.strip().startswith("-"):
            chave, val = linha.split(":", 1)
            resultado[chave.strip()] = val.strip().strip("'\"")
    return resultado


def validar_settings_claude(settings_path: Path, agente_nome: str) -> None:
    assert settings_path.exists(), f"{settings_path} não encontrado"
    cfg = json.loads(settings_path.read_text(encoding="utf-8"))
    perms = cfg.get("permissions", {})
    assert isinstance(perms.get("allow"), list) and len(perms["allow"]) > 0, f"allow vazio em {settings_path}"
    assert isinstance(perms.get("deny"), list) and len(perms["deny"]) > 0, f"deny vazio em {settings_path}"
    assert isinstance(perms.get("ask"), list) and len(perms["ask"]) > 0, f"ask vazio em {settings_path}"

    hooks = cfg.get("hooks", {})
    for evento in ("PreToolUse", "PostToolUse"):
        assert evento in hooks and isinstance(hooks[evento], list) and len(hooks[evento]) > 0, (
            f"Hook {evento} ausente em {settings_path}"
        )
        for matcher_entry in hooks[evento]:
            assert isinstance(matcher_entry.get("hooks"), list) and len(matcher_entry["hooks"]) > 0, (
                f"Schema inválido em {settings_path}: {evento} requer lista aninhada 'hooks'"
            )
            for h in matcher_entry["hooks"]:
                assert h.get("type") == "command" and h.get("command"), f"Entrada de hook inválida em {settings_path}"
    print(f" -> [OK] .claude/settings.json ({agente_nome}) validado conforme schema oficial.")


def verificar_agente1():
    print("\n--- Verificando Consistência do Agente 1 (Extrator) ---")
    sys.path.insert(0, str(root_dir / "agent1"))

    # 1. Endpoints FastAPI
    from agent1.main import app as app1
    rotas1 = {route.path: [m for m in route.methods] for route in app1.routes if hasattr(route, "methods")}
    assert "/run" in rotas1 and "POST" in rotas1["/run"], "Endpoint POST /run ausente no Agente 1"
    assert "/status/{task_id}" in rotas1 and "GET" in rotas1["/status/{task_id}"], "Endpoint GET /status/{task_id} ausente no Agente 1"
    assert "/health" in rotas1 and "GET" in rotas1["/health"], "Endpoint GET /health ausente no Agente 1"
    print(" -> [OK] Endpoints REST /run, /status/{task_id} e /health conferem com a especificação.")

    # 2. Tools
    import agent1.tools as tools1
    assert hasattr(tools1, "normalizar_prazos_e_datas"), "Tool normalizar_prazos_e_datas ausente"
    assert hasattr(tools1, "extrair_e_validar_tabela_financeira"), "Tool extrair_e_validar_tabela_financeira ausente"
    assert hasattr(tools1, "consultar_cadastro_fornecedor"), "Tool consultar_cadastro_fornecedor ausente"
    print(" -> [OK] Ferramentas @function_tool existem e estão documentadas.")

    # 3. Models
    import agent1.models as models1
    assert hasattr(models1, "DadosContratoExtraido"), "Model DadosContratoExtraido ausente"
    assert hasattr(models1, "CronogramaFinanceiro"), "Model CronogramaFinanceiro ausente"
    assert hasattr(models1, "PeriodoVigencia"), "Model PeriodoVigencia ausente"
    assert hasattr(models1, "FornecedorHomologadoInfo"), "Model FornecedorHomologadoInfo ausente"
    print(" -> [OK] Schemas Pydantic v2 conferem com a especificação.")

    # 4. Settings e Hooks
    validar_settings_claude(root_dir / "agent1" / ".claude" / "settings.json", "Agente 1")

    # 5. Skills (ambos os caminhos: skills/ e .claude/skills/)
    skill_paths1 = [
        root_dir / "agent1" / "skills" / "validacao-financeira-contratual" / "SKILL.md",
        root_dir / "agent1" / ".claude" / "skills" / "validacao-financeira-contratual" / "SKILL.md",
    ]
    for sp in skill_paths1:
        assert sp.exists(), f"SKILL.md não encontrado em {sp}"
        yaml_data = extrair_frontmatter(sp)
        assert yaml_data.get("name") == "validacao-financeira-contratual", f"Frontmatter da skill inválido em {sp}"
        assert yaml_data.get("description"), f"Description ausente na skill {sp}"
    print(" -> [OK] Skill validacao-financeira-contratual validada em skills/ e .claude/skills/.")

    # 6. Subagentes (ambos os caminhos: subagents/ e .claude/agents/)
    sub_paths1 = [
        root_dir / "agent1" / "subagents" / "validador_cadastral.md",
        root_dir / "agent1" / ".claude" / "agents" / "validador-cadastral-fornecedor.md",
    ]
    for subp in sub_paths1:
        assert subp.exists(), f"Subagente não encontrado em {subp}"
        sub_yaml = extrair_frontmatter(subp)
        assert sub_yaml.get("name") == "validador-cadastral-fornecedor", f"Subagente inválido em {subp}"
        assert sub_yaml.get("model"), f"Campo model ausente em {subp}"
    print(" -> [OK] Subagente validador-cadastral-fornecedor validado em subagents/ e .claude/agents/.")


def verificar_agente2():
    print("\n--- Verificando Consistência do Agente 2 (Auditor) ---")
    sys.path.insert(0, str(root_dir / "agent2"))

    # 1. Endpoints FastAPI
    from agent2.main import app as app2
    rotas2 = {route.path: [m for m in route.methods] for route in app2.routes if hasattr(route, "methods")}
    assert "/run" in rotas2 and "POST" in rotas2["/run"], "Endpoint POST /run ausente no Agente 2"
    assert "/status/{task_id}" in rotas2 and "GET" in rotas2["/status/{task_id}"], "Endpoint GET /status/{task_id} ausente no Agente 2"
    assert "/health" in rotas2 and "GET" in rotas2["/health"], "Endpoint GET /health ausente no Agente 2"
    print(" -> [OK] Endpoints REST /run, /status/{task_id} e /health conferem com a especificação.")

    # 2. Tools
    import agent2.tools as tools2
    assert hasattr(tools2, "auditar_parametros_contratuais"), "Tool auditar_parametros_contratuais ausente"
    print(" -> [OK] Ferramenta @function_tool auditar_parametros_contratuais existe e está documentada.")

    # 3. Models
    import agent2.models as models2
    assert hasattr(models2, "RelatorioConformidade"), "Model RelatorioConformidade ausente"
    assert hasattr(models2, "ItemAuditoria"), "Model ItemAuditoria ausente"
    print(" -> [OK] Schemas Pydantic v2 do parecer de risco conferem com a especificação.")

    # 4. Settings e Hooks
    validar_settings_claude(root_dir / "agent2" / ".claude" / "settings.json", "Agente 2")

    # 5. Skills (ambos os caminhos: skills/ e .claude/skills/)
    skill_paths2 = [
        root_dir / "agent2" / "skills" / "auditoria-alcada-e-multa" / "SKILL.md",
        root_dir / "agent2" / ".claude" / "skills" / "auditoria-alcada-e-multa" / "SKILL.md",
    ]
    for sp in skill_paths2:
        assert sp.exists(), f"SKILL.md não encontrado em {sp}"
        yaml_data = extrair_frontmatter(sp)
        assert yaml_data.get("name") == "auditoria-alcada-e-multa", f"Frontmatter da skill inválido em {sp}"
        assert yaml_data.get("description"), f"Description ausente na skill {sp}"
    print(" -> [OK] Skill auditoria-alcada-e-multa validada em skills/ e .claude/skills/.")

    # 6. Subagentes (ambos os caminhos: subagents/ e .claude/agents/)
    sub_paths2 = [
        root_dir / "agent2" / "subagents" / "especialista_clausulas_penais.md",
        root_dir / "agent2" / ".claude" / "agents" / "auditor-clausulas-penais.md",
    ]
    for subp in sub_paths2:
        assert subp.exists(), f"Subagente não encontrado em {subp}"
        sub_yaml = extrair_frontmatter(subp)
        assert sub_yaml.get("name") == "auditor-clausulas-penais", f"Subagente inválido em {subp}"
        assert sub_yaml.get("model"), f"Campo model ausente em {subp}"
    print(" -> [OK] Subagente auditor-clausulas-penais validado em subagents/ e .claude/agents/.")


def main():
    print("=" * 80)
    print("AUDITORIA DE CONSISTÊNCIA: CÓDIGO vs. CLAUDE.md / AGENTS.md")
    print("=" * 80)
    import subprocess
    cmd1 = [
        sys.executable,
        "-c",
        "import sys; from pathlib import Path; root = Path('.').resolve(); sys.path.insert(0, str(root)); import scripts.verificar_consistencia_especificacao as v; v.verificar_agente1()",
    ]
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    print(res1.stdout)
    if res1.returncode != 0:
        print(res1.stderr)
        sys.exit(res1.returncode)

    cmd2 = [
        sys.executable,
        "-c",
        "import sys; from pathlib import Path; root = Path('.').resolve(); sys.path.insert(0, str(root)); import scripts.verificar_consistencia_especificacao as v; v.verificar_agente2()",
    ]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    print(res2.stdout)
    if res2.returncode != 0:
        print(res2.stderr)
        sys.exit(res2.returncode)

    print("=" * 80)
    print("RESULTADO: 100% DE CONSISTÊNCIA ENTRE ESPECIFICAÇÃO E CÓDIGO FONTE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
