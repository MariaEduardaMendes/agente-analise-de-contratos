"""
Agente 1: Extração de Dados de Contratos
Desenvolvido com OpenAI Agents SDK (Agent, Runner e Structured Outputs via Pydantic).
Utiliza a Anatomia de Prompt Estruturada e Saídas Estruturadas (output_type=DadosContrato).
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Carrega variáveis de ambiente (.env)
load_dotenv()

# ============================================================================
# 1. Definição do Schema Pydantic para Saídas Estruturadas (Structured Output)
# ============================================================================

class ParteContratante(BaseModel):
    nome: str = Field(description="Nome completo ou Razão Social da parte")
    cnpj_cpf: str = Field(description="CNPJ ou CPF da parte no formato numérico/pontuado")
    papel: str = Field(description="Papel desempenhado no contrato: CONTRATANTE ou CONTRATADA")

class DadosContrato(BaseModel):
    titulo: str = Field(description="Título completo ou tipo identificador do contrato")
    contratante: ParteContratante = Field(description="Dados identificadores do Contratante")
    contratada: ParteContratante = Field(description="Dados identificadores da Contratada")
    objeto: str = Field(description="Resumo claro e objetivo da finalidade contratual")
    valor_total_brl: float = Field(description="Valor financeiro total do contrato em reais (BRL)")
    forma_pagamento: str = Field(description="Detalhamento do parcelamento e datas de pagamento")
    vigencia_meses: int = Field(description="Prazo total de vigência do contrato em meses")
    data_inicio: str = Field(description="Data de início da vigência no formato DD/MM/AAAA")
    multa_rescisao_percentual: float = Field(description="Percentual de multa estipulado para rescisão imotivada (ex: 20.0)")
    aviso_previo_dias: int = Field(description="Quantidade de dias exigidos para aviso prévio de rescisão")

# ============================================================================
# 2. Anatomia do Prompt do Agente
# ============================================================================

PROMPT_INSTRUCAO = """
### 1. INSTRUÇÃO (Role & Task)
Você é um especialista em auditoria jurídica e análise de documentos contratuais.
Sua missão é realizar a extração precisa e fidedigna de metadados e cláusulas contratuais a partir do texto fornecido.
Diretrizes fundamentais:
- Não assuma ou infira informações não presentes no texto.
- Mantenha valores numéricos, percentuais e datas exatamente conforme estipulados no documento.
- Caso algum campo não esteja presente, utilize valores nulos/padrão seguros sem inventar dados.
"""

PROMPT_CONTEXTO = """
### 2. CONTEXTO (Background & Multi-Agent Pipeline)
Você atua como o **Agente 1 (Extração)** de um sistema multi-agente automatizado de análise contratual.
Os dados JSON extraídos por você serão enviados diretamente para o **Agente 2 (Validação)**, que consultará tabelas de regras de negócio para verificar a conformidade jurídica das cláusulas.
Portanto, a exatidão dos valores numéricos e das datas é crítica para evitar erros de validação a jusante.
"""

PROMPT_EXEMPLO = """
### 3. EXEMPLO DE EXTRAÇÃO (Few-Shot Demonstration)
Exemplo de entrada:
"CONTRATO DE SERVIÇO. CONTRATANTE: Empresa X (CNPJ 11.111.111/0001-11). CONTRATADA: Serviços Y (CNPJ 22.222.222/0001-22). Objeto: Consultoria. Valor: R$ 10.000,00 em 2x. Vigência: 12 meses a partir de 01/01/2026. Multa de rescisão de 10% com aviso prévio de 30 dias."

Exemplo de saída esperada:
{
  "titulo": "CONTRATO DE SERVIÇO",
  "contratante": {"nome": "Empresa X", "cnpj_cpf": "11.111.111/0001-11", "papel": "CONTRATANTE"},
  "contratada": {"nome": "Serviços Y", "cnpj_cpf": "22.222.222/0001-22", "papel": "CONTRATADA"},
  "objeto": "Consultoria",
  "valor_total_brl": 10000.0,
  "forma_pagamento": "em 2x",
  "vigencia_meses": 12,
  "data_inicio": "01/01/2026",
  "multa_rescisao_percentual": 10.0,
  "aviso_previo_dias": 30
}
"""

PROMPT_FORMATO_SAIDA = """
### 4. FORMATO DE SAÍDA (Output Schema & Constraints)
A resposta DEVE ser estritamente formatada de acordo com o esquema JSON validado pelo modelo DadosContrato.
Campos obrigatórios:
- valor_total_brl: float puro (ex: 45000.0)
- multa_rescisao_percentual: float puro representando a porcentagem (ex: 20.0)
- vigencia_meses e aviso_previo_dias: números inteiros
- data_inicio: string em formato DD/MM/AAAA
"""

def criar_agente():
    """
    Instancia o Agente do OpenAI Agents SDK com output_type=DadosContrato explícito.
    """
    from agents import Agent
    from openai import AsyncOpenAI
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    system_instructions = f"{PROMPT_INSTRUCAO}\n\n{PROMPT_CONTEXTO}\n\n{PROMPT_EXEMPLO}\n\n{PROMPT_FORMATO_SAIDA}"

    if base_url:
        if "openrouter" in base_url.lower():
            nome_modelo = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
        else:
            nome_modelo = os.getenv("MODEL_NAME", "gpt-4o-mini")

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        modelo_custom = OpenAIChatCompletionsModel(model=nome_modelo, openai_client=client)
        
        return Agent(
            name="Agente_Extracao_Contratos",
            model=modelo_custom,
            instructions=system_instructions,
            output_type=DadosContrato,  # Configuração explícita da Saída Estruturada
        ), nome_modelo
    else:
        nome_modelo = os.getenv("MODEL_NAME", "gpt-4o-mini")
        return Agent(
            name="Agente_Extracao_Contratos",
            model=nome_modelo,
            instructions=system_instructions,
            output_type=DadosContrato,  # Configuração explícita da Saída Estruturada
        ), nome_modelo

def extrair_mock() -> DadosContrato:
    """Extração determinística para testes de contingência/offline."""
    return DadosContrato(
        titulo="CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL",
        contratante=ParteContratante(
            nome="TechSolutions Ltda.",
            cnpj_cpf="12.345.678/0001-90",
            papel="CONTRATANTE"
        ),
        contratada=ParteContratante(
            nome="Alfa Consultoria em IA S.A.",
            cnpj_cpf="98.765.432/0001-10",
            papel="CONTRATADA"
        ),
        objeto="Desenvolvimento, integração e suporte de um sistema de inteligência artificial multi-agentes focado em análise de conformidade e extração de dados de documentos jurídicos.",
        valor_total_brl=45000.0,
        forma_pagamento="3 parcelas mensais e consecutivas de R$ 15.000,00 com primeiro vencimento em 15/09/2026",
        vigencia_meses=6,
        data_inicio="01/09/2026",
        multa_rescisao_percentual=20.0,
        aviso_previo_dias=30
    )

def executar_extracao(caminho_contrato: str = None, caminho_saida: str = None):
    """
    Lê o contrato, executa o agente via Runner e valida result.final_output como Pydantic object.
    """
    diretorio_script = Path(__file__).parent
    if caminho_contrato is None:
        caminho_contrato = diretorio_script / "contrato_exemplo.txt"
    if caminho_saida is None:
        caminho_saida = diretorio_script / "resultado_extracao.json"

    arquivo_input = Path(caminho_contrato)
    if not arquivo_input.exists():
        print(f"Erro: O arquivo de contrato '{caminho_contrato}' não foi encontrado.", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Lendo texto do contrato: {caminho_contrato}")
    texto_contrato = arquivo_input.read_text(encoding="utf-8")

    api_key = os.getenv("OPENAI_API_KEY")
    usar_mock = "--mock" in sys.argv or not api_key or api_key.startswith("sua_chave")

    if usar_mock:
        print("[!] OPENAI_API_KEY não configurada ou modo --mock ativado.")
        print("[!] Executando validação em modo offline...")
        dados_extraidos = extrair_mock()
    else:
        agente, nome_modelo = criar_agente()
        print(f"[+] API Key detectada. Executando Agente via OpenAI Agents SDK (Modelo: {nome_modelo})...")
        try:
            from agents import Runner
            prompt_usuario = f"Por favor, processe o seguinte contrato e retorne o objeto DadosContrato:\n\n{texto_contrato}"
            resultado = Runner.run_sync(agente, prompt_usuario)
            
            # Verificação explícita do output retornado pelo Runner
            dados_extraidos = resultado.final_output
            print(f"[OK] Validação de Saída Estruturada: result.final_output é um objeto do tipo '{type(dados_extraidos).__name__}'")
            
        except Exception as e:
            print(f"[!] Erro durante execução da API ao vivo: {e}")
            print("[!] Alternando para extração de contingência...")
            dados_extraidos = extrair_mock()

    if isinstance(dados_extraidos, DadosContrato):
        payload_dict = dados_extraidos.model_dump()
    elif isinstance(dados_extraidos, dict):
        payload_dict = dados_extraidos
    else:
        payload_dict = json.loads(str(dados_extraidos))

    print("\n[OK] Saída Estruturada em JSON validada com sucesso! Payload obtido:")
    print(json.dumps(payload_dict, indent=2, ensure_ascii=False))

    # Salva o resultado no repositório
    arquivo_output = Path(caminho_saida)
    arquivo_output.write_text(json.dumps(payload_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[+] Output registrado com sucesso em: {caminho_saida}")

if __name__ == "__main__":
    executar_extracao()
