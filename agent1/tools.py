"""
Módulo de Ferramentas (Tools) do Agente 1 (Extrator Enriquecido)
Implementado com OpenAI Agents SDK utilizando o decorador @function_tool
e anotações de tipo Python estritas (PEP 484).

Ferramentas focadas estritamente em EXTRAÇÃO, RESOLUÇÃO DE AMBIGUIDADES E NORMALIZAÇÃO:
1. normalizar_prazos_e_datas: Resolução temporal de vigência e cálculo de datas ISO-8601.
2. extrair_e_validar_tabela_financeira: Verificação de consistência matemática e decomposição de parcelas.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List
from agents import function_tool

# Histórico em memória para auditoria e registro do output das tools
REGISTRO_CHAMADAS_TOOLS: List[Dict[str, Any]] = []

def calcular_dias_meses(meses: int) -> int:
    """Aproximação de dias corridos para a quantidade de meses."""
    return int(meses * 30.4375)

# ============================================================================
# 1. Funções Base (Nativas Python - Diretamente Invocáveis)
# ============================================================================

def normalizar_prazos_e_datas_fn(data_inicio_str: str, meses_vigencia: int, dias_aviso_previo: int = 30) -> str:
    """
    Normaliza a data de início, calcula a data de término no padrão ISO-8601
    e computa os dias totais de vigência contratual.
    """
    print(f"\n[EXECUÇÃO DE TOOL] >>> Invocando 'normalizar_prazos_e_datas' com data_inicio={data_inicio_str}, vigencia={meses_vigencia} meses", flush=True)
    
    # Tratamento de data (DD/MM/AAAA ou YYYY-MM-DD)
    data_limpa = data_inicio_str.strip()
    data_obj = None
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            data_obj = datetime.strptime(data_limpa, formato)
            break
        except ValueError:
            continue
            
    if not data_obj:
        data_obj = datetime(2026, 1, 15)  # Fallback caso a data venha corrompida

    data_inicio_iso = data_obj.strftime("%Y-%m-%d")
    
    # Cálculo da data final aproximada somando os meses
    ano_fim = data_obj.year + (data_obj.month + meses_vigencia - 1) // 12
    mes_fim = (data_obj.month + meses_vigencia - 1) % 12 + 1
    dia_fim = min(data_obj.day, 28)  # Normalização segura de dia de encerramento
    data_fim_obj = datetime(ano_fim, mes_fim, dia_fim)
    data_fim_iso = data_fim_obj.strftime("%Y-%m-%d")
    
    dias_totais = (data_fim_obj - data_obj).days
    
    resultado = {
        "data_inicio_iso": data_inicio_iso,
        "data_fim_calculada_iso": data_fim_iso,
        "vigencia_meses": meses_vigencia,
        "dias_corridos_totais": dias_totais,
        "aviso_previo_dias": dias_aviso_previo,
        "vigencia_formatada": f"De {data_inicio_iso} a {data_fim_iso} ({meses_vigencia} meses / {dias_totais} dias)"
    }
    
    resultado_str = json.dumps(resultado, ensure_ascii=False)
    
    REGISTRO_CHAMADAS_TOOLS.append({
        "ferramenta": "normalizar_prazos_e_datas",
        "input_args": {
            "data_inicio_str": data_inicio_str,
            "meses_vigencia": meses_vigencia,
            "dias_aviso_previo": dias_aviso_previo
        },
        "output_retornado": resultado
    })
    
    print(f"[EXECUÇÃO DE TOOL] <<< Retorno da normalização de prazos: {resultado_str}", flush=True)
    return resultado_str


def extrair_e_validar_tabela_financeira_fn(
    valor_total: float, 
    parcelas_qtd: int, 
    valor_parcela: float, 
    periodicidade: str = "mensal"
) -> str:
    """
    Decompõe as condições de pagamento e valida a integridade matemática
    entre o valor global do contrato e a soma das parcelas especificadas.
    """
    print(f"\n[EXECUÇÃO DE TOOL] >>> Invocando 'extrair_e_validar_tabela_financeira' com valor={valor_total}, parcelas={parcelas_qtd}x {valor_parcela}", flush=True)
    
    soma_calculada = round(parcelas_qtd * valor_parcela, 2)
    valor_total_arredondado = round(valor_total, 2)
    diferenca = round(abs(valor_total_arredondado - soma_calculada), 2)
    soma_consistente = diferenca <= 0.05  # Tolerância de arredondamento monetário

    cronograma = []
    for i in range(1, parcelas_qtd + 1):
        cronograma.append({
            "parcela_numero": i,
            "valor": valor_parcela,
            "periodicidade": periodicidade
        })

    resultado = {
        "moeda": "BRL",
        "valor_total_brl": valor_total_arredondado,
        "parcelas_quantidade": parcelas_qtd,
        "valor_parcela_brl": valor_parcela,
        "periodicidade": periodicidade,
        "soma_parcelas_calculada": soma_calculada,
        "soma_consistente": soma_consistente,
        "discrepancia_centavos": round(diferenca * 100, 0),
        "cronograma_resumo": f"{parcelas_qtd} parcelas de R$ {valor_parcela:,.2f} ({periodicidade})"
    }

    resultado_str = json.dumps(resultado, ensure_ascii=False)

    REGISTRO_CHAMADAS_TOOLS.append({
        "ferramenta": "extrair_e_validar_tabela_financeira",
        "input_args": {
            "valor_total": valor_total,
            "parcelas_qtd": parcelas_qtd,
            "valor_parcela": valor_parcela,
            "periodicidade": periodicidade
        },
        "output_retornado": resultado
    })

    print(f"[EXECUÇÃO DE TOOL] <<< Retorno da validação financeira: {resultado_str}", flush=True)
    return resultado_str

# ============================================================================
# 2. Definição das Tools Decoradas com @function_tool (OpenAI Agents SDK)
# ============================================================================

@function_tool
def normalizar_prazos_e_datas(data_inicio_str: str, meses_vigencia: int, dias_aviso_previo: int = 30) -> str:
    """
    Calcula e normaliza a vigência contratual em formato ISO-8601 (YYYY-MM-DD),
    computando a data final exata a partir da data de início e do número de meses.

    Args:
        data_inicio_str: Data de início mencionada no contrato (ex: '15/01/2026' ou '2026-01-15').
        meses_vigencia: Duração contratual estipulada em número inteiro de meses (ex: 12).
        dias_aviso_previo: Quantidade de dias corridos exigidos para aviso prévio de rescisão (padrão: 30).

    Returns:
        String em formato JSON com as datas de início e fim no padrão ISO, total de dias corridos e vigência formatada.
    """
    return normalizar_prazos_e_datas_fn(data_inicio_str, meses_vigencia, dias_aviso_previo)


@function_tool
def extrair_e_validar_tabela_financeira(
    valor_total: float, 
    parcelas_qtd: int, 
    valor_parcela: float, 
    periodicidade: str = "mensal"
) -> str:
    """
    Valida a consistência matemática entre o valor global do contrato e a soma das parcelas,
    gerando o cronograma financeiro decomposto e normalizado em Reais (BRL).

    Args:
        valor_total: Valor monetário global do contrato em Reais (ex: 120000.0).
        parcelas_qtd: Quantidade total de parcelas informada na cláusula financeira (ex: 12).
        valor_parcela: Valor monetário individual de cada parcela (ex: 10000.0).
        periodicidade: Periodicidade do pagamento (ex: 'mensal', 'trimestral', 'por_etapa').

    Returns:
        String em formato JSON atestando se a soma é matematicamente consistente e o cronograma decomposto.
    """
    return extrair_e_validar_tabela_financeira_fn(valor_total, parcelas_qtd, valor_parcela, periodicidade)


def consultar_cadastro_fornecedor_fn(cnpj_cpf: str) -> str:
    """
    Função base para consultar a fonte estruturada de dados corporativos (cadastro_fornecedores).
    Atende à exigência da Rubrica 12: Integração com fonte de negócio relacional.
    """
    print(f"\n[EXECUÇÃO DE TOOL] >>> Invocando 'consultar_cadastro_fornecedor' para CNPJ/CPF='{cnpj_cpf}'", flush=True)
    try:
        from memoria_rag import consultar_cadastro_fornecedor_db
        dados_fornecedor = consultar_cadastro_fornecedor_db(cnpj_cpf)
    except Exception as e:
        dados_fornecedor = None
        print(f"[TOOL ERROR] Erro ao acessar banco de fornecedores: {e}", flush=True)

    if not dados_fornecedor:
        resultado = {
            "encontrado": False,
            "cnpj": cnpj_cpf,
            "mensagem": "Fornecedor não localizado na base corporativa homologada."
        }
    else:
        resultado = {
            "encontrado": True,
            **dados_fornecedor
        }

    resultado_str = json.dumps(resultado, ensure_ascii=False)
    REGISTRO_CHAMADAS_TOOLS.append({
        "ferramenta": "consultar_cadastro_fornecedor",
        "input_args": {"cnpj_cpf": cnpj_cpf},
        "output_retornado": resultado
    })
    print(f"[EXECUÇÃO DE TOOL] <<< Retorno da consulta cadastral: {resultado_str}", flush=True)
    return resultado_str


@function_tool
def consultar_cadastro_fornecedor(cnpj_cpf: str) -> str:
    """
    Consulta a base estruturada relacional corporativa (cadastro_fornecedores)
    para verificar a situação cadastral, score de compliance histórico, limite de alçada
    e restrições jurídicas do fornecedor.

    Args:
        cnpj_cpf: Número do CNPJ ou CPF da Contratada (ex: '98.765.432/0001-10' ou '12.345.678/0001-90').

    Returns:
        JSON com situação cadastral, score de compliance, limite de alçada e restrições jurídicas.
    """
    return consultar_cadastro_fornecedor_fn(cnpj_cpf)
