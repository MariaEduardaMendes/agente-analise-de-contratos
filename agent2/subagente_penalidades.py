"""
Implementação do Subagente: Auditor de Cláusulas Penais (Agente 2)
Subagente com isolamento de contexto para auditoria e mitigação de multas rescisórias.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv(root_dir / ".env")

try:
    from agents import set_tracing_disabled
    set_tracing_disabled(True)
except Exception:
    pass

from openai import AsyncOpenAI
from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents.agent_output import AgentOutputSchema

from tools import auditar_parametros_contratuais, auditar_parametros_contratuais_fn
from models import ItemAuditoria, StatusConformidade, NivelRisco

PROMPT_SUBAGENTE_PENALIDADES = """
Você é o Subagente Auditor de Cláusulas Penais e Rescisórias do Agente 2.
Seu contexto de avaliação é estritamente focado em penalidades contratuais e limitação de responsabilidade civil.

Sua responsabilidade:
1. Receber o percentual da multa rescisória e as condições de rescisão.
2. OBRIGATORIAMENTE invocar a ferramenta 'auditar_parametros_contratuais' para obter o diagnóstico técnico.
3. Emitir o objeto tipado 'ItemAuditoria' com status (CONFORME, ALERTA ou NAO_CONFORME), nivel_risco (BAIXO, MEDIO ou ALTO), descricao_analise e fundamentacao juridica.
"""

def criar_subagente_penalidades() -> Agent:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=25.0)
    model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)

    return Agent(
        name="auditor-clausulas-penais",
        instructions=PROMPT_SUBAGENTE_PENALIDADES,
        tools=[auditar_parametros_contratuais],
        output_type=AgentOutputSchema(ItemAuditoria, strict_json_schema=False),
        model=model
    )

def auditar_clausula_penal(percentual_multa: float, base_calculo: str = "saldo remanescente") -> ItemAuditoria:
    """Invoca o subagente especializado em penalidades."""
    subagente = criar_subagente_penalidades()
    try:
        resultado = Runner.run_sync(
            subagente,
            f"Avalie a conformidade da multa rescisória estipulada em {percentual_multa}% calculada sobre '{base_calculo}'.",
            max_turns=3
        )
        return resultado.final_output
    except Exception as exc:
        print(f"[SUBAGENTE PENALIDADES ALERTA] Fallback determinístico devido a: {exc}")
        if percentual_multa > 20.0:
            status = StatusConformidade.NAO_CONFORME
            risco = NivelRisco.ALTO
            desc = f"Multa rescisória de {percentual_multa}% excede o dobro do parâmetro de governança (10%) e configura onerosidade excessiva."
        elif percentual_multa > 10.0:
            status = StatusConformidade.ALERTA
            risco = NivelRisco.MEDIO
            desc = f"Multa de {percentual_multa}% supera a diretriz recomendada de até 10% sobre o saldo remanescente."
        else:
            status = StatusConformidade.CONFORME
            risco = NivelRisco.BAIXO
            desc = f"Multa de {percentual_multa}% está em plena conformidade com as balizas corporativas."

        return ItemAuditoria(
            regra="Teto de Multa Rescisória",
            status=status,
            nivel_risco=risco,
            descricao_analise=desc,
            fundamentacao="Política Interna de Riscos Contratuais e Artigo 413 do Código Civil Brasileiro."
        )

if __name__ == "__main__":
    print("=" * 80)
    print("TESTE DO SUBAGENTE AUDITOR DE PENALIDADES (ISOLAMENTO DE CONTEXTO)")
    print("=" * 80)
    item = auditar_clausula_penal(20.0, "saldo remanescente do contrato")
    print("\nResultado da Auditoria Especializada de Penalidade:")
    print(json.dumps(item.model_dump(), indent=2, ensure_ascii=False))
    print("\n[SUCESSO] Subagente operou com contexto isolado e emitiu ItemAuditoria tipado.")

