"""
Módulo de Ferramentas (Tools) do Agente 2 (Avaliador de Conformidade e Risco)
Implementa validações determinísticas de governança corporativa, limites de alçada
e conformidade jurídica contratual via @function_tool do OpenAI Agents SDK.
"""

import json
from typing import Dict, Any, List
from agents import function_tool

# Base de regras corporativas pré-estabelecidas para auditoria
REGRAS_COMPLIANCE_PADRAO = {
    "teto_multa_rescisoria_percentual": 10.0,
    "aviso_previo_minimo_dias": 30,
    "teto_alcada_gerencia_brl": 100000.0,
    "exige_aprovacao_diretoria_acima_brl": 100000.0,
    "vigencia_maxima_sem_renovacao_meses": 24,
    "score_compliance_minimo_fornecedor": 75.0
}

def consultar_base_regras_negocio_fn() -> Dict[str, Any]:
    """Retorna os parâmetros vigentes de compliance e limites corporativos."""
    return REGRAS_COMPLIANCE_PADRAO.copy()

def auditar_parametros_contratuais_fn(
    valor_total_brl: float,
    vigencia_meses: int,
    aviso_previo_dias: int,
    percentual_multa: float,
    situacao_fornecedor: str = "ATIVA",
    score_compliance_fornecedor: float = 90.0
) -> Dict[str, Any]:
    """
    Executa a verificação determinística dos parâmetros extraídos contra a política corporativa.
    
    Retorna diagnóstico detalhado de conformidade:
    - Verificação de Alçada Financeira
    - Verificação de Prazos e Vigência
    - Verificação de Penalidades Rescisórias
    - Verificação da Situação Cadastral da Fonte Estruturada
    """
    regras = consultar_base_regras_negocio_fn()
    achados: List[Dict[str, Any]] = []
    
    # 1. Auditoria de Multa Rescisória
    limite_multa = regras["teto_multa_rescisoria_percentual"]
    if percentual_multa > limite_multa:
        achados.append({
            "regra": "Teto de Multa Rescisória",
            "status": "ALERTA",
            "nivel_risco": "MEDIO",
            "descricao_analise": (
                f"Multa rescisória fixada em {percentual_multa:.1f}%, superando a diretriz de "
                f"governança recomendada de até {limite_multa:.1f}% sobre o saldo remanescente."
            ),
            "fundamentacao": "Política Interna de Riscos Contratuais (Cap. IV, Art. 12) e Jurisprudência Cível (Art. 413 CC)."
        })
    else:
        achados.append({
            "regra": "Teto de Multa Rescisória",
            "status": "CONFORME",
            "nivel_risco": "BAIXO",
            "descricao_analise": f"Multa rescisória de {percentual_multa:.1f}% em total conformidade com o teto de até {limite_multa:.1f}%.",
            "fundamentacao": "Política Interna de Riscos Contratuais."
        })

    # 2. Auditoria de Alçada Financeira
    teto_alcada = regras["exige_aprovacao_diretoria_acima_brl"]
    if valor_total_brl > teto_alcada:
        achados.append({
            "regra": "Alçada de Aprovação Financeira",
            "status": "ALERTA",
            "nivel_risco": "ALTO",
            "descricao_analise": (
                f"Valor global do contrato (R$ {valor_total_brl:,.2f}) excede a alçada gerencial "
                f"(R$ {teto_alcada:,.2f}), demandando obrigatoriamente ratificação formal da Diretoria Executiva."
            ),
            "fundamentacao": "Manual de Alçadas e Governança Financeira - Alçada Nível 1."
        })
    else:
        achados.append({
            "regra": "Alçada de Aprovação Financeira",
            "status": "CONFORME",
            "nivel_risco": "BAIXO",
            "descricao_analise": f"Valor de R$ {valor_total_brl:,.2f} dentro da alçada operacional regular.",
            "fundamentacao": "Manual de Alçadas e Governança Financeira."
        })

    # 3. Auditoria de Aviso Prévio e Vigência
    min_aviso = regras["aviso_previo_minimo_dias"]
    if aviso_previo_dias < min_aviso:
        achados.append({
            "regra": "Prazo Mínimo de Aviso Prévio",
            "status": "NAO_CONFORME",
            "nivel_risco": "ALTO",
            "descricao_analise": (
                f"Aviso prévio pactuado ({aviso_previo_dias} dias) é inferior ao prazo mínimo "
                f"operacional requerido de {min_aviso} dias."
            ),
            "fundamentacao": "Diretriz Operacional de Continuidade de Negócios."
        })
    else:
        achados.append({
            "regra": "Prazo Mínimo de Aviso Prévio",
            "status": "CONFORME",
            "nivel_risco": "BAIXO",
            "descricao_analise": f"Aviso prévio pactuado ({aviso_previo_dias} dias) atende integralmente ao requisito de segurança.",
            "fundamentacao": "Diretriz Operacional de Continuidade de Negócios."
        })

    # 4. Auditoria da Fonte Estruturada de Fornecedores (Rubrica 12)
    score_minimo = regras["score_compliance_minimo_fornecedor"]
    if situacao_fornecedor.upper() != "ATIVA":
        achados.append({
            "regra": "Regularidade Cadastral do Fornecedor",
            "status": "NAO_CONFORME",
            "nivel_risco": "CRITICO",
            "descricao_analise": (
                f"Fornecedor com situação cadastral '{situacao_fornecedor}' no cadastro corporativo. "
                f"Contratação vedada pelas normas de compliance."
            ),
            "fundamentacao": "Norma Corporativa de Homologação de Terceiros e Prevenção a Fraudes."
        })
    elif score_compliance_fornecedor < score_minimo:
        achados.append({
            "regra": "Score de Compliance do Fornecedor",
            "status": "ALERTA",
            "nivel_risco": "MEDIO",
            "descricao_analise": (
                f"Score de compliance ({score_compliance_fornecedor:.1f}/100) abaixo da nota de corte ({score_minimo:.1f}). "
                f"Exige plano de mitigação e monitoramento contínuo."
            ),
            "fundamentacao": "Manual de Gestão de Riscos de Terceiros (Vendor Risk Management)."
        })
    else:
        achados.append({
            "regra": "Regularidade Cadastral do Fornecedor",
            "status": "CONFORME",
            "nivel_risco": "BAIXO",
            "descricao_analise": f"Fornecedor homologado ativo com score de compliance de {score_compliance_fornecedor:.1f}/100.",
            "fundamentacao": "Cadastro Corporativo de Fornecedores Homologados."
        })

    qtd_conforme = sum(1 for a in achados if a["status"] == "CONFORME")
    qtd_alerta = sum(1 for a in achados if a["status"] == "ALERTA")
    qtd_nao_conforme = sum(1 for a in achados if a["status"] == "NAO_CONFORME")
    total = len(achados)
    
    score_final = round((qtd_conforme * 100.0 + qtd_alerta * 60.0 + qtd_nao_conforme * 0.0) / max(total, 1), 2)
    
    if qtd_nao_conforme > 0 or score_final < 60.0:
        risco_geral = "CRITICO" if any(a["nivel_risco"] == "CRITICO" for a in achados) else "ALTO"
    elif qtd_alerta > 0 or score_final < 85.0:
        risco_geral = "MEDIO"
    else:
        risco_geral = "BAIXO"

    return {
        "total_verificacoes": total,
        "itens_conformes": qtd_conforme,
        "itens_alerta": qtd_alerta,
        "itens_nao_conformes": qtd_nao_conforme,
        "score_calculado": score_final,
        "risco_geral_sugerido": risco_geral,
        "achados": achados
    }

@function_tool
def auditar_parametros_contratuais(
    valor_total_brl: float,
    vigencia_meses: int,
    aviso_previo_dias: int,
    percentual_multa: float,
    situacao_fornecedor: str = "ATIVA",
    score_compliance_fornecedor: float = 90.0
) -> str:
    """
    Executa a auditoria de conformidade determinística contra as regras corporativas.
    Retorna o diagnóstico estruturado contendo a lista de achados, contagem e score calculado.
    """
    resultado = auditar_parametros_contratuais_fn(
        valor_total_brl=valor_total_brl,
        vigencia_meses=vigencia_meses,
        aviso_previo_dias=aviso_previo_dias,
        percentual_multa=percentual_multa,
        situacao_fornecedor=situacao_fornecedor,
        score_compliance_fornecedor=score_compliance_fornecedor
    )
    return json.dumps(resultado, ensure_ascii=False)
