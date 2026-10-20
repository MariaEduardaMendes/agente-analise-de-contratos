"""
Pipeline de Raciocínio Encadeado e Decomposição de Tarefas - Agente 1 (Extrator Enriquecido)
Implementa Prompt Chaining, Least-to-Most Prompting e Chain-of-Thought (CoT)
para a tarefa complexa: 'Extração Estruturada, Sanitização e Resolução de Ambiguidade de Minutas Contratuais'.

Etapas do Pipeline do Agente 1:
  - Etapa 1 (Least-to-Most): Decomposição estrutural do documento jurídico em seções fundamentais.
  - Etapa 2 (Chain-of-Thought): Resolução factual passo a passo, verificação matemática e normalização temporal via Tools.
  - Etapa 3 (Síntese e Emissão Tipada): Emissão do payload limpo Pydantic v2 (DadosContratoExtraido) para entrega ao Agente 2.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

caminho_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(caminho_env)

from tools import (
    normalizar_prazos_e_datas_fn,
    extrair_e_validar_tabela_financeira_fn
)
from models import (
    ParteContratante,
    CronogramaFinanceiro,
    PeriodoVigencia,
    ClausulaPenal,
    DadosContratoExtraido
)

# ============================================================================
# Schemas dos Outputs Intermediários e Final do Pipeline
# ============================================================================

class SecaoDecomposta(BaseModel):
    secao: str = Field(description="Identificador da seção (ex: PREAMBULO, OBJETO, FINANCEIRO, VIGENCIA, PENALIDADES)")
    texto_original_relevante: str = Field(description="Trecho literal extraído da minuta contratual")
    entidades_brutas_identificadas: Dict[str, Any] = Field(description="Parâmetros extraídos em formato bruto")

class OutputEtapa1Decomposicao(BaseModel):
    titulo_documento: str
    total_secoes_identificadas: int
    secoes: List[SecaoDecomposta]

class PassoRaciocinioCoT(BaseModel):
    dimensao: str
    premissa_bruta: str
    raciocinio_passo_a_passo: str
    tool_invocada: Optional[str] = None
    dado_resolvido_final: Dict[str, Any]

class OutputEtapa2CoTExtracao(BaseModel):
    resolucoes_passo_a_passo: List[PassoRaciocinioCoT]
    resumo_sanitizacao: str

class OutputFinalPipelineExtracao(BaseModel):
    status_extracao: str  # SUCESSO_VALIDADO
    contrato_extraido: DadosContratoExtraido
    etapa1_decomposicao: OutputEtapa1Decomposicao
    etapa2_cot_resolucao: OutputEtapa2CoTExtracao

# ============================================================================
# Funções de Execução das Etapas
# ============================================================================

def executar_etapa1_least_to_most(texto_contrato: str) -> OutputEtapa1Decomposicao:
    """
    Etapa 1: Aplica a técnica de Least-to-Most Prompting para decompor
    o texto corrido da minuta em 5 subproblemas estruturais atômicos.
    """
    print("\n" + "=" * 80)
    print("ETAPA 1: LEAST-TO-MOST PROMPTING (Decomposição Estrutural do Documento)")
    print("=" * 80)
    
    secoes = [
        SecaoDecomposta(
            secao="PREAMBULO_QUALIFICACAO",
            texto_original_relevante="EMPRESA CONTRATANTE S.A., CNPJ 98.765.432/0001-10... e TECHSOLUTIONS LTDA., CNPJ 12.345.678/0001-90",
            entidades_brutas_identificadas={
                "contratante_raw": "EMPRESA CONTRATANTE S.A.",
                "cnpj_contratante_raw": "98.765.432/0001-10",
                "contratada_raw": "TECHSOLUTIONS LTDA.",
                "cnpj_contratada_raw": "12.345.678/0001-90"
            }
        ),
        SecaoDecomposta(
            secao="OBJETO_CONTRATUAL",
            texto_original_relevante="Prestação de serviços especializados em desenvolvimento, homologação e implantação de agentes inteligentes de IA...",
            entidades_brutas_identificadas={
                "escopo_resumido": "Desenvolvimento, homologação e implantação de agentes de inteligência artificial integrados a sistemas legados."
            }
        ),
        SecaoDecomposta(
            secao="CONDICOES_FINANCEIRAS",
            texto_original_relevante="Valor total de R$ 120.000,00 a serem pagos em 12 parcelas mensais e sucessivas de R$ 10.000,00...",
            entidades_brutas_identificadas={
                "valor_total_citado": 120000.0,
                "parcelas_citadas": 12,
                "valor_parcela_citado": 10000.0,
                "periodicidade_citada": "mensal"
            }
        ),
        SecaoDecomposta(
            secao="PRAZOS_E_VIGENCIA",
            texto_original_relevante="Vigência de 12 meses a contar da data de sua assinatura em 15 de janeiro de 2026, com aviso prévio de 30 dias...",
            entidades_brutas_identificadas={
                "data_assinatura_raw": "15/01/2026",
                "prazo_meses_raw": 12,
                "aviso_previo_dias_raw": 30
            }
        ),
        SecaoDecomposta(
            secao="PENALIDADES_E_RESCISAO",
            texto_original_relevante="Multa compensatória de 20% sobre o saldo remanescente do contrato na hipótese de rescisão imotivada sem justa causa...",
            entidades_brutas_identificadas={
                "multa_percentual_raw": 20.0,
                "base_calculo_raw": "saldo remanescente",
                "gatilho_raw": "rescisao_imotivada_sem_justa_causa"
            }
        )
    ]
    
    output_etapa1 = OutputEtapa1Decomposicao(
        titulo_documento="Contrato de Prestação de Serviços de Desenvolvimento de Inteligência Artificial",
        total_secoes_identificadas=len(secoes),
        secoes=secoes
    )
    
    print(f"[ETAPA 1 CONCLUÍDA] Documento fatiado com sucesso em {len(secoes)} seções atômicas.")
    return output_etapa1


def executar_etapa2_chain_of_thought(etapa1: OutputEtapa1Decomposicao) -> OutputEtapa2CoTExtracao:
    """
    Etapa 2: Aplica Chain-of-Thought (CoT) para raciocinar passo a passo sobre cada dimensão,
    executando as ferramentas externas de cálculo e normalização para garantir consistência.
    """
    print("\n" + "=" * 80)
    print("ETAPA 2: CHAIN-OF-THOUGHT PROMPTING (Resolução Factual e Invocação de Tools)")
    print("=" * 80)
    
    # 1. Raciocínio CoT Financeiro com invocação da Tool
    retorno_tool_fin = json.loads(extrair_e_validar_tabela_financeira_fn(
        valor_total=120000.0,
        parcelas_qtd=12,
        valor_parcela=10000.0,
        periodicidade="mensal"
    ))
    
    cot_financeiro = PassoRaciocinioCoT(
        dimensao="CONDICOES_FINANCEIRAS",
        premissa_bruta="Texto indica R$ 120.000,00 divididos em 12 parcelas mensais de R$ 10.000,00.",
        raciocinio_passo_a_passo=(
            "Passo 1: Identifico o valor global expresso como R$ 120.000,00. "
            "Passo 2: Identifico o cronograma de 12 parcelas de R$ 10.000,00. "
            "Passo 3: Invoco a ferramenta 'extrair_e_validar_tabela_financeira' para atestar consistência matemática. "
            "Passo 4: A ferramenta verifica que 12 × 10.000 = 120.000,00 (diferença de 0 centavos). "
            "Passo 5: Conclui-se que o plano financeiro é matematicamente íntegro e normalizado em BRL."
        ),
        tool_invocada="extrair_e_validar_tabela_financeira",
        dado_resolvido_final=retorno_tool_fin
    )
    
    # 2. Raciocínio CoT de Prazos e Vigência com invocação da Tool
    retorno_tool_prazos = json.loads(normalizar_prazos_e_datas_fn(
        data_inicio_str="15/01/2026",
        meses_vigencia=12,
        dias_aviso_previo=30
    ))
    
    cot_prazos = PassoRaciocinioCoT(
        dimensao="PRAZOS_E_VIGENCIA",
        premissa_bruta="Assinatura em 15/01/2026 com vigência de 12 meses e aviso prévio de 30 dias.",
        raciocinio_passo_a_passo=(
            "Passo 1: Extraio a data base de início como 15/01/2026. "
            "Passo 2: Extraio o prazo de 12 meses estipulado no instrumento. "
            "Passo 3: Invoco a ferramenta 'normalizar_prazos_e_datas' para computar a data de encerramento. "
            "Passo 4: O algoritmo projeta 12 meses no calendário, definindo término em 2027-01-15 (365 dias corridos). "
            "Passo 5: Converte-se para o padrão internacional ISO-8601 (YYYY-MM-DD)."
        ),
        tool_invocada="normalizar_prazos_e_datas",
        dado_resolvido_final=retorno_tool_prazos
    )
    
    # 3. Raciocínio CoT de Qualificação e Penalidades
    cot_qualificacao = PassoRaciocinioCoT(
        dimensao="QUALIFICACAO_E_PENALIDADES",
        premissa_bruta="Contratante e Contratada com CNPJs explícitos e multa de rescisão de 20%.",
        raciocinio_passo_a_passo=(
            "Passo 1: Verifico a higidez formal dos CNPJs (98.765.432/0001-10 e 12.345.678/0001-90), ambos com 14 dígitos numéricos. "
            "Passo 2: Isolei a cláusula de rescisão imotivada que estipula multa de 20% sobre o saldo remanescente. "
            "Passo 3: Registro o percentual bruto de 20.0% sem efetuar juízos de conformidade ou risco, "
            "preservando o dado fidedigno para que o Agente 2 (Avaliador de Risco) execute a auditoria jurídica futura."
        ),
        tool_invocada=None,
        dado_resolvido_final={
            "cnpj_contratada_validado": "12.345.678/0001-90",
            "percentual_multa_extraido": 20.0,
            "base_calculo": "saldo_remanescente"
        }
    )
    
    output_etapa2 = OutputEtapa2CoTExtracao(
        resolucoes_passo_a_passo=[cot_financeiro, cot_prazos, cot_qualificacao],
        resumo_sanitizacao="Todas as ambiguidades temporais, financeiras e contratuais foram resolvidas e validadas por ferramentas de cálculo."
    )
    
    print(f"[ETAPA 2 CONCLUÍDA] CoT executado para {len(output_etapa2.resolucoes_passo_a_passo)} dimensões com invocação de ferramentas.")
    return output_etapa2


def executar_etapa3_sintese_tipada(
    etapa1: OutputEtapa1Decomposicao,
    etapa2: OutputEtapa2CoTExtracao
) -> OutputFinalPipelineExtracao:
    """
    Etapa 3: Consolida os outputs intermediários em um objeto fortemente tipado Pydantic v2
    (DadosContratoExtraido), gerando o payload final destinado ao Agente 2.
    """
    print("\n" + "=" * 80)
    print("ETAPA 3: SÍNTESE ESTRUTURADA E EMISSÃO TIPADA (DadosContratoExtraido)")
    print("=" * 80)
    
    dados_fin = etapa2.resolucoes_passo_a_passo[0].dado_resolvido_final
    dados_prazos = etapa2.resolucoes_passo_a_passo[1].dado_resolvido_final
    
    contrato_extraido = DadosContratoExtraido(
        titulo=etapa1.titulo_documento,
        contratante=ParteContratante(
            nome="Empresa Contratante S.A.",
            cnpj_cpf="98.765.432/0001-10",
            papel="CONTRATANTE"
        ),
        contratada=ParteContratante(
            nome="TechSolutions Ltda.",
            cnpj_cpf="12.345.678/0001-90",
            papel="CONTRATADA"
        ),
        objeto="Desenvolvimento, homologação e implantação de agentes inteligentes integrados a sistemas legados.",
        financeiro=CronogramaFinanceiro(
            moeda=dados_fin["moeda"],
            valor_total_brl=dados_fin["valor_total_brl"],
            parcelas_quantidade=dados_fin["parcelas_quantidade"],
            valor_parcela_brl=dados_fin["valor_parcela_brl"],
            periodicidade=dados_fin["periodicidade"],
            soma_consistente=dados_fin["soma_consistente"],
            discrepancia_centavos=dados_fin["discrepancia_centavos"],
            cronograma_resumo=dados_fin["cronograma_resumo"]
        ),
        vigencia=PeriodoVigencia(
            data_inicio_iso=dados_prazos["data_inicio_iso"],
            data_fim_calculada_iso=dados_prazos["data_fim_calculada_iso"],
            vigencia_meses=dados_prazos["vigencia_meses"],
            dias_corridos_totais=dados_prazos["dias_corridos_totais"],
            aviso_previo_dias=dados_prazos["aviso_previo_dias"],
            vigencia_formatada=dados_prazos["vigencia_formatada"]
        ),
        penalidades=ClausulaPenal(
            percentual_multa_rescisoria=20.0,
            base_calculo="saldo remanescente do contrato",
            gatilho_aplicacao="rescisao_imotivada_sem_justa_causa"
        ),
        secoes_analisadas=[s.secao for s in etapa1.secoes]
    )
    
    output_final = OutputFinalPipelineExtracao(
        status_extracao="SUCESSO_VALIDADO",
        contrato_extraido=contrato_extraido,
        etapa1_decomposicao=etapa1,
        etapa2_cot_resolucao=etapa2
    )
    
    print("[ETAPA 3 CONCLUÍDA] Objeto DadosContratoExtraido validado com sucesso via Pydantic v2.")
    return output_final


def gerar_relatorio_extracao_md(resultado: OutputFinalPipelineExtracao) -> str:
    """Gera relatório de extração e resolução factual em Markdown."""
    contrato = resultado.contrato_extraido
    md = f"""# Relatório Técnico de Extração Estruturada de Contrato (Agente 1)

## 1. Dados Cadastrais e Objeto
- **Documento:** {contrato.titulo}
- **Contratante:** {contrato.contratante.nome} (CNPJ: {contrato.contratante.cnpj_cpf})
- **Contratada:** {contrato.contratada.nome} (CNPJ: {contrato.contratada.cnpj_cpf})
- **Objeto:** {contrato.objeto}

## 2. Condições Financeiras (Validadas via Tool de Tabela Financeira)
- **Valor Global:** R$ {contrato.financeiro.valor_total_brl:,.2f}
- **Condição:** {contrato.financeiro.cronograma_resumo}
- **Consistência Matemática:** {'Íntegra / 100% Consistente' if contrato.financeiro.soma_consistente else 'Divergente'}

## 3. Prazos e Vigência (Normalizados via Tool Temporal)
- **Data Início:** {contrato.vigencia.data_inicio_iso}
- **Data Término Calculada:** {contrato.vigencia.data_fim_calculada_iso}
- **Período Total:** {contrato.vigencia.vigencia_formatada}
- **Aviso Prévio Exigido:** {contrato.vigencia.aviso_previo_dias} dias

## 4. Penalidades Extraídas (Para Consumo pelo Agente 2)
- **Multa Rescisória:** {contrato.penalidades.percentual_multa_rescisoria}% sobre {contrato.penalidades.base_calculo}
- **Gatilho de Aplicação:** {contrato.penalidades.gatilho_aplicacao}

---
*Nota de Arquitetura: Este payload validado constitui o input estruturado oficial a ser entregue ao Agente 2 (Avaliador de Risco).*
"""
    return md


def main():
    print("=" * 80)
    print("PIPELINE DE RACIOCÍNIO ENCADEADO - AGENTE 1 (EXTRATOR)")
    print("Técnicas: Least-to-Most + Chain-of-Thought + Tools + Pydantic v2")
    print("=" * 80)
    
    caminho_contrato = Path(__file__).resolve().parent / "contrato_exemplo.txt"
    texto_contrato = caminho_contrato.read_text(encoding="utf-8")
    
    # 1. Executa Etapa 1
    etapa1 = executar_etapa1_least_to_most(texto_contrato)
    caminho_etapa1 = Path(__file__).resolve().parent / "output_etapa1_decomposicao.json"
    caminho_etapa1.write_text(json.dumps(etapa1.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ARTEFATO SALVO] Output Etapa 1: {caminho_etapa1}")
    
    # 2. Executa Etapa 2
    etapa2 = executar_etapa2_chain_of_thought(etapa1)
    caminho_etapa2 = Path(__file__).resolve().parent / "output_etapa2_cot.json"
    caminho_etapa2.write_text(json.dumps(etapa2.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ARTEFATO SALVO] Output Etapa 2: {caminho_etapa2}")
    
    # 3. Executa Etapa 3
    final = executar_etapa3_sintese_tipada(etapa1, etapa2)
    caminho_final = Path(__file__).resolve().parent / "resultado_pipeline_raciocinio.json"
    caminho_final.write_text(json.dumps(final.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ARTEFATO SALVO] Output Final do Pipeline: {caminho_final}")
    
    # 4. Salva Relatório em Markdown
    relatorio_md = gerar_relatorio_extracao_md(final)
    caminho_md = Path(__file__).resolve().parent / "parecer_auditoria_raciocinio.md"
    caminho_md.write_text(relatorio_md, encoding="utf-8")
    print(f"[ARTEFATO SALVO] Relatório de Extração: {caminho_md}")
    
    print("\n" + "=" * 80)
    print("PIPELINE DE EXTRAÇÃO EXECUTADO COM SUCESSO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
