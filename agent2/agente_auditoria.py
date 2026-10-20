"""
Motor do Agente 2: Avaliador de Conformidade e Risco Contratual
Recebe o payload estruturado (saída do Agente 1 repassada pelo n8n)
e aplica a suíte de auditoria determinística e compilação do relatório Pydantic v2.
"""

from typing import Dict, Any, List
from models import RelatorioConformidade, ItemAuditoria, NivelRisco, StatusConformidade
from tools import auditar_parametros_contratuais_fn


def avaliar_conformidade_contrato(dados_contrato: Dict[str, Any]) -> RelatorioConformidade:
    """
    Executa a auditoria completa de risco e conformidade sobre os dados do contrato.
    Retorna o modelo fortemente tipado RelatorioConformidade.
    """
    titulo = dados_contrato.get("titulo", "Contrato sem título")
    
    # Extrai com fallbacks seguros os valores numéricos essenciais
    financeiro = dados_contrato.get("financeiro", {})
    valor_total = float(financeiro.get("valor_total_brl", 0.0))
    
    vigencia = dados_contrato.get("vigencia", {})
    vigencia_meses = int(vigencia.get("vigencia_meses", 12))
    aviso_previo = int(vigencia.get("aviso_previo_dias", 30))
    
    penalidades = dados_contrato.get("penalidades", {})
    percentual_multa = float(penalidades.get("percentual_multa_rescisoria", 10.0))
    
    # Aciona a tool de verificação determinística
    resultado_auditoria = auditar_parametros_contratuais_fn(
        valor_total_brl=valor_total,
        vigencia_meses=vigencia_meses,
        aviso_previo_dias=aviso_previo,
        percentual_multa=percentual_multa
    )
    
    achados_brutos = resultado_auditoria["achados"]
    itens_auditados: List[ItemAuditoria] = []
    
    qtd_conforme = 0
    qtd_alerta = 0
    qtd_nao_conforme = 0
    recomendacoes: List[str] = []
    
    for item in achados_brutos:
        status_enum = StatusConformidade(item["status"])
        risco_enum = NivelRisco(item["nivel_risco"])
        
        if status_enum == StatusConformidade.CONFORME:
            qtd_conforme += 1
        elif status_enum == StatusConformidade.ALERTA:
            qtd_alerta += 1
            if "Multa" in item["regra"]:
                recomendacoes.append("Negociar redução da cláusula penal para o patamar padrão de até 10%.")
            if "Alçada" in item["regra"]:
                recomendacoes.append("Submeter o contrato à assinatura conjunta da Diretoria Executiva.")
        else:
            qtd_nao_conforme += 1
            recomendacoes.append(f"Ajustar imediatamente a cláusula de {item['regra']} para atender às diretrizes.")
            
        itens_auditados.append(ItemAuditoria(
            regra=item["regra"],
            status=status_enum,
            nivel_risco=risco_enum,
            descricao_analise=item["descricao_analise"],
            fundamentacao=item["fundamentacao"]
        ))
        
    total_regras = len(itens_auditados)
    
    # Cálculo ponderado do score de conformidade (0 a 100)
    # Conforme: peso 1.0, Alerta: peso 0.6, Não Conforme: peso 0.0
    pontos = (qtd_conforme * 100.0 + qtd_alerta * 60.0 + qtd_nao_conforme * 0.0)
    score_final = round(pontos / max(total_regras, 1), 2)
    
    # Determinação do nível de risco geral consolidado
    if qtd_nao_conforme > 0 or score_final < 60.0:
        risco_geral = NivelRisco.ALTO
    elif qtd_alerta > 0 or score_final < 85.0:
        risco_geral = NivelRisco.MEDIO
    else:
        risco_geral = NivelRisco.BAIXO

    # Geração do parecer executivo em Markdown
    parecer_md = f"""# Parecer de Conformidade e Risco Contratual
**Instrumento:** {titulo}  
**Score de Compliance:** {score_final} / 100.0  
**Classificação de Risco:** {risco_geral.value}  

## Sumário Executivo
O contrato foi submetido à auditoria automática contra a matriz de regras corporativas. Foram avaliadas {total_regras} dimensões críticas:
- **Itens Conformes:** {qtd_conforme}
- **Itens em Alerta / Mitigação:** {qtd_alerta}
- **Itens Não Conformes:** {qtd_nao_conforme}

## Principais Recomendações
""" + "\n".join([f"- {rec}" for rec in recomendacoes])

    return RelatorioConformidade(
        contrato_titulo=titulo,
        score_conformidade=score_final,
        nivel_risco_geral=risco_geral,
        total_regras_auditadas=total_regras,
        itens_conformes=qtd_conforme,
        itens_alerta=qtd_alerta,
        itens_nao_conformes=qtd_nao_conforme,
        itens_auditados=itens_auditados,
        recomendacoes_mitigacao=recomendacoes,
        parecer_executivo_markdown=parecer_md
    )
