"""
Motor do Agente 2: Avaliador de Conformidade e Risco Contratual
Desenvolvido com OpenAI Agents SDK (@function_tool, Agent, Runner e validação Pydantic v2).

Recebe o payload estruturado (saída do Agente 1 repassada pelo n8n)
e aciona um Agent inteligente que invoca a tool de auditoria @function_tool
e compila o relatório executivo fortemente tipado em RelatorioConformidade.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

caminho_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(caminho_env)

# Garante path de importação para a pasta agent2
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Desabilita telemetria interna da OpenAI para evitar 401
try:
    from agents import set_tracing_disabled
    set_tracing_disabled(True)
except Exception:
    pass

from openai import AsyncOpenAI
from agents import Agent, Runner, AgentOutputSchema
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

from models import RelatorioConformidade, ItemAuditoria, NivelRisco, StatusConformidade
from tools import auditar_parametros_contratuais, auditar_parametros_contratuais_fn

PROMPT_SISTEMA_AGENTE_AUDITOR = """
### 1. INSTRUÇÃO (Role & Task)
Você é o Agente 2 (Avaliador de Conformidade e Risco Contratual), especialista em Auditoria Jurídica e Governança Corporativa.
Sua missão estrita é:
1. Analisar os dados estruturados do contrato recebidos no input (título, valores, vigência, multas, dados cadastrais).
2. OBRIGATORIAMENTE invocar a ferramenta Python 'auditar_parametros_contratuais' passando:
   - valor_total_brl: valor total do contrato
   - vigencia_meses: vigência em meses
   - aviso_previo_dias: dias de aviso prévio
   - percentual_multa: percentual da multa rescisória
   - situacao_fornecedor: situação cadastral do fornecedor (se houver, default 'ATIVA')
   - score_compliance_fornecedor: score do fornecedor (se houver, default 90.0)
3. Com base no diagnóstico retornado pela ferramenta, preencha o schema RelatorioConformidade:
   - total_regras_auditadas DEVE ser exatamente igual a (itens_conformes + itens_alerta + itens_nao_conformes).
   - popule 'itens_auditados' com os achados retornados.
   - elabore 'recomendacoes_mitigacao' claras e práticas para os pontos de atenção.
   - elabore um parecer executivo formal completo e bem formatado em 'parecer_executivo_markdown'.
"""

def criar_modelo_llm() -> OpenAIChatCompletionsModel:
    """Instancia o modelo LLM conectado ao OpenRouter."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=30.0)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)

def criar_agente_auditor() -> Agent:
    """Cria a instância do Agente 2 com tools e schema de saída tipada RelatorioConformidade."""
    model = criar_modelo_llm()
    return Agent(
        name="AgenteAuditoriaRisco",
        instructions=PROMPT_SISTEMA_AGENTE_AUDITOR,
        tools=[auditar_parametros_contratuais],
        output_type=AgentOutputSchema(RelatorioConformidade, strict_json_schema=False),
        model=model
    )

def avaliar_conformidade_contrato(dados_contrato: Dict[str, Any]) -> RelatorioConformidade:
    """
    Executa a auditoria completa de risco e conformidade sobre os dados do contrato.
    Aciona o Agent de auditoria via Runner.run com a tool auditar_parametros_contratuais
    e retorna o modelo fortemente tipado RelatorioConformidade.
    """
    print("\n[AGENTE 2] Iniciando processo de auditoria de conformidade e risco com LLM real...", flush=True)
    
    agente = criar_agente_auditor()
    payload_str = json.dumps(dados_contrato, ensure_ascii=False, indent=2)
    
    prompt_usuario = (
        f"Por favor, realize a auditoria de conformidade e risco contratual com base nos "
        f"dados estruturados a seguir:\n\n{payload_str}"
    )
    
    try:
        resultado = Runner.run_sync(agente, prompt_usuario)
        relatorio: RelatorioConformidade = resultado.final_output
        if relatorio.score_conformidade <= 0.0 and relatorio.total_regras_auditadas > 0:
            relatorio.score_conformidade = round(
                (relatorio.itens_conformes * 100.0 + relatorio.itens_alerta * 60.0) / max(relatorio.total_regras_auditadas, 1),
                2
            )
        print(f"[AGENTE 2] Auditoria finalizada com sucesso via LLM! Score: {relatorio.score_conformidade} | Risco: {relatorio.nivel_risco_geral.value}", flush=True)
        return relatorio
    except Exception as e:
        print(f"[AGENTE 2 ALERTA] Falha na execução do LLM ({e}). Aplicando resolução direta via tools...", flush=True)
        # Fallback determinístico seguro utilizando a mesma tool nativa
        financeiro = dados_contrato.get("financeiro", {})
        valor_total = float(financeiro.get("valor_total_brl", 0.0))
        vigencia = dados_contrato.get("vigencia", {})
        vigencia_meses = int(vigencia.get("vigencia_meses", 12))
        aviso_previo = int(vigencia.get("aviso_previo_dias", 30))
        penalidades = dados_contrato.get("penalidades", {})
        percentual_multa = float(penalidades.get("percentual_multa_rescisoria", 10.0))
        
        forn = dados_contrato.get("fornecedor_homologado") or {}
        sit_forn = forn.get("situacao_cadastral", "ATIVA")
        score_forn = float(forn.get("score_compliance", 90.0))

        audit = auditar_parametros_contratuais_fn(
            valor_total_brl=valor_total,
            vigencia_meses=vigencia_meses,
            aviso_previo_dias=aviso_previo,
            percentual_multa=percentual_multa,
            situacao_fornecedor=sit_forn,
            score_compliance_fornecedor=score_forn
        )

        itens: List[ItemAuditoria] = [
            ItemAuditoria(
                regra=a["regra"],
                status=StatusConformidade(a["status"]),
                nivel_risco=NivelRisco(a["nivel_risco"]),
                descricao_analise=a["descricao_analise"],
                fundamentacao=a["fundamentacao"]
            )
            for a in audit["achados"]
        ]

        recoms = [
            f"Adequar {it.regra}: {it.descricao_analise}"
            for it in itens if it.status != StatusConformidade.CONFORME
        ] or ["Contrato em conformidade plena com as políticas corporativas."]

        parecer_md = f"""# Parecer de Conformidade e Risco Contratual
**Instrumento:** {dados_contrato.get('titulo', 'Contrato')}  
**Score de Compliance:** {audit['score_calculado']} / 100.0  
**Classificação de Risco:** {audit['risco_geral_sugerido']}  

## Sumário Executivo
- Regras Auditadas: {audit['total_verificacoes']}
- Conformes: {audit['itens_conformes']}
- Alerta: {audit['itens_alerta']}
- Não Conformes: {audit['itens_nao_conformes']}

## Principais Recomendações
""" + "\n".join(f"- {r}" for r in recoms)

        return RelatorioConformidade(
            contrato_titulo=dados_contrato.get("titulo", "Contrato Analisado"),
            score_conformidade=audit["score_calculado"],
            nivel_risco_geral=NivelRisco(audit["risco_geral_sugerido"]),
            total_regras_auditadas=audit["total_verificacoes"],
            itens_conformes=audit["itens_conformes"],
            itens_alerta=audit["itens_alerta"],
            itens_nao_conformes=audit["itens_nao_conformes"],
            itens_auditados=itens,
            recomendacoes_mitigacao=recoms,
            parecer_executivo_markdown=parecer_md
        )

def main():
    print("=" * 80)
    print("AGENTE 2: MOTOR DE AUDITORIA DE CONFORMIDADE E RISCO CONTRATUAL")
    print("=" * 80)
    
    # Carrega output do Agente 1 para teste de encadeamento
    caminho_agente1 = Path(__file__).resolve().parent.parent / "agent1" / "resultado_extracao.json"
    if not caminho_agente1.exists():
        print(f"[ERRO] Arquivo {caminho_agente1} não encontrado. Execute o Agente 1 primeiro.")
        return
        
    dados_contrato = json.loads(caminho_agente1.read_text(encoding="utf-8"))
    relatorio = avaliar_conformidade_contrato(dados_contrato)
    
    print("\n--- RELATÓRIO DE CONFORMIDADE EMITIDO ---")
    print(f"Título: {relatorio.contrato_titulo}")
    print(f"Score: {relatorio.score_conformidade} / 100")
    print(f"Risco Geral: {relatorio.nivel_risco_geral.value}")
    print(f"Regras Auditadas: {relatorio.total_regras_auditadas} (Conformes: {relatorio.itens_conformes}, Alertas: {relatorio.itens_alerta}, Não-Conformes: {relatorio.itens_nao_conformes})")
    print(f"Total Recomendações: {len(relatorio.recomendacoes_mitigacao)}")
    
    # Salva resultado
    caminho_out = Path(__file__).resolve().parent / "resultado_auditoria.json"
    caminho_out.write_text(json.dumps(relatorio.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] Relatório salvo em: {caminho_out}")

if __name__ == "__main__":
    main()
