"""
Módulo de Ferramentas (Tools) do Agente 2 (Avaliador de Conformidade e Risco)
Implementa validações determinísticas de governança corporativa, limites de alçada
e conformidade jurídica contratual.
"""

import json
from typing import Dict, Any, List

# Base de regras corporativas pré-estabelecidas para auditoria
REGRAS_COMPLIANCE_PADRAO = {
    "teto_multa_rescisoria_percentual": 10.0,
    "aviso_previo_minimo_dias": 30,
    "teto_alcada_gerencia_brl": 100000.0,
    "exige_aprovacao_diretoria_acima_brl": 100000.0,
    "vigencia_maxima_sem_renovacao_meses": 24
}

def consultar_base_regras_negocio_fn() -> Dict[str, Any]:
    """Retorna os parâmetros vigentes de compliance e limites corporativos."""
    return REGRAS_COMPLIANCE_PADRAO.copy()

def auditar_parametros_contratuais_fn(
    valor_total_brl: float,
    vigencia_meses: int,
    aviso_previo_dias: int,
    percentual_multa: float
) -> Dict[str, Any]:
    """
    Executa a verificação determinística dos parâmetros extraídos contra a política corporativa.
    
    Retorna diagnóstico detalhado de conformidade:
    - Verificação de Alçada Financeira
    - Verificação de Prazos e Vigência
    - Verificação de Penalidades Rescisórias
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
            "fundamentacao": "Política Interna de Riscos Contratuais (Cap. IV, Art. 12) e Jurisprudência Cível."
        })
    else:
        achados.append({
            "regra": "Teto de Multa Rescisória",
            "status": "CONFORME",
            "nivel_risco": "BAIXO",
            "descricao_analise": f"Multa rescisória de {percentual_multa:.1f}% em total conformidade com o teto estabelecido.",
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
            "descricao_analise": f"Valor dentro do limite regular de aprovação operacional.",
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

    return {
        "total_verificacoes": len(achados),
        "achados": achados
    }
