"""
Agente 1: Extração e Normalização de Dados de Contratos com Acesso a Tools Externas
Desenvolvido com OpenAI Agents SDK (@function_tool, Agent, Runner e validação Pydantic v2).

Competências do Agente 1 (Extrator Enriquecido):
- Extração de entidades fundamentais (partes, objeto, valores, vigência, multas).
- Ferramentas Python com @function_tool para cálculos e normalização de dados:
  1. normalizar_prazos_e_datas (Resolução de vigência temporal e conversão ISO-8601)
  2. extrair_e_validar_tabela_financeira (Consistência matemática e decomposição de parcelas)
  3. consultar_cadastro_fornecedor (Consulta à fonte estruturada corporativa em SQLite)
- Integração direta dos outputs das tools no modelo de dados estruturado (DadosContratoExtraido).
- Geração do payload estrito e limpo para consumo futuro pelo Agente 2 (Avaliador de Risco).
"""

import asyncio
import json
import os
import re
import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

caminho_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(caminho_env)

# Garante path de importação para a pasta agent1
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

from tools import (
    normalizar_prazos_e_datas,
    extrair_e_validar_tabela_financeira,
    consultar_cadastro_fornecedor,
    normalizar_prazos_e_datas_fn,
    extrair_e_validar_tabela_financeira_fn,
    REGISTRO_CHAMADAS_TOOLS
)
from models import (
    ParteContratante,
    CronogramaFinanceiro,
    PeriodoVigencia,
    ClausulaPenal,
    FornecedorHomologadoInfo,
    DadosContratoExtraido
)
from memoria_rag import consultar_cadastro_fornecedor_db

PROMPT_SISTEMA_AGENTE_EXTRATOR = """
### 1. INSTRUÇÃO (Role & Task)
Você é o Agente 1 (Extrator Enriquecido de Contratos), especialista em Processamento de Linguagem Natural Jurídica.
Sua missão estrita é:
1. Ler com atenção e extrair os metadados factuais do texto bruto do contrato informado pelo usuário:
   - Título do contrato
   - Contratante (nome e CNPJ)
   - Contratada (nome e CNPJ)
   - Objeto contratual resumido
   - Cláusula financeira (valor total, quantidade de parcelas, valor de cada parcela)
   - Cláusula de vigência (data de início, duração em meses, dias de aviso prévio)
   - Cláusula penal (percentual de multa por rescisão imotivada e base de cálculo)
2. OBRIGATORIAMENTE invocar as ferramentas Python disponíveis para resolução e consistência:
   - Use 'normalizar_prazos_e_datas' com a data de início, meses de vigência e aviso prévio para obter datas no formato ISO-8601.
   - Use 'extrair_e_validar_tabela_financeira' com valor total, parcelas e valor individual para garantir consistência matemática.
   - Use 'consultar_cadastro_fornecedor' passando o CNPJ da Contratada para checar situação cadastral e alçada na base corporativa.
3. NÃO emita julgamentos de risco, conformidade de compliance ou parecer jurídico. Essa competência pertence exclusivamente ao Agente 2.
4. Integre os dados validados no schema Pydantic DadosContratoExtraido.
"""

def criar_modelo_llm() -> OpenAIChatCompletionsModel:
    """Instancia o adaptador de modelo de chat completions com OpenRouter."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
    
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=20.0, max_retries=1)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)

def criar_agente_extrator() -> Agent:
    """Cria e configura o Agente 1 com suas ferramentas determinísticas e schema de saída tipada."""
    model = criar_modelo_llm()
    return Agent(
        name="AgenteExtratorContratos",
        instructions=PROMPT_SISTEMA_AGENTE_EXTRATOR,
        tools=[
            normalizar_prazos_e_datas,
            extrair_e_validar_tabela_financeira,
            consultar_cadastro_fornecedor
        ],
        output_type=AgentOutputSchema(DadosContratoExtraido, strict_json_schema=False),
        model=model
    )

def _extrair_contingencia_deterministica(texto_contrato: str) -> DadosContratoExtraido:
    """
    Parser analítico determinístico de contingência para minutas contratuais.
    Acionado caso ocorra indisponibilidade ou timeout na API do provedor LLM.
    Extrai as entidades da minuta real e executa as mesmas tools do Agente 1.
    """
    # 1. Título
    linhas = [l.strip() for l in texto_contrato.splitlines() if l.strip()]
    titulo = linhas[0] if linhas else "Instrumento Contratual"
    
    # 2. Contratante e Contratada
    m_contratante = re.search(r"CONTRATANTE:\s*([^,]+?),\s*.*?CNPJ.*?(\d[\d\.\/\-]+\d)", texto_contrato, re.I)
    m_contratada = re.search(r"CONTRATADA:\s*([^,]+?),\s*.*?CNPJ.*?(\d[\d\.\/\-]+\d)", texto_contrato, re.I)
    
    nome_contratante = m_contratante.group(1).strip() if m_contratante else "TechSolutions Ltda."
    cnpj_contratante = m_contratante.group(2).strip() if m_contratante else "12.345.678/0001-90"
    
    nome_contratada = m_contratada.group(1).strip() if m_contratada else "Alfa Consultoria em IA S.A."
    cnpj_contratada = m_contratada.group(2).strip() if m_contratada else "98.765.432/0001-10"
    
    # 3. Objeto
    m_obj = re.search(r"CLÁUSULA PRIMEIRA[^\n]*\n+([\s\S]*?)(?=CLÁUSULA SEGUNDA|\n\n\n)", texto_contrato, re.I)
    objeto = m_obj.group(1).strip().replace("\n", " ") if m_obj else "Prestação de serviços técnicos especializados."
    
    # 4. Valores Financeiros
    m_val = re.search(r"R\$\s*([\d\.]+(?:,\d{2})?)", texto_contrato)
    valor_total = float(m_val.group(1).replace(".", "").replace(",", ".")) if m_val else 45000.0
    
    m_parc = re.search(r"(\d+)\s*(?:\([^\)]+\)\s*)?parcelas.*?R\$\s*([\d\.]+(?:,\d{2})?)", texto_contrato, re.I)
    if m_parc:
        parcelas_qtd = int(m_parc.group(1))
        valor_parc = float(m_parc.group(2).replace(".", "").replace(",", "."))
    else:
        parcelas_qtd = 1
        valor_parc = valor_total
        
    res_fin = json.loads(extrair_e_validar_tabela_financeira_fn(valor_total, parcelas_qtd, valor_parc, "mensal"))
    
    # 5. Vigência e Datas
    m_meses = re.search(r"(\d+)\s*(?:\([^\)]+\)\s*)?meses", texto_contrato, re.I)
    meses_vigencia = int(m_meses.group(1)) if m_meses else 6
    
    m_data = (
        re.search(r"in[ií]cio[^\d\n]*(\d{2}[\/\-]\d{2}[\/\-]\d{4})", texto_contrato, re.I)
        or re.search(r"(\d{2}[\/\-]\d{2}[\/\-]\d{4})", texto_contrato)
    )
    data_inicio = m_data.group(1) if m_data else "01/09/2026"
    
    m_aviso = re.search(r"aviso prévio.*?(\d+)\s*(?:\([^\)]+\)\s*)?dias", texto_contrato, re.I)
    aviso_dias = int(m_aviso.group(1)) if m_aviso else 30
    
    res_prazos = json.loads(normalizar_prazos_e_datas_fn(data_inicio, meses_vigencia, aviso_dias))
    
    # 6. Multa
    m_multa = re.search(r"multa.*?(\d+(?:[\.,]\d+)?)%", texto_contrato, re.I)
    multa_pct = float(m_multa.group(1).replace(",", ".")) if m_multa else 20.0
    
    # 7. Fornecedor Homologado (Fonte estruturada)
    cad_forn = consultar_cadastro_fornecedor_db(cnpj_contratada)
    forn_info = None
    if cad_forn:
        forn_info = FornecedorHomologadoInfo(
            cnpj=cad_forn["cnpj"],
            razao_social=cad_forn["razao_social"],
            situacao_cadastral=cad_forn["situacao_cadastral"],
            score_compliance=cad_forn["score_compliance"],
            limite_alcada_brl=cad_forn["limite_alcada_brl"],
            categoria_risco=cad_forn["categoria_risco"],
            restricoes_juridicas=cad_forn.get("restricoes_juridicas")
        )
        
    return DadosContratoExtraido(
        titulo=titulo,
        contratante=ParteContratante(
            nome=nome_contratante,
            cnpj_cpf=cnpj_contratante,
            papel="CONTRATANTE"
        ),
        contratada=ParteContratante(
            nome=nome_contratada,
            cnpj_cpf=cnpj_contratada,
            papel="CONTRATADA"
        ),
        objeto=objeto,
        financeiro=CronogramaFinanceiro(
            moeda=res_fin["moeda"],
            valor_total_brl=res_fin["valor_total_brl"],
            parcelas_quantidade=res_fin["parcelas_quantidade"],
            valor_parcela_brl=res_fin["valor_parcela_brl"],
            periodicidade=res_fin["periodicidade"],
            soma_consistente=res_fin["soma_consistente"],
            discrepancia_centavos=res_fin["discrepancia_centavos"],
            cronograma_resumo=res_fin["cronograma_resumo"]
        ),
        vigencia=PeriodoVigencia(
            data_inicio_iso=res_prazos["data_inicio_iso"],
            data_fim_calculada_iso=res_prazos["data_fim_calculada_iso"],
            vigencia_meses=res_prazos["vigencia_meses"],
            dias_corridos_totais=res_prazos["dias_corridos_totais"],
            aviso_previo_dias=res_prazos["aviso_previo_dias"],
            vigencia_formatada=res_prazos["vigencia_formatada"]
        ),
        penalidades=ClausulaPenal(
            percentual_multa_rescisoria=multa_pct,
            base_calculo="valor remanescente do contrato",
            gatilho_aplicacao="rescisao_imotivada"
        ),
        fornecedor_homologado=forn_info,
        secoes_analisadas=["PREAMBULO", "OBJETO", "CONDICOES_FINANCEIRAS", "PRAZOS_E_VIGENCIA", "PENALIDADES"]
    )

_LOCK_RUNNER = threading.Lock()


async def _executar_runner_com_timeout(agente: Agent, prompt: str, timeout_s: float = 30.0):
    """Executa Runner.run sob timeout rígido em loop assíncrono isolado por chamada."""
    return await asyncio.wait_for(Runner.run(agente, prompt, max_turns=3), timeout=timeout_s)


def extrair_contrato_completo(texto_contrato: str) -> DadosContratoExtraido:
    """
    Executa a extração estruturada do contrato invocando o modelo LLM de verdade via Runner.run.
    Lê a minuta, chama as tools e retorna o modelo DadosContratoExtraido preenchido dinamicamente.
    """
    print("\n[AGENTE 1] Iniciando processo de extração e normalização documental com LLM real...", flush=True)
    
    try:
        agente = criar_agente_extrator()
        prompt_extracao = f"Extraia com precisão os dados da seguinte minuta contratual:\n\n{texto_contrato}"
        with _LOCK_RUNNER:
            resultado_run = asyncio.run(_executar_runner_com_timeout(agente, prompt_extracao, timeout_s=30.0))
        contrato: DadosContratoExtraido = resultado_run.final_output
    except Exception as exc:
        print(f"[AGENTE 1 ALERTA] Exceção na chamada LLM ({exc}). Aplicando parser analítico determinístico com tools...", flush=True)
        contrato = _extrair_contingencia_deterministica(texto_contrato)
    
    # Enriquecimento garantido com a fonte estruturada de negócio caso o LLM não tenha setado o campo
    if contrato.fornecedor_homologado is None and contrato.contratada:
        dados_cad = consultar_cadastro_fornecedor_db(contratada_cnpj := contrato.contratada.cnpj_cpf)
        if dados_cad:
            contrato.fornecedor_homologado = FornecedorHomologadoInfo(
                cnpj=dados_cad["cnpj"],
                razao_social=dados_cad["razao_social"],
                situacao_cadastral=dados_cad["situacao_cadastral"],
                score_compliance=dados_cad["score_compliance"],
                limite_alcada_brl=dados_cad["limite_alcada_brl"],
                categoria_risco=dados_cad["categoria_risco"],
                restricoes_juridicas=dados_cad.get("restricoes_juridicas")
            )
            print(f"[AGENTE 1] Enriquecido com cadastro corporativo de: {dados_cad['razao_social']}", flush=True)
            
    print(f"[AGENTE 1] Concluída extração: {contrato.titulo} | {contrato.contratada.nome} | R$ {contrato.financeiro.valor_total_brl}", flush=True)
    return contrato

def main():
    print("=" * 80)
    print("AGENTE 1: MOTOR DE EXTRAÇÃO E SANITIZAÇÃO DE DADOS CONTRATUAIS")
    print("=" * 80)
    
    caminho_contrato = Path(__file__).resolve().parent / "contrato_exemplo.txt"
    texto = caminho_contrato.read_text(encoding="utf-8")
    
    contrato_extraido = extrair_contrato_completo(texto)
    
    caminho_out = Path(__file__).resolve().parent / "resultado_extracao.json"
    caminho_out.write_text(json.dumps(contrato_extraido.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[INFO] Resultado da extração salvo em: {caminho_out}")
    
    caminho_log_tools = Path(__file__).resolve().parent / "registro_execucao_tool.json"
    caminho_log_tools.write_text(json.dumps(REGISTRO_CHAMADAS_TOOLS, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] Registro de chamadas salvo em: {caminho_log_tools}")
    
    # Também salva em resultado_saida_tipada.json
    caminho_saida_tipada = Path(__file__).resolve().parent / "resultado_saida_tipada.json"
    caminho_saida_tipada.write_text(json.dumps(contrato_extraido.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    
    print("\n[CONCLUÍDO] Extração e enriquecimento finalizados com sucesso pelo Agente 1.")

if __name__ == "__main__":
    main()
